# Production System Architecture — Marketing Campaigns

**Service ID:** `TS101-SRV-03`  
**Hub Control Plane:** `http://localhost:7867` (`hub/app.py`)  
**Standalone Repo Pattern:** One Docker Compose project (`ts101-<tool>`) + dedicated port + `/t/<tool>` link per app.

```mermaid
flowchart TD
    Hub["🎛️ Marketing Campaigns Hub (localhost:7867)<br/>Clickable Repo Icons · /t/&lt;tool&gt; · Multi-Angle A/B Generator"]

    subgraph StackA["Stack A: Sovereign Growth & Experimentation"]
        Mautic["📣 Mautic (:5300)<br/>Drip Campaigns"]
        GrowthBook["🧪 GrowthBook (:5310)<br/>Bayesian A/B Tests"]
        Umami["📈 Umami (:5320)<br/>UTM Attribution"]
        Shlink["🔗 Shlink (:5330)<br/>Campaign Shortlinks"]
    end

    subgraph StackB["Stack B: Agentic Multi-Angle Ad & Funnel"]
        Listmonk["📧 Listmonk (:5400)<br/>Zero-Tax Broadcasts"]
        Matomo["📊 Matomo (:5410)<br/>Funnel Analytics"]
        Typebot["💬 Typebot (:5420)<br/>Conversational Ad Funnels"]
        Metabase["📉 Metabase (:5430)<br/>ROAS & CAC BI"]
    end

    Hub -->|/t/mautic| Mautic
    Hub -->|/t/growthbook| GrowthBook
    Hub -->|/t/umami| Umami
    Hub -->|/t/shlink| Shlink
    Hub -->|/t/listmonk| Listmonk
    Hub -->|/t/matomo| Matomo
    Hub -->|/t/typebot| Typebot
    Hub -->|/t/metabase| Metabase

    Shlink --> Umami --> GrowthBook --> Mautic
    Typebot --> Listmonk --> Matomo --> Metabase
```
