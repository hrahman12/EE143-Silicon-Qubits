#!/usr/bin/env bash
# Re-export deck.pdf with decktape (3D slides show their PNG posters). Run after unzipping assets.
# CHROME=/path/to/chrome ./build-pdf.sh   (defaults to decktape's own Chrome)
set -euo pipefail
cd "$(dirname "$0")"
PORT=8091
../node_modules/.bin/http-server -p $PORT -c-1 -s & PID=$!
trap 'kill $PID 2>/dev/null' EXIT
sleep 1
ARGS=(reveal --size 1920x1080 --pause 1500 --load-pause 2000 --chrome-arg=--no-sandbox)
[ -n "${CHROME:-}" ] && ARGS+=(--chrome-path "$CHROME")
../node_modules/.bin/decktape "${ARGS[@]}" "http://localhost:$PORT/index.html?export" deck.pdf
