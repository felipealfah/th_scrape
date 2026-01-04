# Use Python 3.11 slim as base
FROM python:3.11-slim

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y \
    curl \
    libnss3 \
    libnspr4 \
    libdbus-1-3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
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

# Install Playwright browsers
RUN /root/.local/bin/uv run playwright install chromium

# Expose port for API
EXPOSE 8000

# Run the FastAPI application
CMD ["/root/.local/bin/uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
