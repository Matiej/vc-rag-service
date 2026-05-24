import os

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=os.getenv("ENV_FILE", ".env.local"),
        env_file_encoding="utf-8",
    )

    app_env: str = "local"
    database_url: str
    pool_size: int = 10
    # Embedding model used for generating image and text vectors via HuggingFace Transformers (CLIP family).
    # The model is loaded once at application startup and kept in memory for the lifetime of the process.
    # Changing this value requires re-vectorizing all existing records (full reindex).
    #
    # Available CLIP-family models (all produce embeddings in the same vector space — image + text compatible):
    #   "openai/clip-vit-base-patch32"   — 512 dim, ~600MB RAM, good baseline, fast on CPU  [current default]
    #   "openai/clip-vit-large-patch14"  — 768 dim, ~1.7GB RAM, better detail recognition
    #   "google/siglip-base-patch16-224" — 768 dim, newer architecture, stronger semantic quality
    embedding_model: str = "openai/clip-vit-base-patch32"
    # How often the vectorization background job runs (in seconds).
    # The job picks up all PENDING images and runs the full pipeline: embed → similarity → candidates.
    vectorize_job_interval_seconds: int = 60


@lru_cache
def get_settings() -> Settings:
    return Settings()
