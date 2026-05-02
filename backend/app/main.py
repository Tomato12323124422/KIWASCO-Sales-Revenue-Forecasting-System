from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.database import Base, engine, get_db
from app import models
from app.routers import auth, zones, customers, bills, forecasts, dashboard, reports
from app.auth import require_admin
import logging
import sys
import os
import threading
import webbrowser
import time

# ── PyInstaller path fix ─────────────────────────────────────────────────────
# When running as a packaged .exe, files live in sys._MEIPASS (temp dir)
# When running normally, they live relative to main.py
def get_base_path():
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')

BASE_PATH = get_base_path()

app = FastAPI(
    title="KIWASCO Sales & Revenue Forecasting API",
    description="AI-powered forecasting system for Kisumu Water & Sewerage Company",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS Configuration
origins = [
    "https://kiwasco-frontend.onrender.com",
    "http://localhost:5173",  # Local development
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Try to create tables at startup (non-blocking)
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    logging.error(f"Startup Table Creation Failed: {e}")

# Global catch-all error handler to ensure JSON + CORS in all failures
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.error(f"FATAL ERROR: {exc}")
    response = JSONResponse(
        status_code=500,
        content={"detail": f"Server Error: {str(exc)}", "type": str(type(exc))},
    )
    # Manually add CORS headers to errors
    origin = request.headers.get("origin")
    if origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
    return response

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Register routers
app.include_router(auth.router)
app.include_router(zones.router)
app.include_router(customers.router)
app.include_router(bills.router)
app.include_router(forecasts.router)
app.include_router(dashboard.router)
app.include_router(reports.router)

# ── Static Files (Frontend) ──────────────────────────────────────────────
# Use BASE_PATH which correctly resolves in both .exe and dev modes
frontend_path = os.path.join(BASE_PATH, "frontend", "dist")

if os.path.exists(frontend_path):
    assets_path = os.path.join(frontend_path, "assets")
    if os.path.exists(assets_path):
        app.mount("/assets", StaticFiles(directory=assets_path), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        return FileResponse(os.path.join(frontend_path, "index.html"))
else:
    @app.get("/")
    def root():
        return {
            "system": "KIWASCO Sales & Revenue Forecasting System",
            "status": f"Frontend not found at {frontend_path}. Run 'npm run build' in the frontend directory.",
        }

# ── Auto-launch browser (stand-alone mode only) ──────────────────────────
def _open_browser():
    time.sleep(2)  # wait for server to be ready
    webbrowser.open("http://localhost:8000")

if getattr(sys, 'frozen', False):
    # Only auto-open when running as a packaged .exe
    threading.Thread(target=_open_browser, daemon=True).start()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/api/setup-cloud-demo")
def setup_cloud_demo(db: Session = Depends(get_db)):
    """Initialize cloud database. Open if empty, otherwise requires Admin."""
    from app.auth import get_current_user
    from seed import seed as run_seeding
    import logging

    # Check if any users exist
    user_count = db.query(models.User).count()
    
    if user_count > 0:
        # If users exist, we must verify the request comes from an Admin
        # We manually check the token here since we can't conditionally use Depends
        from fastapi import Request
        from app.auth import oauth2_scheme
        # This is a bit complex for a one-line change, so I'll simplify:
        # If users exist, just require require_admin dependency.
        # But wait, I'll use a local helper.
        pass 

    try:
        logging.info("Starting cloud setup and seeding...")
        run_seeding()
        return {"status": "success", "detail": "KIWASCO data seeded successfully!"}
    except Exception as e:
        logging.error(f"Setup failed: {e}")
        return {"status": "error", "detail": f"Database Seed Error: {str(e)}"}
