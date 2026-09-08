# ==============================================================================
# AI-Powered Civic Service Assistant - Production Dockerfile
# ==============================================================================
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# Set working directory
WORKDIR /app

# Install essential system dependencies for building Python packages & PostgreSQL
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source code and configurations
COPY . /app/

# Ensure runtime directories exist
RUN mkdir -p /app/data/knowledge_base /app/data/storage /app/data/vector_index

# Expose FastAPI application port
EXPOSE 8000

# Start development / production server with Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
