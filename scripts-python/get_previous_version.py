#!/usr/bin/env python3
"""
Get the previously deployed version from the remote server
"""
import os
import sys
import subprocess


def get_previous_version():
    """Get the current deployed version for rollback purposes"""
    ssh_password = os.getenv('SSH_PASSWORD')
    ssh_ip = os.getenv('SSH_IP')
    repository_name = os.getenv('REPOSITORY_NAME')
    
    if not all([ssh_password, ssh_ip, repository_name]):
        print("::error::Missing required environment variables (SSH_PASSWORD, SSH_IP, REPOSITORY_NAME)", 
              file=sys.stderr)
        sys.exit(1)
    
    try:
        # Run SSH command to get previous version
        cmd = (
            f'sshpass -p "{ssh_password}" '
            f'ssh -o StrictHostKeyChecking=no neteng@{ssh_ip} '
            f'"cat /home/neteng/workspace/{repository_name}/.deployed_version 2>/dev/null || echo \'none\'"'
        )
        
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True
        )
        
        prev_version = result.stdout.strip()
        
        # Write to GITHUB_OUTPUT
        github_output = os.getenv('GITHUB_OUTPUT')
        if github_output:
            with open(github_output, 'a') as f:
                f.write(f"version={prev_version}\n")
        
        print(f"Previous deployed version: {prev_version}")
        return prev_version
        
    except Exception as e:
        print(f"::error::Failed to get previous version: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    get_previous_version()