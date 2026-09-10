#!/usr/bin/env python3
"""Validate canonical and hreflang consistency without grouping unrelated pages."""
import json
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlparse
from bs4 import BeautifulSoup

BASE_URL = "https://dawidmillenium-design.github.io/VideoCameraHoliday/"
SCAN_DIRS = ["comparisons","es-ES","fr-FR","de-DE","de","es","ja-JP","ko-KR","zh-CN","pl-PL","th-TH","it-IT","guides","how-to","destinations","reviews"]

def page_url(path):
    return BASE_URL + path.as_posix()

def clean(url):
    return (url or "").rstrip("/")

def scan():
    groups=defaultdict(list)
    for directory in SCAN_DIRS:
        root=Path(directory)
        if not root.exists(): continue
        for path in root.rglob("*.html"):
            if path.name.startswith("index") or "metadata" in path.name: continue
            groups[path.stem].append(path)
    return groups

def inspect(path):
    soup=BeautifulSoup(path.read_text(encoding="utf-8",errors="replace"),"lxml")
    lang=(soup.html.get("lang","") if soup.html else "").strip()
    canonical=soup.find("link",rel="canonical")
    canonical_url=canonical.get("href","") if canonical else ""
    alternates={}
    for tag in soup.find_all("link",rel="alternate",hreflang=True):
        if tag.get("href"): alternates[tag["hreflang"]]=tag["href"]
    return {"path":path.as_posix(),"url":page_url(path),"lang":lang,"canonical":canonical_url,"alternates":alternates}

def main():
    results={"total_groups":0,"consistent_groups":0,"inconsistent_groups":0,"issues":[]}
    for slug,paths in scan().items():
        pages=[inspect(p) for p in paths]
        issues=[]
        for page in pages:
            if not page["canonical"]:
                issues.append(f'{page["path"]}: Missing canonical tag')
        self_canonical=[p for p in pages if clean(p["canonical"])==clean(p["url"])]
        languages={p["lang"] for p in self_canonical if p["lang"]}
        is_translation_group=len(self_canonical)>1 and len(languages)>1
        if is_translation_group:
            alternate_sets=[set(page["alternates"]) for page in self_canonical]
            expected=set().union(*alternate_sets)
            if "x-default" not in expected:
                issues.append(f"{slug}: Missing x-default from translation cluster")
            for page in self_canonical:
                found=set(page["alternates"])
                if found!=expected:
                    issues.append(f'{page["path"]}: hreflang set {sorted(found)}; expected {sorted(expected)}')
            target_by_lang={p["lang"]:clean(p["url"]) for p in self_canonical}
            for page in self_canonical:
                for lang,target in target_by_lang.items():
                    if clean(page["alternates"].get(lang))!=target:
                        issues.append(f'{page["path"]}: {lang} does not point to {target}')
                if not page["alternates"].get("x-default"):
                    issues.append(f'{page["path"]}: Missing x-default')
        results["total_groups"]+=1
        if issues:
            results["inconsistent_groups"]+=1
            results["issues"].append({"slug":slug,"reason":" | ".join(issues)})
        else:
            results["consistent_groups"]+=1
    Path("hreflang-validation-report.json").write_text(json.dumps(results,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("🌐 Hreflang validation")
    print(f'Total Groups: {results["total_groups"]}')
    print(f'Consistent: {results["consistent_groups"]}')
    print(f'Inconsistent: {results["inconsistent_groups"]}')
    if results["inconsistent_groups"]: raise SystemExit(1)

if __name__=="__main__": main()
