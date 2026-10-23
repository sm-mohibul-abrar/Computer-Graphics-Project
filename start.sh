#!/bin/bash
set -e

export DISPLAY=:99
WEB_PORT="${PORT:-10000}"
INTERNAL_PORT=5999

echo "Initializing display and noVNC proxy on port $WEB_PORT..."

# 1. Start Xvfb virtual display
Xvfb :99 -screen 0 1100x700x24 &
sleep 2

# 2. Start x11vnc on private internal port 5999
# -quiet and log redirection prevent x11vnc from printing 'PORT=5900', stopping Render's port hijacking
x11vnc -display :99 -nopw -forever -shared -rfbport "$INTERNAL_PORT" -listen 127.0.0.1 -no6 -quiet > /tmp/x11vnc.log 2>&1 &
sleep 2

# 3. Start websockify on the public web port (Render binds to this port)
websockify --web /usr/share/novnc/ 0.0.0.0:"$WEB_PORT" 127.0.0.1:"$INTERNAL_PORT" &
sleep 1

# 4. Launch the game loop
while true; do
    echo "Starting Dictator's Dash 3D..."
    python3 /app/11.py || true
    echo "Game stopped. Restarting in 1 second..."
    sleep 1
done