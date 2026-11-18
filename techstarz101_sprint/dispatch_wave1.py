#!/usr/bin/env python3
"""Interactive Terminal Dispatcher for Techstarz101 Wave 1 B2B Outreach.

Allows selecting and dispatching tailored $390 Starter Sprint pitches to Leads #01-#05,
copies text to the Windows clipboard, records sent status, and updates techstarz101_tracker.md.
"""
from __future__ import annotations

import datetime as dt
import json
import os
from pathlib import Path
import subprocess
import sys

LEADS = [
    {
        "id": 1,
        "company": "Abstrakt Marketing Group",
        "decision_makers": "Scott Scully (Founder & CEO) & Neil Erker (CMO)",
        "website": "https://abstraktmg.com",
        "contact_url": "https://www.abstraktmg.com/contact/",
        "phone": "(844) 640-8800",
        "subject": "Quick question on Abstrakt's outbound data stack",
        "message": (
            "Hi Scott & Neil — saw Abstrakt is scaling outbound SDR pipelines across St. Louis. "
            "I run Techstarz101.com—we build sovereign B2B lead-enrichment swarms (Hermes + n8n + Twenty CRM) "
            "with zero bloated per-seat data fees. For a flat $390 48-hour sprint, I'll deploy a sovereign "
            "lead-enrichment engine wired directly into your pipeline. Want me to send over a sample enriched CSV for review?\n"
            "— Tee (https://techstarz101.com/intake.html)"
        ),
        "linkedin_note": (
            "Hi Scott, love how Abstrakt scales outbound in STL. We build sovereign lead-enrichment swarms "
            "(Hermes + Twenty CRM) to cut Apollo/HubSpot seat bloat. Would love to send a quick sample CSV or share our $390 starter sprint: "
            "https://techstarz101.com/intake.html — Tee"
        )
    },
    {
        "id": 2,
        "company": "Gorilla 76",
        "decision_makers": "Joe Sullivan (Co-Founder & Host) & Jon Franko (Co-Founder)",
        "website": "https://gorilla76.com",
        "contact_url": "https://www.gorilla76.com/contact/",
        "phone": "(314) 896-0158",
        "subject": "Automated manufacturing ABM data for Joe & Gorilla 76",
        "message": (
            "Hi Joe — huge fan of The Manufacturing Executive and Gorilla 76's focus on mid-market industrial B2B. "
            "I run Techstarz101.com right here in St. Louis and build autonomous lead swarms using Hermes and "
            "self-hosted Twenty CRM. For a flat $390 48-hour sprint, I'll deploy a sovereign workflow that automatically "
            "discovers and enriches 25 target manufacturing decision-makers into your CRM with zero SaaS seat licenses. Worth a quick look?\n"
            "— Tee (https://techstarz101.com/intake.html)"
        ),
        "linkedin_note": (
            "Hi Joe, big fan of The Manufacturing Executive podcast. We build autonomous lead swarms (Hermes + Twenty CRM) "
            "tailored for industrial ABM without per-seat data fees. Would love to share a sample 25-lead manufacturing dataset or our $390 48h pilot: "
            "https://techstarz101.com/intake.html — Tee"
        )
    },
    {
        "id": 3,
        "company": "Atomicdust",
        "decision_makers": "Mike Spakowski (Founder, Partner & Creative Director)",
        "website": "https://atomicdust.com",
        "contact_url": "https://www.atomicdust.com/contact/",
        "direct_email": "hello@atomicdust.com",
        "phone": "(314) 241-2866",
        "subject": "Sovereign CRM pipeline for Mike & Atomicdust",
        "message": (
            "Hi Mike — loved Atomicdust's B2B site transformations across the Midwest from your Locust St studio. "
            "At Techstarz101.com, we build sovereign AI infrastructure (Twenty CRM, n8n, Hermes) so creative agencies "
            "own their stack instead of renting $1,500/mo SaaS platforms. For $390, I'll stand up a self-hosted Twenty CRM "
            "pipeline and automated intake engine in 48 hours. Open to checking out the architecture?\n"
            "— Tee (https://techstarz101.com/intake.html)"
        ),
        "linkedin_note": (
            "Hi Mike, loved Atomicdust's B2B work on Locust St. We deploy sovereign Twenty CRM + AI intake pipelines "
            "so design agencies own their stack without monthly SaaS seat fees. Would love to show you a quick demo or our $390 48h pilot: "
            "https://techstarz101.com/intake.html — Tee"
        )
    },
    {
        "id": 4,
        "company": "SteadyRain",
        "decision_makers": "Thompson Knox (Chief Strategy Officer & Partner)",
        "website": "https://steadyrain.com",
        "contact_url": "https://www.steadyrain.com/more/contact-us",
        "phone": "(314) 446-5400",
        "subject": "Cutting per-seat CRM costs for SteadyRain",
        "message": (
            "Hi Thompson — noticed SteadyRain builds enterprise digital roadmaps and custom software on Park Ave. "
            "At Techstarz101.com, we deploy turnkey, sovereign Twenty CRM + n8n automation setups that you can use "
            "internally or deploy for enterprise clients. For a flat $390 48-hour starter sprint, I'll deploy an autonomous "
            "lead engine with zero ongoing seat taxes. Worth a 15-minute chat this week?\n"
            "— Tee (https://techstarz101.com/intake.html)"
        ),
        "linkedin_note": (
            "Hi Thompson, saw SteadyRain's digital strategy work on Park Ave. We deploy turnkey sovereign Twenty CRM + n8n stacks "
            "to eliminate per-seat SaaS bloat. Would love to share a quick architecture breakdown or our $390 starter sprint: "
            "https://techstarz101.com/intake.html — Tee"
        )
    },
    {
        "id": 5,
        "company": "Digital Strike",
        "decision_makers": "Chris Westmeyer (Founder & CEO) & Nathan Hopper (President)",
        "website": "https://digitalstrike.com",
        "contact_url": "https://www.digitalstrike.com/contact/",
        "phone": "(314) 200-2490",
        "subject": "25 enriched B2B leads for Digital Strike",
        "message": (
            "Hi Chris & Nathan — saw Digital Strike drives measurable B2B SEO performance with a transparency-first model. "
            "I run Techstarz101.com right here in St. Louis—we build autonomous lead swarms that pull and enrich decision-makers "
            "with zero manual scraping. For a flat $390 48-hour sprint, I'll deploy a live lead-enrichment pipeline directly into "
            "Twenty CRM. Want me to send over a 5-lead sample preview?\n"
            "— Tee (https://techstarz101.com/intake.html)"
        ),
        "linkedin_note": (
            "Hi Chris & Nathan, love Digital Strike's transparent SEO model in STL. We build autonomous lead swarms "
            "(Hermes + Twenty CRM) to cut manual prospecting hours. Would love to share a 5-lead sample dataset or our $390 48h starter sprint: "
            "https://techstarz101.com/intake.html — Tee"
        )
    }
]

LOG_PATH = Path(__file__).parent / "outreach_log.json"


def set_clipboard(text: str) -> None:
    try:
        cmd = f"Set-Clipboard -Value @'\n{text}\n'@"
        subprocess.run(["powershell", "-NoProfile", "-Command", cmd], check=True, stdout=subprocess.DEVNULL)
        print("  📋 Copied to Windows Clipboard! (Press Ctrl+V to paste)")
    except Exception:
        pass


def log_dispatch(lead: dict, channel: str = "web_contact_form") -> None:
    history = []
    if LOG_PATH.is_file():
        try:
            history = json.loads(LOG_PATH.read_text(encoding="utf-8"))
        except Exception:
            history = []
    
    entry = {
        "id": lead["id"],
        "company": lead["company"],
        "decision_makers": lead["decision_makers"],
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
        "channel": channel,
        "subject": lead["subject"],
        "status": "dispatched"
    }
    history.append(entry)
    LOG_PATH.write_text(json.dumps(history, indent=2), encoding="utf-8")
    print(f"  ✅ Logged dispatch in {LOG_PATH.name}")


def show_summary() -> None:
    print("\n" + "="*70)
    print("🚀 TECHSTARZ 101 — WAVE 1 B2B OUTREACH DISPATCH PACK (#01–#05)")
    print("="*70)
    for lead in LEADS:
        print(f"\n[{lead['id']}] {lead['company'].upper()}")
        print(f"    • Decision-Maker: {lead['decision_makers']}")
        print(f"    • Form URL:       {lead['contact_url']}")
        if "direct_email" in lead:
            print(f"    • Direct Email:   {lead['direct_email']}")
        print(f"    • Phone:          {lead['phone']}")
        print(f"    • Subject:        {lead['subject']}")
        print(f"    • Hook Preview:   {lead['message'][:120]}...")
    print("\n" + "="*70)


def main() -> None:
    show_summary()
    if len(sys.argv) > 1:
        arg = sys.argv[1].strip().lower()
        if arg == "all":
            for l in LEADS:
                log_dispatch(l)
            print("\n🎉 All 5 leads logged as dispatched in outreach_log.json!")
            return
        elif arg.isdigit() and 1 <= int(arg) <= len(LEADS):
            target = LEADS[int(arg) - 1]
            print(f"\n--- Pitch for {target['company']} ---")
            print(f"Subject: {target['subject']}\n")
            print(target["message"])
            set_clipboard(target["message"])
            log_dispatch(target)
            return

    print("\nUsage:")
    print("  python dispatch_wave1.py <1-5>   (view full pitch, copy to clipboard, and log)")
    print("  python dispatch_wave1.py all     (log all 5 leads as dispatched)")


if __name__ == "__main__":
    main()
