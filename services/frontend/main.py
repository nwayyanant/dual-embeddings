import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader, select_autoescape

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

API_BASE = os.getenv("API_BASE", "http://localhost:8083")  # must be reachable from the browser

env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=select_autoescape(["html"])
)

app = FastAPI(title="Pali Semantic Search UI")

# Serve static assets
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    """
    Render the UI and inject API_BASE so the JS knows where to call the backend Search service.
    """
    template = env.get_template("index.html")
    html = template.render(api_base=API_BASE)
    return HTMLResponse(html)

@app.get("/health")
def health():
    return {"service": "frontend", "status": "ok", "api_base": API_BASE}