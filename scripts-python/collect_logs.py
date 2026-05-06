#!/usr/bin/env python3
"""
Collect container logs from remote server
"""
import os
import sys
import subprocess


def collect_logs():
    """Collect Docker container logs via SSH"""
    ssh_password = os.getenv('SSH_PASSWORD')
    ssh_ip = os.getenv('SSH_IP')
    container_name = os.getenv('CONTAINER_NAME')
    
    if not all([ssh_password, ssh_ip, container_name]):
        print("::error::Missing required environment variables", file=sys.stderr)
        sys.exit(1)
    
    print("Collecting container logs...")
    
    try:
        cmd = (
            f'sshpass -p "{ssh_password}" '
            f'ssh -o StrictHostKeyChecking=no neteng@{ssh_ip} '
            f'"docker logs --tail 100 {container_name}"'
        )
        
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            check=False
        )
        
        # Write logs to file
        with open('container-logs.txt', 'w') as f:
            f.write(result.stdout)
            if result.stderr:
                f.write("\n=== STDERR ===\n")
                f.write(result.stderr)
        
        print("Container logs collected successfully")
        
    except Exception as e:
        print(f"::warning::Failed to collect logs: {e}", file=sys.stderr)
        # Don't fail the workflow if log collection fails


if __name__ == '__main__':
    collect_logs()