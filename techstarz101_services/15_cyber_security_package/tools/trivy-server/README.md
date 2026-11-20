# 🔬 Aqua Trivy CVE Server (`trivy-server`)

**Stack A · Service #15: Cyber Security Package (`TS101-SRV-15`)**

- **Role:** Fast container image, filesystem, IaC & SBOM vulnerability scanning server
- **Upstream Repo:** https://github.com/aquasecurity/trivy
- **License:** Apache-2.0
- **Local App URL:** http://localhost:7510/healthz
- **One-Click Hub Launch Link:** `http://localhost:7879/t/trivy-server`
- **Estimated RAM:** ~550 MB

## Run Standalone (Independent of Hub)

```bash
cp .env.example .env
docker compose up -d
```

## First-Run Notes
Run `trivy image --server http://localhost:7510 <image>` in CI/CD or from n8n SOAR.
