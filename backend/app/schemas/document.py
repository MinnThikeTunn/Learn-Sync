from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, ConfigDict


class DocumentBase(BaseModel):
    file_name: str
    file_type: str
    file_size_bytes: int = 0
    storage_path: str
    status: str = "pending"
    error_message: Optional[str] = None


class DocumentCreate(DocumentBase):
    user_id: UUID
    course_id: UUID
    folder_id: Optional[UUID] = None


class DocumentResponse(DocumentBase):
    id: UUID
    user_id: UUID
    course_id: UUID
    folder_id: Optional[UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class DocumentUploadResponse(DocumentResponse):
    chunks_created: int = 0
