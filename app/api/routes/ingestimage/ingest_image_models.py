from datetime import datetime

from pydantic import BaseModel


class IngestImageResponse(BaseModel):
    ingested_image_id: int
    embedding_model: str


class IngestImagesResponse(BaseModel):
    ingest_images: list[IngestImageResponse]


class IngestImageRequest(BaseModel):
    external_photo_id: str
    file_storage_uri: str
    image_hash: str
    taken_at: datetime


class IngestImagesRequest(BaseModel):
    ingest_images: list[IngestImageRequest]
