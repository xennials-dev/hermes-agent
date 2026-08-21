---
name: cybersecurity-audit
description: "Audit source code, dependencies, and cloud security posture."
version: 1.0.0
author: Terrance (tee), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Cybersecurity, Audit, SAST, SecurityPosture, Hardening, DevOps]
    related_skills: [sdlc-review, caprover]
---

# Defensive Cybersecurity & Code Security Auditing

Perform static application security testing (SAST), secrets detection, and infrastructure hardening audits.

---

## 1. Quick Reference

| Audit Type | Tool | Command |
|---|---|---|
| **Secrets Scanning** | TruffleHog / Gitleaks | `gitleaks detect --source . -v` |
| **Python Vulnerabilities** | Bandit | `bandit -r ./src -ll` |
| **Node.js Dependencies** | npm audit | `npm audit --audit-level=high` |
| **Docker Container Security** | Trivy | `trivy image my-container:latest` |

---

## 2. Source Code Vulnerability Review Checklist

- [ ] **Input Sanitization**: Ensure SQL parameterized queries, NoSQL input escaping, and command execution boundaries.
- [ ] **Authentication & Tokens**: Validate JWT expiry, secure cookie flags (`HttpOnly; Secure; SameSite=Strict`), and constant-time token comparison.
- [ ] **Access Controls (RBAC)**: Check authorization decorator gates on administrative endpoints.
- [ ] **Secrets Management**: Verify zero hardcoded API keys or credentials in source control.
