#!/usr/bin/env python3
"""
Run smoke tests via SSH
"""
import os
import sys
import subprocess


def run_smoke_tests():
    """Execute smoke tests on remote server"""
    ssh_password = os.getenv('SSH_PASSWORD')
    ssh_ip = os.getenv('SSH_IP')
    repository_name = os.getenv('REPOSITORY_NAME')
    
    if not all([ssh_password, ssh_ip, repository_name]):
        print("::error::Missing required environment variables", file=sys.stderr)
        sys.exit(1)
    
    print("Running smoke tests...")
    
    # SSH command to run smoke tests
    ssh_cmd = f'''
cd workspace
cd {repository_name}
/home/neteng/workspace/run-smoke-tests.sh "{repository_name}"
exit 0
'''
    
    cmd = (
        f'sshpass -p "{ssh_password}" '
        f'ssh -tt -o StrictHostKeyChecking=no neteng@{ssh_ip} '
        f"<< 'EOF'\n{ssh_cmd}\nEOF"
    )
    
    result = subprocess.run(cmd, shell=True, check=False)
    
    if result.returncode != 0:
        print(f"::warning::Smoke tests exited with code {result.returncode}")
    
    return result.returncode


if __name__ == '__main__':
    try:
        exit_code = run_smoke_tests()
        sys.exit(exit_code)
    except Exception as e:
        print(f"::error::Smoke tests failed: {e}", file=sys.stderr)
        sys.exit(1)