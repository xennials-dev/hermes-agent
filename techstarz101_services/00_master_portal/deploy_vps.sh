#!/usr/bin/env bash
# Techstarz101 Master Portal + Service Hubs VPS Deployment Script (Hostinger KVM 2.25.238.185)
set -euo pipefail

REPO_DIR="${REPO_DIR:-/opt/techstarz101-services}"
BRANCH="${BRANCH:-social-media-postiz}"
REPO_URL="${REPO_URL:-https://github.com/xennials-dev/hermes-agent.git}"

echo "[deploy] Syncing repository into ${REPO_DIR}..."
if [ -d "${REPO_DIR}/.git" ]; then
  git -C "${REPO_DIR}" fetch origin "${BRANCH}"
  git -C "${REPO_DIR}" checkout "${BRANCH}"
  git -C "${REPO_DIR}" reset --hard "origin/${BRANCH}"
else
  git clone --depth 1 --branch "${BRANCH}" "${REPO_URL}" "${REPO_DIR}"
fi

cd "${REPO_DIR}"

if [ ! -d ".venv-portal" ]; then
  python3 -m venv .venv-portal
fi
.venv-portal/bin/pip install --quiet --upgrade pip fastapi uvicorn pydantic

# Start Master Command Portal on :7860 via PM2 (or nohup fallback)
if command -v pm2 >/dev/null 2>&1; then
  pm2 delete ts101-master-portal 2>/dev/null || true
  pm2 start .venv-portal/bin/python --name ts101-master-portal -- techstarz101_services/00_master_portal/app.py
  for entry in \
    "ts101-s02:techstarz101_services/02_social_media_closer/hub/app.py" \
    "ts101-s03:techstarz101_services/03_marketing_campaigns/hub/app.py" \
    "ts101-s04:techstarz101_services/04_brand_web_launch/hub/app.py" \
    "ts101-s05:techstarz101_services/05_autonomous_ai_employee/hub/app.py" \
    "ts101-s06:techstarz101_services/06_ai_opportunity_audit/hub/app.py" \
    "ts101-s07:techstarz101_services/07_listmonk_email/hub/app.py" \
    "ts101-s09:techstarz101_services/09_whisperx_speech_ai/hub/app.py" \
    "ts101-s10:techstarz101_services/10_pipecat_voice_ai/hub/app.py" \
    "ts101-s11:techstarz101_services/11_docling_document_rag/hub/app.py" \
    "ts101-s12:techstarz101_services/12_comfyui_creative_engine/hub/app.py" \
    "ts101-s13:techstarz101_services/13_browser_use_web_agent/hub/app.py" \
    "ts101-s14:techstarz101_services/14_claude_finance_agent_suite/hub/app.py" \
    "ts101-s15:techstarz101_services/15_cyber_security_package/hub/app.py"; do
    name="${entry%%:*}"
    script="${entry#*:}"
    pm2 delete "${name}" 2>/dev/null || true
    pm2 start .venv-portal/bin/python --name "${name}" -- "${script}"
  done
  pm2 save
else
  nohup .venv-portal/bin/python techstarz101_services/00_master_portal/app.py >/var/log/ts101-portal.log 2>&1 &
fi

echo "[deploy] Master Portal live on :7860"

