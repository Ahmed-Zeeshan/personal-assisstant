
from voice_assistant.history import History


def test_append_and_load_recent(tmp_path):
    h = History(tmp_path / "history.jsonl")
    h.append("user", "hello")
    h.append("assistant", "hi there")
    items = h.load_recent(50)
    assert len(items) == 2
    assert items[0]["speaker"] == "user"
    assert items[0]["text"] == "hello"
    assert items[1]["speaker"] == "assistant"
    assert items[1]["text"] == "hi there"


def test_load_recent_caps_count(tmp_path):
    h = History(tmp_path / "history.jsonl")
    for i in range(100):
        h.append("user", f"msg-{i}")
    items = h.load_recent(50)
    assert len(items) == 50
    # Last 50, oldest first
    assert items[0]["text"] == "msg-50"
    assert items[-1]["text"] == "msg-99"


def test_clear(tmp_path):
    h = History(tmp_path / "history.jsonl")
    h.append("user", "hello")
    h.clear()
    assert h.load_recent(50) == []


def test_corrupt_lines_are_skipped(tmp_path):
    p = tmp_path / "history.jsonl"
    p.write_text(
        '{"speaker":"user","text":"good","ts":"2026-05-01T00:00:00Z"}\n'
        "{not json}\n"
        '{"speaker":"assistant","text":"also good","ts":"2026-05-01T00:00:01Z"}\n'
    )
    h = History(p)
    items = h.load_recent(50)
    assert len(items) == 2
    assert items[0]["text"] == "good"
    assert items[1]["text"] == "also good"
