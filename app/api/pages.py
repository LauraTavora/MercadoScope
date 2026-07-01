from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import ScrapeJob, Tenant
from app.tenant import resolve_tenant

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def dashboard(
    request: Request,
    tenant: Tenant = Depends(resolve_tenant),
    db: Session = Depends(get_db),
):
    db_tenant = db.get(Tenant, tenant.id)
    jobs = list(
        db.scalars(
            select(ScrapeJob)
            .where(ScrapeJob.tenant_id == tenant.id)
            .order_by(ScrapeJob.created_at.desc())
            .limit(10)
        )
    )
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "tenant": db_tenant,
            "jobs": jobs,
            "settings": get_settings(),
        },
    )
