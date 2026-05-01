"""Gmail send_email tool with OAuth2 (gmail.send scope only)."""

from __future__ import annotations

import base64
import logging
import os
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from voice_assistant.tools.schema import ToolResult

log = logging.getLogger(__name__)
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
OAUTH_TIMEOUT_SECONDS = 120


def _write_secret(path: Path, data: str) -> None:
    """Write a secret file atomically with mode 0o600 (owner-only)."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    fd = os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        os.write(fd, data.encode())
    finally:
        os.close(fd)
    os.replace(str(tmp), str(path))


def _build_service(credentials_file: Path) -> Any:
    """Load OAuth credentials, refresh or run the install flow as needed."""
    # Token file is written next to the credentials file. Heads-up to the
    # operator: avoid placing credentials in a cloud-synced folder.
    token_path = Path(credentials_file).with_name("oauth-token.json")
    creds: Credentials | None = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)  # type: ignore[no-untyped-call]

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(credentials_file), SCOPES)
            creds = flow.run_local_server(port=0, timeout_seconds=OAUTH_TIMEOUT_SECONDS)
        _write_secret(token_path, creds.to_json())

    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def send_email(to: str, subject: str, body: str, *, credentials_file: str) -> ToolResult:
    """Send a plain-text email from the user's Gmail account."""
    to = to.strip() if to else ""
    if not to:
        return ToolResult(ok=False, summary="no recipient", error="empty recipient")
    try:
        service = _build_service(Path(credentials_file).expanduser())
        msg = MIMEText(body)
        msg["to"] = to
        msg["subject"] = subject
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        sent = service.users().messages().send(userId="me", body={"raw": raw}).execute()
        return ToolResult(ok=True, summary=f"sent email to {to} (id={sent.get('id')})")
    except Exception:
        # Detail goes to logs only; the LLM gets a normalized short error.
        log.exception("send_email failed")
        return ToolResult(
            ok=False,
            summary="gmail send failed",
            error="gmail API error — see logs",
        )
