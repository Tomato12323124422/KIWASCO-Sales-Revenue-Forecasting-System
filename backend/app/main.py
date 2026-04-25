from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.database import Base, engine, get_db
from app.routers import auth, zones, customers, bills, forecasts, dashboard, reports
import logging

app = FastAPI(
    title="KIWASCO Sales & Revenue Forecasting API",
    description="AI-powered forecasting system for Kisumu Water & Sewerage Company",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS — Maximum permissiveness for Cloud demo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
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
    return JSONResponse(
        status_code=500,
        content={"detail": f"Server Error: {str(exc)}", "type": str(type(exc))},
    )

# Register routers
app.include_router(auth.router)
app.include_router(zones.router)
app.include_router(customers.router)
app.include_router(bills.router)
app.include_router(forecasts.router)
app.include_router(dashboard.router)
app.include_router(reports.router)

@app.get("/")
def root():
    return {
        "system": "KIWASCO Sales & Revenue Forecasting System",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/api/docs",
    }

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/api/setup-cloud-demo")
def setup_cloud_demo():
    """Initialize cloud database with demo accounts and all historical data (Zones, Customers, Bills)."""
    from seed import seed as run_seeding
    import logging

    try:
        logging.info("Starting cloud setup and seeding...")
        # This will now create users, zones, customers, and bills (additively)
        run_seeding()

        return {
            "status": "success", 
            "detail": "KIWASCO data seeded successfully! You can now log in and explore all zones."
        }
    except Exception as e:
        logging.error(f"Setup failed: {e}")
        return {"status": "error", "detail": f"Database Seed Error: {str(e)}"}
