# Programmatic camera comparisons

The repository generates every unique camera pair from `cameras.csv`. Six rows produce 15 pages; adding a seventh row produces 21.

## Generate locally

PowerShell:

```powershell
./generate_comparisons.ps1
```

Python 3:

```bash
python3 tools/generate_comparisons.py
```

Both commands create the pages in `guides/`, refresh the generated cards in `comparisons/index.html`, and refresh the generated URL block in `sitemap.xml`.

After editing the CSV or template, run the generator and then validate the site:

```bash
python3 tools/check_internal_links.py
```

The GitHub workflow repeats these checks on pull requests. On `main`, it regenerates and commits stale generated output automatically.

## CSV rules

- Keep `id` unique and in lowercase kebab-case.
- Quote values that contain commas or inch marks.
- Use a repository-relative `review_url`; leave it empty when no matching review exists.
- Ratings must be between 0 and 5.
- Prices must be numeric PLN values without currency symbols.

Generated pages use canonical GitHub Pages URLs under `/VideoCameraHoliday/`. Missing product images fall back to the repository's local `media/cameras.jpg` image.
