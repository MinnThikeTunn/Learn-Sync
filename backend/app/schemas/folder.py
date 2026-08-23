from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, ConfigDict
from backend.app.schemas.syllabus import ParsedSyllabus, ParsedEvent


class VirtualFolderBase(BaseModel):
    name: str = Field(..., description="Display name of folder (e.g. 'Week_03_Recursion')")
    materialized_path: str = Field(..., description="Hierarchical path (e.g. '/CS101/Week_03_Recursion')")
    depth: int = Field(default=0, ge=0, description="Folder depth in tree (0 for root course folder)")


class VirtualFolderCreate(VirtualFolderBase):
    id: UUID = Field(default_factory=uuid4, description="Unique folder identifier")
    user_id: UUID = Field(..., description="Owner student UUID")
    course_id: UUID = Field(..., description="Bound course UUID")
    parent_id: Optional[UUID] = Field(None, description="Parent folder UUID if nested")


class VirtualFolderNode(VirtualFolderBase):
    """Hierarchical virtual folder tree node."""
    id: UUID
    user_id: UUID
    course_id: UUID
    parent_id: Optional[UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    children: List["VirtualFolderNode"] = Field(default_factory=list, description="Nested child virtual folders")

    model_config = ConfigDict(from_attributes=True)


class DocumentChunkCreate(BaseModel):
    """500-token chunk model for pgvector document_chunks table."""
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID = Field(..., description="Owner student UUID")
    document_id: UUID = Field(..., description="Source document UUID")
    folder_id: UUID = Field(..., description="Scoped virtual folder UUID")
    chunk_index: int = Field(..., ge=0, description="0-indexed sequence position in document")
    content: str = Field(..., description="Chunk text content (~500 tokens)")
    token_count: int = Field(..., ge=0, description="Actual token count")
    embedding: List[float] = Field(..., description="1536-dimensional vector embedding")

    model_config = ConfigDict(from_attributes=True)


class StagedSyllabusPreviewResponse(BaseModel):
    """API preview response staged for student confirmation before DB persistence."""
    syllabus: ParsedSyllabus
    suggested_folders: List[VirtualFolderCreate]
    suggested_events: List[ParsedEvent]
