# System Architecture — Service #15: Cyber Security Package

## 1. Continuous Defensive Security Loop
```
CI/CD & Production Surfaces
   ├─► SonarQube SAST (:7520) — static code & secret leak review
   ├─► Aqua Trivy Server (:7510) — container & SBOM CVE scanning
   ├─► OWASP ZAP (:7500) — authorized web/API DAST baseline audits
   ├─► Uptime Kuma (:7530) — 24/7 TLS cert expiry & availability watch
   └─► CrowdSec IPS (:7600) — real-time brute-force & probing mitigation
          │
          ▼
   n8n SOAR Playbooks (:7630)
          ├─► Critical CVE & Ban Escalation Alerts
          ├─► GCHQ CyberChef (:7620) — offline DFIR / IOC triage
          └─► Vaultwarden (:7610) — zero-knowledge credential rotation
```

## 2. Port & Network Isolation
- **Modular Hub:** `http://localhost:7879`
- **Stack A:** `:7500` (OWASP ZAP), `:7510` (Trivy), `:7520` (SonarQube), `:7530` (Uptime Kuma)
- **Stack B:** `:7600` (CrowdSec), `:7610` (Vaultwarden), `:7620` (CyberChef), `:7630` (n8n SOAR)
