---
name: caprover
description: "Deploy apps, databases, and services to CapRover PaaS."
version: 0.1.0
author: Terrance (tee), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [DevOps, Deployment, CapRover, PaaS, Docker, Hosting, Databases]
    related_skills: [sdlc-review]
---

# CapRover Deployment & PaaS Management

Manage, configure, and automate application and database deployments to CapRover ("Heroku on Steroids") using `caprover-cli` and the CapRover HTTP API.

---

## 1. Quick Reference

| Action | Command / Workflow |
|---|---|
| **Install CLI** | `npm install -g caprover` (or `npx caprover <cmd>`) |
| **Server Setup** | `caprover serversetup` |
| **Login to Machine** | `caprover login` (stores auth token locally) |
| **Deploy Directory** | `caprover deploy` (packages directory with `captain-definition`) |
| **Deploy Tar / Branch** | `caprover deploy -t ./build.tar` or `caprover deploy -b main` |
| **List Apps** | `caprover list` |
| **Inspect Logs** | `caprover logs -a <app-name>` |

---

## 2. Server Installation (VPS Host Setup)

To spin up a new CapRover PaaS instance on Ubuntu / Debian / Linux VPS:

```bash
# 1. Ensure Docker is installed on target VPS
curl -fsSL https://get.docker.com | sh

# 2. Run CapRover container
docker run -e ACCEPTED_TERMS=true \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /captain:/captain \
  -p 80:80 -p 443:443 -p 3000:3000 \
  caprover/caprover
```

---

## 3. Initializing & Authenticating with CapRover CLI

Once the server is running on `http://<SERVER_IP>:3000`:

```bash
# Interactive setup: maps your wildcard domain (e.g. *.apps.yourdomain.com) and admin email
caprover serversetup

# Login programmatically
caprover login --caproverUrl "https://captain.rootdomain.com" \
  --caproverPassword "your-admin-password" \
  --caproverName "production"
```

---

## 4. Packaging & Deploying Applications

CapRover uses a `captain-definition` file in the root of the project to define build steps.

### A. Generic Dockerfile Deployment
Create `captain-definition`:
```json
{
  "schemaVersion": 2,
  "dockerfilePath": "./Dockerfile"
}
```

### B. Python / FastAPI / Hermes Service Deployment
```json
{
  "schemaVersion": 2,
  "template": "python/3.11"
}
```

### C. Node.js Application
```json
{
  "schemaVersion": 2,
  "template": "node/20"
}
```

### Deploying the App:
```bash
# Deploy current workspace to specific CapRover app
caprover deploy -a my-service -n production
```

---

## 5. One-Click Apps Deployment (Databases & Services)

CapRover supports instant deployment of databases and community templates from `caprover/one-click-apps`:

### Supported Common Templates:
- **PostgreSQL**: `postgres`
- **Redis**: `redis`
- **MongoDB**: `mongo`
- **MySQL / MariaDB**: `mysql`
- **Meilisearch / Elasticsearch**: `meilisearch`
- **Strapi / Directus / WordPress**: `wordpress`

### Deploying via CapRover API:
Execute the companion helper script to deploy or inspect one-click apps:
```bash
python scripts/caprover_helper.py one-click --app-name "my-postgres" --template "postgres" --password "securepassword"
```

---

## 6. Managing Environment Variables & Custom Domains

```bash
# Set environment variables via API / CLI
caprover api --path "/api/v2/user/apps/appDefinitions/update" --method "POST" --data '{
  "appName": "my-service",
  "envVars": [
    {"key": "PORT", "value": "80"},
    {"key": "DATABASE_URL", "value": "postgres://user:pass@srv-captain--my-postgres:5432/db"}
  ]
}'

# Enable SSL for custom domain
caprover api --path "/api/v2/user/apps/appDefinitions/enableCustomDomainSsl" --method "POST" --data '{
  "appName": "my-service",
  "customDomain": "api.mydomain.com"
}'
```
