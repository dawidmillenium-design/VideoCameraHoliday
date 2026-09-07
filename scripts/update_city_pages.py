name: Update City Pages (Breadcrumbs & Schema)

on:
  # Allows you to run this workflow manually from the Actions tab
  workflow_dispatch:

# Grant permissions to push changes back to the repository
permissions:
  contents: write

jobs:
  update-pages:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Run City Page Update Script
        run: |
          echo "🚀 Starting city page updates..."
          python scripts/update_city_pages.py
        continue-on-error: false

      - name: Commit and Push Changes
        uses: stefanzweifel/git-auto-commit-action@v5
        with:
          commit_message: "feat: auto-inject breadcrumbs and JSON-LD schema into 50+ city pages"
          file_pattern: "city-through-the-lens/*.html"
          commit_options: "--no-verify"
