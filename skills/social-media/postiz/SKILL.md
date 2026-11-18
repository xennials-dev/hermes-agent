---
name: postiz
description: >-
  Automate multi-platform social media scheduling and broadcasting for techstarz101.com using Postiz Public API (/public/v1).
  Lists connected social channels (X, LinkedIn, TikTok, Reddit, YouTube, Discord, Facebook/Instagram), publishes immediate
  or scheduled posts/threads, and uploads media.
---

# Postiz Multi-Platform Social Automation Skill (`techstarz101.com`)

Use this skill whenever the user asks to schedule, draft, or broadcast social media posts across `techstarz101.com` accounts (`tfisher@techstarz101.com`) via **Postiz**.

## Configuration (`~/.hermes/.env`)

Secrets live in `.env`:
- `POSTIZ_API_KEY`: API key from **Postiz Dashboard → Settings → Developers → Public API**
- `POSTIZ_BASE_URL`:
  - Self-hosted local Docker: `http://127.0.0.1:5000/api/public/v1`
  - Self-hosted VPS: `https://postiz.techstarz101.com/api/public/v1`
  - Postiz Cloud: `https://api.postiz.com/public/v1`

## CLI Usage (`scripts/postiz_cli.py`)

Run the bundled CLI script using Python:

### 1. Verify Connection & List Connected Channels
```powershell
python "C:\Users\tee\AppData\Local\hermes\skills\social-media\postiz\scripts\postiz_cli.py" channels
```

### 2. Broadcast a Test / Live Post to All Connected Channels Immediately
```powershell
python "C:\Users\tee\AppData\Local\hermes\skills\social-media\postiz\scripts\postiz_cli.py" post --type now --content "Sovereign AI Agents & Local Mesh Workflows are live at https://techstarz101.com/audit — cut SaaS bloat with n8n, Twenty CRM & Hermes Agent."
```

### 3. Schedule a Post or Thread for a Specific ISO-8601 Date
```powershell
python "C:\Users\tee\AppData\Local\hermes\skills\social-media\postiz\scripts\postiz_cli.py" post --type schedule --date "2026-11-18T14:00:00.000Z" --platforms x,linkedin,reddit --content "How we replace $1,850/mo of fragmented SaaS with a sovereign 10-tool AI stack:" --thread "Full architecture & ROI breakdown: https://techstarz101.com/blueprint"
```

### 4. Dry-Run Validation (No API Key Required)
```powershell
python "C:\Users\tee\AppData\Local\hermes\skills\social-media\postiz\scripts\postiz_cli.py" post --dry-run --type now --content "Testing Techstarz 101 multi-channel sync via Postiz + Hermes Agent!"
```

