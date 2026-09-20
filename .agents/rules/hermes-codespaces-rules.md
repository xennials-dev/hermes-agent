# Hermes Agent & AntiGravity Codespaces Policy

1. **Environment**: We are running inside a containerized GitHub Codespace (Ubuntu 24.04).
2. **AST Indexing with CodeGraph**:
   - Always initialize or update CodeGraph (`codegraph init`) before major refactors to reduce token burn by 57%.
   - CodeGraph MCP tool calls eliminate redundant file grep/search across the codebase.
3. **Hermes 5/14 Output Standard**:
   - Deliverable titles must be exactly **5 words** bold (e.g., `**Enterprise Client Billing Invoice Template**`).
   - Deliverable summaries must be exactly **13 to 14 words** description.
   - Save artifacts to `assets/`, `docs/`, or `.hermes/documents/`.
4. **Autonomous Steering**:
   - Live mid-task course corrections should be passed via `/steer <instruction>`.
5. **Port Binding**:
   - Hermes Web UI / Dashboard binds to `0.0.0.0:3000`.
   - Vite Web Client binds to `0.0.0.0:5173`.
   - Gateway API binds to `0.0.0.0:8000`.
