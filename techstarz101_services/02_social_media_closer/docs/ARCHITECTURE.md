# Production System Architecture — Social Media Closer

**Service ID:** `TS101-SRV-02`  
**Control Plane Hub:** `http://localhost:7866` (`hub/app.py`)  
**Isolation Pattern:** One Docker Compose Project (`ts101-<tool>`) + Dedicated Port per Tool

---

## 1. Modular Standalone + Stackable Topology

```mermaid
flowchart TD
    Hub["🎛️ Techstarz101 Hub (localhost:7866)<br/>Clickable Repo Icons · /t/&lt;tool&gt; · Stack Composer"]

    subgraph StackA["Stack A: Sovereign Omnichannel Closer"]
        Postiz["📣 Postiz (:5100)<br/>tools/postiz/"]
        Chatwoot["💬 Chatwoot (:5110)<br/>tools/chatwoot/"]
        N8N["🔀 n8n (:5120)<br/>tools/n8n/"]
        Ollama["🧠 Ollama + WebUI (:5130)<br/>tools/ollama-webui/"]
        Twenty["🗂️ Twenty CRM (:5140)<br/>tools/twenty/"]
    end

    subgraph StackB["Stack B: Agentic Low-Code Closer"]
        Mixpost["🗓️ Mixpost (:5200)<br/>tools/mixpost/"]
        Flowise["🤖 Flowise (:5210)<br/>tools/flowise/"]
        Activepieces["🧩 Activepieces (:5220)<br/>tools/activepieces/"]
        EspoCRM["📇 EspoCRM (:5230)<br/>tools/espocrm/"]
    end

    Hub -->|/t/postiz| Postiz
    Hub -->|/t/chatwoot| Chatwoot
    Hub -->|/t/n8n| N8N
    Hub -->|/t/ollama-webui| Ollama
    Hub -->|/t/twenty| Twenty

    Hub -->|/t/mixpost| Mixpost
    Hub -->|/t/flowise| Flowise
    Hub -->|/t/activepieces| Activepieces
    Hub -->|/t/espocrm| EspoCRM

    Chatwoot -->|Webhook| N8N
    N8N -->|Chat API| Ollama
    N8N -->|REST/GraphQL| Twenty

    Mixpost -->|Trigger| Activepieces
    Activepieces -->|Prediction API| Flowise
    Activepieces -->|REST API| EspoCRM
```

---

## 2. Dedicated Per-Tool Link Lifecycle (`/t/<id>`)

1. User clicks a tool's repo icon or opens `http://localhost:7866/t/<id>`.
2. `launch.html` polls `/api/status` and checks Docker engine readiness.
3. If the tool is `stopped`, the hub auto-generates `.env` from `.env.example` (cryptographically random secrets) and runs `docker compose -f tools/<id>/docker-compose.yml up -d`.
4. Live compose logs stream to the browser while the hub probes the tool's HTTP health endpoint.
5. As soon as the app responds (`HTTP < 500`), the browser automatically redirects straight into the live application URL (e.g., `http://localhost:5100`).
