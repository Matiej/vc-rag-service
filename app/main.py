import logging

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, Request
from sqlalchemy import text
from starlette.responses import JSONResponse

from app.api.routes.health.health_routes import router as health_router
from app.api.routes.ingestimage.ingest_image_routes import router as ingest_image_router
from app.core import dependencies
from app.core.config import get_settings
from app.core.database import engine
from app.exceptions import ImageAlreadyExistsError
from app.jobs.vectorize_job import run_vectorize_job
from app.repository.entities import Base
from app.service.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

app = FastAPI()
scheduler = BackgroundScheduler()

app.include_router(health_router, prefix="/api/v1")
app.include_router(ingest_image_router, prefix="/api/v1")


def init_tables():
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    Base.metadata.create_all(engine)


def init_embedding_service():
    model_name = get_settings().embedding_model
    logger.info("Loading embedding model: %s", model_name)
    dependencies.embedding_service = EmbeddingService(model_name)
    logger.info("Embedding model loaded successfully")


def init_scheduler():
    interval = get_settings().vectorize_job_interval_seconds
    scheduler.add_job(run_vectorize_job, "interval", seconds=interval)
    scheduler.start()
    logger.info("Vectorize job scheduled every %d seconds", interval)


@app.on_event("startup")
def on_startup():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    logger.info("Database connected successfully.")
    init_tables()
    init_embedding_service()
    init_scheduler()


@app.on_event("shutdown")
def on_shutdown():
    scheduler.shutdown()
    logger.info("Scheduler stopped.")


@app.exception_handler(ImageAlreadyExistsError)
def image_already_exists_handler(request: Request, exc: ImageAlreadyExistsError) -> JSONResponse:
    return JSONResponse(
        status_code=409,
        content={"detail": f"Image already exist: {exc.external_photo_id}"},
    )
