from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, ConfigDict


class CourseBase(BaseModel):
    name: str = Field(..., description="Course name (e.g. 'Introductory Computer Science')")
    code: str = Field(..., description="Course code (e.g. 'CS101')")
    term: Optional[str] = Field(None, description="Academic term (e.g. 'Fall 2026')")
    color: Optional[str] = Field("#3b82f6", description="Display color hex code")
    description: Optional[str] = Field(None, description="Course syllabus/overview description")


class CourseCreate(CourseBase):
    pass


class CourseResponse(CourseBase):
    id: UUID
    user_id: UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
