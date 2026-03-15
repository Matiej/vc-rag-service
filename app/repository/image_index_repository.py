from sqlalchemy.orm import Session

from app.repository.entities import ImageIndex


class ImageIndexRepository:

    def __init__(self, session: Session):
        self.session = session

    def save(self, image: ImageIndex) -> ImageIndex:
        self.session.add(image)
        self.session.flush()
        return image

    def find_by_external_photo_id(self, external_photo_id: str) -> ImageIndex | None:
        return (
            self.session.query(ImageIndex)
            .filter(ImageIndex.external_photo_id == external_photo_id)
            .first()
        )

    def get_by_id(self, image_id: int) -> ImageIndex | None:
        return self.session.get(ImageIndex, image_id)

    def exists_by_hash_and_model(self, image_hash: str, embedding_model: str) -> bool:
        return (
                self.session.query(ImageIndex)
                .filter(
                    ImageIndex.image_hash == image_hash,
                    ImageIndex.embedding_model == embedding_model,
                )
                .first() is not None
        )
