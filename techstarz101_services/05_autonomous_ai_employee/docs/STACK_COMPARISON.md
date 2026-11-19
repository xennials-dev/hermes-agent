# Two Open-Source Tool Stacks Comparison — Autonomous AI Employee

## Stack A: Sovereign Executive Orchestrator (4 Standalone Repos)

| Tool Repo | Dedicated Launch Link | Direct Port | Upstream Repo | Role |
| :--- | :--- | :--- | :--- | :--- |
| **Open WebUI** (`tools/open-webui/`) | `http://localhost:7869/t/open-webui` | `:5700` | `open-webui/open-webui` | Executive chat workspace & private RAG |
| **Qdrant** (`tools/qdrant/`) | `http://localhost:7869/t/qdrant` | `:5710/dashboard` | `qdrant/qdrant` | High-speed semantic vector memory |
| **Temporal** (`tools/temporal/`) | `http://localhost:7869/t/temporal` | `:5720` | `temporalio/temporal` | Durable multi-day autonomous workflows |
| **Langfuse** (`tools/langfuse/`) | `http://localhost:7869/t/langfuse` | `:5730` | `langfuse/langfuse` | AI audit traces, prompts & token cost governance |

## Stack B: Visual Multi-Agent Teammate (4 Standalone Repos)

| Tool Repo | Dedicated Launch Link | Direct Port | Upstream Repo | Role |
| :--- | :--- | :--- | :--- | :--- |
| **Dify** (`tools/dify/`) | `http://localhost:7869/t/dify` | `:5800` | `langgenius/dify` | Visual AI teammate & tool-calling studio |
| **AnythingLLM** (`tools/anythingllm/`) | `http://localhost:7869/t/anythingllm` | `:5810` | `Mintplex-Labs/anything-llm` | Private workspace RAG & MCP agent |
| **LiteLLM** (`tools/litellm/`) | `http://localhost:7869/t/litellm` | `:5820/ui` | `BerriAI/litellm` | 100+ model OpenAI gateway & spend caps |
| **NocoDB** (`tools/nocodb/`) | `http://localhost:7869/t/nocodb` | `:5830` | `nocodb/nocodb` | Executive task boards & human approval queues |
