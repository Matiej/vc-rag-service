from fastapi import FastAPI, Request
from sqlalchemy import text
from starlette.responses import JSONResponse

from app.api.routes.health.health_routes import router as health_router
from app.api.routes.ingestimage.ingest_image_routes import router as ingest_image_router
from app.core.database import engine
from app.exceptions import ImageAlreadyExistsError
from app.repository.entities import Base

app = FastAPI()

app.include_router(health_router, prefix="/api/v1")
app.include_router(ingest_image_router, prefix="/api/v1")


def init_tables():
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    Base.metadata.create_all(engine)


@app.on_event("startup")
def test_db_connection():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("Database connected successfully.")
    init_tables()


@app.exception_handler(ImageAlreadyExistsError)
def image_already_exists_handler(request: Request, exc: ImageAlreadyExistsError) -> JSONResponse:
    return JSONResponse(
        status_code=409,
        content={"detail": f"Image already exist: {exc.external_photo_id}"},
    )
