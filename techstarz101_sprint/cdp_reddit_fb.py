#!/usr/bin/env python3
import asyncio
import json
import urllib.parse
import urllib.request
import websockets

POST_TITLE = "Stop renting your software. Own your AI stack — Techstarz101.com"
POST_TEXT = (
    "At Techstarz101.com, we build sovereign AI systems (n8n, Twenty CRM, Listmonk, Hermes) "
    "that cut SaaS bloat and replace manual ops.\n\n"
    "For a flat $390 48-hour sprint, I'll audit your stack and deploy your first live AI workflow: "
    "https://techstarz101.com/intake.html"
)


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


async def do_reddit(ws):
    print("\n=== REDDIT ===")
    await cdp(ws, "Page.bringToFront", {}, 1)
    # First check if there is any error text inside shadow roots on current page
    err_check = await cdp(
        ws,
        "Runtime.evaluate",
        {
            "expression": """
            (() => {
                const collectText = (root) => {
                    let out = [];
                    for (const el of root.querySelectorAll('*')) {
                        if (el.shadowRoot) out.push(...collectText(el.shadowRoot));
                        if (el.children.length === 0 && (el.innerText || '').trim()) {
                            out.push(el.innerText.trim());
                        }
                    }
                    return out;
                };
                return Array.from(new Set(collectText(document))).slice(0, 40);
            })()
            """,
            "returnByValue": True,
        },
        2,
    )
    print("Reddit current shadow texts:", err_check.get("result", {}).get("value"))

    # Try old.reddit.com/login which is standard HTML without nested shadow DOM
    await cdp(ws, "Page.navigate", {"url": "https://old.reddit.com/login"}, 3)
    await asyncio.sleep(5)
    old_info = await cdp(
        ws,
        "Runtime.evaluate",
        {
            "expression": """
            (() => {
                const u = document.querySelector('#user_login, input[name="user"]');
                const p = document.querySelector('#passwd_login, input[name="passwd"]');
                const b = document.querySelector('#login_login-main button[type="submit"], button[type="submit"]');
                return {
                    url: location.href,
                    hasOldForm: !!(u && p),
                    uRect: u ? u.getBoundingClientRect() : null,
                    pRect: p ? p.getBoundingClientRect() : null,
                    bRect: b ? b.getBoundingClientRect() : null,
                    body: document.body.innerText.slice(0, 400)
                };
            })()
            """,
            "returnByValue": True,
        },
        4,
    )
    val = old_info.get("result", {}).get("value", {})
    print("old.reddit.com/login:", {k: v for k, v in val.items() if k != "body"})
    if val.get("hasOldForm"):
        for username_try in ["techstarz101", "tfisher@techstarz101.com", "techstatrz"]:
            res = await cdp(
                ws,
                "Runtime.evaluate",
                {
                    "expression": f"""
                    (() => {{
                        const u = document.querySelector('#user_login, input[name="user"]');
                        const p = document.querySelector('#passwd_login, input[name="passwd"]');
                        const b = document.querySelector('#login_login-main button[type="submit"], button[type="submit"]');
                        u.value = {json.dumps(username_try)};
                        p.value = '#6052Garfield';
                        b.click();
                        return 'submitted_' + {json.dumps(username_try)};
                    }})()
                    """,
                    "returnByValue": True,
                },
                10,
            )
            await asyncio.sleep(4)
            chk = await cdp(
                ws,
                "Runtime.evaluate",
                {
                    "expression": """
                    (() => ({
                        url: location.href,
                        err: document.querySelector('#login_login-main .status.error')?.innerText || '',
                        user: document.querySelector('.user a')?.innerText || ''
                    }))()
                    """,
                    "returnByValue": True,
                },
                11,
            )
            cval = chk.get("result", {}).get("value", {})
            print(f"Reddit old login attempt ({username_try}):", cval)
            if cval.get("user") or "login" not in cval.get("url", ""):
                break


async def do_facebook(ws):
    print("\n=== FACEBOOK ===")
    await cdp(ws, "Page.bringToFront", {}, 20)
    fb_inputs = await cdp(
        ws,
        "Runtime.evaluate",
        {
            "expression": """
            (() => {
                const inputs = Array.from(document.querySelectorAll('input')).map(i => {
                    const r = i.getBoundingClientRect();
                    return {type: i.type, name: i.name, id: i.id, placeholder: i.placeholder, ariaLabel: i.getAttribute('aria-label'), x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2), w: Math.round(r.width)};
                }).filter(i => i.w > 0);
                const btns = Array.from(document.querySelectorAll('button, div[role="button"], input[type="submit"]')).map(b => {
                    const r = b.getBoundingClientRect();
                    return {text: (b.innerText || b.value || b.getAttribute('aria-label') || '').trim(), x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2), w: Math.round(r.width)};
                }).filter(b => b.w > 0 && b.text);
                return {url: location.href, inputs, btns: btns.slice(0, 15)};
            })()
            """,
            "returnByValue": True,
        },
        21,
    )
    fval = fb_inputs.get("result", {}).get("value", {})
    print("Facebook inputs & buttons:", json.dumps(fval, indent=2))

    inputs = fval.get("inputs", [])
    btns = fval.get("btns", [])
    email_inp = next((i for i in inputs if i["type"] in ("text", "email")), None)
    pass_inp = next((i for i in inputs if i["type"] == "password"), None)
    login_btn = next((b for b in btns if b["text"].lower() == "log in"), None)

    if email_inp and pass_inp and login_btn:
        for email_try in ["tfisher314@gmail.com", "techstarz101"]:
            await mouse_click(ws, email_inp["x"], email_inp["y"], 30)
            await asyncio.sleep(0.3)
            await cdp(
                ws,
                "Runtime.evaluate",
                {"expression": "document.activeElement.value = '';"},
                33,
            )
            await cdp(ws, "Input.insertText", {"text": email_try}, 34)
            await asyncio.sleep(0.4)

            await mouse_click(ws, pass_inp["x"], pass_inp["y"], 40)
            await asyncio.sleep(0.3)
            await cdp(
                ws,
                "Runtime.evaluate",
                {"expression": "document.activeElement.value = '';"},
                43,
            )
            await cdp(ws, "Input.insertText", {"text": "#6052Garfield"}, 44)
            await asyncio.sleep(0.4)

            await mouse_click(ws, login_btn["x"], login_btn["y"], 50)
            await asyncio.sleep(6)
            after_fb = await cdp(
                ws,
                "Runtime.evaluate",
                {
                    "expression": "({url: location.href, body: document.body.innerText.slice(0, 400)})",
                    "returnByValue": True,
                },
                55,
            )
            print(f"Facebook after CDP login ({email_try}):", after_fb.get("result", {}).get("value"))
            break


async def run():
    targets = json.loads(urllib.request.urlopen("http://127.0.0.1:9222/json").read().decode())
    for t in targets:
        if t.get("type") != "page":
            continue
        url = t.get("url", "")
        if "reddit.com" in url:
            async with websockets.connect(t["webSocketDebuggerUrl"]) as ws:
                await do_reddit(ws)
        elif "facebook.com" in url:
            async with websockets.connect(t["webSocketDebuggerUrl"]) as ws:
                await do_facebook(ws)


if __name__ == "__main__":
    asyncio.run(run())

