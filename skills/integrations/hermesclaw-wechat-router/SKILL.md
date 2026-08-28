---
name: hermesclaw-wechat-router
description: Multi-agent WeChat multiplexer routing Hermes Agent, OpenClaw, and OpenCode concurrently on a single iLink WeChat account.
tags:
  - integrations
  - wechat
  - openclaw
  - opencode
  - ilink
  - multi-agent
---

# HermesClaw — Multi-Agent WeChat Multiplexer Workflow

`HermesClaw` is a tri-gateway proxy router that owns a single WeChat iLink polling connection and distributes incoming messages across **Hermes Agent**, **OpenClaw**, and **OpenCode (ACP bridge)**.

---

## 🏗️ Architecture

```
                    ┌────────── iLink API ──────────┐
                    │  ilinkai.weixin.qq.com        │
                    └──────────┬────────────────────┘
                               │ (sole poller)
                    ┌──────────▼────────────────────┐
                    │     HermesClaw Router          │
                    │  routes /hermes /openclaw      │
                    │         /opencode /both /three │
                    ├────────┬──────────┬────────────┤
                    │        │          │
              Proxy A      Proxy B    ACP Bridge
              (:19999)     (:19998)   (subprocess)
              OpenClaw     Hermes     OpenCode ACP
```

---

## ⚡ Quick Setup & Configuration

### 1. Configure Hermes Agent Gateway for HermesClaw
Point Hermes Agent's Weixin platform to HermesClaw's local proxy port (`19998`):

In `~/.hermes/config.yaml`:
```yaml
gateway:
  enabled: true
  platforms:
    - weixin

weixin:
  enabled: true
  base_url: "http://127.0.0.1:19998"
```

Or via environment variables in `~/.hermes/.env`:
```env
WEIXIN_BASE_URL=http://127.0.0.1:19998
```

### 2. Configure OpenClaw Gateway
In OpenClaw's config (`~/.openclaw/config.json`):
```json
{
  "channels": {
    "wechat": {
      "base_url": "http://127.0.0.1:19999"
    }
  }
}
```

### 3. Launching HermesClaw
Run the bundled HermesClaw multiplexer script:

```bash
python scripts/hermesclaw/hermesclaw.py
```

---

## 💬 Routing Commands in WeChat

Users can switch or combine agents directly in their WeChat chat:

| Command | Routing Target | Description |
|---|---|---|
| `/hermes` | Hermes Agent | Routes all conversation turns to Hermes Agent |
| `/openclaw` | OpenClaw | Routes all conversation turns to OpenClaw |
| `/opencode` | OpenCode | Routes turns to OpenCode ACP session (supports voice vibe coding) |
| `/both` | Hermes + OpenClaw | Broadcasts messages to both Hermes and OpenClaw simultaneously |
| `/three` | All 3 AI Brains | Multi-agent collaboration across Hermes, OpenClaw, and OpenCode |
| `/status` | Status Report | Returns currently active route and gateway connectivity state |

---

## 🛠️ Key Benefits
- **Zero Token Conflicts**: Prevents 403 HTTP token collision errors caused by multiple pollers on a single iLink credential.
- **Voice & Media Preservation**: Raw iLink protocol messages (audio voice notes, images, documents) are preserved and passed to each agent's native decoders.
- **Vibe Coding over WeChat**: Trigger OpenCode ACP code generations via voice notes directly from mobile WeChat.
