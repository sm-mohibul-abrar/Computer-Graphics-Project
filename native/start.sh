#!/bin/bash
set -e

export DISPLAY=:99
export LIBGL_ALWAYS_SOFTWARE=1
export GALLIUM_DRIVER=llvmpipe
WEB_PORT="${PORT:-10000}"
INTERNAL_PORT=5999

echo "Initializing Xvfb on display :99..."
Xvfb :99 -screen 0 1100x700x24 &

# Wait for X display to become ready instead of arbitrary sleep
echo "Waiting for Xvfb display socket..."
for i in $(seq 1 20); do
    if xdpyinfo -display :99 >/dev/null 2>&1; then
        echo "Xvfb display is active."
        break
    fi
    sleep 0.5
done

# Start x11vnc (force IPv4 and IPv6 off port 5900 to eliminate port collisions)
echo "Starting x11vnc on internal port $INTERNAL_PORT..."
x11vnc -display :99 -nopw -forever -shared \
       -rfbport "$INTERNAL_PORT" -rfbportv6 "$INTERNAL_PORT" \
       -listen 127.0.0.1 -noipv6 -quiet > /tmp/x11vnc.log 2>&1 &
sleep 2

# Start websockify proxy bridging browser WebSockets to VNC
echo "Starting websockify on 0.0.0.0:$WEB_PORT..."
websockify --web /usr/share/novnc/ 0.0.0.0:"$WEB_PORT" 127.0.0.1:"$INTERNAL_PORT" &
sleep 1

# Launch game loop
while true; do
    echo "Starting Dictator's Dash 3D..."
    python3 /app/game.py || true
    echo "Game closed. Restarting in 1 second..."
    sleep 1
done