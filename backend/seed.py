"""
seed.py — Populate KIWASCO database with synthetic billing data (Updated April 2026).
Run: python seed.py

Generates:
  - 7 zones
  - ~2,600 customers
  - ~36 months of billing history (Jan 2022 – Dec 2024)
  - 1 admin + 2 demo users
  - System alerts
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from datetime import date
from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app import models
from app.database import Base
from app.auth import get_password_hash
from app.ml.data_generator import (
    ZONES, generate_customers, generate_bills,
    get_zone_customer_count,
)

Base.metadata.create_all(bind=engine)

START_DATE = date(2022, 1, 1)
END_DATE   = date(2026, 5, 1)  # exclusive (includes April 2026)

def months_between(start: date, end: date) -> int:
    delta = relativedelta(end, start)
    return delta.years * 12 + delta.months

def seed():
    db: Session = SessionLocal()
    try:
        print("🌱 Seeding/Updating KIWASCO database...")

        # ── Zones ─────────────────────────────────────────────────────────
        zone_objs = []
        for zd in ZONES:
            # Check if zone already exists by name
            existing_zone = db.query(models.Zone).filter(models.Zone.name == zd["name"]).first()
            if existing_zone:
                zone_objs.append(existing_zone)
                continue
            
            z = models.Zone(**zd)
            db.add(z)
            db.flush() # flush to get ID
            zone_objs.append(z)
            print(f"  + New zone added: {zd['name']}")

        # ── Users ─────────────────────────────────────────────────────────
        users_to_add = [
            models.User(
                username="admin", email="admin@kiwasco.go.ke",
                full_name="KIWASCO Administrator",
                hashed_password=get_password_hash("admin1234"),
                role="admin", is_active=True,
            ),
            models.User(
                username="analyst", email="analyst@kiwasco.go.ke",
                full_name="Revenue Analyst",
                hashed_password=get_password_hash("analyst1234"),
                role="analyst", is_active=True,
            ),
            models.User(
                username="viewer", email="viewer@kiwasco.go.ke",
                full_name="Management Viewer",
                hashed_password=get_password_hash("viewer1234"),
                role="viewer", is_active=True,
            ),
            models.User(
                username="officer", email="officer@kiwasco.go.ke",
                full_name="Billing Officer",
                hashed_password=get_password_hash("officer1234"),
                role="data_manager", is_active=True,
            ),
        ]
        for u in users_to_add:
            if not db.query(models.User).filter(models.User.username == u.username).first():
                db.add(u)
        print("  ✔ Users check complete")

        # ── Customers + Bills ─────────────────────────────────────────────
        months = months_between(START_DATE, END_DATE)
        total_bills = 0
        total_customers = 0

        for zone in zone_objs:
            # ONLY generate for zones that have no customers (newly added zones)
            if db.query(models.Customer).filter(models.Customer.zone_id == zone.id).count() > 0:
                continue

            count = get_zone_customer_count(zone.name, zone.population)
            # Cap for performance during seeding
            count = min(count, 150)
            customer_dicts = generate_customers(zone.id, zone.name, count)

            for cd in customer_dicts:
                conn_date = cd.pop("connection_date", START_DATE)
                c = models.Customer(**cd, connection_date=conn_date)
                db.add(c)
                db.flush()

                bill_dicts = generate_bills(
                    c.id, zone.name, c.customer_type,
                    start_month=START_DATE, months=months,
                )
                for bd in bill_dicts:
                    db.add(models.Bill(**bd))
                total_bills += len(bill_dicts)
            total_customers += count
            print(f"    → {zone.name}: {count} customers, {count * months} bills")

        print(f"  ✔ {total_customers} customers, {total_bills} bills created")

        # ── Alerts ────────────────────────────────────────────────────────
        alerts_data = [
            {"zone_id": None, "message": "System initialized with KIWASCO historical billing data (2022-2026).",
             "threshold_type": "info", "severity": "info"},
            {"zone_id": zone_objs[3].id, "message": f"{zone_objs[3].name}: AI detected an unusual spike in NRW (42.5%) - possible major pipe burst on Ring Road.",
             "threshold_type": "high_nrw", "severity": "critical"},
            {"zone_id": zone_objs[1].id, "message": f"{zone_objs[1].name}: Prophet model predicts a 15% revenue drop next quarter due to seasonal migration patterns.",
             "threshold_type": "revenue_drop", "severity": "warning"},
            {"zone_id": zone_objs[4].id, "message": f"{zone_objs[4].name}: Collection efficiency at 62% - below the 85% corporate KPI.",
             "threshold_type": "revenue_drop", "severity": "warning"},
            {"zone_id": zone_objs[0].id, "message": f"{zone_objs[0].name}: High Demand Alert - Projected to exceed capacity by 20% during the upcoming July dry season.",
             "threshold_type": "capacity_risk", "severity": "critical"},
            {"zone_id": zone_objs[2].id, "message": f"{zone_objs[2].name}: Anomaly Detection - 12 commercial accounts showing zero consumption despite active status.",
             "threshold_type": "info", "severity": "warning"},
            {"zone_id": zone_objs[5].id, "message": f"{zone_objs[5].name}: Positive Trend - Revenue collection improved by 8% following the new digital payment rollout.",
             "threshold_type": "info", "severity": "info"},
        ]
        for ad in alerts_data:
            db.add(models.Alert(**ad))

        db.commit()
        print("\n✅ Seeding complete!")
        print("\n📋 Login credentials:")
        print("   Admin:   username=admin    password=admin1234")
        print("   Analyst: username=analyst  password=analyst1234")
        print("   Viewer:  username=viewer   password=viewer1234")

    except Exception as e:
        db.rollback()
        print(f"❌ Seed failed: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed()
