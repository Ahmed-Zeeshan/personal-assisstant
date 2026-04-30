#!/usr/bin/env bash
set -euo pipefail

REPO_URL="https://github.com/REPLACE-ME/voice-assistant"
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

OS="$(uname -s)"
case "$OS" in
  Darwin|Linux) ;;
  *) die "Unsupported OS: $OS. Use install.ps1 on Windows." ;;
esac

command -v python3 >/dev/null || die "python3 not found. Install Python ≥3.10 from https://www.python.org/downloads/."
PY_VER="$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
case "$PY_VER" in
  3.10|3.11|3.12|3.13|3.14) ;;
  *) die "Python 3.10+ required (found $PY_VER)." ;;
esac

if [ "$OS" = "Linux" ]; then
  if ! pkg-config --exists portaudio-2.0 2>/dev/null && ! ldconfig -p 2>/dev/null | grep -q libportaudio; then
    if   command -v apt-get >/dev/null; then warn "Missing portaudio. Run: sudo apt-get install -y portaudio19-dev espeak-ng"
    elif command -v dnf     >/dev/null; then warn "Missing portaudio. Run: sudo dnf install -y portaudio-devel espeak-ng"
    elif command -v pacman  >/dev/null; then warn "Missing portaudio. Run: sudo pacman -S --needed portaudio espeak-ng"
    else                                     warn "Install portaudio and espeak-ng from your package manager."
    fi
    die "audio prerequisites missing"
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

if [ ! -f "$CONFIG_DIR/config.yaml" ] && [ -f "$VA_HOME/.venv/share/voice-assistant/config.yaml.example" ]; then
  cp "$VA_HOME/.venv/share/voice-assistant/config.yaml.example" "$CONFIG_DIR/config.yaml"
  say "seeded $CONFIG_DIR/config.yaml from example"
fi

say "done. Set your API key in $CONFIG_DIR/.env, then run: voice-assistant"
