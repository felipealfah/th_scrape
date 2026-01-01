# Use official Selenium Chrome image as base
FROM selenium/standalone-chrome:4.15.0

# Switch to root to install Python dependencies
USER root

# Install Python and pip
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml /app/
COPY . /app/

# Install Python dependencies
RUN pip install --no-cache-dir \
    fastapi>=0.104.1 \
    uvicorn[standard]>=0.24.0 \
    selenium>=4.15.2 \
    pydantic>=2.5.0 \
    pydantic-settings>=2.1.0 \
    python-dotenv>=1.0.0

# Expose port for API
EXPOSE 8000

# Run the FastAPI application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
