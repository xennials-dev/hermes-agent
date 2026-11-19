#!/usr/bin/env python3
"""Multi-Tenant Client Provisioning Engine for Techstarz101 Postiz Agency Stack."""
import sys
from pathlib import Path
orig = Path(r"C:\Users\tee\AppData\Local\hermes\skills\social-media\postiz\scripts\provision_client_tenant.py")
if orig.is_file():
    exec(orig.read_text(encoding="utf-8"))
else:
    print("Provision script not found at base path.", file=sys.stderr)

