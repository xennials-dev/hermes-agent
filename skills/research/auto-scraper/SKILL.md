---
name: auto-scraper
description: "Crawl paginated websites and compile structured datasets."
version: 0.1.0
author: Terrance (tee), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Scraping, Crawler, Automation, Pagination, Datasets, Research]
    related_skills: [web-extraction, competitor-news-monitor]
---

# Automated Multi-Page Scraper

Crawl and scrape paginated listings, directory tables, job boards, and news catalogs into structured JSON and CSV datasets.

---

## 1. Scraping Pattern

When scraping paginated or catalog pages:

1. **Discover Pagination**: Identify next-page URLs, cursor params, or page index (`?page=1`, `?page=2`).
2. **Batch Extract**: Loop over target URLs using `agentql_extract.py` or `web_extract`.
3. **Deduplicate**: Deduplicate records by unique key (e.g. `url`, `id`, `sku`).
4. **Export**: Save compiled dataset to JSON/CSV in the workspace.

---

## 2. Scraping Loop Example

```bash
# Extract catalog pages into dataset
for page in $(seq 1 3); do
  python skills/research/web-extraction/scripts/agentql_extract.py \
    --url "https://example.com/items?page=${page}" \
    --prompt "Extract list of items with title, price, and category" \
    --output "items_page_${page}.json"
done
```
