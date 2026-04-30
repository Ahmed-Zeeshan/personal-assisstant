from __future__ import annotations
import argparse
import logging
import threading
from pathlib import Path
from dotenv import load_dotenv
from voice_assistant.config import load_config
from voice_assistant.logging_setup import configure_logging
from voice_assistant.brain import Brain
from voice_assistant.safety import SafetyPolicy
from voice_assistant.tools import build_registry
from voice_assistant.app import Orchestrator

log = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(prog="voice-assistant")
    parser.add_argument(
        "--config", type=Path, default=Path("config.yaml"),
        help="Path to config file (default: ./config.yaml)",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--text",   action="store_true", help="Text mode (no audio).")
    mode.add_argument("--setup",  action="store_true", help="Run interactive setup wizard.")
    mode.add_argument("--gui",    action="store_true", help="Force desktop window mode.")
    mode.add_argument("--no-gui", action="store_true", help="Force CLI mode even with a display.", dest="no_gui")
    parser.add_argument(
        "--force", action="store_true",
        help="With --setup: overwrite an existing config without prompting.",
    )
    args = parser.parse_args()

    if args.setup:
        from pathlib import Path as _P
        from voice_assistant.setup_wizard import run_wizard
        home = _P.home() / ".voice-assistant"
        run_wizard(
            config_path=home / "config.yaml",
            env_path=home / ".env",
            force=args.force,
        )
        return

    load_dotenv()
    cfg = load_config(args.config)
    configure_logging(level=cfg.logging.level, log_file=cfg.logging.file)

    # Build orchestrator (existing code unchanged) ...
    policy = SafetyPolicy(
        allowed_roots=cfg.safety.allowed_roots,
        destructive_requires_confirmation=cfg.safety.destructive_requires_confirmation,
        delete_rate_per_minute=cfg.safety.delete_rate_per_minute,
    )
    brain = Brain(provider=cfg.brain.provider, model=cfg.brain.model)
    gmail_creds = None
    if cfg.gmail:
        if cfg.gmail.credentials_file.exists():
            gmail_creds = cfg.gmail.credentials_file
        else:
            log.warning(
                "gmail credentials_file %s not found; send_email tool disabled",
                cfg.gmail.credentials_file,
            )
    orch = Orchestrator(
        brain=brain,
        tools=build_registry(policy=policy, gmail_credentials_file=gmail_creds),
    )

    # Mode resolution
    if args.text:
        _run_text_mode(orch)
        return
    if args.no_gui:
        _run_text_mode(orch)
        return
    if args.gui or _gui_available():
        try:
            _run_gui_mode(orch, cfg, args.config)
            return
        except Exception as exc:
            log.warning("GUI mode failed (%s); falling back to voice CLI", exc)
    _run_voice_mode(orch, cfg)


def _gui_available() -> bool:
    """Heuristic: do we have a graphical session AND PyWebView AND the bundle?"""
    import os, sys
    if os.environ.get("VA_NO_GUI"):
        return False
    if sys.platform.startswith("linux"):
        if not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
            return False
    try:
        import webview  # noqa: F401
    except ImportError:
        return False
    try:
        from voice_assistant.desktop.window import _resolve_index_html
        _resolve_index_html()
    except Exception:
        return False
    return True


def _run_gui_mode(orch, cfg, config_path: Path) -> None:
    """GUI runtime: hotkey + audio + STT + orch + TTS, all event-driven."""
    from pathlib import Path as _P
    from voice_assistant.desktop.bridge import Bridge
    from voice_assistant.desktop.events import EventBus
    from voice_assistant.desktop.window import DesktopApp
    from voice_assistant.audio_input import HotkeyListener, record_until_silence
    from voice_assistant.stt import Transcriber
    from voice_assistant.tts import Speaker

    bus = EventBus()
    home = _P.home() / ".voice-assistant"

    transcriber = None
    speaker = None
    listener = None
    if cfg.audio.trigger == "hotkey":
        try:
            transcriber = Transcriber(model_name=cfg.stt.model, language=cfg.stt.language)
            speaker     = Speaker(voice=cfg.tts.voice)
            listener    = HotkeyListener(cfg.audio.hotkey)
        except Exception as exc:
            log.warning("audio init failed (%s); voice mode disabled", exc)

    def _do_request(text: str) -> None:
        bus.publish({"type": "transcript", "speaker": "user", "text": text})
        bus.publish({"type": "status", "value": "thinking"})
        try:
            reply = orch.handle(text)
            bus.publish({"type": "transcript", "speaker": "assistant", "text": reply})
            if speaker is not None:
                bus.publish({"type": "status", "value": "speaking"})
                try:
                    speaker.speak(reply)
                except Exception as exc:
                    log.exception("speaker.speak failed")
                    bus.publish({"type": "toast", "level": "warn", "message": f"TTS failed: {exc}"})
        except Exception as exc:
            log.exception("orch.handle failed")
            bus.publish({"type": "toast", "level": "error", "message": str(exc)})
            bus.publish({"type": "status", "value": "error"})
        finally:
            bus.publish({"type": "status", "value": "idle"})

    def _record_and_run() -> None:
        if transcriber is None:
            bus.publish({"type": "toast", "level": "warn", "message": "Voice not available — type instead."})
            return
        bus.publish({"type": "status", "value": "listening"})
        try:
            audio = record_until_silence(
                silence_seconds=cfg.audio.silence_seconds,
                level_callback=lambda rms: bus.publish({"type": "audio_level", "rms": float(rms)}),
            )
            text = transcriber.transcribe(audio).strip()
            if not text:
                bus.publish({"type": "toast", "level": "info", "message": "Nothing heard."})
                bus.publish({"type": "status", "value": "idle"})
                return
            _do_request(text)
        except Exception as exc:
            log.exception("voice path failed")
            bus.publish({"type": "toast", "level": "error", "message": str(exc)})
            bus.publish({"type": "status", "value": "idle"})

    def _on_text(text: str) -> None:
        threading.Thread(target=_do_request, args=(text,), daemon=True).start()

    def _on_listen_start() -> None:
        threading.Thread(target=_record_and_run, daemon=True).start()

    bridge = Bridge(
        config_path=home / "config.yaml",
        env_path=home / ".env",
        bus=bus,
        on_send_text=_on_text,
        on_listening_start=_on_listen_start,
        on_listening_stop=lambda: None,
    )

    # System-wide hotkey worker thread.
    def _hotkey_worker() -> None:
        if listener is None:
            return
        while True:
            try:
                listener.wait_for_press()
            except Exception:
                break
            _on_listen_start()

    if listener is not None:
        threading.Thread(target=_hotkey_worker, daemon=True).start()

    DesktopApp(bridge=bridge, bus=bus).run()


def _run_text_mode(orch) -> None:
    print("voice-assistant text mode. Ctrl-D to exit.")
    while True:
        try:
            line = input("> ").strip()
        except EOFError:
            print()
            return
        except KeyboardInterrupt:
            print()
            return
        if not line:
            continue
        try:
            print(orch.handle(line))
        except KeyboardInterrupt:
            raise
        except Exception as e:
            log.exception("error in handle")
            print(f"[error: {e}]")


def _run_voice_mode(orch, cfg) -> None:
    from voice_assistant.audio_input import HotkeyListener, record_until_silence
    from voice_assistant.stt import Transcriber
    from voice_assistant.tts import Speaker

    if cfg.audio.trigger != "hotkey":
        raise SystemExit(
            f"audio.trigger='{cfg.audio.trigger}' is not implemented in this build. "
            "Set audio.trigger=hotkey in config.yaml."
        )
    listener = HotkeyListener(cfg.audio.hotkey)
    transcriber = Transcriber(model_name=cfg.stt.model, language=cfg.stt.language)
    speaker = Speaker(voice=cfg.tts.voice)

    print(f"voice-assistant ready. Press {cfg.audio.hotkey} to talk.")
    while True:
        try:
            listener.wait_for_press()
        except KeyboardInterrupt:
            print()
            return
        print("listening...")
        try:
            audio = record_until_silence(silence_seconds=cfg.audio.silence_seconds)
            text = transcriber.transcribe(audio).strip()
            if not text:
                print("(nothing heard)")
                continue
            print(f"you: {text}")
            reply = orch.handle(text)
            print(f"assistant: {reply}")
            speaker.speak(reply)
        except KeyboardInterrupt:
            raise
        except Exception as e:
            log.exception("error in audio loop")
            print(f"[error: {e}]")


if __name__ == "__main__":
    main()
