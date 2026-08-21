---
name: bigset-datasets
description: "Query and store live web datasets in BigSet OSS."
version: 0.1.0
author: Terrance (tee), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [BigSet, Datasets, TinyFish, Knowledge, Storage, Research]
    related_skills: [web-extraction, auto-scraper]
---

# BigSet Live Datasets

Query, publish, and sync dynamic web datasets with BigSet OSS self-hosted instances.

---

## 1. Quick Reference

| Action | Command |
|---|---|
| **Query Dataset** | `curl -s "http://localhost:8000/api/v1/datasets/search?q=QUERY"` |
| **Ingest JSON** | `curl -X POST "http://localhost:8000/api/v1/datasets/ingest" -H "Content-Type: application/json" -d @data.json` |

---

## 2. Ingesting AgentQL Results into BigSet

When Hermes scrapes structured data using AgentQL, it can push records directly to BigSet:

```bash
# 1. Scrape structured data
python skills/research/web-extraction/scripts/agentql_extract.py \
  --url "https://news.ycombinator.com" \
  --prompt "Extract tech headlines" \
  --output news.json

# 2. Push to local BigSet instance
curl -X POST "http://localhost:8000/api/v1/datasets/news/records" \
  -H "Content-Type: application/json" \
  -d @news.json
```
