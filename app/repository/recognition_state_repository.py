from sqlalchemy.orm import Session

from app.repository.entities import RecognitionState


class RecognitionStateRepository:
    def __init__(self, session: Session):
        self.session = session

    def save(self, state: RecognitionState) -> RecognitionState:
        self.session.add(state)
        self.session.flush()
        return state
