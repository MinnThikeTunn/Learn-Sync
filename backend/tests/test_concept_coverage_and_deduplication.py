import uuid
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

from backend.app.services.fsrs_engine import ReviewSessionEngine
from backend.app.services.review_repository import InMemoryReviewAdapter
from backend.app.schemas.fsrs import ScheduleStage


MATCHWISE_SAMPLE_TEXT = """MATCHWISE PRISM // OFFICIAL PROOF OF SIGNATURE 
 PRISM ID: MW-9842-AX 
 VERIFIED: 2024-05-14T08:30:00Z 
 NAME: Alex Mercer 
 FIDELITY: Grade A1 (Production Ready) 
 CHROMATIC SPECIFICATION (OKLCH): 
 - SOLAR RESONANCE: L: 0.85 C: 0.12 H: 75.5 
 - DEEP TEAL ANCHOR: L: 0.45 C: 0.08 H: 220.1 
 - VERDANT SPARK: L: 0.78 C: 0.15 H: 155.3 
 AUTHORIZED SIGNATORY: J. Doe Algorithm (Chief Standardization Officer) 
 VERIFICATION CHECKSUM: 0x9842AXe9f73b88d4c201a0942ff610998f448c5"""


def test_offline_concept_extractor_covers_all_facts():
    """Verifies that the offline NLP/rule-based concept extractor parses all key specifications."""
    cards = ReviewSessionEngine.extract_grounded_concept_cards(
        content=MATCHWISE_SAMPLE_TEXT,
        topic="Matchwise Prism MW 9842 AX",
    )
    assert len(cards) >= 8, f"Expected at least 8 concept cards, got {len(cards)}"

    fronts = [c[0].lower() for c in cards]
    backs = [c[1].lower() for c in cards]
    all_text = " ".join(fronts + backs)

    assert "mw-9842-ax" in all_text
    assert "alex mercer" in all_text
    assert "grade a1" in all_text
    assert "solar resonance" in all_text
    assert "deep teal anchor" in all_text
    assert "verdant spark" in all_text
    assert "0x9842ax" in all_text


def test_schedule_handoff_deduplication():
    """Verifies that calling schedule_handoff repeatedly does NOT produce duplicate flashcards."""
    adapter = InMemoryReviewAdapter()
    engine = ReviewSessionEngine(repository=adapter)
    user_id = uuid.uuid4()
    folder_id = uuid.uuid4()
    doc_id = uuid.uuid4()
    topic = "Matchwise Prism MW 9842 AX"

    mock_chunk = {
        "id": str(uuid.uuid4()),
        "document_id": str(doc_id),
        "folder_id": str(folder_id),
        "chunk_index": 0,
        "content": MATCHWISE_SAMPLE_TEXT,
    }

    with patch("backend.app.services.database.db_service.get_document_chunks", return_value=[mock_chunk]):
        # 1. First handoff
        res1 = engine.schedule_handoff(
            user_id=user_id,
            folder_id=folder_id,
            topic=topic,
            document_id=doc_id,
        )
        first_count = res1.cards_scheduled
        assert first_count >= 8

        total_cards_after_1 = len(adapter.cards)
        assert total_cards_after_1 == first_count

        # 2. Second handoff (simulating re-clicking complete lesson / study handoff)
        res2 = engine.schedule_handoff(
            user_id=user_id,
            folder_id=folder_id,
            topic=topic,
            document_id=doc_id,
        )
        assert res2.cards_scheduled == first_count

        # Card count in repository must NOT double or increase
        total_cards_after_2 = len(adapter.cards)
        assert total_cards_after_2 == first_count, (
            f"Expected {first_count} cards without duplicates, but found {total_cards_after_2}"
        )

        # 3. Third handoff
        res3 = engine.schedule_handoff(
            user_id=user_id,
            folder_id=folder_id,
            topic=topic,
            document_id=doc_id,
        )
        assert res3.cards_scheduled == first_count
        assert len(adapter.cards) == first_count


def test_generic_stubs_are_upgraded_to_real_concepts():
    """Verifies that if a deck only contains legacy generic stubs, schedule_handoff upgrades it with real concept cards."""
    adapter = InMemoryReviewAdapter()
    engine = ReviewSessionEngine(repository=adapter)
    user_id = uuid.uuid4()
    folder_id = uuid.uuid4()
    doc_id = uuid.uuid4()
    topic = "Matchwise Prism MW 9842 AX"

    # Pre-seed with the 3 generic template stubs
    adapter.create_card(
        user_id=user_id,
        folder_id=folder_id,
        document_id=doc_id,
        topic=topic,
        front=f"What is the primary definition and significance of {topic}?",
        back="Generic architecture stub.",
    )
    adapter.create_card(
        user_id=user_id,
        folder_id=folder_id,
        document_id=doc_id,
        topic=topic,
        front=f"What is a common edge-case or failure mode in {topic}?",
        back="Generic error stub.",
    )
    adapter.create_card(
        user_id=user_id,
        folder_id=folder_id,
        document_id=doc_id,
        topic=topic,
        front=f"How does {topic} integrate with practical exam scenarios?",
        back="Generic exam stub.",
    )
    assert len(adapter.cards) == 3

    mock_chunk = {
        "id": str(uuid.uuid4()),
        "document_id": str(doc_id),
        "folder_id": str(folder_id),
        "chunk_index": 0,
        "content": MATCHWISE_SAMPLE_TEXT,
    }

    with patch("backend.app.services.database.db_service.get_document_chunks", return_value=[mock_chunk]):
        res = engine.schedule_handoff(
            user_id=user_id,
            folder_id=folder_id,
            topic=topic,
            document_id=doc_id,
        )
        # Should replace generic stubs with comprehensive concept cards
        assert res.cards_scheduled >= 8
