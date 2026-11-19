import urllib.request
import json
import asyncio
import websockets
import base64

async def main():
    targets = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read().decode('utf-8'))
    fb = [t for t in targets if 'facebook.com' in t.get('url', '')][0]
    print('Connecting to:', fb['webSocketDebuggerUrl'])
    ws = await websockets.connect(fb['webSocketDebuggerUrl'])
    
    await ws.send(json.dumps({'id': 1, 'method': 'Page.enable'}))
    print('Page.enable:', await ws.recv())
    
    await ws.send(json.dumps({'id': 2, 'method': 'Page.bringToFront'}))
    print('bringToFront:', await ws.recv())
    
    await ws.send(json.dumps({'id': 3, 'method': 'Page.captureScreenshot'}))
    raw = await ws.recv()
    res = json.loads(raw)
    data = res.get('result', {}).get('data', '')
    print('Screenshot data length:', len(data))
    if data:
        with open('c:/Users/tee/.gemini/antigravity-ide/scratch/hermes-agent/fb_screen_now.png', 'wb') as f:
            f.write(base64.b64decode(data))
        print('Saved screenshot!')
    await ws.close()

if __name__ == '__main__':
    asyncio.run(main())

