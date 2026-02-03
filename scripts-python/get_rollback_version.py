#!/usr/bin/env python3
"""
Get the version to rollback to
"""
import os
import sys
import subprocess


def write_output(key, value):
    """Write to GITHUB_OUTPUT"""
    github_output = os.getenv('GITHUB_OUTPUT')
    if github_output:
        with open(github_output, 'a') as f:
            f.write(f"{key}={value}\n")


def get_rollback_version():
    """Determine which version to rollback to"""
    skip_build = os.getenv('SKIP_BUILD', 'false')
    ssh_password = os.getenv('SSH_PASSWORD')
    ssh_ip = os.getenv('SSH_IP')
    repository_name = os.getenv('REPOSITORY_NAME')
    previous_version = os.getenv('PREVIOUS_VERSION', '')
    
    if skip_build.lower() == 'true':
        # When skipping build, get the currently deployed version from the server
        if not all([ssh_password, ssh_ip, repository_name]):
            print("::error::Missing required environment variables", file=sys.stderr)
            sys.exit(1)
        
        cmd = (
            f'sshpass -p "{ssh_password}" '
            f'ssh -o StrictHostKeyChecking=no neteng@{ssh_ip} '
            f'"cat /home/neteng/workspace/{repository_name}/.deployed_version.backup 2>/dev/null || echo \'none\'"'
        )
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        prev_version = result.stdout.strip()
    else:
        prev_version = previous_version
    
    write_output('rollback_version', prev_version)
    print(f"Rollback version: {prev_version}")
    
    if prev_version == 'none':
        print("::error::No previous version available for rollback", file=sys.stderr)
        sys.exit(1)
    
    return prev_version


if __name__ == '__main__':
    try:
        get_rollback_version()
    except Exception as e:
        print(f"::error::Failed to get rollback version: {e}", file=sys.stderr)
        sys.exit(1)