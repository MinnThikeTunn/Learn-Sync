import pytest
from uuid import uuid4
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch
from backend.app.services.database import DatabaseService


def test_build_materialized_path():
    """Verify materialized path calculation for root and child folders."""
    db = DatabaseService()
    root_path = db.calculate_materialized_path(parent_path="", folder_name="CS101")
    assert root_path == "/CS101"

    child_path = db.calculate_materialized_path(parent_path="/CS101", folder_name="Week_03_Recursion")
    assert child_path == "/CS101/Week_03_Recursion"


@patch("backend.app.services.database.SupabaseVectorClient")
def test_create_virtual_folder_persists(mock_client_cls):
    """Verify folder insertion calculates path, depth, and persists to Supabase."""
    mock_instance = MagicMock()
    mock_table = MagicMock()
    mock_instance.client.table.return_value = mock_table
    mock_client_cls.return_value = mock_instance

    folder_id = uuid4()
    mock_table.insert.return_value.execute.return_value.data = [{
        "id": str(folder_id),
        "name": "Week_01",
        "materialized_path": "/CS101/Week_01",
        "depth": 1,
    }]

    db = DatabaseService(supabase_client=mock_instance)
    res = db.create_virtual_folder(
        user_id=uuid4(),
        course_id=uuid4(),
        name="Week_01",
        parent_path="/CS101",
        parent_depth=0
    )

    assert res["id"] == str(folder_id)
    assert res["materialized_path"] == "/CS101/Week_01"
    assert res["depth"] == 1


@patch("backend.app.services.database.SupabaseVectorClient")
def test_get_upcoming_events_queries_window(mock_client_cls):
    """Verify query filters events within lookahead window."""
    mock_instance = MagicMock()
    mock_table = MagicMock()
    mock_instance.client.table.return_value = mock_table
    mock_client_cls.return_value = mock_instance

    now = datetime.now(timezone.utc)
    mock_table.select.return_value.eq.return_value.gte.return_value.lte.return_value.order.return_value.execute.return_value.data = [
        {"id": str(uuid4()), "title": "Midterm Exam", "weight": 3.0, "start_time": (now + timedelta(days=1)).isoformat()}
    ]

    db = DatabaseService(supabase_client=mock_instance)
    events = db.get_upcoming_events(user_id=uuid4(), days_ahead=3)
    assert len(events) == 1
    assert events[0]["title"] == "Midterm Exam"
