FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy parent directory files (for shared modules)
COPY ../*.py ./backend/
COPY main.py .

# Set Python path to include parent directory
ENV PYTHONPATH=/app

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash monitor
USER monitor

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import asyncio; print('Monitor service running')" || exit 1

# Run the monitoring service
CMD ["python", "main.py"] 