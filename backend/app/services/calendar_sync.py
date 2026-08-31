import re
import urllib.parse
from typing import Any, Dict, List, Optional
from uuid import UUID
from datetime import datetime, timezone, timedelta
import httpx
from backend.app.core.config import settings


class GoogleIntegrationService:
    """
    Production-grade Google Calendar & Gmail integration:
    - Generates live OAuth 2.0 Authorization URLs with least-privilege scopes
    - Exchanges authorization codes for access and refresh tokens
    - Synchronizes academic events from Google Calendar API v3
    - Inspects scoped Gmail messages for deadline changes & exam shifts
    - Analyzes free/busy time slot availability for the Burnout Guard
    """

    AUTH_URI = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URI = "https://oauth2.googleapis.com/token"
    CALENDAR_API_BASE = "https://www.googleapis.com/calendar/v3"
    GMAIL_API_BASE = "https://gmail.googleapis.com/gmail/v1"

    SCOPES = [
        "https://www.googleapis.com/auth/calendar.readonly",
        "https://www.googleapis.com/auth/gmail.readonly",
    ]

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        redirect_uri: Optional[str] = None,
    ):
        self.client_id = client_id or settings.GOOGLE_CLIENT_ID or ""
        self.client_secret = client_secret or settings.GOOGLE_CLIENT_SECRET or ""
        self.redirect_uri = redirect_uri or settings.GOOGLE_REDIRECT_URI

    def get_oauth_url(self, user_id: UUID, state: Optional[str] = None) -> str:
        """Constructs official Google OAuth 2.0 Authorization URL."""
        state_payload = state or str(user_id)
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.SCOPES),
            "access_type": "offline",
            "prompt": "consent",
            "state": state_payload,
            "include_granted_scopes": "true",
        }
        return f"{self.AUTH_URI}?{urllib.parse.urlencode(params)}"

    def exchange_code_for_tokens(self, code: str) -> Dict[str, Any]:
        """Exchanges authorization code for access and refresh tokens via Google's token endpoint."""
        data = {
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
            "grant_type": "authorization_code",
        }
        with httpx.Client(timeout=15.0) as client:
            resp = client.post(self.TOKEN_URI, data=data)
            if resp.status_code != 200:
                raise RuntimeError(f"Google OAuth token exchange failed ({resp.status_code}): {resp.text}")
            return resp.json()

    def fetch_calendar_events(
        self,
        access_token: str,
        time_min: datetime,
        time_max: datetime,
        calendar_id: str = "primary",
    ) -> List[Dict[str, Any]]:
        """Fetches and maps calendar events from Google Calendar API v3 into LearnSync events format."""
        headers = {"Authorization": f"Bearer {access_token}"}
        params = {
            "timeMin": time_min.isoformat(),
            "timeMax": time_max.isoformat(),
            "singleEvents": "true",
            "orderBy": "startTime",
        }
        url = f"{self.CALENDAR_API_BASE}/calendars/{urllib.parse.quote(calendar_id)}/events"
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(url, headers=headers, params=params)
            if resp.status_code != 200:
                raise RuntimeError(f"Google Calendar API request failed ({resp.status_code}): {resp.text}")
            data = resp.json()

        items = data.get("items", [])
        parsed_events = []
        for item in items:
            summary = item.get("summary", "Untitled Event")
            start_raw = item.get("start", {}).get("dateTime") or item.get("start", {}).get("date")
            end_raw = item.get("end", {}).get("dateTime") or item.get("end", {}).get("date")

            if not start_raw:
                continue

            summary_lower = summary.lower()
            if "exam" in summary_lower or "midterm" in summary_lower or "final" in summary_lower:
                event_type = "exam"
                weight = 3.0
            elif "project" in summary_lower or "milestone" in summary_lower:
                event_type = "project"
                weight = 2.5
            elif "quiz" in summary_lower:
                event_type = "quiz"
                weight = 1.0
            elif "homework" in summary_lower or "assignment" in summary_lower:
                event_type = "assignment"
                weight = 1.5
            else:
                event_type = "other"
                weight = 0.5

            parsed_events.append({
                "external_id": item.get("id"),
                "title": summary,
                "event_type": event_type,
                "start_time": start_raw,
                "end_time": end_raw,
                "weight": weight,
                "source": "google_calendar",
                "description": item.get("description", ""),
            })

        return parsed_events

    def detect_gmail_deadline_shifts(
        self,
        access_token: str,
        query: str = "subject:(exam OR deadline OR quiz OR postponed OR rescheduled)",
        max_results: int = 10,
    ) -> List[Dict[str, Any]]:
        """Queries scoped Gmail messages for announcements indicating deadline changes."""
        headers = {"Authorization": f"Bearer {access_token}"}
        url = f"{self.GMAIL_API_BASE}/users/me/messages"
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(url, headers=headers, params={"q": query, "maxResults": max_results})
            if resp.status_code != 200:
                return []
            data = resp.json()
            messages = data.get("messages", [])

            detected_shifts = []
            for msg_meta in messages:
                msg_id = msg_meta.get("id")
                msg_resp = client.get(f"{self.GMAIL_API_BASE}/users/me/messages/{msg_id}", headers=headers)
                if msg_resp.status_code == 200:
                    msg_body = msg_resp.json()
                    snippet = msg_body.get("snippet", "")
                    detected_shifts.append({
                        "message_id": msg_id,
                        "snippet": snippet,
                        "is_postponed": bool(re.search(r"\b(postponed|moved|extended|rescheduled)\b", snippet, re.IGNORECASE)),
                    })
            return detected_shifts

    def evaluate_free_busy_density(
        self,
        events: List[Dict[str, Any]],
        start_time: datetime,
        days: int = 2,
    ) -> Dict[str, Any]:
        """Calculates booked hours per day and flags consecutive days with zero free study slots (>60 mins)."""
        daily_booked_hours = [0.0] * days
        for i in range(days):
            day_start = start_time + timedelta(days=i)
            day_end = day_start + timedelta(days=1)

            booked_seconds = 0
            for evt in events:
                e_start = evt.get("start_time")
                e_end = evt.get("end_time") or (e_start + timedelta(hours=1) if isinstance(e_start, datetime) else e_start)
                if isinstance(e_start, str):
                    try:
                        e_start = datetime.fromisoformat(e_start)
                    except Exception:
                        continue
                if isinstance(e_end, str):
                    try:
                        e_end = datetime.fromisoformat(e_end)
                    except Exception:
                        continue

                # Overlap with current day
                if e_start and e_end and e_start < day_end and e_end > day_start:
                    overlap_start = max(e_start, day_start)
                    overlap_end = min(e_end, day_end)
                    booked_seconds += max(0, (overlap_end - overlap_start).total_seconds())

            daily_booked_hours[i] = booked_seconds / 3600.0

        consecutive_zero_free = 0
        current_streak = 0
        for booked in daily_booked_hours:
            # Assuming ~8 waking productive hours; if booked >= 7 hours, zero free slots
            if booked >= 7.0:
                current_streak += 1
                consecutive_zero_free = max(consecutive_zero_free, current_streak)
            else:
                current_streak = 0

        return {
            "daily_booked_hours": daily_booked_hours,
            "zero_free_slots_consecutive_days": consecutive_zero_free,
        }


google_sync_service = GoogleIntegrationService()
