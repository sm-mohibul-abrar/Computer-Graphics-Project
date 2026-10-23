FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install Mesa OpenGL rasterizer, FreeGLUT, virtual displays, and noVNC
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

# Copy project files from their actual locations
COPY "First Program/11.py" /app/11.py
COPY start.sh /app/start.sh

# Fix Windows CRLF line endings and grant execution permissions
RUN sed -i 's/\r$//' /app/start.sh && chmod +x /app/start.sh

CMD ["/app/start.sh"]