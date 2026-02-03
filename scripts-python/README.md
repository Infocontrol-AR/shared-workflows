# GitHub Actions Workflow Scripts (Python Version)

This directory contains all Python scripts used by the reusable GitHub Actions workflow. These scripts have been converted from Bash to Python for better maintainability, error handling, and cross-platform compatibility.

## Directory Structure

```
scripts-python/
├── read_version.py              # Read version from app/_version.py
├── validate_commits.py          # Validate GPG signatures and commit messages
├── get_previous_version.py      # Get previously deployed version for rollback
├── compute_version.py           # Calculate version based on branch and inputs
├── deploy_to_server.py          # Main deployment script (runs on remote server)
├── health_check.py              # Perform health checks on deployed service
├── run_smoke_tests.py           # Execute smoke tests via SSH
├── collect_logs.py              # Collect container logs from remote server
├── get_rollback_version.py      # Determine which version to rollback to
├── rollback.py                  # Perform rollback (runs on remote server)
├── verify_rollback_health.py    # Verify rollback was successful
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## Prerequisites

### Python Version
- Python 3.7 or higher

### Python Dependencies

Install required packages:

```bash
pip install -r requirements.txt
```

Dependencies:
- `requests` - For HTTP health checks

### System Dependencies

The following system tools must be available:

- `git` - For repository operations
- `docker` - For container operations
- `sshpass` - For SSH authentication (used by some scripts)
- `ssh` - For remote command execution

## Script Descriptions

### read_version.py
- **Purpose**: Extract version from `app/_version.py` file
- **Used in**: `get-version` job when `SKIP_BUILD = true`
- **Input**: None (reads from file)
- **Output**: Writes `version` to `$GITHUB_OUTPUT`
- **Exit codes**: 0 = success, 1 = file not found or invalid format

**Example**:
```bash
export GITHUB_OUTPUT=/tmp/output
python3 read_version.py
cat /tmp/output
# version=1.2.3
```

### validate_commits.py
- **Purpose**: Validate commit signatures and enforce branch naming conventions
- **Checks**:
  - GPG signature on latest commit (warning if missing)
  - Branch naming pattern (feature/XXX, issue/XXX, etc.)
  - Commit message format (must start with ticket number)
- **Used in**: `pre-build` job (always runs)
- **Exit codes**: 0 = success, 1 = validation failed

**Example**:
```bash
export GITHUB_REF_NAME=feature/123
python3 validate_commits.py
```

### get_previous_version.py
- **Purpose**: Retrieve the currently deployed version from the server
- **Used in**: `pre-build` job
- **Requires**: SSH access to deployment server
- **Environment variables**:
  - `SSH_PASSWORD` - SSH password
  - `SSH_IP` - Server IP address
  - `REPOSITORY_NAME` - Repository name
  - `GITHUB_OUTPUT` - Output file path
- **Output**: Writes `version` to `$GITHUB_OUTPUT`

**Example**:
```bash
export SSH_PASSWORD=secret
export SSH_IP=192.168.1.100
export REPOSITORY_NAME=my-app
export GITHUB_OUTPUT=/tmp/output
python3 get_previous_version.py
```

### compute_version.py
- **Purpose**: Calculate the version tag for the Docker image
- **Logic**:
  - If `IMAGE_TAG` is set, use it
  - Otherwise, calculate based on branch name and version file
- **Used in**: `pre-build` job
- **Environment variables**:
  - `IMAGE_TAG` - Override version (optional)
  - `VERSION_FILE_NAME` - Path to version file
  - `GITHUB_RUN_ID` - Workflow run ID
  - `VERSION_NUMBER` - Increment type (major/minor/patch)
  - `GITHUB_REF_NAME` - Branch name
  - `GITHUB_OUTPUT` - Output file path
- **Output**: Writes `version` to `$GITHUB_OUTPUT`

**Example**:
```bash
export GITHUB_REF_NAME=qa
export VERSION_FILE_NAME=app/_version.py
export VERSION_NUMBER=minor
export GITHUB_RUN_ID=12345
export GITHUB_OUTPUT=/tmp/output
python3 compute_version.py
```

### deploy_to_server.py
- **Purpose**: Main deployment script that runs on the remote server
- **Actions**:
  - Cleans up old Docker resources
  - Logs into Docker registry
  - Backs up current deployment
  - Updates .env file
  - Runs the service-specific deployment script
- **Used in**: `deploy` job
- **Runs on**: Remote deployment server via SSH
- **Environment variables**: Many (see script header)

**Example** (on remote server):
```bash
export VERSION=1.2.3
export REPOSITORY_NAME=my-app
export DOCKER_REGISTRY=registry.example.com
# ... set other environment variables
python3 deploy_to_server.py
```

### health_check.py
- **Purpose**: Verify the deployed service is healthy
- **Method**: HTTP health check with retry logic
- **Used in**: `health-check` job
- **Environment variables**:
  - `HEALTH_CHECK_TIMEOUT` - Timeout in seconds (default: 300)
  - `HEALTH_CHECK_INTERVAL` - Interval in seconds (default: 10)
  - `SSH_IP` - Server IP
  - `CONTAINER_PORT` - Container port
  - `HEALTH_CHECK_ENDPOINT` - Health check path (default: /health)
  - `GITHUB_OUTPUT` - Output file path
- **Output**: Writes `status` (healthy/unhealthy) to `$GITHUB_OUTPUT`
- **Exit codes**: 0 = healthy, 1 = unhealthy

**Example**:
```bash
export SSH_IP=192.168.1.100
export CONTAINER_PORT=8080
export HEALTH_CHECK_ENDPOINT=/health
export HEALTH_CHECK_TIMEOUT=300
export HEALTH_CHECK_INTERVAL=10
export GITHUB_OUTPUT=/tmp/output
python3 health_check.py
```

### run_smoke_tests.py
- **Purpose**: Execute smoke tests on the deployed service
- **Used in**: `health-check` job
- **Runs on**: Remote server via SSH
- **Environment variables**:
  - `SSH_PASSWORD` - SSH password
  - `SSH_IP` - Server IP
  - `REPOSITORY_NAME` - Repository name

**Example**:
```bash
export SSH_PASSWORD=secret
export SSH_IP=192.168.1.100
export REPOSITORY_NAME=my-app
python3 run_smoke_tests.py
```

### collect_logs.py
- **Purpose**: Retrieve container logs from the remote server
- **Used in**: `health-check` job (always runs)
- **Output**: Saves logs to `container-logs.txt`
- **Environment variables**:
  - `SSH_PASSWORD` - SSH password
  - `SSH_IP` - Server IP
  - `CONTAINER_NAME` - Container name

**Example**:
```bash
export SSH_PASSWORD=secret
export SSH_IP=192.168.1.100
export CONTAINER_NAME=my-app-container
python3 collect_logs.py
cat container-logs.txt
```

### get_rollback_version.py
- **Purpose**: Determine which version to rollback to
- **Logic**:
  - If `SKIP_BUILD = true`, read from server's backup
  - Otherwise, use `PREVIOUS_VERSION` from environment
- **Used in**: `rollback` job
- **Environment variables**:
  - `SKIP_BUILD` - Whether build was skipped
  - `SSH_PASSWORD` - SSH password (if SKIP_BUILD=true)
  - `SSH_IP` - Server IP (if SKIP_BUILD=true)
  - `REPOSITORY_NAME` - Repository name (if SKIP_BUILD=true)
  - `PREVIOUS_VERSION` - Previous version (if SKIP_BUILD=false)
  - `GITHUB_OUTPUT` - Output file path
- **Output**: Writes `rollback_version` to `$GITHUB_OUTPUT`

**Example**:
```bash
export SKIP_BUILD=false
export PREVIOUS_VERSION=1.2.2
export GITHUB_OUTPUT=/tmp/output
python3 get_rollback_version.py
```

### rollback.py
- **Purpose**: Perform the actual rollback operation
- **Actions**:
  - Stops current container
  - Restores previous .env file
  - Pulls previous Docker image
  - Starts container with previous version
- **Used in**: `rollback` job
- **Runs on**: Remote deployment server
- **Environment variables**:
  - `ROLLBACK_VERSION` - Version to rollback to
  - `REPOSITORY_NAME` - Repository name
  - `CONTAINER_NAME` - Container name
  - `CONTAINER_PORT` - Container port
  - `DOCKER_REGISTRY` - Docker registry
  - `DOCKER_IMAGE_NAME` - Image name

**Example** (on remote server):
```bash
export ROLLBACK_VERSION=1.2.2
export REPOSITORY_NAME=my-app
export CONTAINER_NAME=my-app-container
export CONTAINER_PORT=8080
export DOCKER_REGISTRY=registry.example.com
export DOCKER_IMAGE_NAME=my-app
python3 rollback.py
```

### verify_rollback_health.py
- **Purpose**: Verify the rolled-back service is healthy
- **Method**: HTTP health check with retry logic
- **Used in**: `rollback` job
- **Environment variables**:
  - `SSH_IP` - Server IP
  - `CONTAINER_PORT` - Container port
  - `HEALTH_CHECK_ENDPOINT` - Health check path (default: /health)
- **Exit codes**: 0 = healthy, 1 = unhealthy

**Example**:
```bash
export SSH_IP=192.168.1.100
export CONTAINER_PORT=8080
export HEALTH_CHECK_ENDPOINT=/health
python3 verify_rollback_health.py
```

## Advantages Over Shell Scripts

### 1. Better Error Handling
Python provides structured exception handling:
```python
try:
    result = compute_version()
except ValueError as e:
    print(f"::error::Invalid version format: {e}")
    sys.exit(1)
except Exception as e:
    print(f"::error::Unexpected error: {e}")
    sys.exit(1)
```

### 2. Cross-Platform Compatibility
Python scripts work on Linux, macOS, and Windows (with minor adjustments).

### 3. Easier Testing
Python scripts can be easily unit tested:
```python
import unittest
from read_version import read_version

class TestReadVersion(unittest.TestCase):
    def test_valid_version(self):
        # Test logic here
        pass
```

### 4. Better String Handling
No need to worry about shell quoting issues:
```python
version = "1.2.3-beta+build.123"  # Works perfectly
```

### 5. Rich Standard Library
Access to powerful libraries for HTTP, JSON, regex, etc.:
```python
import requests
response = requests.get(url, timeout=5)
```

## Testing Scripts Locally

### Prerequisites
```bash
pip install -r requirements.txt
```

### Test Individual Scripts

**Test version reading**:
```bash
# Create test version file
mkdir -p app
echo '__version__ = "1.2.3"' > app/_version.py

# Run script
export GITHUB_OUTPUT=/tmp/test_output
python3 read_version.py

# Check output
cat /tmp/test_output
```

**Test health check**:
```bash
# Start a test server on port 8080
python3 -m http.server 8080 &

# Run health check
export SSH_IP=localhost
export CONTAINER_PORT=8080
export HEALTH_CHECK_ENDPOINT=/
export HEALTH_CHECK_TIMEOUT=30
export HEALTH_CHECK_INTERVAL=5
export GITHUB_OUTPUT=/tmp/test_output
python3 health_check.py

# Cleanup
kill %1
```

### Unit Testing

Create test files:
```python
# test_read_version.py
import unittest
import tempfile
import os
from pathlib import Path

class TestReadVersion(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.app_dir = Path(self.temp_dir) / 'app'
        self.app_dir.mkdir()
        
    def test_valid_version(self):
        version_file = self.app_dir / '_version.py'
        version_file.write_text('__version__ = "1.2.3"')
        
        # Test logic
        # ...
        
if __name__ == '__main__':
    unittest.main()
```

Run tests:
```bash
python3 -m pytest tests/
```

## Debugging

### Enable Debug Output

Add debug prints:
```python
import sys

DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'

def debug_print(msg):
    if DEBUG:
        print(f"[DEBUG] {msg}", file=sys.stderr)

debug_print(f"Processing version: {version}")
```

### Check Environment Variables

```python
import os

print("Environment variables:")
for key, value in os.environ.items():
    if key.startswith(('GITHUB_', 'SSH_', 'DOCKER_')):
        # Mask sensitive values
        if 'PASSWORD' in key or 'TOKEN' in key or 'SECRET' in key:
            value = '***'
        print(f"  {key}={value}")
```

### Logging

Add logging for better debugging:
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
logger.info("Starting deployment...")
```

## Migration from Shell Scripts

### Workflow Changes

Update your workflow to use Python scripts:

```yaml
# Before (shell)
- name: Read version
  run: bash shared-workflows/scripts/read-version.sh

# After (Python)
- name: Read version
  run: python3 shared-workflows/scripts-python/read_version.py
```

### Installing Dependencies

Add a setup step in your workflow:

```yaml
- name: Setup Python dependencies
  run: |
    pip install -r shared-workflows/scripts-python/requirements.txt
```

### File Permissions

Python scripts don't need execute permissions (when run with `python3`), but you can still set them:

```bash
chmod +x scripts-python/*.py
```

## Contributing

When modifying scripts:

1. **Test locally** before committing
2. **Update docstrings** to reflect changes
3. **Add error handling** for edge cases
4. **Update this README** if behavior changes
5. **Consider backward compatibility**

## Troubleshooting

### ImportError: No module named 'requests'

**Solution**:
```bash
pip install -r requirements.txt
```

### Permission Denied

**Solution**:
```bash
chmod +x script_name.py
# or run with python3
python3 script_name.py
```

### SSH Connection Refused

**Solution**:
- Check SSH_IP and SSH_PASSWORD are set correctly
- Verify SSH access: `ssh neteng@${SSH_IP}`
- Check firewall rules

### Health Check Timeout

**Solution**:
- Increase `HEALTH_CHECK_TIMEOUT`
- Verify service is actually running: `docker ps`
- Check service logs: `docker logs container_name`
- Verify health endpoint: `curl http://localhost:8080/health`

## Summary Checklist

- [ ] Python 3.7+ installed
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] System tools available (git, docker, sshpass)
- [ ] Environment variables configured
- [ ] Scripts tested locally
- [ ] Workflow updated to use Python scripts

---

**Last Updated**: January 30, 2024  
**Version**: 2.0.0 (Python Edition)