#!/usr/bin/env python3
"""Autonomous Chrome CDP Publisher for Reddit (r/TechStarz101), Threads (@techstarz101), and Facebook (techstarz101).

Launches Google Chrome with remote debugging enabled on port 9222, attaches via Chrome DevTools Protocol (CDP)
over WebSockets, logs in or uses the active session, fills the post composer, and clicks the Post/Submit button.
"""
from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
import shutil
import subprocess
import urllib.request
import websockets

CHROME_EXE = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
DEFAULT_USER_DATA = Path(os.environ.get("LOCALAPPDATA", r"C:\Users\tee\AppData\Local")) / "Google" / "Chrome" / "User Data"
AUTO_USER_DATA = Path(os.environ.get("LOCALAPPDATA", r"C:\Users\tee\AppData\Local")) / "Google" / "Chrome" / "AutomationData"

POST_TITLE = "Stop renting your software. Own your AI stack — Techstarz101.com ($390 48-Hour Starter Sprint)"
POST_BODY = (
    "Stop renting your software. Own your AI stack.\n\n"
    "At Techstarz101.com, we build sovereign AI systems (n8n, Twenty CRM, Listmonk, Hermes) "
    "that cut SaaS bloat and replace manual ops. For a flat $390 48-hour sprint, I'll audit "
    "your stack and deploy your first live AI workflow—and if it doesn't save you real hours "
    "or monthly SaaS spend in week 1, you don't pay.\n\n"
    "Book your 48-hour starter sprint: https://techstarz101.com/intake.html\n"
    "Full architecture breakdown: https://techstarz101.com/blog.html"
)


def sync_profile_cookies() -> None:
    AUTO_USER_DATA.mkdir(parents=True, exist_ok=True)
    auto_default = AUTO_USER_DATA / "Default"
    auto_default.mkdir(parents=True, exist_ok=True)
    src_default = DEFAULT_USER_DATA / "Default"

    for fname in ["Local State"]:
        s = DEFAULT_USER_DATA / fname
        if s.is_file():
            try:
                shutil.copy2(s, AUTO_USER_DATA / fname)
            except OSError:
                pass

    for rel in ["Preferences", "Login Data", "Web Data", "Network/Cookies", "Cookies"]:
        s = src_default / rel
        d = auto_default / rel
        if s.is_file():
            d.parent.mkdir(parents=True, exist_ok=True)
            try:
                shutil.copy2(s, d)
            except OSError:
                pass


class CDPPage:
    def __init__(self, ws_url: str):
        self.ws_url = ws_url
        self.ws = None
        self.msg_id = 0

    async def __aenter__(self):
        self.ws = await websockets.connect(self.ws_url, max_size=50 * 1024 * 1024)
        await self.call("Page.enable")
        await self.call("Runtime.enable")
        await self.call("DOM.enable")
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self.ws:
            await self.ws.close()

    async def call(self, method: str, params: dict | None = None) -> dict:
        self.msg_id += 1
        req_id = self.msg_id
        await self.ws.send(json.dumps({"id": req_id, "method": method, "params": params or {}}))
        while True:
            raw = await asyncio.wait_for(self.ws.recv(), timeout=20)
            msg = json.loads(raw)
            if msg.get("id") == req_id:
                return msg.get("result", {})

    async def eval(self, expression: str):
        res = await self.call(
            "Runtime.evaluate",
            {"expression": expression, "returnByValue": True, "awaitPromise": True},
        )
        return res.get("result", {}).get("value")


async def automate_reddit(ws_url: str) -> dict:
    async with CDPPage(ws_url) as page:
        await asyncio.sleep(5)
        info = await page.eval("({url: location.href, title: document.title, text: document.body.innerText.slice(0, 600)})")
        print("[Reddit] Loaded:", info.get("url"))

        # Check if on login page or login modal visible (piercing Reddit shreddit shadowRoot)
        if "login" in str(info.get("url", "")).lower() or "log in" in str(info.get("text", "")).lower():
            login_res = await page.eval("""
            (() => {
                const findInput = (sel) => {
                    const direct = document.querySelector(sel);
                    if (direct && direct.tagName === 'INPUT') return direct;
                    if (direct && direct.shadowRoot) return direct.shadowRoot.querySelector('input');
                    return null;
                };
                const userInp = findInput('faceplate-text-input#login-username') || findInput('input[name="username"]') || findInput('#loginUsername');
                const passInp = findInput('faceplate-text-input#login-password') || findInput('input[name="password"]') || findInput('#loginPassword');
                if (userInp && passInp) {
                    const setVal = (el, val) => {
                        el.focus();
                        const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                        setter.call(el, val);
                        el.dispatchEvent(new Event('input', { bubbles: true, composed: true }));
                        el.dispatchEvent(new Event('change', { bubbles: true, composed: true }));
                    };
                    setVal(userInp, 'techstarz101');
                    setVal(passInp, '#6052Garfield');
                    const btns = Array.from(document.querySelectorAll('button.login, button[type="submit"], button'));
                    const loginBtn = btns.find(b => /log in/i.test(b.innerText || b.textContent || ''));
                    if (loginBtn) loginBtn.click();
                    return 'submitted_shadow_login';
                }
                return 'login_inputs_not_found';
            })()
            """)
            print("[Reddit] Login step:", login_res)
            await asyncio.sleep(8)

        # Try filling and clicking Submit/Post on Reddit submit page
        post_res = await page.eval("""
        (() => {
            // Click Post button if already pre-filled via URL query params
            const buttons = Array.from(document.querySelectorAll('button, r-post-form-submit-button'));
            for (const b of buttons) {
                const txt = (b.innerText || b.textContent || '').trim();
                if (/^post$|^submit$/i.test(txt) && !b.disabled) {
                    b.click();
                    return 'clicked_post_button';
                }
            }
            // Also check shadow roots (Reddit shreddit uses web components)
            const findInShadow = (root) => {
                const all = root.querySelectorAll('*');
                for (const el of all) {
                    if (el.tagName === 'BUTTON' && /^post$|^submit$/i.test((el.innerText || '').trim()) && !el.disabled) {
                        el.click();
                        return 'clicked_shadow_post_button';
                    }
                    if (el.shadowRoot) {
                        const r = findInShadow(el.shadowRoot);
                        if (r) return r;
                    }
                }
                return null;
            };
            return findInShadow(document) || 'awaiting_user_click_or_signin';
        })()
        """)
        await asyncio.sleep(4)
        final_url = await page.eval("location.href")
        return {"platform": "reddit", "action": post_res, "url": final_url}


async def automate_threads(ws_url: str) -> dict:
    async with CDPPage(ws_url) as page:
        await asyncio.sleep(5)
        info = await page.eval("({url: location.href, title: document.title, text: document.body.innerText.slice(0, 600)})")
        print("[Threads] Loaded:", info.get("url"))

        # Check if login form is visible
        login_res = await page.eval("""
        (() => {
            const inputs = Array.from(document.querySelectorAll('input'));
            const userInp = inputs.find(i => i.type === 'text' || /username|phone|email/i.test(i.placeholder || ''));
            const passInp = inputs.find(i => i.type === 'password');
            if (userInp && passInp) {
                const setVal = (el, val) => {
                    el.focus();
                    const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                    setter.call(el, val);
                    el.dispatchEvent(new Event('input', { bubbles: true }));
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                };
                setVal(userInp, 'tfisher@techstarz101.com');
                setVal(passInp, '#6052Garfield');
                const btn = Array.from(document.querySelectorAll('div[role="button"], button')).find(b => /^log in$/i.test((b.innerText || '').trim()));
                if (btn) btn.click();
                return 'submitted_threads_login';
            }
            return 'no_login_form';
        })()
        """)
        if login_res == "submitted_threads_login":
            print("[Threads] Submitted login, waiting 7s...")
            await asyncio.sleep(7)

        post_res = await page.eval("""
        (() => {
            const btns = Array.from(document.querySelectorAll('div[role="button"], button'));
            const postBtn = btns.find(b => /^post$/i.test((b.innerText || '').trim()));
            if (postBtn) {
                postBtn.click();
                return 'clicked_threads_post';
            }
            return 'awaiting_user_click_or_signin';
        })()
        """)
        await asyncio.sleep(4)
        final_url = await page.eval("location.href")
        return {"platform": "threads", "login": login_res, "action": post_res, "url": final_url}


async def automate_facebook(ws_url: str) -> dict:
    async with CDPPage(ws_url) as page:
        await asyncio.sleep(5)
        info = await page.eval("({url: location.href, title: document.title})")
        print("[Facebook] Loaded:", info.get("url"))

        login_res = await page.eval("""
        (() => {
            const emailInp = document.querySelector('input[name="email"], input#email');
            const passInp = document.querySelector('input[name="pass"], input#pass');
            if (emailInp && passInp) {
                const setVal = (el, val) => {
                    el.focus();
                    const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                    setter.call(el, val);
                    el.dispatchEvent(new Event('input', { bubbles: true }));
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                };
                setVal(emailInp, 'tfisher314@gmail.com');
                setVal(passInp, '#6149Hancock');
                const btn = document.querySelector('button[name="login"], input[type="submit"], div[aria-label="Log in"], div[aria-label="Accessible login button"]');
                if (btn) btn.click();
                return 'submitted_facebook_login';
            }
            return 'no_login_form';
        })()
        """)
        if login_res == "submitted_facebook_login":
            print("[Facebook] Submitted login, waiting 7s...")
            await asyncio.sleep(7)

        post_res = await page.eval("""
        (() => {
            const postBtn = Array.from(document.querySelectorAll('div[role="button"], button')).find(
                b => /^post$|^publish$|^share now$/i.test((b.innerText || b.getAttribute('aria-label') || '').trim())
            );
            if (postBtn) {
                postBtn.click();
                return 'clicked_facebook_post';
            }
            return 'awaiting_user_click_or_signin';
        })()
        """)
        await asyncio.sleep(4)
        final_url = await page.eval("location.href")
        return {"platform": "facebook", "login": login_res, "action": post_res, "url": final_url}


async def main() -> None:
    sync_profile_cookies()
    urls = [
        "https://www.reddit.com/r/TechStarz101/submit?title=Stop%20renting%20your%20software.%20Own%20your%20AI%20stack%20%E2%80%94%20Techstarz101.com&text=At%20Techstarz101.com%2C%20we%20build%20sovereign%20AI%20systems%20(n8n%2C%20Twenty%20CRM%2C%20Listmonk%2C%20Hermes)%20that%20cut%20SaaS%20bloat%20and%20replace%20manual%20ops.%20For%20a%20flat%20%24390%2048-hour%20sprint%2C%20I'll%20audit%20your%20stack%20and%20deploy%20your%20first%20live%20AI%20workflow%3A%20https%3A%2F%2Ftechstarz101.com%2Fintake.html",
        "https://www.threads.com/intent/post?text=Stop%20renting%20your%20software.%20Own%20your%20AI%20stack.%20At%20Techstarz101.com%2C%20we%20build%20sovereign%20AI%20systems%20(n8n%2C%20Twenty%20CRM%2C%20Listmonk%2C%20Hermes)%20that%20cut%20SaaS%20bloat.%20Flat%20%24390%2048-hour%20sprint%3A%20https%3A%2F%2Ftechstarz101.com%2Fintake.html",
        "https://www.facebook.com/people/techstarz101/61596716728528/",
    ]
    proc = subprocess.Popen(
        [
            str(CHROME_EXE),
            "--remote-debugging-port=9222",
            f"--user-data-dir={AUTO_USER_DATA}",
            "--no-first-run",
            "--no-default-browser-check",
            *urls,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(20):
        try:
            targets = json.loads(urllib.request.urlopen("http://127.0.0.1:9222/json", timeout=3).read().decode("utf-8"))
            if targets:
                break
        except Exception:
            await asyncio.sleep(1)

    await asyncio.sleep(5)
    targets = json.loads(urllib.request.urlopen("http://127.0.0.1:9222/json", timeout=5).read().decode("utf-8"))
    pages = [t for t in targets if t.get("type") == "page"]
    print(f"Connected to Chrome CDP (found {len(pages)} open tabs)")

    results = []
    for p in pages:
        u = p.get("url", "")
        ws = p.get("webSocketDebuggerUrl")
        if not ws:
            continue
        if "reddit.com" in u:
            results.append(await automate_reddit(ws))
        elif "threads.net" in u or "threads.com" in u:
            results.append(await automate_threads(ws))
        elif "facebook.com" in u:
            results.append(await automate_facebook(ws))

    print("\n=== CHROME CDP AUTOMATION SUMMARY ===", flush=True)
    print(json.dumps(results, indent=2), flush=True)
    # Keep Chrome window open for user inspection
    while proc.poll() is None:
        await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())
