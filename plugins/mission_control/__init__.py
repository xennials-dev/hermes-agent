import threading
import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from typing import Optional

app = FastAPI()

@app.get("/")
def read_root():
    html_content = """
    <html>
        <head><title>Hermes Mission Control</title></head>
        <body style="background:#1e1e1e; color:#00ff00; font-family:monospace; padding: 20px;">
            <h1>🚀 Hermes Mission Control</h1>
            <div id="stats">Loading stats...</div>
            <script>
                setInterval(() => {
                    fetch('/stats').then(r => r.json()).then(data => {
                        document.getElementById('stats').innerHTML = 
                            `<p>CPU: ${data.cpu}</p><p>Memory: ${data.memory}</p><p>Threads: ${data.threads}</p>`;
                    });
                }, 1000);
            </script>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/stats")
def get_stats():
    import psutil
    return {
        "cpu": f"{psutil.cpu_percent()}%",
        "memory": f"{psutil.virtual_memory().percent}%",
        "threads": threading.active_count()
    }

def _run_server():
    uvicorn.run(app, host="127.0.0.1", port=8080, log_level="error")

def _handle_mission_control(raw_args: str) -> Optional[str]:
    threading.Thread(target=_run_server, daemon=True).start()
    return "Mission Control Dashboard started! Open http://127.0.0.1:8080 in your browser."

def register(ctx) -> None:
    ctx.register_command("dashboard", handler=_handle_mission_control, description="Launch the Mission Control Web UI.")
