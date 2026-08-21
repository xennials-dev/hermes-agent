---
name: shopping-comparison
description: "Compare product prices and specs across e-commerce sites."
version: 0.1.0
author: Terrance (tee), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Shopping, E-commerce, Comparison, Prices, Research, AgentQL]
    related_skills: [web-extraction, competitor-news-monitor]
---

# Multi-Store Shopping & Price Comparison

Search and compare product pricing, availability, ratings, and specifications across multiple online retailers using structured extraction.

---

## 1. Quick Workflow

1. **Identify Product Targets**: Determine query terms, models, or specific product URLs (Amazon, eBay, Best Buy, Walmart).
2. **Extract Normalized Data**: Extract structured fields:
   - `product_name`
   - `price` (currency + numeric value)
   - `in_stock` (boolean / status)
   - `rating` & `reviews_count`
   - `shipping_cost` / delivery date
3. **Aggregate & Compare**: Rank by total landed cost and highlight best deals.

---

## 2. Command Examples

```bash
# Extract price and stock details from Amazon
python skills/research/web-extraction/scripts/agentql_extract.py \
  --url "https://www.amazon.com/dp/B0CX23V2ZH" \
  --prompt "Extract product name, current price, rating, stock status, and prime delivery options"
```

---

## 3. Comparison Matrix Format

Present findings to the user using Markdown comparison tables:

| Store | Item Title | Price | Shipping | In Stock | Rating | Direct Link |
|---|---|---|---|---|---|---|
| Amazon | Model X Pro | $299.99 | Free (Prime) | Yes | 4.6 (1.2k) | [Link](...) |
| Best Buy | Model X Pro | $289.99 | $5.99 | Yes | 4.7 (400) | [Link](...) |
| B&H | Model X Pro | $299.00 | Free | Backordered | 4.8 (89) | [Link](...) |
