from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.service.embedding_service import EmbeddingService

# Application-level singletons — initialized once at startup in main.py.
# Equivalent of @Bean in Spring — one instance shared across the whole process lifetime.
embedding_service: "EmbeddingService | None" = None
