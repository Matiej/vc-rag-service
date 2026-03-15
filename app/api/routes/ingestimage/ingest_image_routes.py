from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.routes.ingestimage.ingest_image_models import IngestImagesResponse, IngestImagesRequest
from app.core.database import get_db
from app.service.image_ingest_service import ImageIngestService

router = APIRouter()


@router.post("/ingest/images", response_model=IngestImagesResponse)
def ingest_images(payload: IngestImagesRequest, db: Session = Depends(get_db)) -> IngestImagesResponse:
    service = ImageIngestService(db)
    ingested_images = service.ingest_images(payload.ingest_images)
    return IngestImagesResponse(
        ingest_images=ingested_images
    )
