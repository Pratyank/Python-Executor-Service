# Use Python slim image for smaller size
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    pkg-config \
    libprotobuf-dev \
    protobuf-compiler \
    libnl-route-3-dev \
    libnl-3-dev \
    bison \
    flex \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install nsjail
RUN git clone https://github.com/google/nsjail.git /tmp/nsjail \
    && cd /tmp/nsjail \
    && make \
    && cp nsjail /usr/local/bin/ \
    && rm -rf /tmp/nsjail

# Install Python dependencies
RUN pip install --no-cache-dir flask uvicorn pandas numpy

# Create non-root user for security
RUN useradd -m -u 1000 appuser

# Set working directory
WORKDIR /app

# Copy application code
COPY app.py .

# Create temp directory with proper permissions
RUN mkdir -p /tmp && chmod 777 /tmp

# Expose port
EXPOSE 8080

# Run as non-root user
USER root

# Start the application
CMD ["python", "app.py"]