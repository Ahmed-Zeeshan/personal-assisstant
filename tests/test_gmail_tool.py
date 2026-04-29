from unittest.mock import MagicMock, patch
from voice_assistant.tools.gmail import send_email


def test_send_email_calls_gmail_api(tmp_path):
    creds_path = tmp_path / "creds.json"
    creds_path.write_text("{}")

    fake_service = MagicMock()
    fake_send = fake_service.users.return_value.messages.return_value.send
    fake_send.return_value.execute.return_value = {"id": "abc123"}

    with patch(
        "voice_assistant.tools.gmail._build_service", return_value=fake_service
    ):
        r = send_email(
            to="alice@example.com",
            subject="hi",
            body="hello",
            credentials_file=str(creds_path),
        )
    assert r.ok
    assert "abc123" in r.summary
    fake_send.assert_called_once()


def test_send_email_rejects_empty_to(tmp_path):
    creds_path = tmp_path / "creds.json"
    creds_path.write_text("{}")
    r = send_email(
        to="", subject="hi", body="hello",
        credentials_file=str(creds_path),
    )
    assert not r.ok and "recipient" in (r.error or "").lower()
