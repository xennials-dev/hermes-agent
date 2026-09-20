---
name: multi-agent-team
description: Orchestrate a 5-agent specialized bot team (Laura, Drew...
version: 1.0.0
author: Hermes Multi-Agent Suite
license: MIT
platforms:
- linux
- macos
- windows
metadata:
  hermes:
    tags:
    - MultiAgent
    - BotMode
    - TeamOrchestration
    - LocalFirstDashboard
    - CloudflareDeploy
    - CI/CD
---

# Hermes Multi-Agent Bot Team & Bridge

This skill defines the multi-agent team architecture (Laura, Drew, Bob, Cody, Logan), group chat coordination patterns, and tool definitions bridging Hermes to your local FastAPI platform.

---

## 1. The 5-Agent Roster

| Agent Name | Role | Recommended Model | Primary Focus |
| :--- | :--- | :--- | :--- |
| **Laura** | Chief of Staff (Orchestrator) | GPT-4.1 / Claude 3.5 Sonnet | Planning, task breakdown, milestone tracking |
| **Drew** | Research Specialist | DeepSeek-R1 / Claude 3.5 | Tech specs, data models, edge cases |
| **Bob** | Creative Director | Gemini Flash 3.7 / Flux | UI/UX, styling tokens, visual asset specs |
| **Cody** | Lead Developer | DeepSeek-Coder / GPT-4.1 | Implementation, test execution, deployments |
| **Logan** | Observability & Telemetry | Lightweight / Fast LLM | Background logging, timelines, audit trails |

---

## 2. FastAPI Bridge Server

Start the local bridge server:
```powershell
python services/multi_agent_bridge/server.py
```
*(Runs on `http://127.0.0.1:8000`)*

### Supported Endpoints:
1. `POST /tools/run_pipeline` — Trigger the local multi-agent workflow
2. `POST /tools/build_dashboard` — Compile the local-first agent dashboard
3. `POST /tools/deploy_cloudflare` — Deploy build output to Cloudflare Pages
4. `POST /tools/deploy_vercel` — Deploy build output to Vercel
5. `POST /tools/run_tests` — Run automated unit/integration test suites
6. `POST /tools/log_event` — Record telemetry events and logs
7. `GET /tools/get_agent_timeline` — Retrieve Gantt activity timeline
8. `POST /tools/sandbox_execute` — Safe sandboxed command execution

---

## 3. Multi-Agent Group Chat Kickoff Prompts

### Project Kickoff: "Local-First Agent Dashboard"
```text
@Laura

Goal:
Build a local-first agent dashboard that runs on my machine, supports offline mode, and integrates with my Python multi-agent system.

Instructions:
1. Break the project into phases: research, design, implementation, testing, and deployment.
2. Assign tasks to:
   - @Drew for technical specifications and data schemas
   - @Bob for UI/UX, layouts, and visual styling
   - @Cody for coding, testing, and deployment
3. Ensure @Logan monitors and logs all milestones.
4. Have Cody run automated tests before deploying via Cloudflare or Vercel.
```

### Phase 1: Research (to Drew)
```text
@Drew
Research the architecture for our local-first agent dashboard:
- Local SQLite / IndexedDB offline storage
- Sync & state reconciliation strategies
- Component hierarchy & agent telemetry schema
Return a structured specification for @Bob and @Cody.
```

### Phase 2: Design (to Bob)
```text
@Bob
Using Drew's research, design the dashboard UI:
- Modern dark-mode theme with clear visual hierarchy
- Agent activity feed & task runner panel
- Offline status indicator and Gantt timeline view
Output full CSS/UI specifications for Cody.
```

### Phase 3 & 4: Build, Test & Deploy (to Cody)
```text
@Cody
1. Build the dashboard with features: {"offline_mode": true, "agent_list": true, "task_runner": true}.
2. Run automated test verification via run_tests.
3. If tests pass, deploy to Cloudflare Pages and return the live URL.
```
