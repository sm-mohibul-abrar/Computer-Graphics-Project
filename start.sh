#!/bin/bash
set -e

export DISPLAY=:99
WEB_PORT="${PORT:-10000}"
INTERNAL_VNC_PORT=5901

echo "Configured Web Port: $WEB_PORT | Internal VNC Port: $INTERNAL_VNC_PORT"

# 1. Start virtual display matching 1100x700 resolution
echo "Starting Xvfb..."
Xvfb :99 -screen 0 1100x700x24 &
sleep 2

# 2. Start internal VNC server strictly on port 5901 (isolated from Render's public router)
echo "Starting x11vnc on port $INTERNAL_VNC_PORT..."
x11vnc -display :99 -nopw -forever -shared -rfbport "$INTERNAL_VNC_PORT" -listen 127.0.0.1 -no6 &
sleep 2

# 3. Start websockify proxy to translate incoming browser traffic to port 5901
echo "Starting websockify on port $WEB_PORT..."
websockify --web /usr/share/novnc/ 0.0.0.0:"$WEB_PORT" 127.0.0.1:"$INTERNAL_VNC_PORT" &
sleep 1

# 4. Launch the game in an auto-restart loop
while true; do
    echo "Starting Dictator's Dash 3D..."
    python3 /app/11.py || true
    echo "Game stopped. Restarting in 1 second..."
    sleep 1
done