#!/usr/bin/env python3
"""OBS Studio Web Approval Preview & 1-Click 10-Channel Launch Console (http://localhost:7875)."""
from __future__ import annotations

import http.server
import json
from pathlib import Path
import subprocess
import urllib.parse

PORT = 7875
VIDEO_PATH = Path(r"C:\Users\tee\projects\video-agent\output\output_vertical.mp4")
POSTIZ_CLI = Path(r"C:\Users\tee\AppData\Local\hermes\skills\social-media\postiz\scripts\postiz_cli.py")
PY_EXE = r"C:\Users\tee\AppData\Local\hermes\tools\python-3.14.9+20261021-win32-x64\python.exe"

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>OBS Studio — Techstarz101.com Video Approval Monitor</title>
  <style>
    body { margin: 0; background: #0e0f14; color: #f1f5f9; font-family: system-ui, -apple-system, sans-serif; display: flex; flex-direction: column; min-height: 100vh; }
    header { background: #181a22; border-bottom: 1px solid #2d3142; padding: 14px 24px; display: flex; justify-content: space-between; align-items: center; }
    .badge { background: #ef4444; color: #fff; font-weight: 700; font-size: 12px; padding: 4px 10px; border-radius: 999px; letter-spacing: 0.05em; }
    main { flex: 1; display: grid; grid-template-columns: 420px 1fr; gap: 28px; padding: 28px; max-width: 1280px; margin: 0 auto; width: 100%; box-sizing: border-box; }
    .monitor { background: #14161f; border: 2px solid #334155; border-radius: 14px; padding: 16px; display: flex; flex-direction: column; align-items: center; }
    video { width: 100%; max-width: 360px; aspect-ratio: 9 / 16; border-radius: 10px; background: #000; box-shadow: 0 12px 32px rgba(0,0,0,0.6); }
    .panel { background: #14161f; border: 1px solid #2d3142; border-radius: 14px; padding: 24px; display: flex; flex-direction: column; gap: 18px; }
    .copy-box { background: #0b0c10; border: 1px solid #334155; border-radius: 8px; padding: 14px; font-size: 14px; line-height: 1.5; color: #cbd5e1; }
    .channels { display: flex; flex-wrap: wrap; gap: 8px; }
    .ch { background: #1e293b; border: 1px solid #475569; padding: 6px 12px; border-radius: 6px; font-size: 13px; }
    .actions { display: flex; gap: 14px; margin-top: 8px; }
    button { cursor: pointer; border: none; border-radius: 8px; padding: 14px 22px; font-size: 15px; font-weight: 700; transition: 0.15s; }
    .btn-approve { background: #10b981; color: #052e16; flex: 1; }
    .btn-approve:hover { background: #34d399; }
    .btn-obs { background: #3b82f6; color: #fff; }
    #status { margin-top: 12px; padding: 12px; border-radius: 8px; display: none; font-size: 14px; white-space: pre-wrap; }
  </style>
</head>
<body>
  <header>
    <div><strong>🎬 OBS Studio Program Monitor</strong> — Scene: <code>Techstarz101 Approval Preview</code> (9:16 Vertical 1080×1920)</div>
    <span class="badge">AWAITING USER APPROVAL</span>
  </header>
  <main>
    <div class="monitor">
      <video src="/video.mp4" controls autoplay loop muted playsinline></video>
      <p style="font-size:12px;color:#94a3b8;margin-top:10px;">Overlay: "Stop renting your software. Own your AI stack."</p>
    </div>
    <div class="panel">
      <h2 style="margin:0;">Final Post Preview & 10-Channel Approval Gate</h2>
      <div>
        <div style="font-size:12px;color:#94a3b8;margin-bottom:6px;">POST COPY (STAGED IN POSTIZ):</div>
        <div class="copy-box" id="postCopy">At Techstarz101.com, we build sovereign AI systems (n8n, Twenty CRM, Listmonk, Hermes) that cut SaaS bloat and replace manual ops. For a flat $390 48-hour sprint, I'll audit your stack and deploy your first live AI workflow—and if it doesn't save you real hours or monthly SaaS spend, you don't pay. https://techstarz101.com/intake.html</div>
      </div>
      <div>
        <div style="font-size:12px;color:#94a3b8;margin-bottom:6px;">QUEUED DESTINATION CHANNELS (10):</div>
        <div class="channels">
          <span class="ch">✅ Bluesky</span>
          <span class="ch">✅ Instagram</span>
          <span class="ch">✅ Facebook Page</span>
          <span class="ch">✅ X (Twitter)</span>
          <span class="ch">✅ TikTok</span>
          <span class="ch">✅ TikTok Business</span>
          <span class="ch">✅ Reddit</span>
          <span class="ch">✅ Discord</span>
          <span class="ch">✅ Threads</span>
          <span class="ch">✅ YouTube</span>
        </div>
      </div>
      <div class="actions">
        <button class="btn-approve" onclick="approveNow()">✅ APPROVE & LAUNCH TO ALL 10 PLATFORMS NOW</button>
        <button class="btn-obs" onclick="window.open('http://2.25.238.185:4200/launches', '_blank')">Open Postiz Queue ↗</button>
      </div>
      <div id="status"></div>
    </div>
  </main>
  <script>
    async function approveNow() {
      const st = document.getElementById('status');
      st.style.display = 'block';
      st.style.background = '#1e293b';
      st.textContent = 'Publishing live across all 10 connected Postiz channels...';
      const r = await fetch('/approve', { method: 'POST' });
      const data = await r.json();
      st.style.background = data.ok ? '#064e3b' : '#7f1d1d';
      st.textContent = data.output || JSON.stringify(data, null, 2);
    }
  </script>
</body>
</html>
"""


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        if self.path.startswith("/video.mp4"):
            data = VIDEO_PATH.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "video/mp4")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        body = HTML_PAGE.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path == "/approve":
            pitch = (
                "At Techstarz101.com, we build sovereign AI systems (n8n, Twenty CRM, Listmonk, Hermes) "
                "that cut SaaS bloat and replace manual ops. For a flat $390 48-hour sprint, I'll audit "
                "your stack and deploy your first live AI workflow—and if it doesn't save you real hours "
                "or monthly SaaS spend, you don't pay. https://techstarz101.com/intake.html"
            )
            res = subprocess.run(
                [PY_EXE, "-X", "utf8", str(POSTIZ_CLI), "post", "--type", "now", "--content", pitch],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            payload = json.dumps({"ok": res.returncode == 0, "output": res.stdout.strip() or res.stderr.strip()}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)


if __name__ == "__main__":
    server = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"OBS Studio Web Approval Monitor running at http://localhost:{PORT}")
    server.serve_forever()

