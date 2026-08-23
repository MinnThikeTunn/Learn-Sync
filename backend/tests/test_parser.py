import math
import uuid
import pytest
from datetime import datetime
from backend.app.services.parser import (
    DoclingSyllabusParser,
    GeminiVisionSyllabusParser,
    SyllabusIngestionService,
)
from backend.app.schemas.syllabus import SyllabusModule, EventTypeEnum


def test_docling_parser_happy_path():
    """Docling successfully extracts structured modules and exams with confidence >= 0.70."""
    sample_syllabus = """
    CS101: Introduction to Computer Science
    Week 1: Foundations of Computation & Binary
    Week 2: Control Flow & Functions
    Week 3: Recursion and Tree Traversal
    Midterm Exam - October 15, 2026
    """
    parser = DoclingSyllabusParser()
    result = parser.parse(sample_syllabus.encode("utf-8"), "cs101_syllabus.pdf")

    assert result.course_code == "CS101"
    assert result.confidence_score >= 0.70
    assert result.parser_used == "docling"
    assert len(result.modules) == 3
    assert result.modules[0].title == "Foundations of Computation & Binary"
    assert len(result.events) >= 1
    assert result.events[0].event_type == EventTypeEnum.EXAM


def test_docling_fallback_to_gemini_on_low_confidence():
    """When Docling confidence falls below 0.70, the pipeline invokes Gemini Vision fallback."""
    sample_low_conf = "CS102: Complex document LOW_CONFIDENCE_TRIGGER Week 1: Only One Topic"
    service = SyllabusIngestionService()
    result = service.parse_syllabus(sample_low_conf.encode("utf-8"), "scanned_doc.pdf")

    assert result.parser_used == "gemini_vision_fallback"
    assert result.confidence_score >= 0.70
    assert len(result.modules) >= 2


def test_docling_fallback_to_gemini_on_exception():
    """When Docling parser raises an unhandled exception, fallback executes gracefully."""
    sample_corrupt = "CORRUPT_LAYOUT_ERROR binary stream"
    service = SyllabusIngestionService()
    result = service.parse_syllabus(sample_corrupt.encode("utf-8"), "corrupted.pdf")

    assert result.parser_used == "gemini_vision_fallback"
    assert len(result.modules) > 0


def test_virtual_folder_hierarchy_building():
    """Verify root folder (depth 0) and module child folders (depth 1) linking parent_id."""
    user_id = uuid.uuid4()
    course_id = uuid.uuid4()
    modules = [
        SyllabusModule(module_number=1, week_number=1, title="Week 1: Intro to Python & OOP!"),
        SyllabusModule(module_number=2, week_number=2, title="Week 2: Data Structures & Graphs"),
    ]

    folders = SyllabusIngestionService.build_virtual_folder_hierarchy(
        course_code="CS101",
        modules=modules,
        course_id=course_id,
        user_id=user_id
    )

    assert len(folders) == 3
    root = folders[0]
    assert root.depth == 0
    assert root.parent_id is None
    assert root.materialized_path == "/CS101"
    assert root.user_id == user_id
    assert root.course_id == course_id

    child1 = folders[1]
    assert child1.depth == 1
    assert child1.parent_id == root.id
    assert child1.materialized_path == "/CS101/Week_01_Intro_to_Python_and_OOP"

    child2 = folders[2]
    assert child2.depth == 1
    assert child2.parent_id == root.id
    assert child2.materialized_path == "/CS101/Week_02_Data_Structures_and_Graphs"


def test_folder_name_sanitization():
    """Sanitizes messy titles with symbols and spaces into clean path names."""
    raw = "Week 1: Big-O & Complexity (Advanced)???"
    sanitized = SyllabusIngestionService.sanitize_folder_name(raw)
    assert sanitized == "Week_01_Big_O_and_Complexity_Advanced"


def test_chunk_document_sizing_overlap_and_embeddings():
    """Document text is chunked into 500-token blocks with 50-token overlap & 1536-dim normalized embeddings."""
    user_id = uuid.uuid4()
    doc_id = uuid.uuid4()
    folder_id = uuid.uuid4()

    # Generate dummy text with 1200 words
    words = [f"word{i}" for i in range(1200)]
    content = " ".join(words)

    chunks = SyllabusIngestionService.chunk_document(
        content=content,
        document_id=doc_id,
        folder_id=folder_id,
        user_id=user_id,
        target_token_size=500,
        overlap_tokens=50,
        embedding_dim=1536
    )

    assert len(chunks) == 3
    for idx, c in enumerate(chunks):
        assert c.chunk_index == idx
        assert c.user_id == user_id
        assert c.document_id == doc_id
        assert c.folder_id == folder_id
        assert len(c.embedding) == 1536
        # Verify unit normalization (norm ≈ 1.0)
        norm = math.sqrt(sum(x * x for x in c.embedding))
        assert math.isclose(norm, 1.0, rel_tol=1e-4)
