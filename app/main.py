from fastapi import FastAPI
from sqlalchemy import text

from app.api.routes.health.health_routes import router as health_router
from app.core.database import engine
from app.repository.entities import Base, ImageIndex, RecognitionState, RecognitionCandidate, SimilarityMatch

app = FastAPI()

app.include_router(health_router, prefix="/api/v1")

def init_tables():
    Base.metadata.create_all(
        engine,
        tables=[
            ImageIndex.__table__,
            RecognitionState.__table__,
            RecognitionCandidate.__table__,
            SimilarityMatch.__table__,        ]
    )

@app.on_event("startup")
def test_db_connection():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("Database connected successfully.")
    init_tables()

