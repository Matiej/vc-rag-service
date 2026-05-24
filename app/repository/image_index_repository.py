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

    def find_pending(self) -> list[ImageIndex]:
        return (
            self.session.query(ImageIndex)
            .filter(ImageIndex.vector_status == "PENDING")
            .all()
        )

    def find_similar(
        self,
        vector: list[float],
        limit: int = 10,
        min_score: float = 0.75,
    ) -> list[tuple[ImageIndex, float]]:
        """
        Find the most similar images among VERIFIED records only (joined with recognition_state).
        Returns a list of (ImageIndex, similarity_score) pairs where similarity >= min_score.

        Searching only VERIFIED images ensures that candidates are built from human-confirmed data.
        This is the knowledge base — the more verified images, the better the automatic recognition.

        Cosine similarity = 1 - cosine distance.
        A score of 1.0 means identical vectors (same image found in the verified knowledge base).
        """
        from app.repository.entities import RecognitionState
        distance = ImageIndex.embedding_vector.cosine_distance(vector)
        rows = (
            self.session.query(ImageIndex, (1 - distance).label("similarity"))
            .join(RecognitionState, RecognitionState.image_index_id == ImageIndex.id)
            .filter(ImageIndex.embedding_vector.isnot(None))
            .filter(RecognitionState.verification_status == "VERIFIED")
            .order_by(distance)
            .limit(limit)
            .all()
        )
        return [(image, float(score)) for image, score in rows if float(score) >= min_score]
