from __future__ import annotations
import argparse
import logging
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
    parser.add_argument(
        "--text", action="store_true",
        help="Text mode: read prompts from stdin, no audio.",
    )
    args = parser.parse_args()

    load_dotenv()
    cfg = load_config(args.config)
    configure_logging(level=cfg.logging.level, log_file=cfg.logging.file)

    policy = SafetyPolicy(
        allowed_roots=cfg.safety.allowed_roots,
        destructive_requires_confirmation=cfg.safety.destructive_requires_confirmation,
        delete_rate_per_minute=cfg.safety.delete_rate_per_minute,
    )
    brain = Brain(provider=cfg.brain.provider, model=cfg.brain.model)
    orch = Orchestrator(brain=brain, tools=build_registry(policy=policy))

    if args.text:
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
    else:
        # Audio mode wired up in Task 13. For now, fail clearly.
        raise SystemExit("Audio mode not yet implemented. Use --text.")


if __name__ == "__main__":
    main()
