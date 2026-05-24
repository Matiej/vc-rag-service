from sqlalchemy.orm import Session

from app.api.routes.ingestimage.ingest_image_models import IngestImageRequest, IngestImageResponse
from app.core.config import get_settings
from app.exceptions import ImageAlreadyExistsError
from app.repository.entities import ImageIndex, RecognitionState
from app.repository.image_index_repository import ImageIndexRepository
from app.repository.recognition_state_repository import RecognitionStateRepository


class ImageIngestService:
    def __init__(self, session: Session):
        self.image_repository = ImageIndexRepository(session)
        self.state_repository = RecognitionStateRepository(session)
        self.embedding_model = get_settings().embedding_model

    def ingest_images(self, images_requests: list[IngestImageRequest]) -> list[IngestImageResponse]:
        response: list[IngestImageResponse] = []
        for image in images_requests:
            if self.image_repository.exists_by_hash_and_model(image.image_hash, self.embedding_model):
                raise ImageAlreadyExistsError(image.external_photo_id)
            image_index = ImageIndex(
                external_photo_id=image.external_photo_id,
                file_storage_uri=image.file_storage_uri,
                image_hash=image.image_hash,
                embedding_model=self.embedding_model,
                vector_status="PENDING",
                taken_at=image.taken_at,
                meta_data=image.meta_data
            )
            saved_image = self.image_repository.save(image_index)

            recognition_state = RecognitionState(
                image_index_id=saved_image.id,
                analysis_status="RECEIVED",
                suggestion_status="NONE",
                verification_status="UNVERIFIED",
            )
            self.state_repository.save(recognition_state)
            ingest_image_response = IngestImageResponse(
                ingested_image_id=saved_image.id,
                embedding_model=saved_image.embedding_model,
            )
            response.append(ingest_image_response)

        return response
