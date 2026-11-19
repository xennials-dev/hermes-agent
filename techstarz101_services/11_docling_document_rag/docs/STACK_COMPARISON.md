# Stack Comparison — Service #11: Docling Document RAG

| Dimension | Stack A: Sovereign Layout RAG | Stack B: Enterprise Vault & Ingestion |
| --- | --- | --- |
| **Parser / Archive** | IBM Docling Serve (`:6700`) + Apache Tika (`:6730`) | Paperless-ngx Archive (`:6800`) + Docling via n8n |
| **Vector Engine** | Qdrant Dense+Sparse (`:6710`) | Weaviate Hybrid BM25+Vector (`:6810`) |
| **Chat / Workspace UI** | AnythingLLM RAG Studio (`:6720`) | Open WebUI Doc Chat (`:6820`) |
| **Automation** | Direct REST API / AnythingLLM Collectors | n8n Document Pipeline (`:6830`) |
| **RAM Footprint** | ~3.65 GB | ~2.90 GB |
| **Best For** | High-accuracy PDF/table RAG workspaces with instant visual citations | Companies needing a full Paperless document archive + automated zero-touch indexing |

> **Mix & Match:** Open WebUI (`:6820`) is already pre-configured with `CONTENT_EXTRACTION_ENGINE=docling` pointing to `http://host.docker.internal:6700`, so you can check `docling-serve` + `open-webui-rag` + `qdrant-rag` together in one click.
