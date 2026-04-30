from unittest.mock import MagicMock, patch

from voice_assistant.tools.web import web_fetch, web_search


def test_web_search_returns_top_results():
    fake = [
        {"title": "Foo", "href": "https://foo.example/", "body": "Foo desc"},
        {"title": "Bar", "href": "https://bar.example/", "body": "Bar desc"},
    ]
    with patch("voice_assistant.tools.web.DDGS") as ddgs:
        ddgs.return_value.__enter__.return_value.text.return_value = fake
        results = web_search(query="hello", count=2)
    assert len(results) == 2
    assert results[0]["title"] == "Foo"
    assert results[0]["url"] == "https://foo.example/"
    assert "Foo desc" in results[0]["snippet"]


def test_web_search_caps_count():
    with patch("voice_assistant.tools.web.DDGS") as ddgs:
        ddgs.return_value.__enter__.return_value.text.return_value = []
        web_search(query="x", count=999)
    # The DDGS call must use a capped max_results value (≤ 10).
    args, kwargs = ddgs.return_value.__enter__.return_value.text.call_args
    assert kwargs.get("max_results", args[1] if len(args) > 1 else None) <= 10


def test_web_fetch_returns_clean_text():
    with patch("voice_assistant.tools.web.httpx") as httpx_mod, \
         patch("voice_assistant.tools.web.trafilatura") as traf:
        httpx_mod.get.return_value = MagicMock(text="<html>full html</html>", status_code=200,
                                                raise_for_status=MagicMock())
        traf.extract.return_value = "extracted clean text"
        traf.extract_metadata.return_value = MagicMock(title="Page Title")
        out = web_fetch(url="https://example.com/")
    assert out["title"] == "Page Title"
    assert out["text"] == "extracted clean text"


def test_web_fetch_rejects_non_http_urls():
    import pytest
    with pytest.raises(ValueError):
        web_fetch(url="file:///etc/passwd")
    with pytest.raises(ValueError):
        web_fetch(url="javascript:alert(1)")
