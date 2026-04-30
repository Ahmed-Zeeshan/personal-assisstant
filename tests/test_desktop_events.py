import time
from voice_assistant.desktop.events import EventBus


def test_bus_delivers_events_to_subscriber():
    bus = EventBus()
    seen = []
    bus.subscribe(lambda e: seen.append(e))
    bus.publish({"type": "status", "value": "idle"})
    assert seen == [{"type": "status", "value": "idle"}]


def test_audio_level_is_throttled_to_30hz():
    bus = EventBus()
    seen = []
    bus.subscribe(lambda e: seen.append(e))
    # Send 100 audio_level events tightly — only ~3 should pass through within 100ms.
    for i in range(100):
        bus.publish({"type": "audio_level", "rms": i / 100})
    # Allow the throttle window to admit at most ceil(0.1s * 30Hz) + 1 = 4 events.
    # Events emitted within the same millisecond are coalesced to one.
    assert 1 <= len(seen) <= 5, f"throttling broken: {len(seen)} delivered"


def test_audio_level_throttle_releases_over_time():
    bus = EventBus()
    seen = []
    bus.subscribe(lambda e: seen.append(e))
    bus.publish({"type": "audio_level", "rms": 0.1})
    time.sleep(0.05)  # > 1/30s
    bus.publish({"type": "audio_level", "rms": 0.2})
    assert len(seen) == 2


def test_other_event_types_are_not_throttled():
    bus = EventBus()
    seen = []
    bus.subscribe(lambda e: seen.append(e))
    for i in range(10):
        bus.publish({"type": "status", "value": "idle"})
    assert len(seen) == 10
