from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

# Extremely minimal HTML just for testing
SIMPLE_HTML = """
<!DOCTYPE html>
<html>
<head><title>Aurora Quest</title></head>
<body style="background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;text-align:center;padding:50px;">
    <h1>Aurora Quest - Test Deployment</h1>
    <p>If you see this, the deployment works! 🎉</p>
    <button onclick="testAPI()">Test API</button>
    <div id="result"></div>
    <script>async function testAPI(){const r=await fetch('/api/health');const d=await r.json();document.getElementById('result').innerHTML=d.message||'Error'}</script>
</body>
</html>
"""

@app.get("/")
async def root():
    return HTMLResponse(content=SIMPLE_HTML)

@app.get("/api/health")
async def health():
    return {"message": "Aurora Quest API is working! ✨", "status": "ok"}

# Minimal ASGI handler
handler = app
