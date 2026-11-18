---
sidebar_position: 0
title: "Run Nemotron 3 Ultra free in Hermes Agent"
description: "Try NVIDIA Nemotron 3 Ultra on Nous Portal with free-tier access and day 0 support in Hermes Agent"
---

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

# Run Nemotron 3 Ultra free in Hermes Agent

Nous Research has partnered with **Nebius** and **NVIDIA** as part of the **Nemotron Coalition** to provide **Nemotron 3 Ultra** on [Nous Portal](https://portal.nousresearch.com) with dedicated free-tier access. Follow the instructions below to try the model in your Hermes Agent with zero API cost.

:::tip Free Tier Access
The `nvidia/nemotron-3-ultra:free` model is available on the Nous Portal Free plan. The `:free` suffix is what keeps it on the zero-cost tier — make sure to pick that variant.
:::

Select your preferred interface below to get started:

<Tabs groupId="client-type">
  <TabItem value="cli" label="Command Line (CLI)" default>

### 1. Install Hermes Agent

<Tabs groupId="operating-system">
  <TabItem value="unix" label="Linux / macOS / WSL2 / Android">

```bash
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
source ~/.bashrc   # or source ~/.zshrc
```

  </TabItem>
  <TabItem value="windows" label="Windows (PowerShell)">

```powershell
iex (irm https://hermes-agent.nousresearch.com/install.ps1)
```

  </TabItem>
</Tabs>

:::note Reviewing scripts before running
Prefer to inspect first? Download [`install.sh`](https://hermes-agent.nousresearch.com/install.sh), review the contents, and execute locally.
:::

### 2. Connect to Nous Portal

Run the direct portal setup command:

```bash
hermes setup --portal
```

Hermes opens your browser automatically. Sign in (or register) at [Nous Portal](https://portal.nousresearch.com) on the **Free** plan and click **Connect**.

### 3. Select Nemotron 3 Ultra & Start Chatting

Return to your terminal. From the model list, select:

```bash
nvidia/nemotron-3-ultra:free
```

Then launch your agent:

```bash
hermes
```

That's it — you are now interacting with Nemotron 3 Ultra at zero API cost.

  </TabItem>
  <TabItem value="desktop" label="Desktop App (GUI)">

### 1. Download and Install

[Download the Hermes Desktop installer](https://hermes-agent.nousresearch.com/) for macOS or Windows and launch it. Setup completes automatically in under a minute.

### 2. Connect Nous Portal

On first launch, click **Nous Portal (Recommended)** on the setup screen. Your browser will open — sign in to [Nous Portal](https://portal.nousresearch.com) on the **Free** plan and click **Authorize**. The desktop app links automatically.

### 3. Select Nemotron 3 Ultra & Start Chatting

1. On the **Default model** card, click **Change**.
2. Search for `nemotron 3 ultra` and pick the variant tagged **Free tier**:
   ```
   nvidia/nemotron-3-ultra:free
   ```
3. Click **Start chatting**.

  </TabItem>
</Tabs>

## Switching to it later

Already set up with another model?

- **Desktop app:** open the model picker, search for **nemotron 3 ultra**, and select the **Free tier** variant.
- **CLI / TUI:** switch any time from inside a session with `/model nvidia/nemotron-3-ultra:free`, or run `/model` to open the interactive picker.

## Troubleshooting

- **Don't see the model in the list?** Ensure you completed the Nous Portal connection and selected the **Free** plan. In the CLI, run `hermes portal info` to verify login status.
- **Picked the wrong variant?** Re-select `nvidia/nemotron-3-ultra:free` — the `:free` suffix is required to stay on the no-cost tier.
- **Browser didn't open / remote host (CLI)?** See [OAuth over SSH / Remote Hosts](./oauth-over-ssh.md) for port-forwarding instructions.

## See also

- **[Desktop App](../user-guide/desktop.md)** — The native one-click app (macOS, Windows, Linux)
- **[Run Hermes Agent with Nous Portal](./run-hermes-with-nous-portal.md)** — Full Portal walkthrough: models, Tool Gateway, and verification
- **[Nous Portal integration](../integrations/nous-portal.md)** — What's in the subscription
- **[Quickstart](../getting-started/quickstart.md)** — Install-to-chat in under 5 minutes
