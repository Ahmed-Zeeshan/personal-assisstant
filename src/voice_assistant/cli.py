from __future__ import annotations

import argparse
import logging
import threading
from pathlib import Path

from dotenv import load_dotenv

from voice_assistant.app import Orchestrator
from voice_assistant.brain import Brain
from voice_assistant.config import Config, load_config
from voice_assistant.logging_setup import configure_logging
from voice_assistant.safety import SafetyPolicy
from voice_assistant.tools import build_registry

log = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(prog="voice-assistant")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config.yaml"),
        help="Path to config file (default: ./config.yaml)",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--text", action="store_true", help="Text mode (no audio).")
    mode.add_argument("--setup", action="store_true", help="Run interactive setup wizard.")
    mode.add_argument("--gui", action="store_true", help="Force desktop window mode.")
    mode.add_argument(
        "--no-gui", action="store_true", help="Force CLI mode even with a display.", dest="no_gui"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="With --setup: overwrite an existing config without prompting.",
    )
    args = parser.parse_args()

    if args.setup:
        from voice_assistant.setup_wizard import run_wizard

        home = Path.home() / ".voice-assistant"
        run_wizard(
            config_path=home / "config.yaml",
            env_path=home / ".env",
            force=args.force,
        )
        return

    # Load the user's config + secrets from ~/.voice-assistant/.env first; fall back
    # to a project-local .env (useful when developing from the source tree).
    _va_env = Path.home() / ".voice-assistant" / ".env"
    if _va_env.exists():
        load_dotenv(_va_env)
    load_dotenv()  # project-local fallback; does NOT override values already set
    cfg = load_config(args.config)
    configure_logging(level=cfg.logging.level, log_file=cfg.logging.file)

    # Build orchestrator (existing code unchanged) ...
    policy = SafetyPolicy(
        allowed_roots=cfg.safety.allowed_roots,
        destructive_requires_confirmation=cfg.safety.destructive_requires_confirmation,
        delete_rate_per_minute=cfg.safety.delete_rate_per_minute,
    )
    brain = Brain(provider=cfg.brain.provider, model=cfg.brain.model, user=cfg.user)
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
    import os
    import sys

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


def _run_gui_mode(orch: Orchestrator, cfg: Config, config_path: Path) -> None:
    """GUI runtime: hotkey + audio + STT + orch + TTS, all event-driven."""
    from voice_assistant.audio_input import HotkeyListener, record_until_silence
    from voice_assistant.desktop.bridge import Bridge
    from voice_assistant.desktop.events import EventBus
    from voice_assistant.desktop.window import DesktopApp
    from voice_assistant.history import History
    from voice_assistant.stt import Transcriber
    from voice_assistant.tts import make_speaker
    from voice_assistant.tts.streaming import SentenceQueueSpeaker

    bus = EventBus()
    home = Path.home() / ".voice-assistant"
    history = History(home / "history.jsonl")

    transcriber = None
    listener = None
    wake_listener = None
    if cfg.audio.trigger == "hotkey":
        try:
            transcriber = Transcriber(model_name=cfg.stt.model, language=cfg.stt.language)
            listener = HotkeyListener(cfg.audio.hotkey)
        except Exception as exc:
            log.warning("audio init failed (%s); voice mode disabled", exc)
    elif cfg.audio.trigger == "wake_word":
        try:
            transcriber = Transcriber(model_name=cfg.stt.model, language=cfg.stt.language)
        except Exception as exc:
            log.warning("STT init failed (%s); voice mode disabled", exc)

    # Pre-warm the Whisper model in the background so the first hotkey press is fast.
    def _prewarm_transcriber() -> None:
        if transcriber is not None:
            try:
                import numpy as np

                from voice_assistant.audio_types import AudioBuffer

                silence = AudioBuffer(
                    samples=np.zeros(16000, dtype=np.float32),
                    sample_rate=16000,
                )
                transcriber.transcribe(silence)
                log.info("STT pre-warmed")
            except Exception as exc:
                log.debug("STT pre-warm failed (non-fatal): %s", exc)

    threading.Thread(target=_prewarm_transcriber, daemon=True).start()

    # Holder for the active orchestrator. Settings save can swap this out so
    # provider/model/key changes take effect without a restart.
    active_orch: list[Orchestrator] = [orch]  # mutable single-item list for closure capture

    def _reload_brain() -> None:
        """Re-read config + .env and rebuild the orchestrator with the new brain."""
        _va_env_path = Path.home() / ".voice-assistant" / ".env"
        if _va_env_path.exists():
            load_dotenv(_va_env_path, override=True)
        load_dotenv(override=True)
        new_cfg = load_config(config_path)
        new_policy = SafetyPolicy(
            allowed_roots=new_cfg.safety.allowed_roots,
            destructive_requires_confirmation=new_cfg.safety.destructive_requires_confirmation,
            delete_rate_per_minute=new_cfg.safety.delete_rate_per_minute,
        )
        new_brain = Brain(
            provider=new_cfg.brain.provider, model=new_cfg.brain.model, user=new_cfg.user
        )
        new_gmail = None
        if new_cfg.gmail and new_cfg.gmail.credentials_file.exists():
            new_gmail = new_cfg.gmail.credentials_file
        active_orch[0] = Orchestrator(
            brain=new_brain,
            tools=build_registry(policy=new_policy, gmail_credentials_file=new_gmail),
        )
        log.info(
            "orchestrator reloaded with provider=%s model=%s",
            new_cfg.brain.provider,
            new_cfg.brain.model,
        )

    def _do_request(text: str, images: list[str] | None = None) -> None:
        history.append("user", text)
        bus.publish({"type": "transcript", "speaker": "user", "text": text})
        bus.publish({"type": "status", "value": "thinking"})
        buf = ""
        # Build a fresh per-request streaming speaker (isolated queue + thread).
        speaker_for_request: SentenceQueueSpeaker | None = None
        if transcriber is not None:
            try:
                speaker_for_request = SentenceQueueSpeaker(
                    make_speaker(voice_id=cfg.tts.voice, speed=cfg.tts.speed)
                )
            except Exception as exc:
                log.warning("failed to create speaker for request: %s", exc)
        try:
            bus.publish({"type": "transcript_start", "speaker": "assistant"})
            for ev in active_orch[0].handle_stream(text, images=images or []):
                if ev["type"] == "assistant_delta":
                    buf += ev["text"]
                    bus.publish({"type": "transcript_chunk", "text": ev["text"]})
                    if speaker_for_request is not None:
                        bus.publish({"type": "status", "value": "speaking"})
                        speaker_for_request.feed(ev["text"])
                elif ev["type"] == "tool_invoked":
                    bus.publish({"type": "tool_invoked", "name": ev["name"]})
                elif ev["type"] == "tool_result":
                    pass  # not surfaced to UI by default
                elif ev["type"] == "done":
                    if speaker_for_request is not None:
                        speaker_for_request.flush()
                        speaker_for_request.wait()
                    if buf:
                        history.append("assistant", buf)
                    bus.publish({"type": "transcript_end"})
        except Exception as exc:
            log.exception("orch.handle_stream failed")
            if speaker_for_request is not None:
                speaker_for_request.flush()
            bus.publish({"type": "transcript_end"})
            bus.publish({"type": "toast", "level": "error", "message": str(exc)})
            bus.publish({"type": "status", "value": "error"})
        finally:
            bus.publish({"type": "status", "value": "idle"})

    def _record_and_run() -> None:
        if transcriber is None:
            bus.publish(
                {"type": "toast", "level": "warn", "message": "Voice not available — type instead."}
            )
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

    def _on_text(text: str, images: list[str] | None = None) -> None:
        threading.Thread(target=_do_request, args=(text, images), daemon=True).start()

    def _on_listen_start() -> None:
        threading.Thread(target=_record_and_run, daemon=True).start()

    bridge = Bridge(
        config_path=home / "config.yaml",
        env_path=home / ".env",
        bus=bus,
        on_send_text=_on_text,
        on_listening_start=_on_listen_start,
        on_listening_stop=lambda: None,
        on_config_reload=_reload_brain,
        history=history,
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

    # Wake-word listener (alternative to hotkey).
    if cfg.audio.trigger == "wake_word":
        try:
            from voice_assistant.wake import WakeWordListener

            wake_listener = WakeWordListener(
                wake_word=cfg.audio.wake_word,
                sensitivity=cfg.audio.wake_sensitivity,
                on_wake=_on_listen_start,
            )
            wake_listener.start()
        except Exception as exc:
            log.warning("wake-word init failed (%s); voice disabled in GUI", exc)

    DesktopApp(bridge=bridge, bus=bus).run()


def _run_text_mode(orch: Orchestrator) -> None:
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


def _run_voice_mode(orch: Orchestrator, cfg: Config) -> None:
    from voice_assistant.audio_input import HotkeyListener, record_until_silence
    from voice_assistant.stt import Transcriber
    from voice_assistant.tts import make_speaker

    if cfg.audio.trigger != "hotkey":
        raise SystemExit(
            f"audio.trigger='{cfg.audio.trigger}' is not implemented in this build. "
            "Set audio.trigger=hotkey in config.yaml."
        )
    listener = HotkeyListener(cfg.audio.hotkey)
    transcriber = Transcriber(model_name=cfg.stt.model, language=cfg.stt.language)
    speaker = make_speaker(voice_id=cfg.tts.voice, speed=cfg.tts.speed)

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
