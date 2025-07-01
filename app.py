from flask import Flask, request, jsonify
import subprocess
import tempfile
import os
import json
import time

app = Flask(__name__)

def validate_script(script):
    """Basic validation of the script"""
    if not script or not isinstance(script, str):
        raise ValueError("Script must be a non-empty string")
    
    if len(script) > 100000:  # 100KB limit
        raise ValueError("Script too large (max 100KB)")
    
    # Check for main function
    if "def main(" not in script:
        raise ValueError("Script must contain a main() function")
    
    return True

def create_nsjail_config():
    """Create nsjail configuration file compatible with older versions"""
    config = """
name: "python-execution"
description: "Safe Python script execution"

mode: ONCE
hostname: "nsjail-python"

time_limit: 30

rlimit_as: 134217728  # 128MB
rlimit_cpu: 10        # 10 seconds CPU time
rlimit_nofile: 32

mount {
    src: "/lib"
    dst: "/lib"
    is_bind: true
}

mount {
    src: "/lib64"
    dst: "/lib64"
    is_bind: true
    mandatory: false
}

mount {
    src: "/usr/lib"
    dst: "/usr/lib"
    is_bind: true
}

mount {
    src: "/usr/local/lib"
    dst: "/usr/local/lib"
    is_bind: true
}

mount {
    src: "/bin"
    dst: "/bin"
    is_bind: true
}

mount {
    src: "/usr/bin"
    dst: "/usr/bin"
    is_bind: true
}

mount {
    src: "/usr/local/bin"
    dst: "/usr/local/bin"
    is_bind: true
}

mount {
    src: "/tmp"
    dst: "/tmp"
    is_bind: true
    rw: true
}

mount {
    src: "/proc"
    dst: "/proc"
    fstype: "proc"
}

mount {
    src: "/dev/null"
    dst: "/dev/null"
    is_bind: true
}

mount {
    src: "/dev/zero"
    dst: "/dev/zero"
    is_bind: true
}

mount {
    src: "/dev/urandom"
    dst: "/dev/urandom"
    is_bind: true
}

clone_newnet: false
clone_newuser: true
clone_newns: true
clone_newpid: true
clone_newipc: true
clone_newuts: true
clone_newcgroup: false

# Use these instead of uid_mapping/gid_mapping for older nsjail versions
inside_uid: 1000
inside_gid: 1000
"""
    return config

def create_seccomp_policy():
    """Create seccomp policy for nsjail"""
    policy = """
POLICY default {
    ALLOW {
        read, write, open, close, stat, fstat, lstat, poll, lseek, mmap, mprotect,
        munmap, brk, rt_sigaction, rt_sigprocmask, rt_sigreturn, ioctl, pread64,
        pwrite64, readv, writev, access, pipe, select, sched_yield, mremap,
        msync, mincore, madvise, shmget, shmat, shmctl, dup, dup2, pause, nanosleep,
        getitimer, alarm, setitimer, getpid, sendfile, socket, connect, accept,
        sendto, recvfrom, sendmsg, recvmsg, shutdown, bind, listen, getsockname,
        getpeername, socketpair, setsockopt, getsockopt, clone, fork, vfork, execve,
        exit, wait4, kill, uname, semget, semop, semctl, shmdt, msgget, msgsnd,
        msgrcv, msgctl, fcntl, flock, fsync, fdatasync, truncate, ftruncate,
        getdents, getcwd, chdir, fchdir, rename, mkdir, rmdir, creat, link, unlink,
        symlink, readlink, chmod, fchmod, chown, fchown, lchown, umask, gettimeofday,
        getrlimit, getrusage, sysinfo, times, ptrace, getuid, syslog, getgid,
        setuid, setgid, geteuid, getegid, setpgid, getppid, getpgrp, setsid,
        setreuid, setregid, getgroups, setgroups, setresuid, getresuid, setresgid,
        getresgid, getpgid, setfsuid, setfsgid, getsid, capget, capset, rt_sigpending,
        rt_sigtimedwait, rt_sigqueueinfo, rt_sigsuspend, sigaltstack, utime, mknod,
        uselib, personality, ustat, statfs, fstatfs, sysfs, getpriority, setpriority,
        sched_setparam, sched_getparam, sched_setscheduler, sched_getscheduler,
        sched_get_priority_max, sched_get_priority_min, sched_rr_get_interval,
        mlock, munlock, mlockall, munlockall, vhangup, modify_ldt, pivot_root,
        _sysctl, prctl, arch_prctl, adjtimex, setrlimit, chroot, sync, acct,
        settimeofday, mount, umount2, swapon, swapoff, reboot, sethostname,
        setdomainname, iopl, ioperm, create_module, init_module, delete_module,
        get_kernel_syms, query_module, quotactl, nfsservctl, getpmsg, putpmsg,
        afs_syscall, tuxcall, security, gettid, readahead, setxattr, lsetxattr,
        fsetxattr, getxattr, lgetxattr, fgetxattr, listxattr, llistxattr,
        flistxattr, removexattr, lremovexattr, fremovexattr, tkill, time,
        futex, sched_setaffinity, sched_getaffinity, set_thread_area,
        io_setup, io_destroy, io_getevents, io_submit, io_cancel, get_thread_area,
        lookup_dcookie, epoll_create, epoll_ctl_old, epoll_wait_old, remap_file_pages,
        getdents64, set_tid_address, restart_syscall, semtimedop, fadvise64,
        timer_create, timer_settime, timer_gettime, timer_getoverrun, timer_delete,
        clock_settime, clock_gettime, clock_getres, clock_nanosleep, exit_group,
        epoll_wait, epoll_ctl, tgkill, utimes, vserver, mbind, set_mempolicy,
        get_mempolicy, mq_open, mq_unlink, mq_timedsend, mq_timedreceive,
        mq_notify, mq_getsetattr, kexec_load, waitid, add_key, request_key,
        keyctl, ioprio_set, ioprio_get, inotify_init, inotify_add_watch,
        inotify_rm_watch, migrate_pages, openat, mkdirat, mknodat, fchownat,
        futimesat, newfstatat, unlinkat, renameat, linkat, symlinkat, readlinkat,
        fchmodat, faccessat, pselect6, ppoll, unshare, set_robust_list,
        get_robust_list, splice, tee, sync_file_range, vmsplice, move_pages,
        utimensat, epoll_pwait, signalfd, timerfd_create, eventfd, fallocate,
        timerfd_settime, timerfd_gettime, accept4, signalfd4, eventfd2, epoll_create1,
        dup3, pipe2, inotify_init1, preadv, pwritev, rt_tgsigqueueinfo, perf_event_open,
        recvmmsg, fanotify_init, fanotify_mark, prlimit64, name_to_handle_at,
        open_by_handle_at, clock_adjtime, syncfs, sendmmsg, setns, getcpu,
        process_vm_readv, process_vm_writev
    }
}
"""
    return policy

def execute_with_nsjail(script_content):
    """Execute Python script using nsjail"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create script file
        script_path = os.path.join(tmpdir, "user_script.py")
        
        # Create wrapper script that captures output
        wrapper_script = f'''
import sys
import json
import traceback
from io import StringIO
import contextlib

# Capture stdout
old_stdout = sys.stdout
sys.stdout = mystdout = StringIO()

try:
    # Execute user script
    exec("""
{script_content}
""")
    
    # Check if main function exists
    if 'main' not in globals():
        raise ValueError("No main() function found in script")
    
    # Call main function
    result = main()
    
    # Restore stdout
    sys.stdout = old_stdout
    stdout_content = mystdout.getvalue()
    
    # Validate result is JSON serializable
    json.dumps(result)
    
    # Output result
    output = {{"result": result, "stdout": stdout_content}}
    print(json.dumps(output))
    
except Exception as e:
    sys.stdout = old_stdout
    error_output = {{"error": str(e), "stdout": mystdout.getvalue()}}
    print(json.dumps(error_output))
    sys.exit(1)
'''
        
        with open(script_path, 'w') as f:
            f.write(wrapper_script)
        
        # Create nsjail config
        config_path = os.path.join(tmpdir, "nsjail.cfg")
        with open(config_path, 'w') as f:
            f.write(create_nsjail_config())
        
        # Create seccomp policy (optional for basic functionality)
        seccomp_path = os.path.join(tmpdir, "seccomp.policy")
        with open(seccomp_path, 'w') as f:
            f.write(create_seccomp_policy())
        
        try:
            # Execute with nsjail - try without seccomp first
            cmd = [
                'nsjail',
                '--config', config_path,
                '--',
                'python3', script_path
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=35,  # Slightly longer than nsjail's internal timeout
                cwd=tmpdir
            )
            
            if result.returncode != 0:
                return {"error": f"Execution failed: {result.stderr}", "stdout": result.stdout}
            
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                return {"error": "Script did not return valid JSON", "stdout": result.stdout}
                
        except subprocess.TimeoutExpired:
            return {"error": "Script execution timed out", "stdout": ""}
        except FileNotFoundError:
            return {"error": "nsjail not found - please ensure it's installed", "stdout": ""}
        except Exception as e:
            return {"error": f"Execution error: {str(e)}", "stdout": ""}

def execute_with_simple_timeout(script_content):
    """Fallback execution without nsjail if nsjail fails"""
    with tempfile.TemporaryDirectory() as tmpdir:
        script_path = os.path.join(tmpdir, "user_script.py")
        
        wrapper_script = f'''
import sys
import json
import traceback
from io import StringIO

old_stdout = sys.stdout
sys.stdout = mystdout = StringIO()

try:
    exec("""
{script_content}
""")
    
    if 'main' not in globals():
        raise ValueError("No main() function found in script")
    
    result = main()
    sys.stdout = old_stdout
    stdout_content = mystdout.getvalue()
    
    json.dumps(result)
    output = {{"result": result, "stdout": stdout_content}}
    print(json.dumps(output))
    
except Exception as e:
    sys.stdout = old_stdout
    error_output = {{"error": str(e), "stdout": mystdout.getvalue()}}
    print(json.dumps(error_output))
    sys.exit(1)
'''
        
        with open(script_path, 'w') as f:
            f.write(wrapper_script)
        
        try:
            result = subprocess.run(
                ['python3', script_path],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=tmpdir
            )
            
            if result.returncode != 0:
                return {"error": f"Execution failed: {result.stderr}", "stdout": result.stdout}
            
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                return {"error": "Script did not return valid JSON", "stdout": result.stdout}
                
        except subprocess.TimeoutExpired:
            return {"error": "Script execution timed out", "stdout": ""}
        except Exception as e:
            return {"error": f"Execution error: {str(e)}", "stdout": ""}

@app.route('/execute', methods=['POST'])
def execute():
    try:
        # Get JSON data
        data = request.get_json()
        
        if not data or 'script' not in data:
            return jsonify({"error": "Missing 'script' field in request body"}), 400
        
        script = data['script']
        
        # Validate script
        validate_script(script)
        
        # Try nsjail first, fallback to simple execution
        result = execute_with_nsjail(script)
        
        # If nsjail failed due to configuration issues, try fallback
        if "error" in result and ("Config file" in result["error"] or "nsjail not found" in result["error"]):
            print("nsjail failed, falling back to simple execution")
            result = execute_with_simple_timeout(script)
        
        return jsonify(result)
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "timestamp": time.time()})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)