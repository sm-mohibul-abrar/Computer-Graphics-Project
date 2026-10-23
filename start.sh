#!/bin/bash
set -e

export DISPLAY=:99
PORT="${PORT:-10000}"

# 1. Start websockify FIRST so Render's port detector locks onto port 10000
echo "Starting websockify on port $PORT..."
websockify --web /usr/share/novnc/ 0.0.0.0:"$PORT" 127.0.0.1:5900 &
sleep 2

# 2. Start virtual display matching 1100x700 resolution
echo "Starting Xvfb..."
Xvfb :99 -screen 0 1100x700x24 &
sleep 2

# 3. Start VNC server (restricted to IPv4 loopback only)
echo "Starting x11vnc..."
x11vnc -display :99 -nopw -forever -shared -rfbport 5900 -listen 127.0.0.1 -no6 &
sleep 2

# 4. Launch the game in an auto-restart loop
while true; do
    echo "Starting Dictator's Dash 3D..."
    python3 /app/11.py || true
    echo "Game stopped. Restarting in 1 second..."
    sleep 1
done