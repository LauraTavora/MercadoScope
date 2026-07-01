from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.jobs import router as jobs_router
from app.api.pages import router as pages_router
from app.bootstrap import bootstrap_database
from app.config import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    bootstrap_database()
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Coleta pública responsável e análise de preços para portfólio.",
    lifespan=lifespan,
)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(pages_router)
app.include_router(jobs_router)


@app.get("/health", tags=["system"])
def health() -> dict:
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "provider": settings.scraper_provider,
    }
