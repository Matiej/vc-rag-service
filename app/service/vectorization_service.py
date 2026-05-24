import traceback

from sqlalchemy.orm import Session

from app.repository.entities import ImageIndex, RecognitionCandidate, SimilarityMatch
from app.repository.image_index_repository import ImageIndexRepository
from app.repository.recognition_candidate_repository import RecognitionCandidateRepository
from app.repository.recognition_state_repository import RecognitionStateRepository
from app.repository.similarity_match_repository import SimilarityMatchRepository
from app.service.embedding_service import EmbeddingService


class VectorizationService:
    def __init__(self, session: Session, embedding_service: EmbeddingService):
        self.image_repository = ImageIndexRepository(session)
        self.state_repository = RecognitionStateRepository(session)
        self.similarity_repository = SimilarityMatchRepository(session)
        self.candidate_repository = RecognitionCandidateRepository(session)
        self.embedding_service = embedding_service

    def vectorize(self, image_index: ImageIndex) -> None:
        state = self.state_repository.find_by_image_index_id(image_index.id)
        state.analysis_status = "PROCESSING"

        try:
            vector = self.embedding_service.embed_image(image_index.file_storage_uri)
            image_index.embedding_vector = vector
            image_index.vector_status = "VECTORIZED"

            similar = self.image_repository.find_similar(vector)

            if similar:
                self._save_similarity_matches(image_index.id, similar)
                self._save_similarity_candidate(image_index.id, similar[0])
                state.analysis_status = "DONE"
                state.suggestion_status = "SUGGESTED"
                state.verification_status = "PENDING_REVIEW"
            else:
                state.analysis_status = "DONE"
                state.suggestion_status = "UNKNOWN"

        except Exception:
            image_index.vector_status = "FAILED"
            state.analysis_status = "FAILED"
            state.last_error = traceback.format_exc()

    def _save_similarity_matches(
        self,
        image_index_id: int,
        similar: list[tuple[ImageIndex, float]],
    ) -> None:
        matches = [
            SimilarityMatch(
                image_index_id=image_index_id,
                matched_image_index_id=matched.id,
                similarity_score=score,
                rank=rank + 1,
            )
            for rank, (matched, score) in enumerate(similar)
        ]
        self.similarity_repository.save_all(matches)

    def _save_similarity_candidate(
        self,
        image_index_id: int,
        best_match: tuple[ImageIndex, float],
    ) -> None:
        matched_image, score = best_match
        meta = matched_image.meta_data or {}
        candidate = RecognitionCandidate(
            image_index_id=image_index_id,
            source="similarity",
            candidate_brand=meta.get("brand"),
            candidate_model=meta.get("model"),
            candidate_color=meta.get("color"),
            candidate_type=meta.get("type"),
            candidate_year=meta.get("year"),
            confidence=score,
            is_selected=False,
            human_edited=False,
        )
        self.candidate_repository.save(candidate)
