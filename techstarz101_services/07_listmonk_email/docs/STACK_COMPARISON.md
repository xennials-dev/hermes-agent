# Two Open-Source Tool Stacks Comparison — Listmonk Email Marketing

## Stack A: High-Throughput Sovereign Broadcast (4 Standalone Repos)

| Tool Repo | Dedicated Launch Link | Direct Port | Upstream Repo | Role |
| :--- | :--- | :--- | :--- | :--- |
| **Listmonk** (`tools/listmonk/`) | `http://localhost:7871/t/listmonk` | `:6100` | `knadh/listmonk` | High-speed Go newsletter & broadcast engine |
| **Stalwart Mail** (`tools/stalwart/`) | `http://localhost:7871/t/stalwart` | `:6110` | `stalwartlabs/mail-server` | Rust SMTP/JMAP/DKIM/DMARC mail server |
| **Mailpit** (`tools/mailpit/`) | `http://localhost:7871/t/mailpit` | `:6120` | `axllent/mailpit` | Pre-send HTML rendering & SMTP QA sandbox |
| **Reacher** (`tools/reacher/`) | `http://localhost:7871/t/reacher` | `:6130` | `reacherhq/check-if-email-exists` | Self-hosted MX/SMTP list hygiene verifier |

## Stack B: Visual Newsletter & Behavioral Lifecycle (4 Standalone Repos)

| Tool Repo | Dedicated Launch Link | Direct Port | Upstream Repo | Role |
| :--- | :--- | :--- | :--- | :--- |
| **Keila** (`tools/keila/`) | `http://localhost:7871/t/keila` | `:6200` | `pentacent/keila` | Visual block-editor Mailchimp alternative |
| **Roundcube** (`tools/roundcube/`) | `http://localhost:7871/t/roundcube` | `:6210` | `roundcube/roundcubemail` | Self-hosted reply inbox for warm responses |
| **n8n Email** (`tools/n8n-email/`) | `http://localhost:7871/t/n8n-email` | `:6220` | `n8n-io/n8n` | Behavioral drips, bounces & CRM sync |
| **Adminer** (`tools/adminer/`) | `http://localhost:7871/t/adminer` | `:6230` | `vrana/adminer` | Direct SQL audience segmentation studio |
