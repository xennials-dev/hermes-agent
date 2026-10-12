#!/bin/bash
set -u

BASE_DIR="/root/.hermes/hermes-agent/cloned_repos"
LOG_FILE="/var/log/hermes-upstream-sync.log"
STATUS_FILE="${BASE_DIR}/sync_status.json"
DATE_STR="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

echo "=== Upstream Sync Run: ${DATE_STR} ===" >> "${LOG_FILE}"

declare -A REPOS=(
  ["openclaw"]="https://github.com/openclaw/openclaw.git"
  ["grok-build"]="https://github.com/xai-org/grok-build.git"
  ["nanoclaw"]="https://github.com/Clawland-AI/nanoclaw.git"
  ["eigent"]="https://github.com/eigent-ai/eigent.git"
  ["ClawSwarm"]="https://github.com/The-Swarm-Corporation/ClawSwarm.git"
  ["suna"]="https://github.com/kortix-ai/suna.git"
  ["OpenMausBot"]="https://github.com/andreycurious252/OpenMausBot.git"
  ["openwork"]="https://github.com/different-ai/openwork.git"
  ["clawe"]="https://github.com/getclawe/clawe.git"
  ["cowork-os"]="https://github.com/cowork-os/cowork-os.git"
  ["rea"]="https://github.com/morluto/rea.git"
  ["awesome-osint"]="https://github.com/jivoi/awesome-osint.git"
)

mkdir -p "${BASE_DIR}"

for name in "${!REPOS[@]}"; do
  url="${REPOS[$name]}"
  target="${BASE_DIR}/${name}"
  echo "Checking ${name}..." >> "${LOG_FILE}"

  if [ ! -d "${target}/.git" ]; then
    echo "Cloning ${name} from ${url}..." >> "${LOG_FILE}"
    git clone --depth 50 "${url}" "${target}" >> "${LOG_FILE}" 2>&1 || true
  fi

  if [ -d "${target}/.git" ]; then
    cd "${target}" || continue
    git fetch origin >> "${LOG_FILE}" 2>&1 || true
    
    BRANCH=$(git symbolic-ref --short HEAD 2>/dev/null || echo "main")
    LOCAL=$(git rev-parse HEAD 2>/dev/null || echo "")
    REMOTE=$(git rev-parse "origin/${BRANCH}" 2>/dev/null || git rev-parse origin/main 2>/dev/null || echo "")

    if [ -n "$REMOTE" ] && [ "$LOCAL" != "$REMOTE" ]; then
      echo "Update available for ${name}: ${LOCAL} -> ${REMOTE}. Pulling..." >> "${LOG_FILE}"
      git pull origin "${BRANCH}" >> "${LOG_FILE}" 2>&1 || true
      NEW_LOCAL=$(git rev-parse HEAD 2>/dev/null)
      echo "Updated ${name} to ${NEW_LOCAL}" >> "${LOG_FILE}"

      if [ -f "package.json" ]; then
        (npm install --prefer-offline --no-audit || true) >> "${LOG_FILE}" 2>&1
      elif [ -f "Cargo.toml" ]; then
        (cargo check || true) >> "${LOG_FILE}" 2>&1
      elif [ -f "setup.py" ] || [ -f "pyproject.toml" ]; then
        (pip install --no-cache-dir -e . || true) >> "${LOG_FILE}" 2>&1
      fi
    else
      echo "${name} is up to date at ${LOCAL}" >> "${LOG_FILE}"
    fi
  fi
done

# Write status JSON
python3 - << 'PYEOF'
import os, json, subprocess

base = "/root/.hermes/hermes-agent/cloned_repos"
repos = ["openclaw", "grok-build", "nanoclaw", "eigent", "ClawSwarm", "suna", "OpenMausBot", "openwork", "clawe", "cowork-os"]
status = {"last_sync": subprocess.check_output(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"]).decode().strip(), "repos": {}}

for r in repos:
    p = os.path.join(base, r)
    if os.path.isdir(os.path.join(p, ".git")):
        try:
            head = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=p).decode().strip()
            msg = subprocess.check_output(["git", "log", "-1", "--pretty=%s"], cwd=p).decode().strip()
            remote = subprocess.check_output(["git", "remote", "get-url", "origin"], cwd=p).decode().strip()
            status["repos"][r] = {"commit": head, "message": msg, "remote": remote, "status": "synced"}
        except Exception as e:
            status["repos"][r] = {"status": "error", "error": str(e)}
    else:
        status["repos"][r] = {"status": "missing"}

with open(os.path.join(base, "sync_status.json"), "w") as f:
    json.dump(status, f, indent=2)
PYEOF

echo "=== Upstream Sync Finished ===" >> "${LOG_FILE}"
