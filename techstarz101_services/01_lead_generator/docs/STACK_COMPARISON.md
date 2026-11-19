# Tool Stacks Architecture & Comparison — Lead Generator (<60s)

To give production teams full architectural flexibility, Techstarz101 specifies **two distinct open-source technology stacks** for the Lead Generator service:

---

## Stack A: High-Throughput Sovereign Pipeline Stack (Deterministic Orchestration)

Stack A is designed for high-concurrency, deterministic outbound pipelines where speed, strict data schemas, and CRM integration are paramount.

```mermaid
flowchart TD
    subgraph INGESTION["1. High-Throughput Web Ingestion"]
        Crawl4AI["Crawl4AI (Open Source LLM Web Crawler)"]
        SearXNG["SearXNG (Self-Hosted Metasearch Engine)"]
    end

    subgraph ENRICHMENT["2. Sovereign Enrichment & Verification"]
        Ollama["Ollama / vLLM (Local LLM Inference)"]
        Truemail["Truemail (Open Source Email RFC/MX Verifier)"]
        Instructor["Instructor / Pydantic (Structured Entity Parser)"]
    end

    subgraph ORCHESTRATION["3. Workflow & Orchestration"]
        N8N["n8n (Self-Hosted Automation Server)"]
        Redis["Redis (Job Queue & Cache)"]
    end

    subgraph SYSTEM_RECORD["4. CRM & Auto-Booking"]
        TwentyCRM["Twenty CRM (Self-Hosted GraphQL/PostgreSQL CRM)"]
        CalCom["Cal.com (Open Source Scheduling Infrastructure)"]
    end

    SearXNG --> Crawl4AI
    Crawl4AI --> N8N
    N8N --> Truemail
    N8N --> Ollama
    Ollama --> Instructor
    Instructor --> TwentyCRM
    Instructor --> CalCom
```

### Component Breakdown
1. **Discovery & Crawling:** **Crawl4AI** (`https://github.com/unclecode/crawl4ai`) + **SearXNG** (`https://github.com/searxng/searxng`).
   - *Why:* Crawl4AI delivers markdown-optimized HTML extraction at 6x speed of raw Playwright, stripping boilerplate and ads.
2. **Orchestration & Workflow:** **n8n Self-Hosted** (`https://github.com/n8n-io/n8n`).
   - *Why:* Visual workflow routing, error handling, rate-limiting, and webhook triggers with zero licensing cost.
3. **Email Verification:** **Truemail** (`https://github.com/truemail-rb/truemail`).
   - *Why:* Deep multi-regex RFC-compliant validation, MX record lookup, DNS tests, and mock SMTP handshake.
4. **Structured Enrichment:** **Ollama / vLLM** + **Instructor Python**.
   - *Why:* Guarantees strict JSON schema conformance without hallucinations, extracting CEO/Founder contacts and custom hooks.
5. **System of Record & Calendar:** **Twenty CRM** (`https://twenty.com`) + **Cal.com** (`https://cal.com`).
   - *Why:* Modern open-source CRM with native GraphQL APIs and self-hosted Cal.com appointment dispatch.

---

## Stack B: Agentic Autonomous Swarm Stack (Adaptive Zero-API RPA)

Stack B is built for complex, dynamic B2B discovery where lead data is locked behind non-standard web forms, multi-step portals, and modern interactive web apps.

```mermaid
flowchart TD
    subgraph SWARM_CORE["1. Autonomous Multi-Agent Swarm"]
        Hermes["Hermes Agent Core (Reasoning & Task Dispatch)"]
        LangGraph["LangGraph / CrewAI (Multi-Agent State Machine)"]
    end

    subgraph BROWSER_RPA["2. Zero-API Browser Automation"]
        BrowserUse["Browser-Use (Vision-Guided Web Agent)"]
        Playwright["Playwright Headless Chrome Engine"]
    end

    subgraph DATA_STORE["3. High-Speed Analytical Database"]
        DuckDB["DuckDB / PostgreSQL + pgvector"]
        Shlink["Shlink (Open Source Attribution Shortlinks)"]
    end

    subgraph CONVERSATIONAL_BOOKING["4. Conversational Booking Engine"]
        Typebot["Typebot (Self-Hosted Conversational Intake)"]
        CalComAPI["Cal.com API Direct Dispatch"]
    end

    Hermes --> LangGraph
    LangGraph --> BrowserUse
    BrowserUse --> Playwright
    Playwright --> DuckDB
    DuckDB --> Shlink
    Shlink --> Typebot
    Typebot --> CalComAPI
```

### Component Breakdown
1. **Agent Intelligence & Planning:** **Hermes Agent Core** + **LangGraph** (`https://github.com/langchain-ai/langgraph`).
   - *Why:* Manages complex multi-step research loops, retries failing websites, pivots search queries when data is thin.
2. **Zero-API Web Interaction:** **Browser-Use** (`https://github.com/browser-use/browser-use`) + **Playwright**.
   - *Why:* Uses vision and DOM tree analysis to click through pagination, interact with directory search inputs, and extract hidden contact modals.
3. **Analytical Data Lake:** **DuckDB** + **PostgreSQL**.
   - *Why:* Columnar in-memory processing for 250+ leads in sub-second time, with persistent PostgreSQL export.
4. **Attribution & Conversational Booking:** **Shlink** (`https://shlink.io`) + **Typebot** (`https://typebot.io`).
   - *Why:* Self-hosted shortlink generator to track email click-through rates and route leads into an interactive qualification chat that books directly into Cal.com.

---

## Comparison Matrix

| Feature / Dimension | Stack A (Sovereign Pipeline) | Stack B (Agentic Swarm) |
| :--- | :--- | :--- |
| **Primary Strength** | Raw speed (<45s for 250 leads), high concurrency | Adapts to messy, dynamic, protected directories |
| **Compute Footprint** | Low–Medium (runs on standard 4GB–8GB VPS) | Medium–High (GPU recommended for vision browser) |
| **Operational Complexity**| Low (Docker Compose up & run) | Medium (requires agent loop supervision) |
| **CRM Integration** | Native Twenty CRM GraphQL integration | PostgreSQL / DuckDB direct tabular export |
| **Best Used For** | Daily automated lead generation batches | High-value bespoke accounts with deep research |
