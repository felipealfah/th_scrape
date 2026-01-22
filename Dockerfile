FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for Playwright Chromium
# Using Playwright's recommended dependencies for Debian
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Playwright core dependencies
    libnss3 \
    libnspr4 \
    libdbus-1-3 \
    libx11-6 \
    libxext6 \
    libxrender1 \
    libglib2.0-0 \
    libxcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libxkbcommon0 \
    libgbm1 \
    fonts-liberation \
    xdg-utils \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (this will also install system libraries if needed)
RUN python -m playwright install --with-deps chromium

# Copy application code
COPY . .

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/api/v1/notion/health', timeout=5)" || exit 1

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
