#!/usr/bin/env python3
"""Generate every camera pair, plus sitemap and comparison-hub entries."""

from __future__ import annotations

import argparse
import csv
import html
import json
import re
from itertools import combinations
from pathlib import Path


BASE_URL = "https://dawidmillenium-design.github.io/VideoCameraHoliday/"
FALLBACK_IMAGE = BASE_URL + "media/cameras.jpg"
START_MARKER = "<!-- BEGIN GENERATED CAMERA COMPARISONS -->"
END_MARKER = "<!-- END GENERATED CAMERA COMPARISONS -->"
REQUIRED_COLUMNS = {
    "id", "name", "brand", "type", "sensor", "resolution", "video_max",
    "weight", "price_pln", "rating", "image_url", "pros", "cons",
    "best_for", "review_url",
}


def e(value: object) -> str:
    return html.escape(str(value), quote=True)


def list_html(value: str) -> str:
    return "".join(f"<li>{e(item.strip())}</li>" for item in value.split(",") if item.strip())


def replace_block(path: Path, body: str, indent: str) -> None:
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER), re.DOTALL)
    replacement = START_MARKER + "\n" + body.rstrip() + "\n" + indent + END_MARKER
    updated, count = pattern.subn(replacement, text, count=1)
    if count != 1:
        raise ValueError(f"Generated block markers not found exactly once in {path}")
    path.write_text(updated, encoding="utf-8", newline="\n")


def load_cameras(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError("CSV header is missing")
        missing = REQUIRED_COLUMNS.difference(reader.fieldnames)
        if missing:
            raise ValueError(f"Missing CSV columns: {', '.join(sorted(missing))}")
        cameras = list(reader)
    if len(cameras) < 2:
        raise ValueError("At least two camera rows are required")
    ids: set[str] = set()
    for camera in cameras:
        camera_id = camera["id"]
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", camera_id):
            raise ValueError(f"Invalid id {camera_id!r}; use lowercase kebab-case")
        if camera_id in ids:
            raise ValueError(f"Duplicate camera id: {camera_id}")
        ids.add(camera_id)
        float(camera["price_pln"])
        rating = float(camera["rating"])
        if not 0 <= rating <= 5:
            raise ValueError(f"Rating for {camera_id} must be between 0 and 5")
    return cameras


def schema(a: dict[str, str], b: dict[str, str], title: str, description: str, canonical: str) -> str:
    data = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": title,
        "description": description,
        "url": canonical,
        "inLanguage": "pl-PL",
        "breadcrumb": {
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Strona główna", "item": BASE_URL},
                {"@type": "ListItem", "position": 2, "name": "Porównania", "item": BASE_URL + "comparisons/"},
                {"@type": "ListItem", "position": 3, "name": f'{a["name"]} vs {b["name"]}', "item": canonical},
            ],
        },
        "mainEntity": {
            "@type": "ItemList",
            "numberOfItems": 2,
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "item": {"@type": "Product", "name": a["name"], "brand": {"@type": "Brand", "name": a["brand"]}, "image": FALLBACK_IMAGE}},
                {"@type": "ListItem", "position": 2, "item": {"@type": "Product", "name": b["name"], "brand": {"@type": "Brand", "name": b["brand"]}, "image": FALLBACK_IMAGE}},
            ],
        },
    }
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"), sort_keys=False)
    return f'<script type="application/ld+json">{payload}</script>'


def render_pair(template: str, a: dict[str, str], b: dict[str, str]) -> tuple[str, str, str]:
    filename = f'{a["id"]}-vs-{b["id"]}.html'
    relative_url = f"guides/{filename}"
    canonical = BASE_URL + relative_url
    title = f'{a["name"]} vs {b["name"]} – porównanie 2026'
    description = (
        f'Porównaj {a["name"]} i {b["name"]}: ceny, matryce, jakość wideo, wagę, '
        "zalety i wady. Sprawdź, który model lepiej pasuje do Twoich podróży."
    )
    rating_a, rating_b = float(a["rating"]), float(b["rating"])
    price_a, price_b = float(a["price_pln"]), float(b["price_pln"])
    if rating_a > rating_b:
        rating_verdict = f'{a["name"]} ({a["rating"]}/5,0)'
    elif rating_b > rating_a:
        rating_verdict = f'{b["name"]} ({b["rating"]}/5,0)'
    else:
        rating_verdict = f'Remis – oba modele mają ocenę {a["rating"]}/5,0'

    def review_link(camera: dict[str, str]) -> str:
        url = camera["review_url"].strip()
        return f'<a href="{e(url)}" class="btn">Pełna recenzja</a>' if url else ""

    values = {
        "{{TITLE}}": e(title),
        "{{META_DESC}}": e(description),
        "{{CANONICAL_URL}}": e(canonical),
        "{{JSON_LD}}": schema(a, b, title, description, canonical),
        "{{CAMERA_A}}": e(a["name"]), "{{CAMERA_B}}": e(b["name"]),
        "{{SUBTITLE}}": e(f'Porównanie parametrów, ceny oraz zastosowań: {a["best_for"]} kontra {b["best_for"]}.'),
        "{{IMG_A}}": e(a["image_url"]), "{{IMG_B}}": e(b["image_url"]),
        "{{RATING_A}}": e(a["rating"]), "{{RATING_B}}": e(b["rating"]),
        "{{PRICE_A}}": e(a["price_pln"]), "{{PRICE_B}}": e(b["price_pln"]),
        "{{PROS_A_HTML}}": list_html(a["pros"]), "{{PROS_B_HTML}}": list_html(b["pros"]),
        "{{CONS_A_HTML}}": list_html(a["cons"]), "{{CONS_B_HTML}}": list_html(b["cons"]),
        "{{REVIEW_LINK_A_HTML}}": review_link(a), "{{REVIEW_LINK_B_HTML}}": review_link(b),
        "{{TYPE_A}}": e(a["type"]), "{{TYPE_B}}": e(b["type"]),
        "{{SENSOR_A}}": e(a["sensor"]), "{{SENSOR_B}}": e(b["sensor"]),
        "{{RESOLUTION_A}}": e(a["resolution"]), "{{RESOLUTION_B}}": e(b["resolution"]),
        "{{VIDEO_A}}": e(a["video_max"]), "{{VIDEO_B}}": e(b["video_max"]),
        "{{WEIGHT_A}}": e(a["weight"]), "{{WEIGHT_B}}": e(b["weight"]),
        "{{BEST_A}}": e(a["best_for"]), "{{BEST_B}}": e(b["best_for"]),
        "{{VERDICT_A}}": e(f'priorytetem jest {a["best_for"]}.'),
        "{{VERDICT_B}}": e(f'priorytetem jest {b["best_for"]}.'),
        "{{RATING_VERDICT}}": e(rating_verdict),
        "{{PRICE_CLASS_A}}": "winner" if price_a <= price_b else "",
        "{{PRICE_CLASS_B}}": "winner" if price_b <= price_a else "",
        "{{RATING_CLASS_A}}": "winner" if rating_a >= rating_b else "",
        "{{RATING_CLASS_B}}": "winner" if rating_b >= rating_a else "",
    }
    content = template
    for placeholder, value in values.items():
        content = content.replace(placeholder, value)
    unresolved = sorted(set(re.findall(r"\{\{[A-Z0-9_]+\}\}", content)))
    if unresolved:
        raise ValueError(f"Unresolved placeholders in {filename}: {', '.join(unresolved)}")
    return filename, relative_url, content


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default="cameras.csv")
    parser.add_argument("--template", default="comparison_template.html")
    parser.add_argument("--output-dir", default="guides")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    csv_path = Path(args.csv).resolve() if Path(args.csv).is_absolute() else root / args.csv
    template_path = Path(args.template).resolve() if Path(args.template).is_absolute() else root / args.template
    output_dir = Path(args.output_dir).resolve() if Path(args.output_dir).is_absolute() else root / args.output_dir
    cameras = load_cameras(csv_path)
    template = template_path.read_text(encoding="utf-8")
    output_dir.mkdir(parents=True, exist_ok=True)

    urls: list[str] = []
    cards: list[str] = []
    expected: set[Path] = set()
    for a, b in combinations(cameras, 2):
        filename, relative_url, content = render_pair(template, a, b)
        target = output_dir / filename
        target.write_text(content, encoding="utf-8", newline="\n")
        expected.add(target.resolve())
        canonical = BASE_URL + relative_url
        urls.append(f"    <url><loc>{e(canonical)}</loc><changefreq>monthly</changefreq><priority>0.7</priority></url>")
        cards.append(
            f'''            <a class="comp-card" href="/VideoCameraHoliday/{e(relative_url)}">
                <div class="vs-icon">📷⚔️🎥 <span>PL</span></div>
                <h3>{e(a["name"])} vs {e(b["name"])}</h3>
                <p>Porównanie ceny, parametrów wideo, wagi oraz najlepszych zastosowań.</p>
                <div class="badge-group"><span class="badge badge-new">2026</span><span class="badge">Polski</span></div>
            </a>'''
        )
        print(f"Generated: {relative_url}")

    camera_ids = {camera["id"] for camera in cameras}
    for candidate in output_dir.glob("*-vs-*.html"):
        if candidate.resolve() not in expected and any(candidate.name.startswith(camera_id + "-vs-") for camera_id in camera_ids):
            candidate.unlink()

    replace_block(root / "sitemap.xml", "\n".join(urls), "    ")
    replace_block(root / "comparisons/index.html", "\n\n".join(cards), "            ")
    print(f"Success! Generated {len(expected)} comparison pages and refreshed the hub and sitemap.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
