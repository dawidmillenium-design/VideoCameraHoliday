import os, re, sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

DRY  = "--dry" in sys.argv
ROOT = os.path.dirname(os.path.abspath(__file__))
INDEX    = os.path.join(ROOT, "index.html")
CITY_DIR = os.path.join(ROOT, "city-through-the-lens")

SHELL_CSS = '<link rel="stylesheet" href="/VideoCameraHoliday/assets/site-shell.css">'
SHELL_JS  = '<script src="/VideoCameraHoliday/assets/site-shell.js" defer></script>'

with open(INDEX, encoding="utf-8") as f:
    index_html = f.read()

m_nav  = re.search(r"<nav\b[^>]*>.*?</nav>", index_html, re.S)
m_foot = re.search(r"<footer\b[^>]*>.*?</footer>", index_html, re.S)
if not m_nav:
    sys.exit("ERROR: <nav> not found in index.html")

nav    = m_nav.group(0)
footer = m_foot.group(0) if m_foot else ""

def fix_names(text):
    text = text.replace("DJI Osmo Pocket 3", "DJI Osmo Pocket 4P")
    text = text.replace("Dji Osmo Pocket 3", "DJI Osmo Pocket 4P")
    text = text.replace("DJI Pocket 3", "DJI Pocket 4P")
    text = text.replace("Dji Pocket 3", "DJI Pocket 4P")
    text = text.replace("dji-osmo-pocket-3-review.html", "dji-osmo-pocket-4p-review.html")
    text = text.replace("dji-pocket-3-vs-gopro-hero-13.html", "dji-pocket-4p-vs-gopro-hero-13-black.html")
    text = re.sub(r"GoPro Hero 13(?! Black)", "GoPro Hero 13 Black", text)
    text = re.sub(r"gopro-hero-13(?!-black)", "gopro-hero-13-black", text)
    return text

nav, footer = fix_names(nav), fix_names(footer)
nav = nav.replace('href="/VideoCameraHoliday/" class="active"', 'href="/VideoCameraHoliday/"')
nav = nav.replace('href="/VideoCameraHoliday/city-through-the-lens/">',
                  'href="/VideoCameraHoliday/city-through-the-lens/" class="active">')

def city_title(fname):
    base = os.path.splitext(fname)[0]
    for s in ("-interview-preview", "-interview", "-preview", "-guide", "-filming-guide"):
        base = base.replace(s, "")
    return base.replace("-", " ").strip().title()

fixed, mismatches = 0, []

for fname in sorted(os.listdir(CITY_DIR)):
    if not fname.endswith(".html"):
        continue
    path = os.path.join(CITY_DIR, fname)
    with open(path, encoding="utf-8") as f:
        html = f.read()
    original = html

    html = re.sub(r"<nav\b[^>]*>.*?</nav>", lambda m: nav, html, count=1, flags=re.S)
    if re.search(r"<footer\b", html, re.S):
        html = re.sub(r"<footer\b[^>]*>.*?</footer>", lambda m: footer, html, count=1, flags=re.S)
    elif footer:
        html = html.replace("</body>", footer + "\n</body>", 1)

    html = re.sub(r"<link[^>]*site-shell\.css[^>]*>", "", html)
    if "/assets/site-shell.css" not in html:
        html = html.replace("</head>", SHELL_CSS + "\n</head>", 1)
    html = re.sub(r"<script[^>]*site-shell\.js[^>]*>\s*</script>", "", html)
    if "site-shell.js" not in html:
        html = html.replace("</body>", SHELL_JS + "\n</body>", 1)

    if fname != "index.html" and 'class="breadcrumb"' not in html:
        crumb = ('<nav class="breadcrumb" aria-label="Breadcrumb">\n'
                 '  <a href="/VideoCameraHoliday/">Home</a><span class="sep">&#8250;</span>\n'
                 '  <a href="/VideoCameraHoliday/city-through-the-lens/">City Through the Lens</a>'
                 '<span class="sep">&#8250;</span>\n'
                 '  <span class="current">' + city_title(fname) + '</span>\n'
                 '</nav>')
        html = html.replace("</nav>", "</nav>\n" + crumb, 1)

    html = fix_names(html)

    if fname != "index.html":
        tokens = [t for t in os.path.splitext(fname)[0].replace("-", " ").split()
                  if t not in ("city", "interview", "preview", "guide", "the", "filming")]
        h1 = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S)
        h1_text = re.sub(r"<[^>]+>", " ", h1.group(1)).lower() if h1 else ""
        if tokens and any(t not in h1_text for t in tokens):
            mismatches.append((fname, h1.group(1).strip() if h1 else "(no H1)"))

    if html != original:
        fixed += 1
        if not DRY:
            with open(path, "w", encoding="utf-8") as f:
                f.write(html)

print(("[DRY RUN] " if DRY else "") + "City pages repaired: %d" % fixed)
if mismatches:
    print("")
    print("[WARN] CONTENT MISMATCH - filename does not match H1 (manual fix needed):")
    for fname, h1 in mismatches:
        print("   " + fname)
        print("      -> H1: " + h1)
        print("")
else:
    print("[OK] No filename/H1 mismatches detected.")