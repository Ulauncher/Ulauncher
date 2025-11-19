#!/usr/bin/env bash

# Stream a GTK app running inside Xvfb to a browser via MJPEG/HTTP.

set -euo pipefail

APP_CMD=${1:-}
DISPLAY_NUM=${DISPLAY_NUM:-99}
RESOLUTION=${RESOLUTION:-1280x1000}
FRAMERATE=${FRAMERATE:-5}
PORT=${PORT:-8080}
JPEG_QUALITY=${JPEG_QUALITY:-85}

if [[ -z "$APP_CMD" ]]; then
  echo "Usage: $0 <app-command>" >&2
  echo "Example: $0 'python3 sample_app.py'" >&2
  echo "Example: $0 'gedit'" >&2
  echo "Example: $0 './my_gtk_app --option'" >&2
  exit 1
fi

if ! command -v Xvfb >/dev/null; then
  echo "Xvfb is required but not installed." >&2
  exit 1
fi

if ! command -v gst-launch-1.0 >/dev/null; then
  echo "gstreamer (gst-launch-1.0) is required but not installed." >&2
  exit 1
fi

if ! command -v python3 >/dev/null; then
  echo "python3 is required but not installed." >&2
  exit 1
fi

# Parse WIDTHxHEIGHT from the resolution string.
if [[ $RESOLUTION =~ ^([0-9]+)x([0-9]+)$ ]]; then
  WIDTH=${BASH_REMATCH[1]}
  HEIGHT=${BASH_REMATCH[2]}
else
  echo "Invalid RESOLUTION format. Use WIDTHxHEIGHT (e.g. 1280x720)." >&2
  exit 1
fi

cleanup() {
  [[ -n "${SERVER_PID:-}" ]] && kill "$SERVER_PID" 2>/dev/null || true
  [[ -n "${APP_PID:-}" ]] && kill "$APP_PID" 2>/dev/null || true
  [[ -n "${XVFB_PID:-}" ]] && kill "$XVFB_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

DISPLAY=":$DISPLAY_NUM"
SCREEN_SPEC="${WIDTH}x${HEIGHT}x24"

echo "Starting Xvfb on display $DISPLAY with resolution ${WIDTH}x${HEIGHT}..."
Xvfb "$DISPLAY" -screen 0 "$SCREEN_SPEC" >/tmp/xvfb-stream.log 2>&1 &
XVFB_PID=$!
sleep 1

echo "Launching GTK app: $APP_CMD"
env -i DISPLAY=":$DISPLAY_NUM" GDK_BACKEND=x11 PATH="$PATH" HOME="$HOME" bash -c "$APP_CMD" &
APP_PID=$!

echo "Starting MJPEG HTTP stream on http://0.0.0.0:${PORT}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
python3 "$SCRIPT_DIR/stream_server.py" "$DISPLAY" "$WIDTH" "$HEIGHT" "$FRAMERATE" "$JPEG_QUALITY" "$PORT" &
SERVER_PID=$!

wait "$SERVER_PID"
