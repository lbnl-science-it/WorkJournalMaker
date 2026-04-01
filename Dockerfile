# ABOUTME: Production container for WorkJournalMaker server mode
# ABOUTME: Runs FastAPI with uvicorn, persists data via volume mount

FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p /data/users

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/api/health/')" || exit 1

# Run in server mode
CMD ["uvicorn", "web.app:app", "--host", "0.0.0.0", "--port", "8000"]
