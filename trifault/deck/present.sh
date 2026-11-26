#!/usr/bin/env bash
# Serve the deck locally (model-viewer can't load .glb files from file://) and open it.
# Speaker view: press S in the browser.
set -euo pipefail
cd "$(dirname "$0")"
PORT="${PORT:-8080}"
URL="http://localhost:${PORT}/index.html"

if [ ! -d assets/3d ] && [ -f ../verdict-to-atom-3D.zip ]; then
  echo "Unzipping ../verdict-to-atom-3D.zip into assets/"
  unzip -oq ../verdict-to-atom-3D.zip -d assets/
fi

if [ -x ../node_modules/.bin/http-server ]; then
  SERVER=(../node_modules/.bin/http-server -p "$PORT" -c-1 -s)
elif command -v http-server >/dev/null 2>&1; then
  SERVER=(http-server -p "$PORT" -c-1 -s)
elif command -v npx >/dev/null 2>&1 && npx --no-install http-server --help >/dev/null 2>&1; then
  SERVER=(npx --no-install http-server -p "$PORT" -c-1 -s)
elif command -v npx >/dev/null 2>&1; then
  SERVER=(npx -y http-server -p "$PORT" -c-1 -s)   # needs network the first time
else
  SERVER=(python3 -m http.server "$PORT")           # offline fallback
fi

"${SERVER[@]}" &
PID=$!
trap 'kill $PID 2>/dev/null' EXIT INT TERM
sleep 1
echo "Deck: $URL   (Ctrl-C to stop)"
if command -v open >/dev/null 2>&1; then open "$URL"
elif command -v xdg-open >/dev/null 2>&1; then xdg-open "$URL"
elif command -v start >/dev/null 2>&1; then start "$URL"
fi
wait $PID
