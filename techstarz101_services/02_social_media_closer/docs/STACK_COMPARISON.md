# Two Open-Source Tool Stacks Comparison — Social Media Closer

Every tool below is built as an **individual standalone repo** under `tools/<id>/` with its own port and dedicated launch link (`/t/<id>`), and can be stacked together or swapped freely.

---

## Stack A: Sovereign Omnichannel Closer (5 Individual Tools)

| Tool Repo | Dedicated Link | Direct Port | Upstream Repo | Role in Stack |
| :--- | :--- | :--- | :--- | :--- |
| **Postiz** (`tools/postiz/`) | `http://localhost:7866/t/postiz` | `:5100` | `gitroomhq/postiz-app` | Auto-post & schedule across 30+ social networks |
| **Chatwoot** (`tools/chatwoot/`) | `http://localhost:7866/t/chatwoot` | `:5110` | `chatwoot/chatwoot` | Unified 24/7 DM inbox (FB, IG, X, WhatsApp, Telegram) |
| **n8n** (`tools/n8n/`) | `http://localhost:7866/t/n8n` | `:5120` | `n8n-io/n8n` | Event-driven workflow glue between inbox, LLM & CRM |
| **Ollama + Open WebUI** (`tools/ollama-webui/`) | `http://localhost:7866/t/ollama-webui` | `:5130` | `ollama/ollama` + `open-webui/open-webui` | Local sovereign LLM (`llama3.2:3b`) generating sales replies |
| **Twenty CRM** (`tools/twenty/`) | `http://localhost:7866/t/twenty` | `:5140` | `twentyhq/twenty` | Modern GraphQL/PostgreSQL CRM for qualified DM leads |

---

## Stack B: Agentic Low-Code Closer (4 Individual Tools)

| Tool Repo | Dedicated Link | Direct Port | Upstream Repo | Role in Stack |
| :--- | :--- | :--- | :--- | :--- |
| **Mixpost** (`tools/mixpost/`) | `http://localhost:7866/t/mixpost` | `:5200` | `inovector/mixpost` | Lightweight MIT-licensed Buffer alternative |
| **Flowise** (`tools/flowise/`) | `http://localhost:7866/t/flowise` | `:5210` | `FlowiseAI/Flowise` | Drag-and-drop visual AI agent builder for DM closing |
| **Activepieces** (`tools/activepieces/`) | `http://localhost:7866/t/activepieces` | `:5220` | `activepieces/activepieces` | Open-source Zapier alternative for hand-offs & follow-ups |
| **EspoCRM** (`tools/espocrm/`) | `http://localhost:7866/t/espocrm` | `:5230` | `espocrm/espocrm` | Fast, low-RAM CRM for leads, tasks & opportunities |

---

## Decision Matrix

| Criterion | Stack A (Sovereign Omnichannel) | Stack B (Agentic Low-Code) |
| :--- | :--- | :--- |
| **Best For** | High-volume multi-channel teams needing a full live DM inbox | Solo founders & agencies wanting visual drag-and-drop AI agents |
| **Combined RAM** | ~9.7 GB (or ~1.5 GB per individual tool) | ~3.1 GB total (runs easily on a 4–8 GB VPS) |
| **Customizability** | Deep API/code + n8n webhooks | Visual no-code Flowise + Activepieces |
| **Mix & Match** | Any Stack A tool can be checked alongside any Stack B tool in the Hub! | Full cross-stack webhook compatibility via Hub `:7866` |
