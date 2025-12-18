# ContentFlow Worker - Multi-processing Content Processing Engine
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy worker code
COPY . .

# Set Python path to include contentflow-lib
ENV PYTHONPATH="/app:/app/../contentflow-lib:${PYTHONPATH}"

# Environment variables (can be overridden)
ENV WORKER_NAME=contentflow-worker
ENV NUM_PROCESSING_WORKERS=4
ENV NUM_SOURCE_WORKERS=2
ENV LOG_LEVEL=INFO

# Run the worker
CMD ["python", "main.py"]
