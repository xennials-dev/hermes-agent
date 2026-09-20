# Hermes Agent Ecosystem Localhost Setup

Here is a curated list of the core repositories and integrations needed to run the full Hermes agent ecosystem flawlessly on your local machine, including integrations for advanced user modeling and desktop control.

## Core Ecosystem Repositories

1. **[Hermes Agent (Core)](https://github.com/NousResearch/hermes-agent)**: The central repository built by Nous Research. It features the primary learning loop, FTS5 session search, cron scheduler, and the terminal/gateway interface.
2. **[Honcho](https://github.com/plasticlabs/honcho)**: The dialectic user modeling system that Hermes integrates with to build a deepening model of the user across sessions.
3. **[Computer-Use-Linux (MCP Server)](https://github.com/NousResearch/computer-use-linux)**: A specialized MCP (Model Context Protocol) server for Linux desktop control, offering Wayland/X11 input, screenshots, and window targeting.
4. **[HermesClaw](https://github.com/hermesclaw/HermesClaw)** *(Optional)*: A community bridge for connecting Hermes Agent and OpenClaw, particularly useful if you are migrating from or integrating with WeChat environments.

## Custom Integrations

To ensure your existing custom multi-agent orchestration frameworks run alongside the core ecosystem, make sure to clone and integrate:
* **Xennials Agent**: Your custom orchestration framework (`scratch/xennials`).
* **Hermes Sports Betting Agent**: Your predictive agent utilizing the Logarithmic Method (Shin-Shortcut) for odds calculations (`scratch/hermes-agent/predictive_ai_core`).

*(Make sure these are cloned into your workspace if you plan to link them via RPC or as subagents to the main Hermes gateway.)*

---

## Localhost Deployment Guide

Follow these steps to initialize and deploy the core Hermes environment locally.

### 1. Install the Core Agent

Open your terminal (Linux, macOS, WSL2, or Termux) and run the installer script. This will set up the managed Python environment (via `uv`), Node.js, and other dependencies automatically:

```bash
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
```

*(Note: If you are setting this up natively on Windows PowerShell, run: `iex (irm https://hermes-agent.nousresearch.com/install.ps1)` instead.)*

### 2. Reload Your Shell

Apply the new path configurations:

```bash
source ~/.bashrc  # Or source ~/.zshrc if you use Zsh
```

### 3. Initialize the Setup Wizard

Run the Hermes setup wizard to configure your environment, toolsets, and model providers:

```bash
hermes setup
```

If you are using local models (e.g., via Ollama, LM Studio, or a local Docker container), you can specify your local endpoint here. You can also quickly switch models later using:

```bash
hermes model
```

### 4. Start the Messaging Gateway (Optional)

If you want to interact with your agent outside the standard CLI (e.g., via a local web UI or a connected platform like Telegram or Discord), set up and start the gateway process:

```bash
hermes gateway setup
hermes gateway start
```

### 5. Launch the CLI

To start chatting with your agent and trigger your local skill loops directly from the terminal, simply run:

```bash
hermes
```
