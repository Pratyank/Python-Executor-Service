import json
import os
import tempfile
import subprocess
import sys
import time
from flask import Flask, request, jsonify
from werkzeug.exceptions import BadRequest
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Security limits
MAX_SCRIPT_SIZE = 10000  # 10KB
EXECUTION_TIMEOUT = 30   # 30 seconds

def validate_script(script):
    """Basic input validation for the Python script"""
    if not script or not isinstance(script, str):
        raise ValueError("Script must be a non-empty string")
    
    if len(script) > MAX_SCRIPT_SIZE:
        raise ValueError(f"Script too large. Maximum size: {MAX_SCRIPT_SIZE} bytes")
    
    # Check if script contains main() function
    if "def main(" not in script:
        raise ValueError("Script must contain a main() function")
    
    return True

def create_nsjail_config_cloudrun(script_path):
    """Create Cloud Run compatible nsjail configuration"""
    
    config_content = f'''
name: "python-executor"
mode: ONCE
time_limit: {EXECUTION_TIMEOUT}
log_level: ERROR

# Only essential resource limits
rlimit_as: 134217728
rlimit_as_type: VALUE
rlimit_cpu: 30
rlimit_cpu_type: VALUE

# Disable ALL namespace isolation for Cloud Run
clone_newnet: false
clone_newuser: false
clone_newns: false
clone_newpid: false
clone_newipc: false
clone_newuts: false
clone_newcgroup: false

# Keep all environment variables
keep_env: true

# Script file mount
mount {{
    src: "{script_path}"
    dst: "/tmp/script.py"
    is_bind: true
    rw: false
}}

# Execution
exec_bin {{
    path: "/usr/bin/python3"
    arg: "/tmp/script.py"
}}
'''
    
    return config_content

def create_nsjail_config_minimal(script_path):
    """Create minimal nsjail configuration for WSL/container environments"""
    
    config_content = f'''
name: "python-executor"
description: "Safe Python script execution - minimal config"

mode: ONCE
hostname: "python-jail"
cwd: "/tmp"
time_limit: {EXECUTION_TIMEOUT}
log_level: ERROR

# Basic resource limits
rlimit_as: 134217728
rlimit_as_type: VALUE
rlimit_cpu: 30
rlimit_cpu_type: VALUE
rlimit_fsize: 1048576
rlimit_fsize_type: VALUE
rlimit_nofile: 32
rlimit_nofile_type: VALUE
rlimit_nproc: 10
rlimit_nproc_type: VALUE

# Minimal namespace isolation - disable problematic ones
clone_newnet: false
clone_newuser: false
clone_newns: false
clone_newpid: false
clone_newipc: false
clone_newuts: false
clone_newcgroup: false

# Environment
keep_env: true

# Script file
mount {{
    src: "{script_path}"
    dst: "/tmp/script.py"
    is_bind: true
    rw: false
}}

# Execution binary
exec_bin {{
    path: "/usr/bin/python3"
    arg: "-u"
    arg: "/tmp/script.py"
}}
'''
    
    return config_content

def create_nsjail_config_ultra_minimal(script_path):
    """Create ultra-minimal nsjail configuration for maximum compatibility"""
    
    config_content = f'''
name: "python-executor"
description: "Safe Python script execution - ultra minimal config"

mode: ONCE
time_limit: {EXECUTION_TIMEOUT}
log_level: ERROR

# Only basic resource limits
rlimit_as: 134217728
rlimit_as_type: VALUE
rlimit_cpu: 30
rlimit_cpu_type: VALUE

# Disable all namespace isolation
clone_newnet: false
clone_newuser: false
clone_newns: false
clone_newpid: false
clone_newipc: false
clone_newuts: false
clone_newcgroup: false

# Keep environment
keep_env: true

# Script file
mount {{
    src: "{script_path}"
    dst: "/tmp/script.py"
    is_bind: true
    rw: false
}}

# Execution binary
exec_bin {{
    path: "/usr/bin/python3"
    arg: "-u"
    arg: "/tmp/script.py"
}}
'''
    
    return config_content

def create_nsjail_config_full(script_path):
    """Create full nsjail configuration for native Linux environments"""
    
    config_content = f'''
name: "python-executor"
description: "Safe Python script execution - full config"

mode: ONCE
hostname: "python-jail"
cwd: "/tmp"
time_limit: {EXECUTION_TIMEOUT}
log_level: ERROR

# Resource limits
rlimit_as: 134217728
rlimit_as_type: VALUE
rlimit_cpu: 30
rlimit_cpu_type: VALUE
rlimit_fsize: 1048576
rlimit_fsize_type: VALUE
rlimit_nofile: 32
rlimit_nofile_type: VALUE
rlimit_nproc: 10
rlimit_nproc_type: VALUE

# Namespace isolation
clone_newnet: false
clone_newuser: false
clone_newns: true
clone_newpid: true
clone_newipc: true
clone_newuts: true
clone_newcgroup: false

# Environment
keep_env: false
envar: "PATH=/usr/local/bin:/usr/bin:/bin"
envar: "PYTHONPATH=/usr/local/lib/python3.11/site-packages:/usr/lib/python3.11/site-packages"
envar: "HOME=/tmp"
envar: "TMPDIR=/tmp"

# Mount /proc
mount_proc: true

# Essential system mounts
mount {{
    src: "/usr"
    dst: "/usr"
    is_bind: true
    rw: false
}}

mount {{
    src: "/lib"
    dst: "/lib"
    is_bind: true
    rw: false
}}

mount {{
    src: "/lib64"
    dst: "/lib64"
    is_bind: true
    rw: false
    mandatory: false
}}

mount {{
    src: "/bin"
    dst: "/bin"
    is_bind: true
    rw: false
}}

mount {{
    src: "/etc/ld.so.cache"
    dst: "/etc/ld.so.cache"
    is_bind: true
    rw: false
    mandatory: false
}}

mount {{
    src: "/etc/passwd"
    dst: "/etc/passwd"
    is_bind: true
    rw: false
    mandatory: false
}}

mount {{
    src: "/etc/group"
    dst: "/etc/group"
    is_bind: true
    rw: false
    mandatory: false
}}

mount {{
    src: "/tmp"
    dst: "/tmp"
    is_bind: true
    rw: true
}}

# Script file
mount {{
    src: "{script_path}"
    dst: "/tmp/script.py"
    is_bind: true
    rw: false
}}

# Execution binary
exec_bin {{
    path: "/usr/bin/python3"
    arg: "-u"
    arg: "/tmp/script.py"
}}

# Seccomp policy - allow essential syscalls for Python
seccomp_string: "POLICY a {{ ALLOW {{ access, arch_prctl, brk, close, dup, dup2, execve, exit, exit_group, fcntl, fstat, futex, getcwd, getdents, getdents64, getegid, geteuid, getgid, getpid, getppid, getrandom, getrlimit, gettid, getuid, ioctl, lseek, lstat, madvise, mmap, mprotect, munmap, nanosleep, newfstatat, open, openat, pipe, pipe2, poll, pread64, prlimit64, read, readlink, rt_sigaction, rt_sigprocmask, rt_sigreturn, set_robust_list, set_tid_address, stat, statx, sysinfo, uname, wait4, write, clock_getres, clock_gettime, clock_nanosleep, prctl, getrusage, times }} DEFAULT KILL }}"
'''
    
    return config_content

def create_nsjail_config_no_mount(script_content):
    """Create nsjail configuration that doesn't use file mounts - passes script via stdin"""
    
    # Fix the f-string issue by escaping outside of the f-string
    escaped_script = script_content.replace('"', '\\"').replace('\n', '\\n')
    
    config_content = f'''
name: "python-executor"
mode: ONCE
time_limit: {EXECUTION_TIMEOUT}
log_level: ERROR

# Basic resource limits
rlimit_as: 134217728
rlimit_as_type: VALUE
rlimit_cpu: 30
rlimit_cpu_type: VALUE

# Disable all namespace isolation
clone_newnet: false
clone_newuser: false
clone_newns: false
clone_newpid: false
clone_newipc: false
clone_newuts: false
clone_newcgroup: false

# Keep environment
keep_env: true

# Execute python with script from stdin
exec_bin {{
    path: "/usr/bin/python3"
    arg: "-u"
    arg: "-c"
    arg: "{escaped_script}"
}}
'''
    
    return config_content

def execute_script_with_nsjail(script):
    """Execute Python script using nsjail with fallback configurations"""
    script_path = None
    config_path = None
    
    try:
        # Create wrapper script
        safe_script = f"""
import sys
import json
import math
import random
import datetime
import re
import base64
import hashlib
import uuid
import itertools
import functools
import collections
import copy

# Allow pandas and numpy if available
try:
    import pandas as pd
    import numpy as np
except ImportError:
    pass

# Allow basic os operations (limited)
import os

# User's script
{script}

# Execute main and capture result
if __name__ == "__main__":
    try:
        result = main()
        # Ensure result is JSON serializable
        json.dumps(result)
        print("__RESULT_START__")
        print(json.dumps(result))
        print("__RESULT_END__")
    except Exception as e:
        print("__ERROR_START__")
        print(f"Error in main(): {{str(e)}}")
        print("__ERROR_END__")
        sys.exit(1)
"""

        # Create temporary file for the script in a location that should be accessible
        temp_dir = "/tmp"
        os.makedirs(temp_dir, exist_ok=True)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, dir=temp_dir) as f:
            f.write(safe_script)
            f.flush()
            script_path = f.name
        
        # Make sure the file is readable
        os.chmod(script_path, 0o644)
        
        # Verify file exists and is readable
        if not os.path.exists(script_path):
            raise Exception(f"Script file not created: {script_path}")
        
        app.logger.info(f"Created script file: {script_path}")
        
        # Try configurations in order of preference for Cloud Run
        configs = [
            ("no-mount", lambda path: create_nsjail_config_no_mount(safe_script)),
            ("cloudrun", create_nsjail_config_cloudrun),
            ("ultra-minimal", create_nsjail_config_ultra_minimal),
            ("minimal", create_nsjail_config_minimal),
            ("full", create_nsjail_config_full)
        ]
        
        last_error = None
        
        for config_name, config_func in configs:
            try:
                app.logger.info(f"Trying {config_name} nsjail configuration")
                
                # Create nsjail config
                if config_name == "no-mount":
                    config_content = config_func(script_path)
                else:
                    config_content = config_func(script_path)
                
                with tempfile.NamedTemporaryFile(mode='w', suffix='.cfg', delete=False, dir=temp_dir) as config_file:
                    config_file.write(config_content)
                    config_file.flush()
                    config_path = config_file.name
                
                # Make sure config file is readable
                os.chmod(config_path, 0o644)
                
                app.logger.info(f"Created config file: {config_path}")
                app.logger.info(f"Config content preview: {config_content[:200]}...")
                
                # Execute with nsjail
                cmd = ['/usr/local/bin/nsjail', '--config', config_path]
                
                app.logger.info(f"Executing command: {' '.join(cmd)}")
                
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd=temp_dir
                )
                
                try:
                    stdout, stderr = process.communicate(timeout=EXECUTION_TIMEOUT + 5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    raise Exception("Script execution timed out")
                finally:
                    # Clean up config file
                    try:
                        if config_path and os.path.exists(config_path):
                            os.unlink(config_path)
                            config_path = None
                    except Exception as e:
                        app.logger.warning(f"Failed to cleanup config file: {e}")
                
                app.logger.info(f"Process return code: {process.returncode}")
                app.logger.info(f"stdout: {stdout}")
                app.logger.info(f"stderr: {stderr}")
                
                # Check nsjail execution
                if process.returncode == 0:
                    # Success! Parse output and return
                    result, stdout_clean = parse_script_output(stdout)
                    return result, stdout_clean
                else:
                    # Log detailed error information
                    app.logger.error(f"{config_name} config failed with return code {process.returncode}")
                    app.logger.error(f"stdout: {stdout}")
                    app.logger.error(f"stderr: {stderr}")
                    last_error = f"Script execution failed with {config_name} config (return code {process.returncode}): {stderr}"
                    continue
                    
            except Exception as e:
                app.logger.warning(f"{config_name} config error: {str(e)}")
                last_error = str(e)
                continue
            finally:
                # Clean up config file if it exists
                try:
                    if config_path and os.path.exists(config_path):
                        os.unlink(config_path)
                        config_path = None
                except Exception as e:
                    app.logger.warning(f"Failed to cleanup config file: {e}")
        
        # If we get here, all configs failed
        raise Exception(last_error or "All nsjail configurations failed")
        
    except Exception as e:
        app.logger.error(f"Execution error: {str(e)}")
        raise e
    finally:
        # Clean up script file
        try:
            if script_path and os.path.exists(script_path):
                os.unlink(script_path)
        except Exception as e:
            app.logger.warning(f"Failed to cleanup script file: {e}")

def parse_script_output(stdout):
    """Parse the output from the sandboxed script execution"""
    lines = stdout.split('\n')
    result = None
    stdout_lines = []
    capturing_result = False
    
    for line in lines:
        if line == "__RESULT_START__":
            capturing_result = True
        elif line == "__RESULT_END__":
            capturing_result = False
        elif line.startswith("__ERROR_START__"):
            error_msg = ""
            for i, l in enumerate(lines):
                if l == "__ERROR_START__":
                    for j in range(i+1, len(lines)):
                        if lines[j] == "__ERROR_END__":
                            break
                        error_msg += lines[j] + "\n"
                    break
            raise Exception(error_msg.strip())
        elif capturing_result:
            try:
                result = json.loads(line)
            except json.JSONDecodeError:
                continue
        else:
            if not line.startswith("__") and line.strip() and not line.startswith('['):
                stdout_lines.append(line)
    
    if result is None:
        raise Exception("main() function did not return a valid JSON object")
    
    return result, '\n'.join(stdout_lines)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    nsjail_available = os.path.exists('/usr/local/bin/nsjail')
    if not nsjail_available:
        return jsonify({
            "status": "unhealthy", 
            "error": "nsjail not available",
            "nsjail": False,
            "python": sys.version
        }), 503
    
    return jsonify({
        "status": "healthy", 
        "nsjail": True,
        "python": sys.version,
        "temp_dir": "/tmp",
        "temp_writable": os.access("/tmp", os.W_OK)
    })

@app.route('/execute', methods=['POST'])
def execute():
    """Execute Python script endpoint"""
    try:
        # Check if nsjail is available
        if not os.path.exists('/usr/local/bin/nsjail'):
            return jsonify({"error": "nsjail is not available - execution not permitted"}), 503
        
        # Validate request
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400
        
        data = request.get_json()
        if not data or 'script' not in data:
            return jsonify({"error": "Missing 'script' field in request body"}), 400
        
        script = data['script']
        
        # Validate script
        validate_script(script)
        
        # Execute with nsjail only
        result, stdout = execute_script_with_nsjail(script)
        
        return jsonify({
            "result": result,
            "stdout": stdout,
            "execution_method": "nsjail"
        })
        
    except ValueError as e:
        return jsonify({"error": f"Validation error: {str(e)}"}), 400
    except Exception as e:
        app.logger.error(f"Execution error: {str(e)}")
        return jsonify({"error": f"Execution error: {str(e)}"}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)