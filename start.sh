#!/bin/bash
set -e

export DISPLAY=:99

# 1. Start virtual display matching 1100x700
Xvfb :99 -screen 0 1100x700x24 &
sleep 2

# 2. Start VNC server
x11vnc -display :99 -nopw -forever -shared -rfbport 5900 -listen localhost &
sleep 1

# 3. Start WebSocket bridge on Render's assigned PORT
PORT="${PORT:-10000}"
websockify --web /usr/share/novnc/ 0.0.0.0:"$PORT" localhost:5900 &
sleep 1

# 4. Run the game in an auto-restart loop
while true; do
    echo "Starting Dictator's Dash 3D..."
    python3 /app/11.py || true
    echo "Game stopped. Restarting in 1 second..."
    sleep 1
done