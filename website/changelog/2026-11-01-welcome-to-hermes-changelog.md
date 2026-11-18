---
slug: 2026-11-01-welcome-to-hermes-changelog
title: Hermes Agent November 2026 Release Highlights
authors:
  - name: Nous Research Team
    title: Core Maintainers
    url: https://github.com/NousResearch
    image_url: https://github.com/NousResearch.png
tags: [releases, changelog, features]
---

Welcome to the official **Hermes Agent Changelog**! This feed tracks major feature releases, gateway expansions, performance optimizations, and breaking changes across the Hermes Agent ecosystem.

<!-- truncate -->

## What's New in Recent Builds

### 1. Synthesia Interactive Avatar Skill
Hermes now includes real-time interactive avatar control via the `synthesia-avatar` skill. The agent can drive continuous video generation, stream interactive visual avatars across sessions, and present dynamic interactive updates.

### 2. High-Precision Cron & Multi-Profile Scheduler
- Fully decoupled cron ticker (`scheduler_tick`) with resilient `advance_next_runs` recovery.
- Resilient catch-up execution after hibernation or process restarts across multiplexed profiles.

### 3. Expanded Proactive OSINT Toolset
Integrated structured investigation workflows for open-source intelligence:
- Digital footprint mapping
- Domain, handle, and infrastructure triage
- Automated resolution of gateway degraded states during high-volume reconnaissance

### 4. Omnichannel Gateway Refinements
- Hardened multi-connection desktop gateway pairing.
- Session provenance tracking across switching CLI and background daemon modes.
- Improved reaction and mention dispatch across Telegram, Discord, and Slack channels.

Stay tuned for upcoming weekly updates and deep dives into the learning loop architecture!

