# Use Python 3.11 with Playwright base image
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (chromium only for efficiency)
RUN playwright install chromium

# Copy application code
COPY . .

# Create directories for persistent data
RUN mkdir -p /app/data /app/logs /app/debug_logs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
ENV DATA_DIR=/app/data

# Health check - check DB connection and basic proxy config
HEALTHCHECK --interval=30s --timeout=15s --start-period=10s --retries=3 \
    CMD python -c "from get_db_connection import get_db_connection; \
                   from scraper import get_random_proxy_config; \
                   conn = get_db_connection(); \
                   proxy_config = get_random_proxy_config(); \
                   exit(0 if conn and proxy_config else 1)" || exit 1

# Default command with proper argument handling
CMD ["python", "scraper.py"] 