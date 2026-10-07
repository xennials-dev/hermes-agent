# CRM for HermesAgent – Design Overview

## 🎯 Goal

Create a **Customer Relationship Management (CRM)** system that:

- Hosts **Chinese local LLMs** and other opensource/free models.
- Provides a **Hugging Face NVIDIA router** similar to existing routers.
- Exposes a clean API for the **Hermesagent** to call for model inference, knowledgebase lookup, and workflow automation.
- Is **plugandplay** with the current Hermes codebase (commands, tools, web UI).

---

## 📦 Architecture

```text
+----------------------+   +----------------------+   +--------------------+
|  Frontend (React)    |   |  FastAPI (CRM API)   |   |  Model Workers     |
|  – Dashboard,        |   |  – /crm/* endpoints  |   |  – Local Chinese   |
|    Customer UI       |   |  – /models/* router  |   |    LLMs (glm4,     |
|  – Auth (OAuth)      |   |  – /router/*         |   |    bloomz)         |
+----------------------+   +----------------------+   +--------------------+
        |                         |                         |
        +----------> Hermesagent <--------------------------+
```

### Components

1. **Frontend** – A modern Vite + React SPA (styled with glassmorphism, dark mode, smooth microanimations).
2. **CRM API** – FastAPI app under `hermes_cli/web_routers/crm.py` exposing CRUD for customers, contacts, deals, and a `/router` endpoint that selects the best model for a request.
3. **Model Workers** – Docker containers running:
   - **Chinese LLMs** (e.g., `glm4chinese`, `bloomz`) using Hugging Face `transformers` with GPU support.
   - **Hugging Face NVIDIA router** – a thin FastAPI service that proxies to HF models on an NVIDIA GPU, mirroring the existing `huggingface_router` pattern.
   - **Opensource free models** – `llama27b`, `phi2`, `Mistral7B` etc.
4. **Hermes Integration Layer** – New CLI commands and internal tools to:
   - Register/unregister models (`hermes model register`, `hermes model list`).
   - Query the router (`hermes model invoke`).
   - Use CRMspecific commands (`/crm add-customer`, `/crm list-deals`).

---

## 🛠️ Implementation Steps

1. **Create CRM API module** (`hermes_cli/web_routers/crm.py`).
   - Define Pydantic models (`Customer`, `Contact`, `Deal`).
   - Implement CRUD routes, protected by the existing `auth` utilities.
2. **Add Model Router** (`hermes_cli/web_routers/model_router.py`).
   - Reuse the pattern from `local_models.py` but add a **registry** that includes Chinese LLMs and the HFNVIDIA router.
   - Expose `POST /router/infer` which takes `{model_name, prompt, parameters}` and returns `{output}`.
3. **Docker Compose** (`docker-compose.yml` in the new `crm` folder).
   - Services: `crm-api`, `glm-chinese`, `bloom-z`, `hf-nvidia-router`, `postgres` (for CRM data).
4. **CLI Extensions** – add a new mixin `cli_model_mixin.py` with commands:

   ```bash
   hermes model list
   hermes model register <name> <dockerservice>
   hermes model invoke <name> "<prompt>"
   hermes crm add-customer --name "Acme Corp" --email "a@acme.com"
   ```

5. **Configuration** – extend `config.yaml` with a `models:` section listing each model, its docker service name, GPU requirements, and a friendly alias.
6. **Testing & Debugging**
   - Unit tests for API endpoints (`tests/test_crm_api.py`).
   - Integration test that spins up the Docker compose stack and runs a sample inference.
   - Add **structured logging** (`hermes_logging.py`) for model routing latency, GPU memory usage, and request IDs.
   - Use the existing **Hermesagent debugger** (`hermes tools debug`) to step through model selection logic.

---

## 🔧 Debugging & Monitoring Ideas

| Area | Tool / Approach | Why |
| :--- | :--- | :--- |
| **Model latency** | Insert `time.perf_counter()` around the inference call and emit a `metrics` event (`hermes metrics record`). | Spot slow models quickly. |
| **GPU health** | Deploy `nvidia-smi` inside each model container and expose `/metrics` (Prometheus). | Prevent OOM crashes. |
| **API errors** | Centralized exception handler in FastAPI that logs stack traces to `agent.log` and returns a structured error payload. | Provide clear error toasts and diagnostics. |
| **CRM data integrity** | Use PostgreSQL constraints + Alembic migrations; run `hermes db migrate` to apply. | Prevent schema drift and corrupt data. |
| **Hermesagent commands** | Add a **commandregistry** entry (`/crm add-customer`) that calls the CRM API via the internal HTTP client (`tools.browser_tool`). | Enable conversational CRM actions. |

---

## 🧩 Example HermesAgent Extensions

### 1. New CLI mixin (`cli_model_mixin.py`)

```python
class ModelMixin:
    @cli.command(name="model")
    def model(self, args: List[str]):
        """Toplevel `hermes model` command dispatcher."""
        sub = args[0] if args else "list"
        if sub == "list":
            self._list_models()
        elif sub == "register":
            self._register_model(args[1:])
        elif sub == "invoke":
            self._invoke_model(args[1:])
```

### 2. New `/crm` slash command (in `hermes_cli/cli_crm_mixin.py`)

```python
@slash_command(name="crm", description="CRM helper commands")
async def crm(self, sub: str, **kwargs):
    if sub == "add-customer":
        await self._call_api("/crm/customers", json=kwargs)
    elif sub == "list-deals":
        await self._call_api("/crm/deals")
```

### 3. Router registration (in `hermes_cli/web_routers/local_models.py`)

```python
MODEL_REGISTRY = {
    "glmchinese": {"service": "glm-chinese", "gpu": True},
    "bloomz": {"service": "bloom-z", "gpu": True},
    "hfnvidia": {"service": "hf-nvidia-router", "gpu": True},
    # Opensource fallbacks
    "llama27b": {"service": "llama2", "gpu": False},
}
```

---

## 📚 Further Reading & Resources

- **FastAPI docs** – <https://fastapi.tiangolo.com/>
- **Hugging Face Transformers GPU guide** – <https://huggingface.co/docs/transformers/v4.38.0/en/quickstart#run-on-gpu>
- **NVIDIA Triton Inference Server** – can be swapped in for the HFNVIDIA router if you need higher throughput.
- **Hermesagent development guide** – see `AGENTS.md` in the repository for pluginstyle extensions.

---

## 🎨 UI/UX Aesthetic Tips (consistent with the “wow” requirement)

- Use a **darkmode primary palette** (`hsl(220, 10%, 12%)` background, `hsl(210, 60%, 70%)` accent).
- Apply **glassmorphism cards** for customer details (`backdrop-filter: blur(12px)`).
- Add **microanimations**: hover elevation, subtle fadein for table rows, and a **loading shimmer** while models warmup.
- Leverage **Google Fonts – Inter** for clean typography.
- Include a **realtime activity feed** showing model inference requests (use WebSocket from the CRM API).

---

*This design document lives at [crm_design.md](file:///c:/Users/tee/.gemini/antigravity-ide/scratch/hermes-agent/crm_design.md). Feel free to tweak any section or ask for deeper code samples.*
