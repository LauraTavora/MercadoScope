from sqlalchemy import select

from app.database import Base, SessionLocal, engine
from app.models import Plan, Tenant


PLANS = [
    {"code": "starter", "name": "Starter", "max_items_per_job": 50, "max_pages_per_job": 1},
    {"code": "pro", "name": "Pro", "max_items_per_job": 250, "max_pages_per_job": 5},
    {"code": "agency", "name": "Agency", "max_items_per_job": 1000, "max_pages_per_job": 10},
]


def bootstrap_database() -> None:
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        for definition in PLANS:
            plan = db.scalar(select(Plan).where(Plan.code == definition["code"]))
            if not plan:
                db.add(Plan(**definition))
        db.commit()

        default_plan = db.scalar(select(Plan).where(Plan.code == "pro"))
        tenant = db.scalar(select(Tenant).where(Tenant.slug == "demo-store"))
        if not tenant and default_plan:
            db.add(Tenant(slug="demo-store", name="Loja Demo", plan_id=default_plan.id))
            db.commit()
