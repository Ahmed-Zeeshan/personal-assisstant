from __future__ import annotations
import base64
import logging
from email.mime.text import MIMEText
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from voice_assistant.tools.schema import ToolResult

log = logging.getLogger(__name__)
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


def _build_service(credentials_file: Path):
    """Load OAuth credentials, refresh or run the install flow as needed."""
    token_path = Path(credentials_file).with_name("oauth-token.json")
    creds: Credentials | None = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(credentials_file), SCOPES
            )
            creds = flow.run_local_server(port=0)
        token_path.write_text(creds.to_json())

    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def send_email(
    to: str, subject: str, body: str, *, credentials_file: str
) -> ToolResult:
    """Send a plain-text email from the user's Gmail account."""
    if not to:
        return ToolResult(ok=False, summary="no recipient", error="empty recipient")
    try:
        service = _build_service(Path(credentials_file).expanduser())
        msg = MIMEText(body)
        msg["to"] = to
        msg["subject"] = subject
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        sent = (
            service.users()
            .messages()
            .send(userId="me", body={"raw": raw})
            .execute()
        )
        return ToolResult(
            ok=True, summary=f"sent email to {to} (id={sent.get('id')})"
        )
    except Exception as e:
        log.exception("send_email failed")
        return ToolResult(ok=False, summary="gmail send failed", error=str(e))
