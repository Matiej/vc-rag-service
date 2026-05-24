import logging

from app.core import dependencies
from app.core.database import SessionLocal
from app.repository.image_index_repository import ImageIndexRepository
from app.service.vectorization_service import VectorizationService

logger = logging.getLogger(__name__)


def run_vectorize_job() -> None:
    """
    Background job — picks up all PENDING images and runs the full vectorization pipeline:
      embed_image → save vector → similarity search → save candidates → update recognition_state

    Each image is processed in its own commit/rollback so a single failure does not
    block the remaining images in the batch.

    Scheduled via APScheduler in main.py — equivalent of @Scheduled in Spring Boot.
    """
    logger.info("Vectorize job: starting")
    session = SessionLocal()
    try:
        pending = ImageIndexRepository(session).find_pending()
        logger.info("Vectorize job: found %d pending images", len(pending))

        for image in pending:
            try:
                VectorizationService(session, dependencies.embedding_service).vectorize(image)
                session.commit()
                logger.info("Vectorize job: image id=%d vectorized successfully", image.id)
            except Exception:
                session.rollback()
                logger.exception("Vectorize job: failed to vectorize image id=%d", image.id)

    finally:
        session.close()

    logger.info("Vectorize job: done")
