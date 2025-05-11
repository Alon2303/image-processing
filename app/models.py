from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID

class ImageUploadResponse(BaseModel):
    image_id: UUID
    filename: str
    url: str

class ImageVersion(BaseModel):
    version_id: UUID
    image_id: UUID
    filename: str
    url: str
    created_at: str
    transformation: Optional[str] = None

class ImageMetadata(BaseModel):
    image_id: UUID
    filename: str
    versions: List[ImageVersion]
    created_at: str 