---
name: web-extraction
description: "Extract structured data from web pages via natural language."
version: 0.1.0
author: Terrance (tee), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Web, Extraction, Scraping, AgentQL, Data, AI]
    related_skills: [competitor-news-monitor, arxiv]
---

# Structured Web Extraction

Extract structured data from any dynamic or authenticated web page using AgentQL queries and natural language extraction prompts.

---

## 1. Quick Reference

| Task | Method | Example |
|---|---|---|
| **Natural Language Extract** | AgentQL API / Python | `python scripts/agentql_extract.py --url "https://example.com" --prompt "List all article titles and dates"` |
| **AgentQL Query File** | AgentQL SDK | `agentql query -u "https://news.ycombinator.com" -f query.aql` |
| **Hermes Web Extract** | Built-in tool | `web_extract(urls=["https://example.com"], prompt="...")` |

---

## 2. Using the AgentQL Extraction Script

Run extraction directly from the terminal or subagents:

```bash
# Extract products and pricing from an e-commerce page
python skills/research/web-extraction/scripts/agentql_extract.py \
  --url "https://news.ycombinator.com" \
  --prompt "Extract the top 10 stories with title, url, points, and author" \
  --output stories.json
```

---

## 3. Query Language Syntax (AQL)

For precise extraction, AgentQL queries use a GraphQL-like syntax:

```graphql
{
    stories[] {
        title
        link
        score(points)
        by(author)
    }
}
```
