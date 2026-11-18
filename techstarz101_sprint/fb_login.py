#!/usr/bin/env python3
"""Type user-supplied Facebook credentials into the open login page. Stops at 2FA/CAPTCHA."""
import asyncio
import json
import sys
import urllib.request
import websockets

EMAIL = sys.argv[1]
PASSWORD = sys.argv[2]


async def main():
    targets = json.loads(urllib.request.urlopen("http://127.0.0.1:9222/json").read().decode())
    tab = next(t for t in targets if t.get("type") == "page" and "facebook.com" in t.get("url", ""))
    async with websockets.connect(tab["webSocketDebuggerUrl"], max_size=50 * 1024 * 1024) as ws:
        i = 0

        async def call(m, p=None):
            nonlocal i
            i += 1
            await ws.send(json.dumps({"id": i, "method": m, "params": p or {}}))
            while True:
                r = json.loads(await ws.recv())
                if r.get("id") == i:
                    return r.get("result", {})

        async def ev(e):
            return (await call("Runtime.evaluate", {"expression": e, "returnByValue": True})).get("result", {}).get("value")

        async def click(x, y):
            await call("Input.dispatchMouseEvent", {"type": "mouseMoved", "x": x, "y": y})
            for t in ("mousePressed", "mouseReleased"):
                await call("Input.dispatchMouseEvent", {"type": t, "x": x, "y": y, "button": "left", "clickCount": 1})

        await call("Page.bringToFront")
        if "facebook.com/login" not in (await ev("location.href")):
            await call("Page.navigate", {"url": "https://www.facebook.com/login"})
            await asyncio.sleep(4)

        f = await ev("""
        (() => {
            const c = el => { const r = el.getBoundingClientRect(); return {x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2)}; };
            const e = Array.from(document.querySelectorAll('input')).find(i => (i.type === 'text' || i.type === 'email') && i.getBoundingClientRect().width > 0);
            const p = Array.from(document.querySelectorAll('input[type="password"]')).find(i => i.getBoundingClientRect().width > 0);
            const b = Array.from(document.querySelectorAll('button, div[role="button"], input[type="submit"]')).find(x => /^log in$/i.test((x.innerText || x.value || '').trim()) && x.getBoundingClientRect().width > 0);
            return e && p && b ? {e: c(e), p: c(p), b: c(b)} : null;
        })()
        """)
        if not f:
            print("Login form not found:", await ev("document.body.innerText.slice(0,300)"))
            return

        for key, text in (("e", EMAIL), ("p", PASSWORD)):
            await click(f[key]["x"], f[key]["y"])
            await asyncio.sleep(0.3)
            await ev("document.activeElement.select && document.activeElement.select()")
            await call("Input.dispatchKeyEvent", {"type": "keyDown", "key": "Backspace", "code": "Backspace", "windowsVirtualKeyCode": 8})
            await call("Input.dispatchKeyEvent", {"type": "keyUp", "key": "Backspace", "code": "Backspace", "windowsVirtualKeyCode": 8})
            await call("Input.insertText", {"text": text})
            await asyncio.sleep(0.4)
        await click(f["b"]["x"], f["b"]["y"])
        await asyncio.sleep(8)

        state = await ev("({url: location.href, loggedIn: document.cookie.includes('c_user='), body: document.body.innerText.slice(0, 400)})")
        print(json.dumps(state, indent=2))


if __name__ == "__main__":
    asyncio.run(main())

