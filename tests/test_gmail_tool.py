import base64
import os
import stat
from pathlib import Path
from unittest.mock import MagicMock, patch

from voice_assistant.tools.gmail import _write_secret, send_email


def test_send_email_calls_gmail_api_with_correct_payload(tmp_path):
    creds_path = tmp_path / "creds.json"
    creds_path.write_text("{}")

    fake_service = MagicMock()
    fake_send = fake_service.users.return_value.messages.return_value.send
    fake_send.return_value.execute.return_value = {"id": "abc123"}

    with patch("voice_assistant.tools.gmail._build_service", return_value=fake_service):
        r = send_email(
            to="alice@example.com",
            subject="hi there",
            body="hello body",
            credentials_file=str(creds_path),
        )
    assert r.ok
    assert "abc123" in r.summary
    fake_send.assert_called_once()
    raw = fake_send.call_args.kwargs["body"]["raw"]
    decoded = base64.urlsafe_b64decode(raw).decode()
    assert "to: alice@example.com" in decoded
    assert "subject: hi there" in decoded
    assert "hello body" in decoded


def test_send_email_strips_whitespace_recipient(tmp_path):
    creds_path = tmp_path / "creds.json"
    creds_path.write_text("{}")
    r = send_email(to="   ", subject="hi", body="x", credentials_file=str(creds_path))
    assert not r.ok
    assert "recipient" in (r.error or "").lower()


def test_send_email_rejects_empty_to(tmp_path):
    creds_path = tmp_path / "creds.json"
    creds_path.write_text("{}")
    r = send_email(to="", subject="hi", body="x", credentials_file=str(creds_path))
    assert not r.ok
    assert "recipient" in (r.error or "").lower()


def test_send_email_normalises_error_string(tmp_path):
    creds_path = tmp_path / "creds.json"
    creds_path.write_text("{}")
    with patch(
        "voice_assistant.tools.gmail._build_service",
        side_effect=RuntimeError("private-info-leak: invalid_grant token=secret"),
    ):
        r = send_email(
            to="alice@example.com",
            subject="x",
            body="y",
            credentials_file=str(creds_path),
        )
    assert not r.ok
    assert "secret" not in (r.error or "")
    assert "see logs" in (r.error or "")


def test_write_secret_uses_0600(tmp_path: Path):
    target = tmp_path / "token.json"
    _write_secret(target, '{"x": 1}')
    mode = stat.S_IMODE(os.stat(target).st_mode)
    assert mode == 0o600
    assert target.read_text() == '{"x": 1}'
