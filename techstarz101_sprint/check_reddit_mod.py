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


async def main():
    targets = json.loads(urllib.request.urlopen("http://127.0.0.1:9222/json").read().decode())
    for t in targets:
        if t.get("type") != "page":
            continue
        url = t.get("url", "")
        if "reddit.com" in url:
            async with websockets.connect(t["webSocketDebuggerUrl"]) as ws:
                res = await cdp(
                    ws,
                    "Runtime.evaluate",
                    {
                        "expression": """
                        Array.from(document.querySelectorAll('a[href*="/comments/"]')).map(a => a.href)
                        """,
                        "returnByValue": True,
                    },
                    1,
                )
                print("Reddit post links:", list(dict.fromkeys(res.get("result", {}).get("value", []))))
        elif "facebook.com" in url:
            async with websockets.connect(t["webSocketDebuggerUrl"]) as ws:
                await cdp(ws, "Page.navigate", {"url": "https://www.facebook.com/techstarz101"}, 2)
                await asyncio.sleep(4)
                res = await cdp(
                    ws,
                    "Runtime.evaluate",
                    {
                        "expression": "({url: location.href, title: document.title, body: document.body.innerText.slice(0, 800)})",
                        "returnByValue": True,
                    },
                    3,
                )
                print("Facebook /techstarz101:", json.dumps(res.get("result", {}).get("value"), indent=2))


if __name__ == "__main__":
    asyncio.run(main())
