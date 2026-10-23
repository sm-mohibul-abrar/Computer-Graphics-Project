#!/bin/bash
set -e

export DISPLAY=:99
PORT="${PORT:-10000}"

echo "Starting display and server setup..."

# 1. Start virtual display matching 1100x700 resolution
echo "Starting Xvfb..."
Xvfb :99 -screen 0 1100x700x24 &
sleep 2

# 2. Start x11vnc strictly on a UNIX socket (closes ALL TCP and IPv6 ports)
echo "Starting x11vnc on unix socket..."
rm -f /tmp/vnc.sock
x11vnc -display :99 -nopw -forever -shared -unixsockonly /tmp/vnc.sock &
sleep 2

# 3. Start websockify proxying browser traffic directly into the unix socket
echo "Starting websockify on 0.0.0.0:$PORT..."
websockify --web /usr/share/novnc/ 0.0.0.0:"$PORT" --unix-target=/tmp/vnc.sock &
sleep 1

# 4. Launch the game in an auto-restart loop
while true; do
    echo "Starting Dictator's Dash 3D..."
    python3 /app/11.py || true
    echo "Game stopped. Restarting in 1 second..."
    sleep 1
done