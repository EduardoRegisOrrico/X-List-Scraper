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

# Health check - improved to check both DB and proxy connections
HEALTHCHECK --interval=30s --timeout=15s --start-period=10s --retries=3 \
    CMD python -c "from scraper import get_db_connection, check_decodo_connection; \
                   conn = get_db_connection(); \
                   proxy_ok, _ = check_decodo_connection(0); \
                   exit(0 if conn and proxy_ok else 1)" || exit 1

# Default command with proper argument handling
CMD ["python", "scraper.py"] 