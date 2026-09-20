---
name: rag-streaming-pipeline
description: Streaming data into vector stores with hybrid BM25 + dens...
platforms:
- linux
- macos
- windows
---

# RAG Streaming Pipeline & Vector Search Playbook

When building or optimizing streaming Retrieval-Augmented Generation (RAG) workflows:

## 1. Ingestion & Streaming Buffer
- Ingest real-time documents or stream chunks through an event queue (Kafka / Redis Streams / Webhook).
- Buffer records in sliding windows to avoid excessive discrete embedding API calls.

## 2. Token-Aware Chunking Strategy
- Apply recursive text splitting with dynamic overlap:
  - Chunk size: 512 to 1024 tokens.
  - Chunk overlap: 10% to 15% (50 to 150 tokens) to maintain cross-boundary semantic continuity.
  - Preserve code fence blocks (```) and markdown headers (`#`, `##`) as structural boundaries.

## 3. Hybrid Retrieval Architecture
- Generate dense vector embeddings via NVIDIA NV-Embed or text-embedding-3 models.
- Index sparse lexical tokens using BM25 / SPLADE for keyword exact matches.
- Combine dense and sparse ranks using Reciprocal Rank Fusion (RRF):
  $$RRF\_score(d) = \sum_{m \in M} \frac{1}{60 + r_m(d)}$$

## 4. Re-Ranking & Context Window Assembly
- Pass top-20 retrieved passages to a cross-encoder re-ranker (e.g. `nvidia/reranking-mistral-4b` or `bge-reranker-large`).
- Format top-5 re-ranked results into the prompt context with source attribution tags `[doc:id:chunk]`.
