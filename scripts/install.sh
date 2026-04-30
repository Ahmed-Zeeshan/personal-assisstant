#!/usr/bin/env bash
set -euo pipefail

REPO_URL="https://github.com/Ahmed-Zeeshan/personal-assisstant"
VA_HOME="${VA_HOME:-$HOME/.local/share/voice-assistant}"
LAUNCHER_DIR="${HOME}/.local/bin"
CONFIG_DIR="${HOME}/.voice-assistant"

say()  { printf '\033[1;35m>>> %s\033[0m\n' "$*"; }
warn() { printf '\033[1;33m!!! %s\033[0m\n' "$*"; }
die()  { printf '\033[1;31mxxx %s\033[0m\n' "$*" >&2; exit 1; }

uninstall() {
  say "removing $VA_HOME"
  rm -rf "$VA_HOME"
  rm -f "$LAUNCHER_DIR/voice-assistant"
  if [ -d "$CONFIG_DIR" ]; then
    read -rp "Also delete $CONFIG_DIR (holds OAuth tokens & config)? [y/N] " ans
    case "$ans" in y|Y) rm -rf "$CONFIG_DIR" ;; esac
  fi
  say "uninstalled."
  exit 0
}

[ "${1:-}" = "--uninstall" ] && uninstall

if [ "${1:-}" = "--no-setup" ]; then
  export SKIP_SETUP=1
  shift
fi

OS="$(uname -s)"
case "$OS" in
  Darwin|Linux) ;;
  *) die "Unsupported OS: $OS. Use install.ps1 on Windows." ;;
esac

command -v python3 >/dev/null || die "python3 not found. Install Python ≥3.11 from https://www.python.org/downloads/."
command -v git     >/dev/null || die "git not found. pip needs git to install from $REPO_URL — install git from your package manager."
PY_VER="$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
case "$PY_VER" in
  3.11|3.12|3.13|3.14) ;;
  *) die "Python 3.11+ required (found $PY_VER)." ;;
esac

if [ "$OS" = "Linux" ]; then
  # portaudio is a hard requirement: sounddevice fails to install without its headers/lib.
  if ! pkg-config --exists portaudio-2.0 2>/dev/null && ! ldconfig -p 2>/dev/null | grep -q libportaudio; then
    if   command -v apt-get >/dev/null; then warn "Missing portaudio. Run: sudo apt-get install -y portaudio19-dev"
    elif command -v dnf     >/dev/null; then warn "Missing portaudio. Run: sudo dnf install -y portaudio-devel"
    elif command -v pacman  >/dev/null; then warn "Missing portaudio. Run: sudo pacman -S --needed portaudio"
    else                                     warn "Install portaudio from your package manager."
    fi
    die "portaudio missing — sounddevice cannot install without it"
  fi
  # espeak-ng is needed at TTS runtime by piper, but pip install succeeds without it.
  # Soft-warn so the user gets a working install and can fix this before voice mode.
  if ! command -v espeak-ng >/dev/null; then
    if   command -v apt-get >/dev/null; then warn "espeak-ng not installed (needed for voice replies). Run: sudo apt-get install -y espeak-ng"
    elif command -v dnf     >/dev/null; then warn "espeak-ng not installed (needed for voice replies). Run: sudo dnf install -y espeak-ng"
    elif command -v pacman  >/dev/null; then warn "espeak-ng not installed (needed for voice replies). Run: sudo pacman -S --needed espeak-ng"
    else                                     warn "espeak-ng not installed (needed for voice replies). Install from your package manager."
    fi
    warn "install will continue; install espeak-ng later before using voice mode"
  fi
fi

say "installing into $VA_HOME"
mkdir -p "$VA_HOME" "$LAUNCHER_DIR" "$CONFIG_DIR"

say "creating venv"
python3 -m venv "$VA_HOME/.venv"

say "installing voice-assistant from $REPO_URL"
"$VA_HOME/.venv/bin/pip" install --upgrade pip >/dev/null
"$VA_HOME/.venv/bin/pip" install "voice-assistant[audio,gmail] @ git+$REPO_URL"

say "linking launcher → $LAUNCHER_DIR/voice-assistant"
ln -sf "$VA_HOME/.venv/bin/voice-assistant" "$LAUNCHER_DIR/voice-assistant"

case ":$PATH:" in
  *":$LAUNCHER_DIR:"*) ;;
  *) warn "$LAUNCHER_DIR is not on PATH. Add this to your shell rc: export PATH=\"\$HOME/.local/bin:\$PATH\"" ;;
esac

if [ "${SKIP_SETUP:-}" != "1" ]; then
  say "running setup wizard"
  if ! "$VA_HOME/.venv/bin/voice-assistant" --setup --force; then
    warn "setup wizard exited non-zero; re-run later with: voice-assistant --setup"
  fi
else
  say "skipping setup wizard (SKIP_SETUP=1)"
fi

say "done. Run: voice-assistant"
