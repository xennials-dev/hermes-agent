# Production Deployment Guide — Social Media Closer

## 1. Localhost Review (Windows / macOS / Linux)

1. Ensure **Docker Desktop** (or Docker Engine) is running.
2. Start the Service #02 Hub:
   ```powershell
   python techstarz101_services/02_social_media_closer/hub/app.py
   ```
3. Open **[http://localhost:7866](http://localhost:7866)**.
4. Click any individual tool's repo icon (or open `http://localhost:7866/t/<tool>`) to auto-generate its `.env`, boot its containers, and launch directly into that app.

---

## 2. Standalone Single-Tool Deployment (CLI)

Every tool can be deployed completely independently without the hub:

```bash
cd techstarz101_services/02_social_media_closer/tools/postiz
cp .env.example .env   # replace __HEX*__ placeholders with random strings
docker compose up -d
```

Repeat for any of the 9 tool folders (`postiz`, `chatwoot`, `n8n`, `ollama-webui`, `twenty`, `mixpost`, `flowise`, `activepieces`, `espocrm`).

---

## 3. Wiring Live Stack Automations

### Stack A (Chatwoot → n8n → Ollama → Twenty CRM)
1. Launch `n8n` (`/t/n8n`) and import `automations/stack_a_dm_closer.n8n.json`.
2. In `Chatwoot` (`/t/chatwoot`), go to **Settings → Integrations → Webhooks** and add:
   - `http://host.docker.internal:7866/api/closer/chatwoot-webhook` (or your n8n webhook URL).
3. In `Twenty CRM` (`/t/twenty`), create an API key under **Settings → APIs & Webhooks** and save it via `POST /api/settings` on the Hub.

### Stack B (Mixpost → Flowise → Activepieces → EspoCRM)
1. Launch `Flowise` (`/t/flowise`) and load `automations/stack_b_flowise_closer.json`.
2. Launch `Activepieces` (`/t/activepieces`) and point a webhook flow to `http://host.docker.internal:7866/api/closer/generic-webhook` with `"stack": "B"`.
3. Launch `EspoCRM` (`/t/espocrm`) using username `admin` and the generated password from `tools/espocrm/.env`.
