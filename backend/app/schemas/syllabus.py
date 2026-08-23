from datetime import datetime
from enum import Enum
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict


class EventTypeEnum(str, Enum):
    EXAM = "exam"
    ASSIGNMENT = "assignment"
    QUIZ = "quiz"
    LECTURE = "lecture"
    PROJECT = "project"
    OTHER = "other"


class EventSourceEnum(str, Enum):
    SYLLABUS = "syllabus"
    GOOGLE_CALENDAR = "google_calendar"
    MANUAL = "manual"


class ParsedEvent(BaseModel):
    """Event extracted from syllabus calendar/schedule."""
    title: str = Field(..., description="Name of the exam, assignment, or deadline")
    event_type: EventTypeEnum = Field(default=EventTypeEnum.ASSIGNMENT, description="Category of event")
    start_time: datetime = Field(..., description="Deadline or event start timestamp (UTC)")
    end_time: Optional[datetime] = Field(None, description="Optional deadline end timestamp (UTC)")
    weight: float = Field(default=1.0, ge=0.0, description="Grading weight or relative priority")
    raw_text: Optional[str] = Field(None, description="Original row text parsed from syllabus")
    
    model_config = ConfigDict(from_attributes=True)


class GradingWeight(BaseModel):
    """Grading category and percentage contribution."""
    category: str = Field(..., description="Category name (e.g. 'Midterm Exam', 'Homework')")
    percentage: float = Field(..., ge=0.0, le=100.0, description="Percentage of total grade (0.0 - 100.0)")
    description: Optional[str] = Field(None, description="Details or policies regarding this category")


class SyllabusModule(BaseModel):
    """Academic module or weekly unit extracted from syllabus."""
    module_number: Optional[int] = Field(None, description="1-indexed sequence number")
    week_number: Optional[int] = Field(None, description="Course week number if specified")
    title: str = Field(..., description="Module/Week topic title (e.g. 'Recursion and Trees')")
    description: Optional[str] = Field(None, description="Summary of covered material")
    topics: List[str] = Field(default_factory=list, description="Sub-topics or concept bullet points")
    reading_materials: List[str] = Field(default_factory=list, description="Chapters, papers, or textbook pages")
    start_date: Optional[datetime] = Field(None, description="Module scheduled start date")
    end_date: Optional[datetime] = Field(None, description="Module scheduled end date")
    events: List[ParsedEvent] = Field(default_factory=list, description="Events/deadlines occurring in this module")


class ParsedSyllabus(BaseModel):
    """Structured output from syllabus parsing pipeline."""
    course_code: str = Field(..., description="Normalized course code (e.g. 'CS101', 'MATH204')")
    course_name: str = Field(..., description="Course full title (e.g. 'Introduction to Computer Science')")
    instructor: Optional[str] = Field(None, description="Instructor name")
    term: Optional[str] = Field(None, description="Academic term (e.g. 'Fall 2026')")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Parser confidence score in [0.0, 1.0]")
    parser_used: Literal["docling", "gemini_vision_fallback", "mock"] = Field(..., description="Parser engine executed")
    grading_weights: List[GradingWeight] = Field(default_factory=list, description="Extracted grading weight rules")
    modules: List[SyllabusModule] = Field(default_factory=list, description="Extracted course modules / weekly units")
    events: List[ParsedEvent] = Field(default_factory=list, description="Aggregated course events and deadlines")
    raw_markdown: Optional[str] = Field(None, description="Extracted raw markdown document text")
