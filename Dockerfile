# Use Python 3.11 slim as base
FROM python:3.11-slim

# Install system dependencies for Playwright (comprehensive Chromium deps + ALSA)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    fonts-noto-color-emoji \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libasound2 \
    libcairo2 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libexpat1 \
    libgbm1 \
    libglib2.0-0 \
    libgtk-3-0 \
    libhyphen0 \
    libjpeg62-turbo \
    libnspr4 \
    libnss3 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libpangoft2-1.0-0 \
    libpng16-16 \
    libssl3 \
    libwebp7 \
    libx11-6 \
    libx11-xcb1 \
    libxcb-dri3-0 \
    libxcb-render0 \
    libxcb-shm0 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxkbcommon0 \
    libxkbcommon-x11-0 \
    libxrandr2 \
    libxrender1 \
    libxtst6 \
    libwoff1 \
    libxcb1 \
    libwayland-server0 \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    export PATH="/root/.local/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml /app/
COPY . /app/

# Install dependencies using uv
RUN /root/.local/bin/uv sync --frozen

# Install Playwright browsers with optimizations
RUN /root/.local/bin/uv run playwright install chromium

# Expose port for API
EXPOSE 8000

# Run the FastAPI application with optimized settings for production
# --workers: single worker to reduce memory consumption
# --timeout-keep-alive: 75 seconds for connection reuse
# --ws-ping-timeout: 20 seconds for websocket ping timeout
CMD ["/root/.local/bin/uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--timeout-keep-alive", "75"]
