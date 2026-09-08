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
    processing_job_id: Optional[str] = None


class DocumentChunkDetail(BaseModel):
    id: Optional[str] = None
    chunk_index: int
    content: str
    token_count: int = 0


class DocumentContentResponse(BaseModel):
    id: UUID
    file_name: str
    file_type: str
    file_size_bytes: int = 0
    storage_path: str
    status: str
    signed_url: Optional[str] = None
    raw_url: str
    full_text: str
    chunks: List[DocumentChunkDetail] = []
    total_chunks: int = 0
    total_words: int = 0
    estimated_read_time_minutes: int = 1

