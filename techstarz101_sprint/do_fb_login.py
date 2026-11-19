import urllib.request
import json
import asyncio
import websockets
import base64
import time

async def main():
    targets = json.loads(urllib.request.urlopen("http://127.0.0.1:9222/json").read().decode("utf-8"))
    fb_pages = [t for t in targets if "facebook.com" in t.get("url", "")]
    if not fb_pages:
        print("No Facebook tab found!")
        return
    fb = fb_pages[0]
    ws = await websockets.connect(fb["webSocketDebuggerUrl"])
    
    js_code = """
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
            const btn = document.querySelector('button[name="login"], input[type="submit"], button#loginbutton');
            if (btn) {
                btn.click();
                return 'SUBMITTED_LOGIN_CLICKED';
            }
            return 'BUTTON_NOT_FOUND';
        }
        return 'INPUTS_NOT_FOUND';
    })()
    """
    
    await ws.send(json.dumps({
        "id": 1,
        "method": "Runtime.evaluate",
        "params": {"expression": js_code, "returnByValue": True}
    }))
    raw = await ws.recv()
    res = json.loads(raw)
    action_res = res.get("result", {}).get("result", {}).get("value")
    print(f"Login execution result: {action_res}")
    
    # Wait 6 seconds for 2FA screen or navigation
    await asyncio.sleep(6)
    
    # Check new URL & Title
    await ws.send(json.dumps({
        "id": 2,
        "method": "Runtime.evaluate",
        "params": {
            "expression": "({url: location.href, title: document.title, text: document.body.innerText.slice(0, 500)})",
            "returnByValue": True
        }
    }))
    raw2 = await ws.recv()
    info = json.loads(raw2).get("result", {}).get("result", {}).get("value", {})
    print(f"Updated URL: {info.get('url')}")
    print(f"Updated Title: {info.get('title')}")
    print(f"Snippet: {info.get('text', '')[:200]}")
    
    # Take screenshot
    await ws.send(json.dumps({"id": 3, "method": "Page.captureScreenshot"}))
    raw3 = await ws.recv()
    b64 = json.loads(raw3).get("result", {}).get("data", "")
    if b64:
        with open("c:/Users/tee/.gemini/antigravity-ide/scratch/hermes-agent/techstarz101_sprint/fb_2fa_prompt.png", "wb") as f:
            f.write(base64.b64decode(b64))
        print("Captured screenshot: fb_2fa_prompt.png")
    
    await ws.close()

if __name__ == "__main__":
    asyncio.run(main())

