#!/usr/bin/env python3
"""
Deploy to server - runs on the remote deployment server
"""
import os
import sys
import subprocess
from datetime import datetime


def run_command(cmd, check=True):
    """Run a shell command"""
    print(f"Running: {cmd[:100]}...")
    result = subprocess.run(cmd, shell=True, check=check)
    return result


def main():
    """Main deployment logic"""
    # Get environment variables
    version = os.getenv('VERSION')
    repository_name = os.getenv('REPOSITORY_NAME')
    docker_registry = os.getenv('DOCKER_REGISTRY')
    docker_username = os.getenv('DOCKER_USERNAME')
    docker_password = os.getenv('DOCKER_PASSWORD')
    container_name = os.getenv('CONTAINER_NAME')
    container_port = os.getenv('CONTAINER_PORT')
    docker_image_name = os.getenv('DOCKER_IMAGE_NAME')
    
    # Required secrets/configs
    qdrant_url = os.getenv('QDRANT_URL')
    qdrant_api_key = os.getenv('QDRANT_API_KEY')
    embedding_model = os.getenv('EMBEDDING_MODEL')
    azure_sas_token = os.getenv('AZURE_STORAGE_SAS_TOKEN')
    azure_account_name = os.getenv('AZURE_STORAGE_ACCOUNT_NAME')
    azure_container_name = os.getenv('AZURE_STORAGE_CONTAINER_NAME')
    unstructured_url = os.getenv('UNSTRUCTURED_API_URL')
    unstructured_key = os.getenv('UNSTRUCTURED_API_KEY')
    llamaparse_key = os.getenv('LLAMAPARSE_API_KEY')
    fireworks_key = os.getenv('FIREWORKS_API_KEY')
    fireworks_model = os.getenv('FIREWORKS_MODEL')
    fw_api_key = os.getenv('FW_API_KEY')
    fw_endpoint = os.getenv('FW_ENDPOINT')
    fw_model = os.getenv('FW_MODEL')
    debug = os.getenv('DEBUG', 'false')
    
    # Kafka configs (optional)
    kafka_registry_url = os.getenv('KAFKA_SCHEMA_REGISTRY_URL', '')
    kafka_registry_key = os.getenv('KAFKA_SCHEMA_REGISTRY_API_KEY', '')
    kafka_registry_secret = os.getenv('KAFKA_SCHEMA_REGISTRY_API_SECRET', '')
    kafka_bootstrap = os.getenv('KAFKA_BOOTSTRAP', '')
    kafka_username = os.getenv('KAFKA_SASL_USERNAME', '')
    kafka_password = os.getenv('KAFKA_SASL_PASSWORD', '')
    
    print("=== Deployment started ===")
    print(f"Version: {version}")
    print(f"Repository: {repository_name}")
    
    # Clean up Docker resources
    run_command("docker buildx prune -af", check=False)
    run_command("docker system prune -af", check=False)
    
    # Login to Docker registry
    run_command(f'docker login {docker_registry} -u {docker_username} -p "{docker_password}"')
    
    # Change to workspace
    os.chdir('/home/neteng/workspace')
    
    # Create repository directory if it doesn't exist
    if not os.path.exists(repository_name):
        print(f"Folder does not exist, creating it...")
        os.makedirs(repository_name)
    
    os.chdir(repository_name)
    
    # Save current version for rollback
    if os.path.exists('.deployed_version'):
        run_command('cp .deployed_version .deployed_version.backup', check=False)
    
    with open('.deployed_version', 'w') as f:
        f.write(version)
    
    # Backup existing .env
    if os.path.exists('.env'):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        run_command(f'cp .env .env.bak.{timestamp}', check=False)
    
    # Copy new .env template
    run_command('cp ../.env.example .env')
    
    # Update .env file
    run_command('chmod +x /tmp/update-env.sh')
    run_command('cat .env')
    
    # Build update-env.sh command
    update_cmd = [
        '/tmp/update-env.sh .env',
        f'QDRANT_URL "{qdrant_url}"',
        f'QDRANT_API_KEY "{qdrant_api_key}"',
        f'EMBEDDING_MODEL "{embedding_model}"',
        f'AZURE_STORAGE_SAS_TOKEN "{azure_sas_token}"',
        f'AZURE_STORAGE_ACCOUNT_NAME "{azure_account_name}"',
        f'AZURE_STORAGE_CONTAINER_NAME "{azure_container_name}"',
        f'UNSTRUCTURED_API_URL "{unstructured_url}"',
        f'UNSTRUCTURED_API_KEY "{unstructured_key}"',
        f'LLAMAPARSE_API_KEY "{llamaparse_key}"',
        f'FIREWORKS_API_KEY "{fireworks_key}"',
        f'FIREWORKS_MODEL "{fireworks_model}"',
        f'FW_API_KEY "{fw_api_key}"',
        f'FW_ENDPOINT "{fw_endpoint}"',
        f'FW_MODEL "{fw_model}"',
        f'DEBUG "{debug}"',
        f'DOCKER_REGISTRY "{docker_registry}"',
        f'DOCKER_IMAGE_NAME "{docker_image_name}"',
        f'VERSION "{version}"',
        f'KAFKA_SCHEMA_REGISTRY_URL "{kafka_registry_url}"',
        f'KAFKA_SCHEMA_REGISTRY_API_KEY "{kafka_registry_key}"',
        f'KAFKA_SCHEMA_REGISTRY_API_SECRET "{kafka_registry_secret}"',
        f'KAFKA_BOOTSTRAP "{kafka_bootstrap}"',
        f'KAFKA_SASL_USERNAME "{kafka_username}"',
        f'KAFKA_SASL_PASSWORD "{kafka_password}"'
    ]
    
    run_command(' '.join(update_cmd))
    
    # Source .env and export variables
    # Note: In Python, we'll set environment variables directly
    with open('.env', 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value.strip('"').strip("'")
    
    # Set additional environment variables
    os.environ['CONTAINER_NAME'] = container_name
    os.environ['CONTAINER_PORT'] = container_port
    os.environ['DOCKER_REGISTRY'] = docker_registry
    os.environ['DOCKER_IMAGE_NAME'] = docker_image_name
    os.environ['VERSION'] = version
    os.environ['NETWORK_NAME'] = 'achilles-middleware-network'
    os.environ['SSH_IP'] = os.getenv('SSH_IP', '')
    
    # Run deployment script
    print("Running deployment script...")
    run_command('/tmp/deployment.sh')
    
    print("=== Deployment completed successfully ===")
    print(f"Container: {container_name}")
    print("All services started successfully!")
    print(f"To view logs --> docker logs -f {container_name}")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"::error::Deployment failed: {e}", file=sys.stderr)
        sys.exit(1)