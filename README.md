# Python Executor Service

A secure Python code execution service built for Google Cloud Run using nsjail for sandboxing. This service enables customers to execute arbitrary Python code on a cloud server by sending a Python script and receiving the execution result of the main() function.

**Take-Home Challenge Implementation** - This project fulfills the requirements for a safe, containerized Python execution API with robust security measures.

## 🎯 Challenge Requirements Met

This implementation addresses all specified criteria:

✅ **1. Lightweight Docker Image**
- Uses Ubuntu 22.04 base with minimal dependencies
- Multi-layer caching for efficient builds
- Optimized package installation and cleanup

✅ **2. Simple Local Execution**
- Single `docker run` command starts the service
- No additional configuration required

✅ **3. Complete Documentation**
- Example cURL requests with Cloud Run URL
- Clear API documentation and usage examples

✅ **4. Input Validation**
- Script size limits (10KB max)
- Required main() function validation
- JSON structure verification
- Timeout enforcement (30 seconds)

✅ **5. Security & Sandboxing**
- **nsjail** isolation with multiple fallback configurations
- Resource limits (CPU, memory, file system)
- Namespace isolation and seccomp filtering
- Restricted system access and process limits

✅ **6. Essential Libraries Available**
- **os, pandas, numpy** pre-installed
- Additional libraries: json, math, random, datetime, etc.
- Secure import restrictions prevent malicious operations

✅ **7. Flask + nsjail Implementation**
- Flask web framework for API endpoints
- nsjail compiled from source for maximum compatibility
- Multiple configuration strategies for different environments

The service uses:
- **Flask** web framework for the API
- **nsjail** for secure sandboxing and isolation
- **Google Cloud Run** for scalable deployment
- **Docker** containerization with Ubuntu 22.04

## 📁 Project Structure

```
python-executor/
├── app.py                 # Main Flask application
├── Dockerfile            # Container build configuration
├── requirements.txt      # Python dependencies
├── cloudbuild.yaml      # Google Cloud Build configuration
├── startup.sh           # Container startup script (optional)
├── nsjail_base.cfg      # Base nsjail configuration (reference)
└── README.md           # This file
```

## 🔧 File Analysis

### Required Files for Cloud Run:

1. **`app.py`** ✅ **REQUIRED**
   - Main Flask application with API endpoints
   - Contains multiple nsjail configurations with fallback strategies
   - Handles script validation, execution, and output parsing

2. **`Dockerfile`** ✅ **REQUIRED**
   - Builds the container image
   - Installs system dependencies and compiles nsjail from source
   - Sets up Python environment

3. **`requirements.txt`** ✅ **REQUIRED**
   - Python package dependencies
   - Includes Flask, pandas, numpy, and other libraries

4. **`cloudbuild.yaml`** ✅ **REQUIRED** (for CI/CD)
   - Google Cloud Build configuration
   - Automates building and deploying to Cloud Run

### Optional Files:

5. **`startup.sh`** ⚠️ **OPTIONAL**
   - Container startup script with health checks
   - Not currently used in Dockerfile CMD
   - Could be useful for debugging but adds complexity

6. **`nsjail_base.cfg`** ⚠️ **REFERENCE ONLY**
   - Static nsjail configuration file
   - Not used by the application (configs are generated dynamically)
   - Keep for reference but not needed for deployment

## 🚀 Deployment

### Prerequisites
- Google Cloud Project with billing enabled
- Cloud Build and Cloud Run APIs enabled
- Docker and gcloud CLI installed locally

### Deploy to Cloud Run

1. **Set up Google Cloud Project:**
   ```bash
   # Set project ID
   export PROJECT_ID="your-project-id"
   gcloud config set project $PROJECT_ID
   
   # Enable required APIs
   gcloud services enable cloudbuild.googleapis.com
   gcloud services enable run.googleapis.com
   ```

2. **Deploy using Cloud Build (Recommended):**
   ```bash
   # This builds and deploys automatically
   gcloud builds submit --config cloudbuild.yaml
   ```

3. **Get your Cloud Run URL:**
   ```bash
   gcloud run services describe python-executor \
     --region us-central1 \
     --format 'value(status.url)'
   ```

4. **Test the deployed service:**
   ```bash
   # Replace URL with your actual Cloud Run URL
   curl -X POST https://python-executor-YOUR_HASH-uc.a.run.app/execute \
     -H "Content-Type: application/json" \
     -d '{"script": "def main():\n    return {\"deployed\": True, \"service\": \"working\"}"}'
   ```

## 📡 API Specification

### Execute Python Script
```bash
POST /execute
Content-Type: application/json
```

**Request Body:**
```json
{
  "script": "def main():\n    return {'result': 'Hello World'}"
}
```

**Success Response:**
```json
{
  "result": {"result": "Hello World"},
  "stdout": "",
  "execution_method": "nsjail"
}
```

**Error Response:**
```json
{
  "error": "Validation error: Script must contain a main() function"
}
```

### Health Check
```bash
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "nsjail": true,
  "python": "3.10.x",
  "temp_dir": "/tmp",
  "temp_writable": true
}
```

## 💡 Example Scripts

### Basic Example
```python
def main():
    return {"message": "Hello World", "status": "success"}
```

### With Pandas/Numpy
```python
def main():
    import pandas as pd
    import numpy as np
    
    # Create sample data
    data = pd.DataFrame({
        'values': np.random.randint(1, 100, 10)
    })
    
    return {
        "mean": float(data['values'].mean()),
        "max": int(data['values'].max()),
        "count": len(data)
    }
```

### With OS Operations (Limited)
```python
def main():
    import os
    import json
    
    # Limited OS operations allowed
    current_dir = os.getcwd()
    temp_files = os.listdir('/tmp')
    
    return {
        "current_directory": current_dir,
        "temp_file_count": len(temp_files)
    }
```

## 🔒 Security Implementation

The service implements multiple layers of security to handle malicious scripts:

### nsjail Sandboxing
- **Process isolation**: Separate namespace for each execution
- **Resource limits**: CPU (30s), Memory (128MB), File size (1MB)
- **Filesystem restrictions**: Read-only system mounts, limited temp access
- **Network isolation**: No network access from executed scripts
- **Seccomp filtering**: Restricted system calls

### Application-Level Security
- **Input validation**: Script size limits, required main() function
- **Execution timeout**: 30-second hard limit per script
- **Output parsing**: Only main() return value captured, stdout separated
- **Error handling**: Safe error messages without system information

### Cloud Run Security
- **Container isolation**: Each request runs in isolated container instance
- **No persistent storage**: Stateless execution prevents data leakage
- **Managed infrastructure**: Google's security baseline applied

### Malicious Script Protection
The service can safely handle:
- Infinite loops (timeout protection)
- Memory bombs (resource limits)
- File system attacks (read-only mounts)
- Network requests (disabled networking)
- System calls (seccomp filtering)
- Fork bombs (process limits)

## 📋 Script Requirements & Validation

### Requirements
1. **Must contain a `main()` function**
2. **main() must return JSON-serializable data**
3. **Script size under 10KB**
4. **Execution completes within 30 seconds**

### Available Libraries
**Built-in modules:**
- `os` (limited operations)
- `json`, `math`, `random`, `datetime`
- `re`, `base64`, `hashlib`, `uuid`
- `itertools`, `functools`, `collections`, `copy`

**Data science libraries:**
- `pandas` - Data manipulation and analysis
- `numpy` - Numerical computing

### Validation Examples

✅ **Valid Script:**
```python
def main():
    import pandas as pd
    data = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
    return data.sum().to_dict()
```

❌ **Invalid - No main() function:**
```python
def calculate():
    return {"result": 42}
```

❌ **Invalid - Non-JSON return:**
```python
def main():
    import pandas as pd
    return pd.DataFrame({'A': [1, 2, 3]})  # DataFrame not JSON-serializable
```

❌ **Invalid - Script too large:**
```python
# Scripts over 10KB are rejected
```

## 🛠️ Development & Testing

### Local Development
```bash
# Build and run locally (single command as required)
docker build -t python-executor . && docker run -p 8080:8080 python-executor

# Test endpoints
curl http://localhost:8080/health
curl -X POST http://localhost:8080/execute \
  -H "Content-Type: application/json" \
  -d '{"script": "def main():\n    return {\"hello\": \"world\"}"}'
```

### Development without Docker (Optional)
```bash
# Install system dependencies (Ubuntu/Debian)
sudo apt-get update && sudo apt-get install -y \
  python3 python3-pip nsjail

# Install Python dependencies
pip install -r requirements.txt

# Run Flask application
python app.py
```

### Testing Different Script Types
```bash
# Test with pandas
curl -X POST http://localhost:8080/execute \
  -H "Content-Type: application/json" \
  -d '{
    "script": "def main():\n    import pandas as pd\n    df = pd.DataFrame({\"x\": [1,2,3]})\n    return {\"sum\": int(df.sum().iloc[0])}"
  }'

# Test with numpy
curl -X POST http://localhost:8080/execute \
  -H "Content-Type: application/json" \
  -d '{
    "script": "def main():\n    import numpy as np\n    arr = np.array([1,2,3,4,5])\n    return {\"mean\": float(np.mean(arr))}"
  }'

# Test error handling
curl -X POST http://localhost:8080/execute \
  -H "Content-Type: application/json" \
  -d '{"script": "def calculate(): return 42"}'  # Missing main()
```

## 📊 Monitoring and Logging

The service includes comprehensive logging:
- Request/response logging
- Execution method tracking
- Error handling and reporting
- Performance metrics

Monitor via Google Cloud Console:
- Cloud Run metrics
- Cloud Logging
- Error Reporting

## 🔧 Configuration

### Environment Variables
- `PORT`: Server port (default: 8080)
- `PYTHONUNBUFFERED`: Disable output buffering
- `PYTHONDONTWRITEBYTECODE`: Prevent .pyc files

### Resource Limits
- Memory: 1GB
- CPU: 2 vCPUs  
- Timeout: 60 seconds
- Max instances: 10

## 🚨 Troubleshooting

### Common Issues:

1. **nsjail not found**
   - Check Dockerfile nsjail compilation
   - Verify `/usr/local/bin/nsjail` exists

2. **Permission denied**
   - Ensure proper file permissions in container
   - Check Cloud Run service account permissions

3. **Script execution timeout**
   - Optimize script performance
   - Check for infinite loops

4. **Import errors**
   - Verify required packages in requirements.txt
   - Check if packages are available in container

## 🎯 Implementation Details

### Docker Image Optimization
- **Base**: Ubuntu 22.04 (compact but functional)
- **Size optimizations**: Multi-layer caching, package cleanup
- **Build efficiency**: Dependencies cached separately from code

### nsjail Configuration Strategy
The service implements multiple fallback configurations:

1. **No-mount config** (Cloud Run optimized)
2. **Ultra-minimal config** (Container environments)  
3. **Cloud Run specific config** (GCP optimized)
4. **Minimal config** (WSL/container compatible)
5. **Full config** (Native Linux with maximum isolation)

This ensures compatibility across different deployment environments.

### Response Format Compliance
```json
{
  "result": "...",    // Exact return value of main() function
  "stdout": "...",    // Print statements and console output
  "execution_method": "nsjail"
}
```

**Output Separation:**
- `result`: Only captures the return value of `main()` 
- `stdout`: Print statements and console output (separate from result)
- Error handling: Validation errors vs. execution errors

---

## 📋 Take-Home Challenge Submission
**Cloud Run URL**: https://python-executor-551536072450.us-central1.run.app/execute
**Time to Complete**: [4 hours]

### Verification Checklist
- ✅ Single `docker run` command starts service locally
- ✅ Cloud Run deployment accessible via public URL
- ✅ `/execute` endpoint accepts multiline JSON with script
- ✅ Returns `result` (main() output) and `stdout` separately  
- ✅ Input validation for main() function requirement
- ✅ nsjail security implementation with resource limits
- ✅ pandas, numpy, os libraries available
- ✅ Flask framework used for API
- ✅ Docker image optimized for size and efficiency
- ✅ Comprehensive documentation with cURL examples
