#!/bin/bash

# Startup script for Cloud Run to ensure nsjail works properly
set -e

echo "Starting Python execution service with nsjail..."

# Check if nsjail is available
if [ ! -f /usr/local/bin/nsjail ]; then
    echo "ERROR: nsjail not found at /usr/local/bin/nsjail"
    exit 1
fi

# Make sure nsjail is executable
#chmod +x /usr/local/bin/nsjail

# Test nsjail basic functionality
echo "Testing nsjail installation..."
/usr/local/bin/nsjail --help > /dev/null 2>&1 || {
    echo "ERROR: nsjail not working properly"
    exit 1
}

# Create necessary directories
mkdir -p /tmp/nsjail
chmod 777 /tmp/nsjail

# Check Python installation
python3 --version

# Test basic imports
python3 -c "import pandas, numpy; print('Libraries OK')" || {
    echo "WARNING: Some Python libraries may not be available"
}

echo "All checks passed. Starting Flask application..."

# Start the Flask application
exec python3 app.py