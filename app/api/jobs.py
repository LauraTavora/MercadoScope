from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import ProductSnapshot, ScrapeJob, Tenant
from app.schemas import JobCreate, JobOut, ProductOut
from app.services.exporter import export_csv
from app.services.jobs import execute_job
from app.services.report import build_pdf_report
from app.tenant import resolve_tenant

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


def _get_owned_job(db: Session, tenant: Tenant, job_id: str) -> ScrapeJob:
    job = db.scalar(
        select(ScrapeJob).where(ScrapeJob.id == job_id, ScrapeJob.tenant_id == tenant.id)
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job não encontrado")
    return job


@router.post("", response_model=JobOut, status_code=202)
def create_job(
    payload: JobCreate,
    background_tasks: BackgroundTasks,
    tenant: Tenant = Depends(resolve_tenant),
    db: Session = Depends(get_db),
) -> ScrapeJob:
    db_tenant = db.get(Tenant, tenant.id)
    if not db_tenant:
        raise HTTPException(status_code=404, detail="Tenant não encontrado")
    max_pages = min(payload.max_pages, db_tenant.plan.max_pages_per_job)
    job = ScrapeJob(
        tenant_id=db_tenant.id,
        query=payload.query,
        category_url=str(payload.category_url) if payload.category_url else None,
        provider=get_settings().scraper_provider,
        sort=payload.sort,
        max_pages=max_pages,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    background_tasks.add_task(execute_job, job.id)
    return job


@router.get("/{job_id}", response_model=JobOut)
def get_job(
    job_id: str,
    tenant: Tenant = Depends(resolve_tenant),
    db: Session = Depends(get_db),
) -> ScrapeJob:
    return _get_owned_job(db, tenant, job_id)


@router.get("/{job_id}/products", response_model=list[ProductOut])
def get_products(
    job_id: str,
    tenant: Tenant = Depends(resolve_tenant),
    db: Session = Depends(get_db),
) -> list[ProductSnapshot]:
    _get_owned_job(db, tenant, job_id)
    return list(
        db.scalars(
            select(ProductSnapshot)
            .where(ProductSnapshot.job_id == job_id)
            .order_by(ProductSnapshot.position)
        )
    )


@router.get("/{job_id}/export.csv")
def download_csv(
    job_id: str,
    tenant: Tenant = Depends(resolve_tenant),
    db: Session = Depends(get_db),
) -> FileResponse:
    job = _get_owned_job(db, tenant, job_id)
    products = [
        {
            "position": p.position,
            "title": p.title,
            "price": p.price,
            "currency": p.currency,
            "rating": p.rating,
            "review_count": p.review_count,
            "sold_quantity": p.sold_quantity,
            "product_url": p.product_url,
            "image_url": p.image_url,
        }
        for p in job.products
    ]
    if not products:
        raise HTTPException(status_code=409, detail="O job ainda não possui produtos")
    path = get_settings().exports_dir / f"{job_id}.csv"
    export_csv(products, path)
    return FileResponse(path, media_type="text/csv", filename=f"mercadoscope-{job_id}.csv")


@router.get("/{job_id}/report.pdf")
def download_report(
    job_id: str,
    tenant: Tenant = Depends(resolve_tenant),
    db: Session = Depends(get_db),
) -> FileResponse:
    job = _get_owned_job(db, tenant, job_id)
    products = [
        {
            "position": p.position,
            "title": p.title,
            "price": p.price,
            "currency": p.currency,
            "rating": p.rating,
            "review_count": p.review_count,
            "sold_quantity": p.sold_quantity,
            "product_url": p.product_url,
            "image_url": p.image_url,
        }
        for p in job.products
    ]
    if not products:
        raise HTTPException(status_code=409, detail="O job ainda não possui produtos")
    settings = get_settings()
    path = settings.reports_dir / f"{job_id}.pdf"
    build_pdf_report(job.query, products, path, settings.app_version)
    return FileResponse(path, media_type="application/pdf", filename=f"relatorio-{job_id}.pdf")
