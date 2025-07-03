# Use Ubuntu as base to match the nsjail compilation environment
FROM ubuntu:22.04

# Install Python and system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    autoconf \
    bison \
    flex \
    gcc \
    g++ \
    git \
    libprotobuf-dev \
    libprotobuf23 \
    libtool \
    make \
    pkg-config \
    protobuf-compiler \
    wget \
    libnl-3-dev \
    libnl-3-200 \
    libnl-route-3-dev \
    libnl-route-3-200 \
    procps \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Build nsjail from source
RUN git clone https://github.com/google/nsjail.git /nsjail
WORKDIR /nsjail
RUN make -j$(nproc)
RUN cp nsjail /usr/local/bin/nsjail && chmod +x /usr/local/bin/nsjail

# Test nsjail works
RUN echo "Testing nsjail..." && \
    ldd /usr/local/bin/nsjail && \
    /usr/local/bin/nsjail --help > /dev/null 2>&1 && echo "nsjail OK" || echo "nsjail failed"

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Create directories that nsjail might need
RUN mkdir -p /tmp && chmod 777 /tmp

# Create symlink for compatibility
RUN ln -sf /usr/bin/python3 /usr/local/bin/python3

# Copy app code
COPY app.py .

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=8080

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=60s --timeout=30s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Simple startup command
CMD ["python3", "app.py"]