#!/usr/bin/env python3
import asyncio
import json
import urllib.parse
import urllib.request
import websockets

POST_TITLE = "Stop renting your software. Own your AI stack — Techstarz101.com"
POST_TEXT = (
    "Stop renting your software. Own your AI stack.\n\n"
    "At Techstarz101.com, we build sovereign AI systems (n8n, Twenty CRM, Listmonk, Hermes) "
    "that cut SaaS bloat. Flat $390 48-hour sprint: https://techstarz101.com/intake.html"
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


async def handle_threads(ws):
    print("\n--- [1] THREADS ---")
    await cdp(ws, "Page.bringToFront", {}, 1)
    # Check if composer dialog is already open
    res = await cdp(
        ws,
        "Runtime.evaluate",
        {
            "expression": """
            (() => {
                const btns = Array.from(document.querySelectorAll('div[role="button"], button'));
                const postBtns = btns.filter(b => /^post$/i.test((b.innerText || '').trim()));
                return postBtns.map((b, i) => {
                    const r = b.getBoundingClientRect();
                    const inDialog = !!b.closest('[role="dialog"]');
                    return {
                        i,
                        inDialog,
                        x: Math.round(r.x + r.width / 2),
                        y: Math.round(r.y + r.height / 2),
                        w: Math.round(r.width),
                        h: Math.round(r.height),
                        ariaDisabled: b.getAttribute('aria-disabled')
                    };
                });
            })()
            """,
            "returnByValue": True,
        },
        2,
    )
    post_btns = res.get("result", {}).get("value", [])
    print("Threads Post buttons found:", post_btns)

    dialog_btns = [b for b in post_btns if b.get("inDialog") and b["w"] > 0]
    if not dialog_btns:
        # Navigate to /intent/post again
        nav_url = "https://www.threads.com/intent/post?text=" + urllib.parse.quote(POST_TEXT)
        await cdp(ws, "Page.navigate", {"url": nav_url}, 3)
        await asyncio.sleep(6)
        res = await cdp(
            ws,
            "Runtime.evaluate",
            {
                "expression": """
                (() => {
                    const btns = Array.from(document.querySelectorAll('div[role="button"], button'));
                    const postBtns = btns.filter(b => /^post$/i.test((b.innerText || '').trim()));
                    return postBtns.map((b, i) => {
                        const r = b.getBoundingClientRect();
                        const inDialog = !!b.closest('[role="dialog"]');
                        return {
                            i,
                            inDialog,
                            x: Math.round(r.x + r.width / 2),
                            y: Math.round(r.y + r.height / 2),
                            w: Math.round(r.width),
                            h: Math.round(r.height),
                            ariaDisabled: b.getAttribute('aria-disabled')
                        };
                    });
                })()
                """,
                "returnByValue": True,
            },
            4,
        )
        post_btns = res.get("result", {}).get("value", [])
        dialog_btns = [b for b in post_btns if b.get("inDialog") and b["w"] > 0]

    target = dialog_btns[-1] if dialog_btns else (post_btns[-1] if post_btns else None)
    if target:
        print(f"Clicking Threads modal Post button at ({target['x']}, {target['y']})...")
        await mouse_click(ws, target["x"], target["y"], 10)
        await asyncio.sleep(7)

    # Check profile page for published post
    await cdp(ws, "Page.navigate", {"url": "https://www.threads.com/@techstarz101"}, 20)
    await asyncio.sleep(6)
    prof = await cdp(
        ws,
        "Runtime.evaluate",
        {
            "expression": """
            (() => {
                const links = Array.from(document.querySelectorAll('a[href*="/post/"]')).map(a => a.href);
                return {
                    url: location.href,
                    postLinks: Array.from(new Set(links)).slice(0, 5),
                    body: document.body.innerText.slice(0, 700)
                };
            })()
            """,
            "returnByValue": True,
        },
        21,
    )
    print("Threads @techstarz101 profile:", json.dumps(prof.get("result", {}).get("value"), indent=2))


async def handle_reddit(ws):
    print("\n--- [2] REDDIT ---")
    await cdp(ws, "Page.bringToFront", {}, 30)
    # Inspect the login form and button coordinates
    info = await cdp(
        ws,
        "Runtime.evaluate",
        {
            "expression": """
            (() => {
                const uHost = document.querySelector('faceplate-text-input#login-username');
                const pHost = document.querySelector('faceplate-text-input#login-password');
                const u = uHost?.shadowRoot?.querySelector('input') || document.querySelector('input[name="username"]');
                const p = pHost?.shadowRoot?.querySelector('input') || document.querySelector('input[name="password"]');
                const uRect = (u || uHost)?.getBoundingClientRect();
                const pRect = (p || pHost)?.getBoundingClientRect();
                const btns = Array.from(document.querySelectorAll('button, [role="button"]'));
                const loginBtn = btns.find(b => /log in/i.test((b.innerText || '').trim()) && b.getBoundingClientRect().y > 200);
                const bRect = loginBtn?.getBoundingClientRect();
                return {
                    url: location.href,
                    uRect: uRect ? {x: Math.round(uRect.x + uRect.width/2), y: Math.round(uRect.y + uRect.height/2)} : null,
                    pRect: pRect ? {x: Math.round(pRect.x + pRect.width/2), y: Math.round(pRect.y + pRect.height/2)} : null,
                    bRect: bRect ? {x: Math.round(bRect.x + bRect.width/2), y: Math.round(bRect.y + bRect.height/2), text: loginBtn.innerText.trim()} : null,
                    uVal: u?.value,
                    pLen: p?.value?.length
                };
            })()
            """,
            "returnByValue": True,
        },
        31,
    )
    val = info.get("result", {}).get("value", {})
    print("Reddit login state:", val)

    if val.get("uRect") and val.get("pRect"):
        # Click username input with real mouse event, select all, and type
        await mouse_click(ws, val["uRect"]["x"], val["uRect"]["y"], 40)
        await asyncio.sleep(0.4)
        await cdp(
            ws,
            "Runtime.evaluate",
            {
                "expression": """
                (() => {
                    const u = document.querySelector('faceplate-text-input#login-username')?.shadowRoot?.querySelector('input');
                    if (u) u.value = '';
                })()
                """
            },
            43,
        )
        await cdp(ws, "Input.insertText", {"text": "techstarz101"}, 44)
        await asyncio.sleep(0.5)

        # Click password input with real mouse event, clear, and type
        await mouse_click(ws, val["pRect"]["x"], val["pRect"]["y"], 50)
        await asyncio.sleep(0.4)
        await cdp(
            ws,
            "Runtime.evaluate",
            {
                "expression": """
                (() => {
                    const p = document.querySelector('faceplate-text-input#login-password')?.shadowRoot?.querySelector('input');
                    if (p) p.value = '';
                })()
                """
            },
            53,
        )
        await cdp(ws, "Input.insertText", {"text": "#6052Garfield"}, 54)
        await asyncio.sleep(0.8)

        # Re-read login button rect after inputs are filled
        btn_res = await cdp(
            ws,
            "Runtime.evaluate",
            {
                "expression": """
                (() => {
                    const btns = Array.from(document.querySelectorAll('button'));
                    const loginBtn = btns.find(b => /^log in$/i.test((b.innerText || '').trim()) && b.getBoundingClientRect().y > 250);
                    if (!loginBtn) return null;
                    const r = loginBtn.getBoundingClientRect();
                    return {x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2), disabled: loginBtn.disabled};
                })()
                """,
                "returnByValue": True,
            },
            55,
        )
        b_rect = btn_res.get("result", {}).get("value")
        print("Reddit Login button after typing:", b_rect)
        if b_rect:
            await mouse_click(ws, b_rect["x"], b_rect["y"], 60)
            await asyncio.sleep(7)

    after_login = await cdp(
        ws,
        "Runtime.evaluate",
        {
            "expression": "({url: location.href, body: document.body.innerText.slice(0, 600)})",
            "returnByValue": True,
        },
        70,
    )
    print("Reddit after login click:", after_login.get("result", {}).get("value"))


async def handle_facebook(ws):
    print("\n--- [3] FACEBOOK ---")
    await cdp(ws, "Page.bringToFront", {}, 80)
    await cdp(ws, "Page.navigate", {"url": "https://www.facebook.com/login"}, 81)
    await asyncio.sleep(4)
    # Try logging in with tfisher314@gmail.com + #6052Garfield
    fb_res = await cdp(
        ws,
        "Runtime.evaluate",
        {
            "expression": """
            (() => {
                const e = document.querySelector('input#email, input[name="email"]');
                const p = document.querySelector('input#pass, input[name="pass"]');
                const b = document.querySelector('button#loginbutton, button[name="login"]');
                if (!e || !p) return 'NO_FB_INPUTS';
                e.focus();
                e.value = 'tfisher314@gmail.com';
                e.dispatchEvent(new Event('input', {bubbles: true}));
                p.focus();
                p.value = '#6052Garfield';
                p.dispatchEvent(new Event('input', {bubbles: true}));
                if (b) b.click();
                return 'SUBMITTED_FB_GMAIL';
            })()
            """,
            "returnByValue": True,
        },
        82,
    )
    print("Facebook login attempt (tfisher314@gmail.com):", fb_res.get("result", {}).get("value"))
    await asyncio.sleep(6)
    fb_after = await cdp(
        ws,
        "Runtime.evaluate",
        {
            "expression": "({url: location.href, title: document.title, body: document.body.innerText.slice(0, 500)})",
            "returnByValue": True,
        },
        83,
    )
    print("Facebook after login:", fb_after.get("result", {}).get("value"))


async def run():
    targets = json.loads(urllib.request.urlopen("http://127.0.0.1:9222/json").read().decode())
    for t in targets:
        if t.get("type") != "page":
            continue
        url = t.get("url", "")
        if "threads.com" in url:
            async with websockets.connect(t["webSocketDebuggerUrl"]) as ws:
                await handle_threads(ws)
        elif "reddit.com" in url:
            async with websockets.connect(t["webSocketDebuggerUrl"]) as ws:
                await handle_reddit(ws)
        elif "facebook.com" in url:
            async with websockets.connect(t["webSocketDebuggerUrl"]) as ws:
                await handle_facebook(ws)


if __name__ == "__main__":
    asyncio.run(run())
