#!/usr/bin/env python3
# =============================================================================
# Outlook (O365) → Google Calendar one-way sync
#
# CRON SETUP — run every hour:
#   0 * * * * /path/to/venv/bin/python /path/to/sync_outlook_to_google.py >> /var/log/cal_sync.log 2>&1
#
# FIRST-RUN SETUP:
#   1. python -m venv venv && venv/bin/pip install -r requirements.txt
#   2. cp .env.example .env  # fill in real credentials
#   3. Place credentials.json (from Google Cloud Console) in this directory
#   4. Run once interactively to complete both OAuth flows:
#        venv/bin/python sync_outlook_to_google.py
#   5. Verify state.json, token.json, .ms_token_cache.json were created
#   6. Add the cron entry above (update the paths)
# =============================================================================

import json
import logging
import os
import sys
import time
from datetime import datetime, timezone, timedelta
from typing import Any

import msal
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

GRAPH_BASE = "https://graph.microsoft.com/v1.0"
GRAPH_SCOPES = ["Calendars.Read", "offline_access", "User.Read"]
GOOGLE_SCOPES = ["https://www.googleapis.com/auth/calendar"]

STATE_FILE = "state.json"
MS_TOKEN_CACHE = ".ms_token_cache.json"

MAX_RETRIES = 5
RETRY_STATUSES = {429, 500, 502, 503, 504}

CALENDAR_VIEW_SELECT = (
    "id,subject,start,end,body,location,isAllDay,isCancelled,"
    "recurrence,organizer,attendees,showAs"
)


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def setup_logging() -> logging.Logger:
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    return logging.getLogger(__name__)


logger = setup_logging()


# ---------------------------------------------------------------------------
# State management
# ---------------------------------------------------------------------------

StateDict = dict[str, Any]


def load_state(path: str = STATE_FILE) -> StateDict:
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"delta_link": None, "event_map": {}, "last_sync": None}


def save_state(state: StateDict, path: str = STATE_FILE) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(state, f, indent=2)
    os.replace(tmp, path)


# ---------------------------------------------------------------------------
# Microsoft Graph authentication
# ---------------------------------------------------------------------------

def build_msal_app(client_id: str, client_secret: str, tenant_id: str) -> msal.ConfidentialClientApplication:
    cache = msal.SerializableTokenCache()
    if os.path.exists(MS_TOKEN_CACHE):
        with open(MS_TOKEN_CACHE) as f:
            cache.deserialize(f.read())
    app = msal.ConfidentialClientApplication(
        client_id=client_id,
        client_credential=client_secret,
        authority=f"https://login.microsoftonline.com/{tenant_id}",
        token_cache=cache,
    )
    return app


def _save_ms_cache(app: msal.ConfidentialClientApplication) -> None:
    if app.token_cache.has_state_changed:
        with open(MS_TOKEN_CACHE, "w") as f:
            f.write(app.token_cache.serialize())


def acquire_ms_token(app: msal.ConfidentialClientApplication, scopes: list[str]) -> str:
    accounts = app.get_accounts()
    result = None

    if accounts:
        result = app.acquire_token_silent(scopes, account=accounts[0])

    if not result or "access_token" not in result:
        logger.info("No cached Microsoft token — starting device code flow")
        flow = app.initiate_device_flow(scopes=scopes)
        if "user_code" not in flow:
            raise RuntimeError(f"Device flow failed: {flow.get('error_description', flow)}")
        print(f"\n{flow['message']}\n", flush=True)
        result = app.acquire_token_by_device_flow(flow)

    if "access_token" not in result:
        raise RuntimeError(f"Microsoft auth failed: {result.get('error_description', result)}")

    _save_ms_cache(app)
    return result["access_token"]


# ---------------------------------------------------------------------------
# Microsoft Graph API
# ---------------------------------------------------------------------------

def graph_request(
    method: str,
    url: str,
    token: str,
    params: dict | None = None,
    retries: int = MAX_RETRIES,
) -> dict:
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    wait = 1
    for attempt in range(retries + 1):
        resp = requests.request(method, url, headers=headers, params=params, timeout=30)
        if resp.status_code not in RETRY_STATUSES:
            resp.raise_for_status()
            return resp.json()
        if attempt == retries:
            resp.raise_for_status()
        retry_after = int(resp.headers.get("Retry-After", wait))
        logger.warning("HTTP %s from Graph API; retrying in %ss", resp.status_code, retry_after)
        time.sleep(retry_after)
        wait = min(wait * 2, 60)
    return {}


def _paginate_graph(token: str, first_url: str, params: dict | None = None) -> tuple[list[dict], str | None]:
    events: list[dict] = []
    delta_link: str | None = None
    url: str | None = first_url

    while url:
        page = graph_request("GET", url, token, params=params if url == first_url else None)
        events.extend(page.get("value", []))
        delta_link = page.get("@odata.deltaLink")
        url = page.get("@odata.nextLink")

    return events, delta_link


def fetch_outlook_events_full(
    token: str,
    days_past: int = 90,
    days_future: int = 90,
) -> tuple[list[dict], str]:
    now = datetime.now(timezone.utc)
    start = (now - timedelta(days=days_past)).strftime("%Y-%m-%dT%H:%M:%SZ")
    end = (now + timedelta(days=days_future)).strftime("%Y-%m-%dT%H:%M:%SZ")

    url = f"{GRAPH_BASE}/me/calendarView/delta"
    params = {
        "startDateTime": start,
        "endDateTime": end,
        "$select": CALENDAR_VIEW_SELECT,
        "$top": "50",
    }

    events, delta_link = _paginate_graph(token, url, params)

    if not delta_link:
        raise RuntimeError("No deltaLink returned from full calendarView sync")

    return events, delta_link


def fetch_outlook_events_delta(token: str, delta_link: str) -> tuple[list[dict], str]:
    events, new_delta_link = _paginate_graph(token, delta_link)

    if not new_delta_link:
        raise RuntimeError("No deltaLink returned from delta sync — token may have expired")

    return events, new_delta_link


# ---------------------------------------------------------------------------
# Field mapping helpers
# ---------------------------------------------------------------------------

def strip_html(content: str | None) -> str:
    if not content:
        return ""
    soup = BeautifulSoup(content, "html.parser")
    for br in soup.find_all("br"):
        br.replace_with("\n")
    return soup.get_text()


def outlook_to_google_event(ev: dict) -> dict:
    google: dict[str, Any] = {}

    google["summary"] = ev.get("subject", "(no title)")

    body = ev.get("body", {})
    if body.get("contentType") == "html":
        google["description"] = strip_html(body.get("content"))
    else:
        google["description"] = body.get("content", "")

    is_all_day = ev.get("isAllDay", False)
    start = ev.get("start", {})
    end = ev.get("end", {})

    if is_all_day:
        google["start"] = {"date": start.get("dateTime", "")[:10]}
        google["end"] = {"date": end.get("dateTime", "")[:10]}
    else:
        tz = start.get("timeZone", "UTC")
        google["start"] = {"dateTime": start.get("dateTime", ""), "timeZone": tz}
        google["end"] = {"dateTime": end.get("dateTime", ""), "timeZone": end.get("timeZone", tz)}

    location = ev.get("location", {}).get("displayName")
    if location:
        google["location"] = location

    organizer_email = ev.get("organizer", {}).get("emailAddress", {}).get("address", "").lower()
    attendees = []
    for att in ev.get("attendees", []):
        email = att.get("emailAddress", {}).get("address", "")
        if email and email.lower() != organizer_email:
            attendees.append({"email": email})
    if attendees:
        google["attendees"] = attendees

    if ev.get("isCancelled"):
        google["status"] = "cancelled"

    return google


# ---------------------------------------------------------------------------
# Google Calendar authentication
# ---------------------------------------------------------------------------

def get_google_service(credentials_file: str, token_file: str = "token.json"):
    creds = None
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, GOOGLE_SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_file, GOOGLE_SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_file, "w") as f:
            f.write(creds.to_json())

    return build("calendar", "v3", credentials=creds)


# ---------------------------------------------------------------------------
# Google Calendar operations
# ---------------------------------------------------------------------------

def google_create_event(service, calendar_id: str, body: dict) -> str:
    result = service.events().insert(calendarId=calendar_id, body=body).execute()
    return result["id"]


def google_update_event(service, calendar_id: str, google_event_id: str, body: dict) -> None:
    try:
        service.events().patch(
            calendarId=calendar_id, eventId=google_event_id, body=body
        ).execute()
    except HttpError as e:
        if e.resp.status == 404:
            logger.warning("Google event %s not found during update — skipping", google_event_id)
        else:
            raise


def google_delete_event(service, calendar_id: str, google_event_id: str) -> None:
    try:
        service.events().delete(calendarId=calendar_id, eventId=google_event_id).execute()
    except HttpError as e:
        if e.resp.status == 404:
            logger.warning("Google event %s already deleted", google_event_id)
        else:
            raise


# ---------------------------------------------------------------------------
# Core sync logic
# ---------------------------------------------------------------------------

def sync(
    state: StateDict,
    ms_token: str,
    google_service,
    calendar_id: str,
    days_past: int,
    days_future: int,
) -> tuple[int, int, int]:
    if state["delta_link"] is None:
        logger.info("First run — performing full calendar sync (±%d/%d days)", days_past, days_future)
        events, new_delta_link = fetch_outlook_events_full(ms_token, days_past, days_future)
    else:
        logger.info("Incremental sync using stored delta link")
        events, new_delta_link = fetch_outlook_events_delta(ms_token, state["delta_link"])

    logger.info("Fetched %d event(s) from Outlook", len(events))

    created = updated = deleted = 0

    for ev in events:
        outlook_id = ev.get("id", "")
        try:
            if "@removed" in ev:
                if outlook_id in state["event_map"]:
                    google_delete_event(google_service, calendar_id, state["event_map"][outlook_id])
                    del state["event_map"][outlook_id]
                    deleted += 1
            elif outlook_id in state["event_map"]:
                body = outlook_to_google_event(ev)
                google_update_event(google_service, calendar_id, state["event_map"][outlook_id], body)
                updated += 1
            else:
                body = outlook_to_google_event(ev)
                google_id = google_create_event(google_service, calendar_id, body)
                state["event_map"][outlook_id] = google_id
                created += 1
        except Exception as e:
            logger.error("Error processing event %s: %s", outlook_id, e)

    state["delta_link"] = new_delta_link
    state["last_sync"] = datetime.now(timezone.utc).isoformat()

    return created, updated, deleted


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    load_dotenv()

    required = ["MS_CLIENT_ID", "MS_CLIENT_SECRET", "MS_TENANT_ID"]
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        logger.error("Missing required environment variables: %s", ", ".join(missing))
        sys.exit(1)

    credentials_file = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
    if not os.path.exists(credentials_file):
        logger.error("Google credentials file not found: %s", credentials_file)
        sys.exit(1)

    calendar_id = os.getenv("GOOGLE_CALENDAR_ID", "primary")
    days_past = int(os.getenv("SYNC_WINDOW_DAYS_PAST", "90"))
    days_future = int(os.getenv("SYNC_WINDOW_DAYS_FUTURE", "90"))

    state = load_state()

    ms_app = build_msal_app(
        os.environ["MS_CLIENT_ID"],
        os.environ["MS_CLIENT_SECRET"],
        os.environ["MS_TENANT_ID"],
    )
    ms_token = acquire_ms_token(ms_app, GRAPH_SCOPES)

    google_service = get_google_service(credentials_file)

    created, updated, deleted = sync(
        state, ms_token, google_service, calendar_id, days_past, days_future
    )

    save_state(state)
    logger.info("Sync complete: %d created, %d updated, %d deleted", created, updated, deleted)


if __name__ == "__main__":
    main()
