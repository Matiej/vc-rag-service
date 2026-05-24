from sqlalchemy.orm import Session

from app.repository.entities import RecognitionCandidate


class RecognitionCandidateRepository:
    def __init__(self, session: Session):
        self.session = session

    def save(self, candidate: RecognitionCandidate) -> RecognitionCandidate:
        self.session.add(candidate)
        self.session.flush()
        return candidate

    def find_by_image_index_id(self, image_index_id: int) -> list[RecognitionCandidate]:
        return (
            self.session.query(RecognitionCandidate)
            .filter(RecognitionCandidate.image_index_id == image_index_id)
            .order_by(RecognitionCandidate.confidence.desc())
            .all()
        )

    def find_selected_by_image_index_id(self, image_index_id: int) -> RecognitionCandidate | None:
        return (
            self.session.query(RecognitionCandidate)
            .filter(
                RecognitionCandidate.image_index_id == image_index_id,
                RecognitionCandidate.is_selected == True,
            )
            .first()
        )
