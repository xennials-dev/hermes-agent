#!/usr/bin/env bash
# ==============================================================================
# Hermes Agent - Turnkey VPS Deployment Script (Hostinger KVM VPS: 2.25.238.185)
# Target Subdomain: hermes.techstarz101.com
# ==============================================================================

set -e

VPS_IP="2.25.238.185"
DOMAIN="hermes.techstarz101.com"
APP_DIR="/opt/apps/hermes-agent"

echo "=========================================================="
echo "🚀 Deploying Hermes Agent to Hostinger VPS ($VPS_IP)"
echo "Target Domain: https://$DOMAIN"
echo "=========================================================="

# Check if running locally on the VPS or remotely via SSH
if [ "$(hostname -I | grep -o "$VPS_IP" || true)" != "$VPS_IP" ] && [ "$EUID" -ne 0 ]; then
    echo "⚡ Initiating remote deployment over SSH..."
    ssh root@$VPS_IP "bash -s" < "$0"
    exit 0
fi

echo "📦 1. Provisioning Target Directory ($APP_DIR)..."
mkdir -p "$APP_DIR"
cd "$APP_DIR"

echo "🐍 2. Setting up Python Virtual Environment & Dependencies..."
if ! command -v python3 &>/dev/null; then
    apt-get update -y && apt-get install -y python3 python3-pip python3-venv git
fi

if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

source .venv/bin/activate
pip install --upgrade pip
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
elif [ -f "pyproject.toml" ]; then
    pip install .
fi

echo "🌐 3. Configuring Nginx Reverse Proxy for $DOMAIN..."
NGINX_CONF="/etc/nginx/sites-available/$DOMAIN.conf"
cat << 'EOF' > "$NGINX_CONF"
server {
    listen 80;
    listen [::]:80;
    server_name hermes.techstarz101.com;

    location / {
        proxy_pass http://127.0.0.1:9118;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

ln -sf "$NGINX_CONF" /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

echo "🔒 4. Securing SSL with Let's Encrypt Certbot..."
if command -v certbot &>/dev/null; then
    certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos --email admin@techstarz101.com --redirect || echo "Note: DNS must resolve to 2.25.238.185 for certbot challenge"
fi

echo "⚙️ 5. Starting Service via PM2 / Systemd..."
if command -v pm2 &>/dev/null; then
    pm2 start ecosystem.config.cjs || pm2 restart hermes-agent
    pm2 save
else
    cp hermes-agent.service /etc/systemd/system/
    systemctl daemon-reload
    systemctl enable hermes-agent
    systemctl restart hermes-agent
fi

echo "=========================================================="
echo "✅ Hermes Agent successfully deployed to VPS!"
echo "Check logs: pm2 logs hermes-agent OR journalctl -u hermes-agent -f"
echo "=========================================================="
