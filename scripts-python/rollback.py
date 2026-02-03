#!/usr/bin/env python3
"""
Perform rollback to previous version
Runs on the remote deployment server
"""
import os
import sys
import subprocess
import glob


def run_command(cmd, check=True):
    """Run a shell command"""
    print(f"Running: {cmd[:100]}...")
    result = subprocess.run(cmd, shell=True, check=check)
    return result


def rollback():
    """Execute rollback to previous version"""
    rollback_version = os.getenv('ROLLBACK_VERSION')
    repository_name = os.getenv('REPOSITORY_NAME')
    container_name = os.getenv('CONTAINER_NAME')
    container_port = os.getenv('CONTAINER_PORT')
    docker_registry = os.getenv('DOCKER_REGISTRY')
    docker_image_name = os.getenv('DOCKER_IMAGE_NAME')
    
    print("=== Rollback started ===")
    
    # Navigate to repository directory
    repo_path = f"/home/neteng/workspace/{repository_name}"
    os.chdir(repo_path)
    
    # Stop current container
    run_command(f"docker stop {container_name}", check=False)
    run_command(f"docker rm {container_name}", check=False)
    
    # Restore previous .env if available
    env_backups = glob.glob(".env.bak.*")
    if env_backups:
        latest_backup = sorted(env_backups)[-1]
        run_command(f"cp {latest_backup} .env")
        print(f"Restored .env from {latest_backup}")
    
    # Restore previous version marker
    if os.path.exists('.deployed_version.backup'):
        run_command('cp .deployed_version.backup .deployed_version')
    
    # Load environment from .env
    with open('.env', 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value.strip('"').strip("'")
    
    # Set rollback version and container settings
    os.environ['VERSION'] = rollback_version
    os.environ['CONTAINER_NAME'] = container_name
    os.environ['CONTAINER_PORT'] = container_port
    os.environ['DOCKER_REGISTRY'] = docker_registry
    os.environ['DOCKER_IMAGE_NAME'] = docker_image_name
    os.environ['NETWORK_NAME'] = 'achilles-middleware-network'
    
    image_url = f"{docker_registry}/{docker_image_name}:{rollback_version}"
    
    print(f"Pulling previous image: {image_url}")
    run_command(f"docker pull {image_url}")
    
    # Start container with previous version
    docker_run_cmd = f"""
docker run -d \
  --name {container_name} \
  --network achilles-middleware-network \
  -p {container_port}:{container_port} \
  --env-file .env \
  --restart unless-stopped \
  {image_url}
"""
    
    run_command(docker_run_cmd)
    
    print("=== Rollback completed ===")
    print(f"Rolled back to version: {rollback_version}")


if __name__ == '__main__':
    try:
        rollback()
    except Exception as e:
        print(f"::error::Rollback failed: {e}", file=sys.stderr)
        sys.exit(1)