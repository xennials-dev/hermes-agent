#!/usr/bin/env bash
set -euo pipefail

echo "=========================================================="
echo "🚀 Bootstrapping Hermes Agent & CodeGraph in Codespaces..."
echo "=========================================================="

# 1. Install prerequisites & utilities
sudo apt-get update && sudo apt-get install -y \
    curl git jq tree tmux build-essential ripgrep

# 2. Configure Git safe directories and automated upstream sync protocols
git config --global --add safe.directory "*"
git config --global pull.rebase true
git config --global rebase.autoStash true
git config --global alias.sync-upstream "!git fetch upstream && git pull upstream main"
git config --global alias.sync-status "!git log --oneline -n 10 && git status"

# Configure upstream remote if not present
if ! git remote | grep -q "upstream"; then
    git remote add upstream https://github.com/NousResearch/hermes-agent.git || true
fi
git config remote.upstream.fetch "+refs/heads/main:refs/remotes/upstream/main" || true

# 3. Ensure uv is installed for blazing fast Python environment management
if ! command -v uv &> /dev/null; then
    echo "📦 Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

# 4. Bootstrap Hermes Agent from the local repository
echo "⚙️ Setting up Hermes Agent environment..."
if [ -f "./setup-hermes.sh" ]; then
    bash ./setup-hermes.sh || true
fi

# 5. Install CodeGraph CLI
echo "📦 Installing CodeGraph..."
if ! command -v codegraph &> /dev/null; then
    curl -fsSL https://raw.githubusercontent.com/colbymchenry/codegraph/main/install.sh | sh || true
fi

# 6. Configure Shell Profiles & PATH
for rc in "$HOME/.bashrc" "$HOME/.zshrc"; do
    if [ -f "$rc" ]; then
        grep -q 'hermes' "$rc" || echo 'export PATH="$HOME/.hermes/bin:$HOME/.codegraph/bin:$HOME/.local/bin:$PATH"' >> "$rc"
    fi
done
export PATH="$HOME/.hermes/bin:$HOME/.codegraph/bin:$HOME/.local/bin:$PATH"

# 7. Scaffold directories for Hermes artifacts & AntiGravity customizations
mkdir -p /workspaces/.agents/{rules,skills,plugins}
mkdir -p assets docs .hermes/documents

# 8. Pre-seed AntiGravity & Hermes co-existence rules
cat <<'EOF' > /workspaces/.agents/rules/hermes-rules.md
# Hermes & AntiGravity Co-existence Guidelines

1. **CodeGraph Pre-indexing**:
   Always run `codegraph init` before repository-wide refactoring to save AST tokens (-57% token burn).
2. **Hermes 5/14 Output Standard**:
   - Title: Exactly 5 words bold title.
   - Summary: Exactly 13 to 14 words summary.
   - Output directory: Save to `assets/` or `docs/`.
3. **Container State**:
   - User: `vscode`
   - Bound host: `0.0.0.0` or `127.0.0.1`
EOF

# 9. Initialize CodeGraph AST index if available
if command -v codegraph &> /dev/null; then
    echo "🔍 Initializing CodeGraph AST Index..."
    codegraph init || true
    codegraph install || true
fi

echo "=========================================================="
echo "✅ Codespace Ready for Hermes Agent & AntiGravity Pairings"
echo "=========================================================="
