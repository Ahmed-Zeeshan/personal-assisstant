from unittest.mock import patch

from voice_assistant.tools.system import open_app, open_url


def test_open_url_calls_webbrowser():
    with patch("voice_assistant.tools.system.webbrowser.open") as wb:
        wb.return_value = True
        r = open_url("https://example.com")
    assert r.ok
    wb.assert_called_once_with("https://example.com")


def test_open_url_rejects_non_http():
    r = open_url("file:///etc/passwd")
    assert not r.ok and "http" in (r.error or "").lower()


def test_open_app_requires_confirmation():
    r = open_app("firefox")
    assert not r.ok and "confirmation" in (r.summary or "").lower()


def test_open_app_runs_subprocess_when_confirmed():
    with patch("voice_assistant.tools.system.subprocess.Popen") as popen:
        popen.return_value.pid = 4242
        r = open_app("firefox", confirmed=True)
    assert r.ok
    popen.assert_called_once()


def test_open_app_rejects_empty_command():
    r = open_app("", confirmed=True)
    assert not r.ok
