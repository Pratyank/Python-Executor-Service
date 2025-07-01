# Safe Python Script Execution Service

A secure Flask-based API service that executes arbitrary Python scripts in a sandboxed environment using nsjail for security isolation.

## Overview

This service allows users to execute Python scripts remotely by sending them via HTTP POST requests. The service executes the `main()` function of the provided script and returns both the result and any stdout output in a JSON response.

## Features

- Secure script execution using nsjail sandboxing
- Support for popular Python libraries (pandas, numpy, os)
- Input validation and error handling
- Lightweight Docker container
- Deployed on Google Cloud Run
- Fallback execution mode for compatibility

## API Specification

### Execute Script
- **Endpoint**: `POST /execute`
- **Content-Type**: `application/json`
- **Request Body**:
  ```json
  {
    "script": "def main():\n    return {'result': 'Hello World'}"
  }
  ```

### Health Check
- **Endpoint**: `GET /health`
- **Response**:
  ```json
  {
    "status": "healthy",
    "timestamp": 1234567890.123
  }
  ```

## Response Format

### Success Response
```json
{
  "result": {
    "your": "data",
    "from": "main function"
  },
  "stdout": "any print statements from the script"
}
```

### Error Response
```json
{
  "error": "Error message describing what went wrong",
  "stdout": "any output before the error occurred"
}
```

## Requirements

The Python script must:
1. Contain a `main()` function
2. Return JSON-serializable data from `main()`
3. Be under 100KB in size

## Quick Start

### Using the Deployed Service

Test the service immediately using the deployed Google Cloud Run URL:

```bash
curl -X POST https://stacksync-pratyank-440034568524.northamerica-northeast1.run.app/execute \
  -H "Content-Type: application/json" \
  -d '{
    "script": "import pandas as pd\nimport numpy as np\n\ndef main():\n    df = pd.DataFrame({\"a\": [1, 2, 3], \"b\": [4, 5, 6]})\n    arr = np.array([1, 2, 3])\n    return {\n        \"dataframe_sum\": df.sum().to_dict(),\n        \"numpy_mean\": float(np.mean(arr)),\n        \"message\": \"Hello from Cloud Run!\"\n    }"
  }'
```

Expected response:
```json
{
  "result": {
    "dataframe_sum": {"a": 6, "b": 15},
    "numpy_mean": 2.0,
    "message": "Hello from Cloud Run!"
  },
  "stdout": ""
}
```

### Running Locally with Docker

1. **Build the Docker image:**
   ```bash
   docker build -t python-executor .
   ```

2. **Run the container:**
   ```bash
   docker run -p 8080:8080 python-executor
   ```

3. **Test locally:**
   ```bash
   curl -X POST http://localhost:8080/execute \
     -H "Content-Type: application/json" \
     -d '{
       "script": "def main():\n    return {\"message\": \"Hello from local Docker!\"}"
     }'
   ```

## Example Usage

### Basic Calculation
```bash
curl -X POST https://stacksync-pratyank-440034568524.northamerica-northeast1.run.app/execute \
  -H "Content-Type: application/json" \
  -d '{
    "script": "def main():\n    result = 10 + 15 * 2\n    return {\"calculation\": result, \"message\": \"Math works!\"}"
  }'
```

### Data Processing with Pandas
```bash
curl -X POST https://stacksync-pratyank-440034568524.northamerica-northeast1.run.app/execute \
  -H "Content-Type: application/json" \
  -d '{
    "script": "import pandas as pd\n\ndef main():\n    data = {\"name\": [\"Alice\", \"Bob\", \"Charlie\"], \"age\": [25, 30, 35]}\n    df = pd.DataFrame(data)\n    return {\n        \"total_records\": len(df),\n        \"avg_age\": float(df[\"age\"].mean())\n    }"
  }'
```

### NumPy Array Operations
```bash
curl -X POST https://stacksync-pratyank-440034568524.northamerica-northeast1.run.app/execute \
  -H "Content-Type: application/json" \
  -d '{
    "script": "import numpy as np\n\ndef main():\n    arr = np.array([1, 2, 3, 4, 5])\n    return {\n        \"sum\": float(np.sum(arr)),\n        \"mean\": float(np.mean(arr)),\n        \"std_dev\": float(np.std(arr))\n    }"
  }'
```

### Script with Print Statements
```bash
curl -X POST https://stacksync-pratyank-440034568524.northamerica-northeast1.run.app/execute \
  -H "Content-Type: application/json" \
  -d '{
    "script": "def main():\n    print(\"Processing data...\")\n    data = [1, 2, 3, 4, 5]\n    print(f\"Data length: {len(data)}\")\n    result = sum(data)\n    print(f\"Sum calculated: {result}\")\n    return {\"sum\": result, \"count\": len(data)}"
  }'
```

## Security Features

- **Sandboxing**: Uses nsjail to isolate script execution
- **Resource Limits**: 
  - Memory: 128MB
  - CPU Time: 10 seconds
  - Execution Time: 30 seconds
  - File Size: 100KB max
- **Filesystem Isolation**: Limited filesystem access
- **Network Isolation**: No network access from scripts
- **Syscall Filtering**: Restricted system calls via seccomp

## Available Libraries

The service includes these Python libraries:
- `pandas` - Data manipulation and analysis
- `numpy` - Numerical computing
- `os` - Operating system interface
- `json` - JSON encoder/decoder
- `time` - Time-related functions
- Standard library modules (math, datetime, etc.)

## Error Handling

The service validates:
- Script must be a non-empty string
- Script must contain a `main()` function
- Script size must be under 100KB
- `main()` function must return JSON-serializable data

Common error scenarios:
- Missing `main()` function
- Non-JSON serializable return value
- Script execution timeout
- Runtime errors in script

## Architecture

- **Framework**: Flask
- **Sandboxing**: nsjail
- **Container**: Docker (Alpine Linux base)
- **Deployment**: Google Cloud Run
- **Region**: northamerica-northeast1

## Project Structure

```
.
├── app.py              # Main Flask application
├── Dockerfile          # Container configuration
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## Deployment Information

- **Service URL**: https://stacksync-pratyank-440034568524.northamerica-northeast1.run.app
- **Region**: northamerica-northeast1
- **Platform**: Google Cloud Run
- **Access**: Public (no authentication required)

## Health Check

Verify the service is running:
```bash
curl https://stacksync-pratyank-440034568524.northamerica-northeast1.run.app/health
```

## Development

### Prerequisites
- Docker
- Google Cloud SDK (for deployment)

### Local Development
1. Clone the repository
2. Build: `docker build -t python-executor .`
3. Run: `docker run -p 8080:8080 python-executor`
4. Test: `curl http://localhost:8080/health`

### Deployment to Cloud Run
```bash
# Build and push to Google Container Registry
docker build -t gcr.io/stacksync-464600/test-image .
docker push gcr.io/stacksync-464600/test-image

# Deploy to Cloud Run
gcloud run deploy stacksync-pratyank \
  --image gcr.io/stacksync-464600/test-image \
  --region northamerica-northeast1 \
  --platform managed \
  --allow-unauthenticated
```

## Benchmarks

This take-home challenge implementation includes:
- Secure script execution with nsjail
- Comprehensive input validation
- Support for required libraries (pandas, numpy, os)
- Lightweight Docker container
- Complete documentation with examples
- Deployed and tested on Google Cloud Run

**Estimated completion time**: 2-3 hours (including testing and documentation)

## Support

For issues or questions, please check the error messages in the API responses. The service provides detailed error information for debugging.