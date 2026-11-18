#!/usr/bin/env python3
import asyncio
import json
import urllib.request
import websockets


async def cdp(ws, method, params=None, msg_id=1):
    await ws.send(json.dumps({"id": msg_id, "method": method, "params": params or {}}))
    while True:
        r = json.loads(await ws.recv())
        if r.get("id") == msg_id:
            return r.get("result", {})


async def mouse_click(ws, x, y, base_id=100):
    await cdp(ws, "Input.dispatchMouseEvent", {"type": "mouseMoved", "x": x, "y": y}, base_id)
    await cdp(
        ws,
        "Input.dispatchMouseEvent",
        {"type": "mousePressed", "x": x, "y": y, "button": "left", "clickCount": 1},
        base_id + 1,
    )
    await cdp(
        ws,
        "Input.dispatchMouseEvent",
        {"type": "mouseReleased", "x": x, "y": y, "button": "left", "clickCount": 1},
        base_id + 2,
    )


async def main():
    targets = json.loads(urllib.request.urlopen("http://127.0.0.1:9222/json").read().decode())
    fb_tab = next((t for t in targets if t.get("type") == "page" and "facebook.com" in t.get("url", "")), None)
    if not fb_tab:
        fb_tab = next((t for t in targets if t.get("type") == "page"), None)

    async with websockets.connect(fb_tab["webSocketDebuggerUrl"]) as ws:
        await cdp(ws, "Page.bringToFront", {}, 1)

        # 1. Check where the business share link redirects
        await cdp(ws, "Page.navigate", {"url": "https://www.facebook.com/share/1DYG33EtkW/?mibextid=wwXIfr"}, 2)
        await asyncio.sleep(5)
        share_info = await cdp(
            ws,
            "Runtime.evaluate",
            {
                "expression": "({url: location.href, title: document.title, body: document.body.innerText.slice(0, 600)})",
                "returnByValue": True,
            },
            3,
        )
        print("Share link resolved to:", json.dumps(share_info.get("result", {}).get("value"), indent=2))

        # 2. Check https://www.facebook.com/tfisher314
        await cdp(ws, "Page.navigate", {"url": "https://www.facebook.com/tfisher314"}, 4)
        await asyncio.sleep(5)
        page_info = await cdp(
            ws,
            "Runtime.evaluate",
            {
                "expression": "({url: location.href, title: document.title, body: document.body.innerText.slice(0, 600)})",
                "returnByValue": True,
            },
            5,
        )
        print("Profile/Page link resolved to:", json.dumps(page_info.get("result", {}).get("value"), indent=2))

        # 3. Try logging in at https://www.facebook.com/login with username 'tfisher314'
        await cdp(ws, "Page.navigate", {"url": "https://www.facebook.com/login"}, 6)
        await asyncio.sleep(4)
        fb_inputs = await cdp(
            ws,
            "Runtime.evaluate",
            {
                "expression": """
                (() => {
                    const inputs = Array.from(document.querySelectorAll('input')).map(i => {
                        const r = i.getBoundingClientRect();
                        return {type: i.type, name: i.name, x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2), w: Math.round(r.width)};
                    }).filter(i => i.w > 0);
                    const btns = Array.from(document.querySelectorAll('button, div[role="button"], input[type="submit"]')).map(b => {
                        const r = b.getBoundingClientRect();
                        return {text: (b.innerText || b.value || b.getAttribute('aria-label') || '').trim(), x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2), w: Math.round(r.width)};
                    }).filter(b => b.w > 0 && b.text);
                    return {inputs, btns: btns.slice(0, 10)};
                })()
                """,
                "returnByValue": True,
            },
            7,
        )
        fval = fb_inputs.get("result", {}).get("value", {})
        inputs = fval.get("inputs", [])
        btns = fval.get("btns", [])
        email_inp = next((i for i in inputs if i["type"] in ("text", "email")), None)
        pass_inp = next((i for i in inputs if i["type"] == "password"), None)
        login_btn = next((b for b in btns if b["text"].lower() == "log in"), None)

        if email_inp and pass_inp and login_btn:
            await mouse_click(ws, email_inp["x"], email_inp["y"], 10)
            await asyncio.sleep(0.3)
            await cdp(ws, "Runtime.evaluate", {"expression": "document.activeElement.value = '';"}, 13)
            await cdp(ws, "Input.insertText", {"text": "tfisher314"}, 14)
            await asyncio.sleep(0.4)

            await mouse_click(ws, pass_inp["x"], pass_inp["y"], 20)
            await asyncio.sleep(0.3)
            await cdp(ws, "Runtime.evaluate", {"expression": "document.activeElement.value = '';"}, 23)
            await cdp(ws, "Input.insertText", {"text": "#6052Garfield"}, 24)
            await asyncio.sleep(0.4)

            await mouse_click(ws, login_btn["x"], login_btn["y"], 30)
            await asyncio.sleep(6)
            after_fb = await cdp(
                ws,
                "Runtime.evaluate",
                {
                    "expression": "({url: location.href, title: document.title, body: document.body.innerText.slice(0, 600)})",
                    "returnByValue": True,
                },
                35,
            )
            print("Facebook after login (tfisher314):", json.dumps(after_fb.get("result", {}).get("value"), indent=2))


if __name__ == "__main__":
    asyncio.run(main())

