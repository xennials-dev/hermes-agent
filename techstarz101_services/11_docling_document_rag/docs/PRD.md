# Product Requirements Document (PRD) — Service #11: Docling Document RAG

## 1. Objective
Replace brittle, low-accuracy PDF text extraction (which scrambles multi-column financial tables and legal clauses) with a 100% self-hosted, layout-aware Document RAG platform powered by **IBM Docling** (93.6% table structure accuracy), hybrid vector search, and citation-grounded chat.

## 2. Target Users & Use Cases
- **Finance, Accounting & Audit Teams:** Query multi-page financial statements, balance sheets, and vendor invoices without hallucinated row/column misalignment.
- **Legal & Compliance Operations:** Search contracts, redlines, and regulatory filings with hybrid BM25 exact clause matching + semantic retrieval.
- **Enterprise Knowledge & Operations:** Automatically watch incoming folders/Paperless-ngx uploads and index structured Markdown into Qdrant or Weaviate via n8n.

## 3. Core Functional Requirements
1. **Table-Atomic Parsing:** Preserve multi-column tables intact as structured Markdown and JSON rather than splitting mid-row across arbitrary token windows.
2. **Dual Vector & Vault Architecture:** Offer both a lightweight Qdrant + AnythingLLM stack (Stack A) and a full Paperless-ngx + Weaviate + Open WebUI + n8n enterprise archive stack (Stack B).
3. **Standalone Modularity:** Every tool runs independently under `tools/<id>/` on dedicated ports (`:6700`–`:6830`) with clickable `/t/<id>` launch URLs.
4. **Zero-Docker Preview Utility:** Ship a live Table Extractor & RAG Chunking Simulator (`POST /api/docling/parse-and-chunk`) right inside the Hub.
