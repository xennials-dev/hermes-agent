import { spawn } from 'node:child_process';
import { rmSync, existsSync } from 'node:fs';
import path from 'node:path';

const CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const FFMPEG_PATH = "ffmpeg";

class CDPClient {
  constructor(wsUrl) {
    this.wsUrl = wsUrl;
    this.ws = null;
    this.id = 1;
    this.callbacks = new Map();
  }

  async connect() {
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket(this.wsUrl);
      this.ws.onopen = () => resolve();
      this.ws.onerror = (err) => reject(err);
      this.ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        if (msg.id && this.callbacks.has(msg.id)) {
          const { resolve, reject } = this.callbacks.get(msg.id);
          this.callbacks.delete(msg.id);
          if (msg.error) {
            reject(new Error(msg.error.message));
          } else {
            resolve(msg.result);
          }
        }
      };
    });
  }

  send(method, params = {}) {
    return new Promise((resolve, reject) => {
      const id = this.id++;
      this.callbacks.set(id, { resolve, reject });
      this.ws.send(JSON.stringify({ id, method, params }));
    });
  }

  close() {
    if (this.ws) {
      this.ws.close();
    }
  }
}

async function renderComposition({ url, outputPath, duration, width = 1920, height = 1080, fps = 30 }) {
  console.log(`\n==============================================`);
  console.log(`Starting HyperFrames Render`);
  console.log(`URL: ${url}`);
  console.log(`Output: ${outputPath}`);
  console.log(`Resolution: ${width}x${height} @ ${fps}fps | Duration: ${duration}s`);
  console.log(`==============================================\n`);

  const tempProfile = path.join(process.env.TEMP || 'C:\\Temp', `chrome_render_${Date.now()}`);
  
  // 1. Launch Chrome Headless
  console.log(`Launching Headless Chrome...`);
  const chrome = spawn(CHROME_PATH, [
    '--headless=new',
    '--remote-debugging-port=9222',
    `--user-data-dir=${tempProfile}`,
    '--disable-gpu',
    '--hide-scrollbars',
    `--window-size=${width},${height}`,
    'about:blank'
  ]);

  await new Promise(r => setTimeout(r, 2000));

  try {
    // 2. Open new target page
    const newPageRes = await fetch(`http://127.0.0.1:9222/json/new?${encodeURIComponent(url)}`, { method: 'PUT' });
    const pageData = await newPageRes.json();
    console.log(`Target Page Created: ${pageData.id}`);

    const client = new CDPClient(pageData.webSocketDebuggerUrl);
    await client.connect();

    await client.send('Page.enable');
    await client.send('Runtime.enable');
    await client.send('Emulation.setDeviceMetricsOverride', {
      width,
      height,
      deviceScaleFactor: 1,
      mobile: false
    });

    console.log(`Waiting for page and GSAP timeline initialization...`);
    let ready = false;
    for (let i = 0; i < 40; i++) {
      const evalRes = await client.send('Runtime.evaluate', {
        expression: `Boolean(document.readyState === 'complete' && window.__timelines && window.__timelines.length > 0)`,
        returnByValue: true
      });
      if (evalRes?.result?.value === true) {
        ready = true;
        break;
      }
      await new Promise(r => setTimeout(r, 250));
    }

    if (!ready) {
      console.warn(`Warning: window.__timelines not detected, rendering document anyway...`);
    } else {
      console.log(`GSAP timelines successfully attached.`);
    }

    // 2.5 Auto-detect composition duration and dimensions if not specified
    const metaRes = await client.send('Runtime.evaluate', {
      expression: `(() => {
        const root = document.getElementById('root');
        return {
          duration: root ? parseFloat(root.getAttribute('data-duration')) : null,
          width: root ? parseInt(root.getAttribute('data-width'), 10) : null,
          height: root ? parseInt(root.getAttribute('data-height'), 10) : null
        };
      })()`,
      returnByValue: true
    });

    const detected = metaRes?.result?.value;
    const finalDuration = duration || detected?.duration || 12;
    const finalWidth = width || detected?.width || 1920;
    const finalHeight = height || detected?.height || 1080;

    console.log(`Composition detected: ${finalWidth}x${finalHeight} @ ${fps}fps | Duration: ${finalDuration}s`);

    // 3. Start ffmpeg process
    console.log(`Spawning FFmpeg encoder...`);
    const ffmpeg = spawn(FFMPEG_PATH, [
      '-y',
      '-f', 'image2pipe',
      '-vcodec', 'mjpeg',
      '-framerate', String(fps),
      '-i', '-',
      '-c:v', 'libx264',
      '-pix_fmt', 'yuv420p',
      '-preset', 'fast',
      '-crf', '18',
      outputPath
    ]);

    let ffmpegErr = '';
    ffmpeg.stderr.on('data', (d) => {
      ffmpegErr += d.toString();
    });

    const totalFrames = Math.round(finalDuration * fps);
    console.log(`Rendering ${totalFrames} frames...`);

    const startTime = Date.now();

    for (let frame = 0; frame < totalFrames; frame++) {
      const timeSec = frame / fps;
      
      // Step GSAP timeline deterministically
      await client.send('Runtime.evaluate', {
        expression: `
          if (window.__timelines) {
            window.__timelines.forEach(tl => {
              tl.pause();
              tl.seek(${timeSec}, false);
            });
          }
        `
      });

      // Capture frame as high-quality JPEG
      const screenshot = await client.send('Page.captureScreenshot', {
        format: 'jpeg',
        quality: 95,
        captureBeyondViewport: false
      });

      const buffer = Buffer.from(screenshot.data, 'base64');
      
      // Write to ffmpeg pipe with proper backpressure handling
      if (!ffmpeg.stdin.write(buffer)) {
        await new Promise(r => ffmpeg.stdin.once('drain', r));
      }

      if (frame % 30 === 0 || frame === totalFrames - 1) {
        const percent = Math.round((frame / totalFrames) * 100);
        const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
        console.log(`[Frame ${frame}/${totalFrames}] ${percent}% complete (${elapsed}s elapsed)`);
      }
    }

    console.log(`Finalizing video stream...`);
    ffmpeg.stdin.end();

    await new Promise((resolve, reject) => {
      ffmpeg.on('close', (code) => {
        if (code === 0) resolve();
        else reject(new Error(`FFmpeg exited with code ${code}\n${ffmpegErr}`));
      });
      ffmpeg.on('error', reject);
    });

    client.close();
    await fetch(`http://127.0.0.1:9222/json/close/${pageData.id}`);

    console.log(`\n Render Complete! Video saved to: ${outputPath}\n`);

  } finally {
    chrome.kill('SIGKILL');
    try {
      if (existsSync(tempProfile)) {
        rmSync(tempProfile, { recursive: true, force: true });
      }
    } catch (_) {}
  }
}

// Parse CLI Arguments
const rawArgs = process.argv.slice(2);

if (rawArgs.includes('--help') || rawArgs.includes('-h')) {
  console.log(`
HyperFrames Video Renderer
==========================
Usage:
  node scripts/render-hyperframes.js [composition-path] [options]

Examples:
  node scripts/render-hyperframes.js videos/showcase/index.html
  node scripts/render-hyperframes.js videos/fiverr-intro/index.html --output videos/fiverr-intro/intro.mp4
  node scripts/render-hyperframes.js videos/showcase/index.html --duration 12 --fps 30

Options:
  -o, --output <path>    Output MP4 file path (default: <composition-dir>/<name>.mp4)
  -d, --duration <sec>   Override composition duration in seconds (auto-detected by default)
  --fps <number>         Frame rate (default: 30)
  -h, --help             Show this help message
`);
  process.exit(0);
}

let targetInput = rawArgs.find(a => !a.startsWith('-')) || 'videos/showcase/index.html';
let customOutput = null;
let customDuration = null;
let customFps = 30;

for (let i = 0; i < rawArgs.length; i++) {
  if (rawArgs[i] === '--output' || rawArgs[i] === '-o') {
    customOutput = rawArgs[++i];
  } else if (rawArgs[i] === '--duration' || rawArgs[i] === '-d') {
    customDuration = parseFloat(rawArgs[++i]);
  } else if (rawArgs[i] === '--fps') {
    customFps = parseInt(rawArgs[++i], 10);
  }
}

// Normalize path or URL
let targetUrl = targetInput;
if (!targetInput.startsWith('http://') && !targetInput.startsWith('https://')) {
  // Convert relative file path to local Vite URL
  const normalized = targetInput.replace(/\\/g, '/').replace(/^\.\//, '');
  targetUrl = `http://localhost:3000/${normalized}`;
}

const defaultOutputDir = path.dirname(targetInput.startsWith('http') ? 'videos/output.mp4' : targetInput);
const defaultOutputName = path.basename(targetInput, path.extname(targetInput)) + '.mp4';
const finalOutputPath = path.resolve(customOutput || path.join(defaultOutputDir, defaultOutputName === 'index.mp4' ? 'output.mp4' : defaultOutputName));

renderComposition({
  url: targetUrl,
  outputPath: finalOutputPath,
  duration: customDuration,
  fps: customFps
}).catch(err => {
  console.error("Render failed:", err);
  process.exit(1);
});
