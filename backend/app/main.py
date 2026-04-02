from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.database import Base, engine, get_db
from app.routers import auth, zones, customers, bills, forecasts, dashboard, reports

# Create all tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="KIWASCO Sales & Revenue Forecasting API",
    description="AI-powered forecasting system for Kisumu Water & Sewerage Company",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS — allow React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten in production to your Render/Vercel URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
def setup_cloud_demo(db: Session = Depends(get_db)):
    """Initialize empty cloud database with demo accounts and data."""
    from app.models import User, Zone
    from app.auth import get_password_hash
    import logging

    if db.query(User).filter(User.username == "admin").first():
        return {"status": "already_setup", "detail": "Demo accounts already exist."}
        
    logging.info("Creating demo accounts...")
    demos = [
        {"username": "admin", "password": "admin1234", "role": "admin", "full_name": "System Admin"},
        {"username": "analyst", "password": "analyst1234", "role": "analyst", "full_name": "Data Analyst"},
        {"username": "viewer", "password": "viewer1234", "role": "viewer", "full_name": "KIWASCO Viewer"},
    ]
    for d in demos:
        user = User(
            username=d["username"],
            email=f"{d['username']}@kiwasco.co.ke",
            full_name=d["full_name"],
            hashed_password=get_password_hash(d["password"]),
            role=d["role"]
        )
        db.add(user)
    db.commit()

    return {
        "status": "success", 
        "detail": "Created demo accounts: admin, analyst, viewer. You can now log in!"
    }
