# Product Requirements Document (PRD) — Service #15: Cyber Security Package

## 1. Objective
Give SMBs, agencies, and engineering teams a complete, 100% open-source, self-hosted **defensive security operations (SOC) & AppSec package** covering SAST, authorized DAST, container/SBOM CVE scanning, active brute-force IPS, zero-knowledge credential management, offline DFIR analysis, and automated SOAR alerting.

## 2. Core Defensive Pillars
1. **Shift-Left AppSec:** Catch OWASP Top 10 flaws, hardcoded credentials, and vulnerable Docker layers before production via **SonarQube** (`:7520`), **Aqua Trivy** (`:7510`), and authorized **OWASP ZAP** (`:7500`) baseline scans.
2. **Runtime Perimeter Defense & Availability:** Detect and block brute-force/CVE probing with **CrowdSec** (`:7600`) and monitor SSL/TLS certificate expiry 24/7 with **Uptime Kuma** (`:7530`).
3. **Zero-Trust Secrets & Incident Response:** Centralize team secrets in **Vaultwarden** (`:7610`), analyze suspicious artifacts safely offline in **GCHQ CyberChef** (`:7620`), and route high-severity alerts through **n8n SOAR** (`:7630`).
4. **Authorized Use Only:** All active scanners (OWASP ZAP, Trivy) are strictly intended for assets owned or explicitly authorized by the operator.
