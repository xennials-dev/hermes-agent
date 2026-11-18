#!/usr/bin/env python3
"""Wait for a manual Facebook login in the CDP Chrome window, then post to the techstarz101 Page.

Never automates login, CAPTCHA, or 2FA - the user completes those in the visible window.
"""
import asyncio
import json
import urllib.request
import websockets

PAGE_URL = "https://www.facebook.com/profile.php?id=61596716728528"
POST_TEXT = (
    "Stop renting your software. Own your AI stack.\n\n"
    "At Techstarz101.com, we build sovereign AI systems (n8n, Twenty CRM, Listmonk, Hermes) "
    "that cut SaaS bloat and replace manual ops.\n\n"
    "For a flat $390 48-hour sprint, I'll audit your stack and deploy your first live AI workflow: "
    "https://techstarz101.com/intake.html"
)
WAIT_FOR_LOGIN_SECONDS = 900


class Page:
    def __init__(self, ws):
        self.ws = ws
        self.i = 0

    async def call(self, method, params=None):
        self.i += 1
        await self.ws.send(json.dumps({"id": self.i, "method": method, "params": params or {}}))
        while True:
            r = json.loads(await self.ws.recv())
            if r.get("id") == self.i:
                return r.get("result", {})

    async def eval(self, expr):
        r = await self.call("Runtime.evaluate", {"expression": expr, "returnByValue": True})
        return r.get("result", {}).get("value")

    async def click(self, x, y):
        for t in ("mouseMoved", "mousePressed", "mouseReleased"):
            p = {"type": t, "x": x, "y": y}
            if t != "mouseMoved":
                p.update(button="left", clickCount=1)
            await self.call("Input.dispatchMouseEvent", p)

    async def find(self, regex, scope="document"):
        return await self.eval(f"""
        (() => {{
            const root = {scope} || document;
            const els = Array.from(root.querySelectorAll('div[role="button"], button, span, [aria-label]'));
            const re = new RegExp({json.dumps(regex)}, 'i');
            for (const el of els) {{
                const t = ((el.getAttribute('aria-label') || '') + ' ' + (el.innerText || '')).trim();
                const r = el.getBoundingClientRect();
                if (re.test(t) && r.width > 0 && r.height > 0 && el.getAttribute('aria-disabled') !== 'true') {{
                    return {{x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2), t: t.slice(0, 60)}};
                }}
            }}
            return null;
        }})()
        """)


async def main():
    targets = json.loads(urllib.request.urlopen("http://127.0.0.1:9222/json").read().decode())
    tab = next(t for t in targets if t.get("type") == "page" and "facebook.com" in t.get("url", ""))
    async with websockets.connect(tab["webSocketDebuggerUrl"], max_size=50 * 1024 * 1024) as ws:
        p = Page(ws)
        await p.call("Page.bringToFront")
        current = await p.eval("location.href") or ""
        if "two_step_verification" not in current and "checkpoint" not in current:
            await p.call("Page.navigate", {"url": "https://www.facebook.com/login"})
        print("ACTION REQUIRED: sign in to Facebook in the open Chrome window (incl. any 2FA/CAPTCHA).", flush=True)

        for _ in range(WAIT_FOR_LOGIN_SECONDS // 5):
            await asyncio.sleep(5)
            logged_in = await p.eval("document.cookie.includes('c_user=')")
            if logged_in:
                print("Facebook login detected.", flush=True)
                break
        else:
            print("TIMEOUT: no Facebook login detected.", flush=True)
            return

        await p.call("Page.navigate", {"url": PAGE_URL})
        await asyncio.sleep(6)

        # Switch into the Page identity if Facebook offers it
        switch = await p.find(r"^switch now$|^switch$|switch into")
        if switch:
            print("Switching to Page profile:", switch["t"], flush=True)
            await p.click(switch["x"], switch["y"])
            await asyncio.sleep(4)
            confirm = await p.find(r"^switch$")
            if confirm:
                await p.click(confirm["x"], confirm["y"])
            await asyncio.sleep(6)
            await p.call("Page.navigate", {"url": PAGE_URL})
            await asyncio.sleep(6)

        composer = await p.find(r"what's on your mind|create post|write something")
        if not composer:
            print("Composer not found:", await p.eval("document.body.innerText.slice(0, 500)"), flush=True)
            return
        await p.click(composer["x"], composer["y"])
        await asyncio.sleep(4)

        box = await p.eval("""
        (() => {
            const d = document.querySelector('[role="dialog"] [contenteditable="true"][role="textbox"]');
            if (!d) return null;
            d.focus();
            const r = d.getBoundingClientRect();
            return {x: Math.round(r.x + 20), y: Math.round(r.y + r.height/2)};
        })()
        """)
        if not box:
            print("Post text box not found.", flush=True)
            return
        await p.click(box["x"], box["y"])
        await p.call("Input.insertText", {"text": POST_TEXT})
        await asyncio.sleep(3)

        nxt = await p.find(r"^next$", "document.querySelector('[role=\"dialog\"]')")
        if nxt:
            await p.click(nxt["x"], nxt["y"])
            await asyncio.sleep(3)
        post = await p.find(r"^post$", "document.querySelector('[role=\"dialog\"]')")
        if not post:
            print("Post button not found.", flush=True)
            return
        await p.click(post["x"], post["y"])
        print("CLICKED_FACEBOOK_POST", flush=True)
        await asyncio.sleep(10)

        await p.call("Page.navigate", {"url": PAGE_URL})
        await asyncio.sleep(6)
        body = await p.eval("document.body.innerText")
        print("POST_VISIBLE_ON_PAGE:", "Own your AI stack" in (body or ""), flush=True)
        links = await p.eval("Array.from(new Set(Array.from(document.querySelectorAll('a[href*=\"/posts/\"], a[href*=\"story_fbid\"], a[href*=\"pfbid\"]')).map(a => a.href.split('?')[0]))).slice(0, 5)")
        print("POST_LINKS:", links, flush=True)


if __name__ == "__main__":
    asyncio.run(main())

