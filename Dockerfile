FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PORT=10000
EXPOSE 10000

# Install OpenGL, FreeGLUT, Xvfb, x11vnc, and noVNC
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-opengl \
    freeglut3-dev \
    libgl1-mesa-glx \
    libgl1-mesa-dri \
    xvfb \
    x11vnc \
    novnc \
    websockify \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install PyOpenGL
RUN pip3 install --no-cache-dir PyOpenGL PyOpenGL_accelerate

# Copy project files directly from root
COPY 11.py /app/11.py
COPY start.sh /app/start.sh

# Embed auto-connect and auto-scale directly into index.html
RUN echo '<!DOCTYPE html><html><head><meta http-equiv="refresh" content="0; url=/vnc.html?autoconnect=true&resize=scale" /></head><body></body></html>' > /usr/share/novnc/index.html

# Fix Windows CRLF line endings and grant execution permissions
RUN sed -i 's/\r$//' /app/start.sh && chmod +x /app/start.sh

CMD ["/app/start.sh"]