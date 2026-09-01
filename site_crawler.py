#!/usr/bin/env python3
"""
site_crawler.py

Crawl the published site and report broken links.

Usage:
  1. python -m venv .venv && source .venv/bin/activate
  2. pip install requests beautifulsoup4 lxml
  3. python site_crawler.py

Outputs:
  - report.csv
  - report.json

Notes:
  - Respects only the SITE_DOMAIN and SITE_PATH_PREFIX below.
  - Use MAX_PAGES to limit crawl size while testing.
"""
import re
import json
import csv
import time
from urllib.parse import urlparse, urljoin, urldefrag
from collections import deque
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuration
SITE_DOMAIN = "dawidmillenium-design.github.io"
SITE_PATH_PREFIX = "/VideoCameraHoliday"
SEED = f"https://{SITE_DOMAIN}{SITE_PATH_PREFIX}/"
HEADERS = {"User-Agent": "LinkChecker/1.0 (+https://github.com/)"}
MAX_WORKERS = 10
MAX_PAGES = 2000  # set to None or large number to crawl whole site
HTTP_TIMEOUT = 8
OUTPUT_CSV = "report.csv"
OUTPUT_JSON = "report.json"

# Tags/attributes to extract
TAG_ATTRS = [
    ("a", "href"),
    ("img", "src"),
    ("script", "src"),
    ("link", "href"),
    ("source", "src"),
    ("iframe", "src"),
    ("video", "src"),
    ("audio", "src"),
    ("embed", "src"),
]

def same_site(url):
    try:
        p = urlparse(url)
        if p.scheme not in ('http', 'https'):
            return False
        return p.netloc.lower() == SITE_DOMAIN and p.path.startswith(SITE_PATH_PREFIX)
    except Exception:
        return False

def normalize_url(base, link):
    if not link:
        return None
    link = link.strip()
    # ignore mailto:, javascript:, tel:
    if link.startswith(("mailto:", "javascript:", "tel:")):
        return None
    # remove fragments
    link, _ = urldefrag(link)
    # join relative URLs
    full = urljoin(base, link)
    return full

def fetch(url):
    try:
        r = requests.head(url, allow_redirects=True, timeout=HTTP_TIMEOUT, headers=HEADERS)
        code = r.status_code
        # some servers respond 405/501 to HEAD; use GET fallback
        if code in (405, 501, 400) or code == 0 or code >= 400 and r.request.method.lower() == 'head':
            r = requests.get(url, allow_redirects=True, timeout=HTTP_TIMEOUT, headers=HEADERS)
            code = r.status_code
        # We return text for HTML pages to parse
        ct = r.headers.get("Content-Type","")
        text = r.text if 'html' in ct.lower() else None
        return code, text
    except Exception as e:
        return None, None

def parse_links(html, base_url):
    links = []
    soup = BeautifulSoup(html or "", "lxml")
    for tag, attr in TAG_ATTRS:
        for t in soup.find_all(tag):
            val = t.get(attr)
            if val:
                links.append((val, tag, attr, str(t)[:200]))
    # meta og:image
    for m in soup.find_all("meta"):
        if m.get("property","").lower() in ("og:image","og:image:url") and m.get("content"):
            links.append((m.get("content"), "meta", "content", "meta-og-image"))
    # JSON-LD
    for script in soup.find_all("script", {"type":"application/ld+json"}):
        try:
            parsed = json.loads(script.string or "{}")
        except Exception:
            # try to extract URLs with regex fallback
            for u in re.findall(r'https?://[^"\s\']+', script.string or ""):
                links.append((u, "json-ld", "raw", "jsonld-regex"))
            continue
        def collect(obj):
            if isinstance(obj, dict):
                for k,v in obj.items():
                    if isinstance(v, str) and (k in ("@id","url","mainEntityOfPage") or v.startswith("http")):
                        links.append((v, "json-ld", k, "json-ld"))
                    else:
                        collect(v)
            elif isinstance(obj, list):
                for i in obj:
                    collect(i)
        collect(parsed)
    # dedupe preserving order
    seen = set()
    out = []
    for l in links:
        if l[0] not in seen:
            seen.add(l[0])
            out.append(l)
    return out

def crawl():
    visited_pages = set()
    queue = deque([SEED])
    results = []
    in_progress = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {}
        while queue or futures:
            # submit job if we can
            while queue and len(futures) < MAX_WORKERS and (MAX_PAGES is None or len(visited_pages) < MAX_PAGES):
                url = queue.popleft()
                if url in visited_pages:
                    continue
                visited_pages.add(url)
                futures[executor.submit(fetch, url)] = url
            if not futures:
                break
            # wait for any future to complete
            done, _ = as_completed(futures).__next__(), None
            # actually as_completed above isn't correct to get single; use pop after iterating
            # Instead process completed futures in a loop
            completed = []
            for fut in list(futures.keys()):
                if fut.done():
                    completed.append(fut)
            if not completed:
                time.sleep(0.1)
                continue
            for fut in completed:
                url = futures.pop(fut)
                code, text = fut.result()
                results.append({
                    "source": url,
                    "tag": "page",
                    "attribute": "fetch",
                    "target": url,
                    "resolved": url,
                    "http_status": code,
                    "note": "page-fetch"
                })
                if text:
                    links = parse_links(text, url)
                    for raw, tag, attr, snippet in links:
                        norm = normalize_url(url, raw)
                        if not norm:
                            # ignored (mailto/javascript/tel)
                            results.append({
                                "source": url,
                                "tag": tag,
                                "attribute": attr,
                                "target": raw,
                                "resolved": None,
                                "http_status": None,
                                "note": "skipped-non-http"
                            })
                            continue
                        code_t, _ = None, None
                        # If same site and within prefix, schedule crawling the page if it's HTML
                        if same_site(norm):
                            # schedule fetch of the target page for crawling if it's an HTML page and not visited
                            if norm not in visited_pages and (MAX_PAGES is None or len(visited_pages) < MAX_PAGES):
                                queue.append(norm)
                        # check the link status (HEAD/GET)
                        code_t, _ = fetch(norm)
                        results.append({
                            "source": url,
                            "tag": tag,
                            "attribute": attr,
                            "target": raw,
                            "resolved": norm,
                            "http_status": code_t,
                            "note": "link-check"
                        })
            # loop continues until no more futures and queue exhausted
    return results

def save(results):
    # save CSV
    fieldnames = ["source","tag","attribute","target","resolved","http_status","note"]
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as cf:
        writer = csv.DictWriter(cf, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow(r)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as jf:
        json.dump(results, jf, indent=2, ensure_ascii=False)
    print(f"Wrote {len(results)} rows to {OUTPUT_CSV} and {OUTPUT_JSON}")

if __name__ == "__main__":
    print("Starting crawl from:", SEED)
    res = crawl()
    save(res)
    print("Done.")
