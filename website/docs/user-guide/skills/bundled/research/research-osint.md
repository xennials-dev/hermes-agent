---
title: "Osint — Probe OSINT on people, handles, emails, and phone numbers"
sidebar_label: "Osint"
description: "Probe OSINT on people, handles, emails, and phone numbers"
---

{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */}

# Osint

Probe OSINT on people, handles, emails, and phone numbers.

## Skill metadata

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/research/osint` |
| Version | `1.0.0` |
| Author | Hermes Agent |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `Research`, `OSINT`, `Security`, `Reconnaissance` |
| Related skills | [`grounded-citations`](../../bundled/research/research-grounded-citations.md), [`arxiv`](../../bundled/research/research-arxiv.md) |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# OSINT Investigation Framework (Awesome-OSINT)

Open Source Intelligence framework grounded in Awesome-OSINT.

## Proactive Behavior Contract

When asked for information, background, verification, or intelligence about a **person**, **username**, **email address**, **phone number**, or **online entity**:
1. Proactively run reconnaissance across applicable vectors (username, email, social footprint, public records).
2. Synthesize findings into an **Intelligence Dossier** with verified source citations, confidence ratings, and cross-referenced identities.

---

## Investigation Vectors & Tactical Playbook

### 1. Username & Handle Reconnaissance
When given a handle or username (e.g. `johndoe`, `crypto_dev`):
- Run the bundled reconnaissance utility:
  ```bash
  python skills/research/osint/scripts/person_recon.py --username <username>
  ```
- Cross-reference with major developer and social platforms:
  - **Developer**: GitHub (`api.github.com/users/<user>`), GitLab, PyPI, npm, DockerHub.
  - **Forums & Tech**: Hacker News (`news.ycombinator.com/user?id=<user>`), Reddit, Medium, Dev.to.
  - **Social & Messaging**: Twitter/X, Telegram (`t.me/<user>`), Keybase, Steam.
- Extract avatar hashes, bios, PGP keys, mutual followers, and commit author emails.

### 2. Email Address Intelligence
When an email address is provided or discovered:
- Run email reconnaissance:
  ```bash
  python skills/research/osint/scripts/person_recon.py --email <email>
  ```
- **Gravatar & Avatars**: Check Gravatar MD5 hash to discover linked real names, blogs, and public profile images.
- **Breach Exposure**: Query breach records (HaveIBeenPwned patterns, DeHashed, LeakCheck) to assess compromise history and affiliated usernames.
- **Domain Verification**: Inspect domain MX/SPF records, WHOIS, and corporate associations.

### 3. Phone Number & Telephony OSINT
When analyzing a phone number:
- Format and normalize into E.164:
  ```bash
  python skills/research/osint/scripts/person_recon.py --phone <number>
  ```
- Check carrier, line type (VoIP, mobile, landline), and country code via public lookup APIs (FreeCarrierLookup, NumVerify, Sync.ME).
- Search for messaging apps registration (WhatsApp, Telegram, Signal).

### 4. Public Records, Corporate & Legal Checks
- **Company & Corporate**: OpenSanctions, Crunchbase, SEC filings, UK Companies House.
- **Court & Legal**: Judyrecords, Caselaw Access Project, California Justice Watch.
- **Sanctions & PEP**: OpenSanctions database for public office holders and watchlist matches.

---

## Output Format: Executive Intelligence Dossier

Format findings into a structured Markdown report:

```markdown
# OSINT Dossier: [Target Name / Handle]

### Executive Summary
- Primary Identifier: [Target Identifier]
- Target Category: [Individual / Developer / Executive / Alias]
- Confidence Rating: [High / Medium / Preliminary]
- Key Findings: [Summary of key discovered facts]

### 1. Discovered Digital Identities & Social Accounts
| Platform | Handle / URL | Status | Verified Attributes |
|---|---|---|---|
| GitHub | [link] | Active | 42 repos |

### 2. Contact & Telecom Vectors
- Email Addresses: [Discovered emails, gravatar matches]
- Phone Information: [Carrier, country, line type]
- Associated Domains: [Personal blogs, portfolio sites]

### 3. Breach & Exposure Assessment
- Known Breaches: [Breach events or clean status]
- Public Keys / PGP: [PGP fingerprint or Keybase proofs]

### 4. Cross-Referenced Evidence & Timeline
- Timeline events, commit timestamps, public activity.

### 5. Recommended Next Steps
- Specific areas where further pivoting or human validation is recommended.
```
