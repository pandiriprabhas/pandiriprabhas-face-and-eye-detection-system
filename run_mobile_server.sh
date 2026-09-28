#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
RUNSERVER_PATTERN="backend/manage.py runserver"
STARTUP_PROBE_PID=""
RUNSERVER_PID=""
TUNNEL_PID=""
TUNNEL_LOG=""
MANAGE_CHILDREN="0"

cleanup() {
  local exit_code="${1:-$?}"

  if [[ "$MANAGE_CHILDREN" != "1" ]]; then
    return 0
  fi

  if [[ -n "${STARTUP_PROBE_PID:-}" ]] && kill -0 "$STARTUP_PROBE_PID" >/dev/null 2>&1; then
    kill "$STARTUP_PROBE_PID" >/dev/null 2>&1 || true
    wait "$STARTUP_PROBE_PID" >/dev/null 2>&1 || true
  fi

  if [[ -n "${RUNSERVER_PID:-}" ]] && kill -0 "$RUNSERVER_PID" >/dev/null 2>&1; then
    kill "$RUNSERVER_PID" >/dev/null 2>&1 || true
    wait "$RUNSERVER_PID" >/dev/null 2>&1 || true
  fi

  if [[ -n "${TUNNEL_PID:-}" ]] && kill -0 "$TUNNEL_PID" >/dev/null 2>&1; then
    kill "$TUNNEL_PID" >/dev/null 2>&1 || true
    wait "$TUNNEL_PID" >/dev/null 2>&1 || true
  fi

  pkill -f "$RUNSERVER_PATTERN" >/dev/null 2>&1 || true
  return 0
}

trap 'cleanup $?' EXIT
trap 'cleanup $?; exit 130' INT
trap 'cleanup $?; exit 143' TERM

if pgrep -f "backend/manage.py runserver" >/dev/null 2>&1; then
  if [[ "${FORCE_RESTART:-0}" == "1" ]]; then
    echo "FORCE_RESTART=1 -> stopping existing Django runserver process(es)..."
    pkill -f "backend/manage.py runserver" || true
  else
    echo "A Django runserver is already running."
    echo "Use the existing server terminal, or stop it first with Ctrl+C."
    echo "If you want this script to restart it automatically, run:"
    echo "FORCE_RESTART=1 bash run_mobile_server.sh"
    exit 0
  fi
fi

if [[ ! -d "$ROOT_DIR/.venv" ]]; then
  echo "Missing .venv. Create it first: python -m venv .venv"
  exit 1
fi

source "$ROOT_DIR/.venv/bin/activate"
PYTHON_BIN="$ROOT_DIR/.venv/bin/python"

DEFAULT_PORT="${APP_PORT:-8001}"
AUTO_TUNNEL="${AUTO_TUNNEL:-0}"

LAN_IP="$("$PYTHON_BIN" - <<'PY'
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
try:
    s.connect(("8.8.8.8", 80))
    print(s.getsockname()[0])
finally:
    s.close()
PY
)"

validate_public_url() {
  local url="$1"
  URL_CHECK_OUTPUT="$($PYTHON_BIN - "$url" <<'PY'
from urllib.parse import urlparse
import socket
import sys

url = (sys.argv[1] or "").strip()
if not url:
    print("ERR: PUBLIC_BASE_URL is empty.")
    sys.exit(2)

if "your-public-url.example" in url or ".example" in url:
    print("ERR: PUBLIC_BASE_URL is still a placeholder (example domain).")
    sys.exit(3)

parsed = urlparse(url)
if parsed.scheme not in {"http", "https"} or not parsed.netloc:
    print("ERR: PUBLIC_BASE_URL must look like http(s)://host[:port].")
    sys.exit(4)

host = parsed.hostname or ""
try:
    socket.gethostbyname(host)
except OSError:
    print(f"ERR: PUBLIC_BASE_URL host cannot be resolved by DNS: {host}")
    sys.exit(5)

print("OK")
PY
)" || {
    echo "$URL_CHECK_OUTPUT"
    echo "Use a real public/tunnel URL, for example from ngrok/cloudflared, then rerun."
    exit 1
  }
}

PORT_CHECK="$("$PYTHON_BIN" - "$DEFAULT_PORT" <<'PY'
import socket
import sys

port = int(sys.argv[1])
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    code = s.connect_ex(("127.0.0.1", port))
print(code)
PY
)"

if [[ "$PORT_CHECK" == "0" ]]; then
  echo "Port $DEFAULT_PORT is already in use."
  echo "Stop the process using that port, or choose another fixed port explicitly:"
  echo "APP_PORT=8000 FORCE_RESTART=1 bash run_mobile_server.sh"
  echo "APP_PORT=8001 FORCE_RESTART=1 bash run_mobile_server.sh"
  exit 1
fi

SELECTED_PORT="$DEFAULT_PORT"

start_cloudflare_tunnel() {
  if ! command -v cloudflared >/dev/null 2>&1; then
    echo "AUTO_TUNNEL=1 requested, but 'cloudflared' is not installed."
    echo "Install with: brew install cloudflared"
    exit 1
  fi

  mkdir -p "$ROOT_DIR/logs"
  TUNNEL_LOG="$ROOT_DIR/logs/cloudflared-tunnel.log"
  : > "$TUNNEL_LOG"

  echo "Starting Cloudflare tunnel for http://127.0.0.1:${SELECTED_PORT} ..."
  cloudflared tunnel --url "http://127.0.0.1:${SELECTED_PORT}" >"$TUNNEL_LOG" 2>&1 &
  TUNNEL_PID=$!

  local attempts=0
  local max_attempts=30
  local discovered_url=""

  while [[ "$attempts" -lt "$max_attempts" ]]; do
    attempts=$((attempts + 1))
    discovered_url="$(grep -Eo 'https://[a-zA-Z0-9.-]+\.trycloudflare\.com' "$TUNNEL_LOG" | head -n1 || true)"
    if [[ -n "$discovered_url" ]]; then
      QR_BASE_URL="$discovered_url"
      PUBLIC_MODE="1"
      echo "[PASS] Cloudflare tunnel URL: $QR_BASE_URL"
      return 0
    fi
    sleep 1
  done

  echo "[FAIL] Could not read tunnel URL from cloudflared output within timeout."
  echo "[FAIL] Last cloudflared log lines:"
  tail -n 30 "$TUNNEL_LOG" || true
  exit 1
}

if [[ -n "${PUBLIC_BASE_URL:-}" ]]; then
  PUBLIC_MODE="1"
  QR_BASE_URL="${PUBLIC_BASE_URL%/}"
  validate_public_url "$QR_BASE_URL"
elif [[ "$AUTO_TUNNEL" == "1" ]]; then
  PUBLIC_MODE="0"
  QR_BASE_URL=""
  start_cloudflare_tunnel
else
  PUBLIC_MODE="0"
  QR_BASE_URL="http://$LAN_IP:$SELECTED_PORT"
fi

export PUBLIC_BASE_URL="$QR_BASE_URL"

run_startup_probe() {
  local local_url="http://127.0.0.1:${SELECTED_PORT}/"
  local target_url="${PUBLIC_BASE_URL}/"

  (
    local attempts=0
    local max_attempts=40

    while [[ "$attempts" -lt "$max_attempts" ]]; do
      attempts=$((attempts + 1))

      if curl --silent --max-time 2 --output /dev/null "$local_url"; then
        echo "[PASS] Server local check: $local_url"

        if curl --silent --max-time 2 --output /dev/null "$target_url"; then
          if [[ "$PUBLIC_MODE" == "1" ]]; then
            echo "[PASS] Server public URL check from laptop: $target_url"
          else
            echo "[PASS] Server LAN check from laptop: $target_url"
          fi
        else
          if [[ "$PUBLIC_MODE" == "1" ]]; then
            echo "[FAIL] Server public URL check from laptop: $target_url"
            echo "[FAIL] Verify tunnel is running and forwarding to port $SELECTED_PORT."
          else
            echo "[FAIL] Server LAN check from laptop: $target_url"
          fi
        fi

        echo "[PHONE CHECK] Open this exact URL on phone before scanning QR: $target_url"
        return 0
      fi

      sleep 1
    done

    echo "[FAIL] Server startup check timed out: $local_url"
    echo "[FAIL] Django started but did not respond within startup probe window."
  ) &
  STARTUP_PROBE_PID=$!
}

echo "PUBLIC_BASE_URL=$PUBLIC_BASE_URL"
echo "Starting Django on 0.0.0.0:$SELECTED_PORT"
if [[ "$PUBLIC_MODE" == "1" ]]; then
  echo "Phone check: public mode enabled. Phone can be on any network if this URL is reachable."
else
  echo "Phone check: connect phone to the same Wi-Fi as laptop (disable mobile data for testing)."
fi
echo "Open on phone: $PUBLIC_BASE_URL/"
echo ""
echo "=== ESC Key Listener ==="
echo "Focus on this terminal and press ESC to stop the server gracefully."
echo ""

"$PYTHON_BIN" backend/manage.py migrate
"$PYTHON_BIN" backend/manage.py regenerate_qr_codes --base-url "$PUBLIC_BASE_URL"
MANAGE_CHILDREN="1"
run_startup_probe
"$PYTHON_BIN" backend/manage.py runserver "0.0.0.0:$SELECTED_PORT" &
RUNSERVER_PID=$!

if [[ -f "$ROOT_DIR/esc_listener.py" ]]; then
  "$PYTHON_BIN" "$ROOT_DIR/esc_listener.py" "$RUNSERVER_PID" &
  ESC_LISTENER_PID=$!
fi

wait "$RUNSERVER_PID" 2>/dev/null || true

if [[ -n "${ESC_LISTENER_PID:-}" ]] && kill -0 "$ESC_LISTENER_PID" >/dev/null 2>&1; then
  kill -9 "$ESC_LISTENER_PID" >/dev/null 2>&1 || true
  wait "$ESC_LISTENER_PID" >/dev/null 2>&1 || true
fi
