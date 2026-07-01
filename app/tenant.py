from fastapi import Header, HTTPException, Request
from sqlalchemy import select

from app.config import get_settings
from app.database import SessionLocal
from app.models import Tenant


async def resolve_tenant(
    request: Request,
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
) -> Tenant:
    slug = x_tenant_id or request.cookies.get("tenant_slug") or get_settings().default_tenant_slug
    with SessionLocal() as db:
        tenant = db.scalar(select(Tenant).where(Tenant.slug == slug))
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant não encontrado")
        _ = tenant.plan.name
        db.expunge(tenant)
        return tenant
