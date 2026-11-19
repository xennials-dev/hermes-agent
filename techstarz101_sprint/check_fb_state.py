import urllib.request
import json
import asyncio
import websockets
import base64

async def main():
    targets = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read().decode('utf-8'))
    fb_pages = [t for t in targets if 'facebook.com' in t.get('url', '')]
    if not fb_pages:
        print('No FB page')
        return
    fb = fb_pages[0]
    ws = await websockets.connect(fb['webSocketDebuggerUrl'])
    
    await ws.send(json.dumps({'id': 1, 'method': 'Page.captureScreenshot'}))
    res = json.loads(await ws.recv())
    b64 = res.get('result', {}).get('data', '')
    if b64:
        with open('c:/Users/tee/.gemini/antigravity-ide/scratch/hermes-agent/fb_current_state.png', 'wb') as f:
            f.write(base64.b64decode(b64))
        print('Saved fb_current_state.png')

    js_code = """
    (() => {
        return {
            url: location.href,
            title: document.title,
            bodyText: document.body ? document.body.innerText.slice(0, 1000) : '',
            allButtons: Array.from(document.querySelectorAll('button, a, div[role="button"], input')).map(e => ({
                tag: e.tagName,
                type: e.type || '',
                text: (e.innerText || e.value || e.placeholder || e.ariaLabel || '').trim()
            })).filter(x => x.text)
        };
    })()
    """
    await ws.send(json.dumps({'id': 2, 'method': 'Runtime.evaluate', 'params': {'expression': js_code, 'returnByValue': True}}))
    res2 = json.loads(await ws.recv())
    print('DOM INFO:', json.dumps(res2.get('result', {}).get('result', {}).get('value'), indent=2))
    await ws.close()

if __name__ == '__main__':
    asyncio.run(main())

