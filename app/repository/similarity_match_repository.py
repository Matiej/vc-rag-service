from sqlalchemy.orm import Session

from app.repository.entities import SimilarityMatch


class SimilarityMatchRepository:
    def __init__(self, session: Session):
        self.session = session

    def save_all(self, matches: list[SimilarityMatch]) -> None:
        self.session.add_all(matches)
        self.session.flush()

    def find_by_image_index_id(self, image_index_id: int) -> list[SimilarityMatch]:
        return (
            self.session.query(SimilarityMatch)
            .filter(SimilarityMatch.image_index_id == image_index_id)
            .order_by(SimilarityMatch.rank)
            .all()
        )
