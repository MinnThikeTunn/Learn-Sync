import pytest
from uuid import uuid4
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock
from backend.app.schemas.workload import WorkloadMode
from backend.app.services.workload import WorkloadEngine


@patch("backend.app.services.database.db_service")
def test_evaluate_user_workload_queries_db_and_logs(mock_db):
    """Verify live workload calculation queries upcoming events from DB and records log."""
    user_id = uuid4()
    now = datetime.now(timezone.utc)
    mock_db.get_upcoming_events.return_value = [
        {
            "id": str(uuid4()),
            "user_id": str(user_id),
            "title": "CS101 Final Exam",
            "event_type": "exam",
            "weight": 3.0,
            "start_time": (now + timedelta(days=1)).isoformat(),
            "is_completed": False
        }
    ]
    mock_db.record_workload_log.return_value = {"id": str(uuid4()), "score": 0.375}

    response = WorkloadEngine.evaluate_user_workload(user_id=user_id, previous_mode=WorkloadMode.FREE)

    assert response.score > 0.0
    assert response.active_event_count == 1
    mock_db.get_upcoming_events.assert_called_once_with(user_id=user_id, days_ahead=3)
    mock_db.record_workload_log.assert_called_once()
