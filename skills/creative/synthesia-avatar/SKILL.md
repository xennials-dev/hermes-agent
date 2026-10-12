---
name: synthesia-avatar
description: "Control Synthesia interactive avatars and stream sessions."
version: 1.0.0
author: Antigravity, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Synthesia, Avatar, Video, Streaming, WebRTC]
    related_skills: []
---

# Synthesia Avatar Skill

Manage Synthesia interactive avatars and start real-time conversational streaming sessions. This skill provisions interactive avatars from Synthesia Studio source models and initializes WebRTC/LiveKit interactive streaming sessions. It does not perform legacy batch video rendering or manage video template editing.

## When to Use

- Use when an interactive avatar is needed for real-time conversational streaming.
- Use when converting an existing Studio avatar (`sourceId: av_*`) into an interactive avatar.
- Use when checking avatar provisioning status or launching LiveKit streaming sessions.
- Do not use for legacy static video generation (`/v2/videos`) or template manipulation.

## Prerequisites

- Synthesia API key with `interactive_avatars:write` scope stored as `SYNTHESIA_API_KEY` in `.env`.
- Target Studio avatar ID (formatted as `av_<id>`).
- A LiveKit cloud or self-hosted server URL (`wss://...`) and valid client access token for real-time streaming sessions.

## How to Run

Execute the helper script via the `terminal` tool using python:

```bash
python skills/creative/synthesia-avatar/scripts/synthesia_client.py <command> [options]
```

Inspect responses or configuration using `read_file`.

## Quick Reference

| Command | Key Arguments | Purpose |
| --- | --- | --- |
| `validate-key` | `[--api-key KEY]` | Verify Synthesia credentials and reachability |
| `provision-avatar` | `--source-id av_xxx [--regenerate]` | Convert Studio avatar to interactive avatar |
| `avatar-status` | `--source-id av_xxx` | Poll provisioning state (`queued`, `completed`, `failed`) |
| `start-session` | `--avatar-id av_xxx --livekit-url URL --livekit-token TOKEN` | Start real-time WebRTC avatar session |

## Procedure

1. **Verify Credentials**: Run `python skills/creative/synthesia-avatar/scripts/synthesia_client.py validate-key` via `terminal` to confirm API authentication.
2. **Provision Avatar**: Use `provision-avatar --source-id av_xxx` to initiate interactive avatar conversion.
3. **Poll Generation Status**: Check progress with `avatar-status --source-id av_xxx`. When `done` is `true` and `status` is `completed`, the avatar is ready.
4. **Connect LiveKit Session**: Start the session with `start-session --avatar-id av_xxx --livekit-url wss://your-livekit-url --livekit-token your-token`.

## Pitfalls

- **Concurrency Limits**: Free accounts permit 1 concurrent session; paid accounts permit up to 100 concurrent sessions. Exceeding limits returns HTTP `429` with `concurrency_limit`.
- **Asynchronous Creation**: Avatar generation is asynchronous; do not start a session until `status` is `completed`.
- **LiveKit Prerequisites**: Interactive avatar streams require LiveKit server credentials (`wss://...`) and client tokens to receive video and audio tracks.

## Verification

Run `validate-key` with the `terminal` tool to verify network connectivity and credentials:

```bash
python skills/creative/synthesia-avatar/scripts/synthesia_client.py validate-key
```

A return code of `0` with `"valid": true` confirms ready operational status.
