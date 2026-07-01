from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import delete

from app.config import get_settings
from app.database import SessionLocal
from app.models import JobStatus, ProductSnapshot, ScrapeJob
from app.services.scraper import ScrapeRequest, build_scraper


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def execute_job(job_id: str) -> None:
    settings = get_settings()
    with SessionLocal() as db:
        job = db.get(ScrapeJob, job_id)
        if not job:
            return
        tenant = job.tenant
        max_items = tenant.plan.max_items_per_job
        job.status = JobStatus.running.value
        job.progress = 2
        job.started_at = utcnow()
        db.commit()
        request = ScrapeRequest(
            query=job.query,
            category_url=job.category_url,
            max_pages=min(job.max_pages, tenant.plan.max_pages_per_job),
            max_items=max_items,
            sort=job.sort,
        )

    async def progress(value: int) -> None:
        with SessionLocal() as db:
            current = db.get(ScrapeJob, job_id)
            if current:
                current.progress = max(current.progress, min(value, 95))
                db.commit()

    try:
        scraper = build_scraper(settings)
        products = await scraper.scrape(request, progress)
        with SessionLocal() as db:
            job = db.get(ScrapeJob, job_id)
            if not job:
                return
            db.execute(delete(ProductSnapshot).where(ProductSnapshot.job_id == job_id))
            for product in products:
                db.add(ProductSnapshot(job_id=job_id, **product))
            job.item_count = len(products)
            job.progress = 100
            job.status = JobStatus.completed.value
            job.finished_at = utcnow()
            db.commit()
    except Exception as exc:
        with SessionLocal() as db:
            job = db.get(ScrapeJob, job_id)
            if job:
                job.status = JobStatus.failed.value
                job.error_message = str(exc)[:2000]
                job.progress = 100
                job.finished_at = utcnow()
                db.commit()

