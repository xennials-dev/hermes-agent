# Production Deployment Guide — Lead Generator (<60s)

This guide covers deploying the Techstarz101 Lead Generator service in production on any Linux/Ubuntu Hostinger VPS, cloud server, or on-premise infrastructure using Docker Compose.

---

## 1. System Requirements

- **Operating System:** Ubuntu 22.04 LTS / Debian 12 / Rocky Linux 9
- **CPU:** Minimum 4 vCPU cores (8 vCPU recommended for 1,000+ lead bursts)
- **RAM:** Minimum 8 GB (16 GB recommended if running local Ollama LLM)
- **Disk:** 50 GB NVMe SSD
- **Docker:** Engine 24.0+ & Docker Compose v2.20+

---

## 2. Directory Structure & Environment Setup

Clone or place the service repository into `/opt/techstarz101/01_lead_generator`:

```bash
mkdir -p /opt/techstarz101/01_lead_generator
cd /opt/techstarz101/01_lead_generator
```

Create the production `.env` file:

```bash
# Service Configuration
SERVICE_PORT=7865
ENVIRONMENT=production
LOG_LEVEL=info

# Database & Cache
POSTGRES_DB=techstarz_leads
POSTGRES_USER=postgres
POSTGRES_PASSWORD=generate_a_secure_password_here
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
REDIS_URL=redis://redis:6379/0

# Twenty CRM Integration
TWENTY_GRAPHQL_ENDPOINT=http://twenty-server:3000/graphql
TWENTY_API_KEY=your_twenty_crm_api_key

# Cal.com Scheduling
CALCOM_BASE_URL=https://cal.com
CALCOM_EVENT_SLUG=techstarz101/audit

# Local/Remote LLM
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=nemotron-mini:latest
```

---

## 3. Launching via Docker Compose

Run the stack in detached mode:

```bash
docker compose up -d
```

### Checking Service Health

```bash
# View active containers
docker compose ps

# Follow application logs
docker compose logs -f lead-generator-api

# Test health check endpoint
curl -f http://localhost:7865/health || exit 1
```

---

## 4. Reverse Proxy & SSL (Nginx + Certbot)

Add the following Nginx server block in `/etc/nginx/sites-available/leadgen.techstarz101.com`:

```nginx
server {
    server_name leadgen.techstarz101.com;

    location / {
        proxy_pass http://127.0.0.1:7865;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
```

Enable site and request SSL certificate:
```bash
ln -s /etc/nginx/sites-available/leadgen.techstarz101.com /etc/nginx/sites-enabled/
certbot --nginx -d leadgen.techstarz101.com
systemctl reload nginx
```
