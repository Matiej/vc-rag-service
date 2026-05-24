from sqlalchemy.orm import Session

from app.repository.entities import RecognitionState


class RecognitionStateRepository:
    def __init__(self, session: Session):
        self.session = session

    def save(self, state: RecognitionState) -> RecognitionState:
        self.session.add(state)
        self.session.flush()
        return state

    def find_by_image_index_id(self, image_index_id: int) -> RecognitionState | None:
        return (
            self.session.query(RecognitionState)
            .filter(RecognitionState.image_index_id == image_index_id)
            .first()
        )
