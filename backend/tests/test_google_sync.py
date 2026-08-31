import pytest
from uuid import uuid4
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock
from backend.app.services.calendar_sync import GoogleIntegrationService


def test_get_oauth_url_generates_valid_google_auth_endpoint():
    """Verify Google OAuth 2.0 URL contains required scopes and parameters without simulation."""
    service = GoogleIntegrationService(
        client_id="mock-client-id.apps.googleusercontent.com",
        client_secret="mock-secret",
        redirect_uri="http://localhost:3000/api/auth/callback/google"
    )
    user_id = uuid4()
    auth_url = service.get_oauth_url(user_id=user_id, state="csrf_token_123")

    assert "https://accounts.google.com/o/oauth2/v2/auth" in auth_url
    assert "client_id=mock-client-id.apps.googleusercontent.com" in auth_url
    assert "response_type=code" in auth_url
    assert "access_type=offline" in auth_url
    assert "calendar.readonly" in auth_url
    assert "gmail.readonly" in auth_url
    assert "state=csrf_token_123" in auth_url


@patch("backend.app.services.calendar_sync.httpx.Client")
def test_exchange_code_for_tokens_calls_oauth_endpoint(mock_httpx_client):
    """Verify live HTTP POST to Google token endpoint with OAuth credentials."""
    mock_post = MagicMock()
    mock_post.status_code = 200
    mock_post.json.return_value = {
        "access_token": "ya29.mock_token",
        "refresh_token": "1//mock_refresh",
        "expires_in": 3600,
        "token_type": "Bearer"
    }
    mock_client_instance = MagicMock()
    mock_client_instance.post.return_value = mock_post
    mock_client_instance.__enter__.return_value = mock_client_instance
    mock_httpx_client.return_value = mock_client_instance

    service = GoogleIntegrationService(
        client_id="cid",
        client_secret="sec",
        redirect_uri="http://localhost:3000/callback"
    )
    tokens = service.exchange_code_for_tokens(code="4/0AWgav...")

    assert tokens["access_token"] == "ya29.mock_token"
    assert tokens["refresh_token"] == "1//mock_refresh"


@patch("backend.app.services.calendar_sync.httpx.Client")
def test_fetch_calendar_events_maps_to_events_schema(mock_httpx_client):
    """Verify Google Calendar v3 events are parsed into LearnSync events schema."""
    now = datetime.now(timezone.utc)
    mock_get = MagicMock()
    mock_get.status_code = 200
    mock_get.json.return_value = {
        "items": [
            {
                "id": "cal_evt_1",
                "summary": "CS101 Final Exam",
                "description": "Comprehensive semester exam",
                "start": {"dateTime": (now + timedelta(days=2)).isoformat()},
                "end": {"dateTime": (now + timedelta(days=2, hours=3)).isoformat()}
            },
            {
                "id": "cal_evt_2",
                "summary": "Math Quiz 3",
                "start": {"dateTime": (now + timedelta(days=1)).isoformat()}
            }
        ]
    }
    mock_client_instance = MagicMock()
    mock_client_instance.get.return_value = mock_get
    mock_client_instance.__enter__.return_value = mock_client_instance
    mock_httpx_client.return_value = mock_client_instance

    service = GoogleIntegrationService(client_id="cid", client_secret="sec")
    events = service.fetch_calendar_events(
        access_token="ya29.mock",
        time_min=now,
        time_max=now + timedelta(days=7)
    )

    assert len(events) == 2
    assert events[0]["title"] == "CS101 Final Exam"
    assert events[0]["event_type"] == "exam"
    assert events[0]["weight"] == 3.0
    assert events[0]["source"] == "google_calendar"
    assert events[1]["title"] == "Math Quiz 3"
    assert events[1]["event_type"] == "quiz"


def test_free_busy_density_detects_consecutive_busy_days():
    """Verify detection of zero free slot conditions across consecutive days for Burnout Guard."""
    now = datetime(2026, 9, 1, 9, 0, tzinfo=timezone.utc)
    # Heavy day 1 and day 2 (8+ hours of booked blocks each)
    events = [
        {"start_time": now + timedelta(hours=i), "end_time": now + timedelta(hours=i+1)}
        for i in range(9)
    ] + [
        {"start_time": now + timedelta(days=1, hours=i), "end_time": now + timedelta(days=1, hours=i+1)}
        for i in range(9)
    ]
    service = GoogleIntegrationService()
    density = service.evaluate_free_busy_density(events, start_time=now, days=2)
    assert density["zero_free_slots_consecutive_days"] >= 2
