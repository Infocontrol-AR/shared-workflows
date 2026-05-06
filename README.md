# Reusable Build and Deploy Pipeline

A comprehensive GitHub Actions reusable workflow for building, testing, deploying, and managing containerized applications with built-in rollback capabilities, health checks, and version management.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
  - [Input Parameters](#input-parameters)
  - [Required Secrets](#required-secrets)
  - [Environment Variables](#environment-variables)
- [Branch Strategy](#branch-strategy)
- [Version Management](#version-management)
- [Usage Examples](#usage-examples)
- [Pipeline Stages](#pipeline-stages)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)
- [Advanced Features](#advanced-features)

---

## Overview

This reusable workflow provides a complete CI/CD pipeline for containerized applications. It handles:

- Automated version management based on branch naming
- Docker image building and registry management
- Security scanning with Trivy
- Code quality checks with SonarQube
- Automated deployment to self-hosted servers
- Health checks and smoke tests
- Automatic rollback on deployment failures
- GPG commit signature validation
- Commit message enforcement based on ticket numbers

## Features

### 🚀 Core Features

- **Multi-stage Pipeline**: Pre-build → Build → Test → Deploy → Health Check → Rollback (if needed)
- **Flexible Version Management**: Automatic semantic versioning or custom image tags
- **Branch-based Workflows**: Different behaviors for feature, bugfix, hotfix, QA, and main branches
- **Security First**: Built-in security scanning, GPG signature checking, and Bandit analysis
- **Skip Build Mode**: Deploy existing images without rebuilding
- **Smart Rollback**: Automatic rollback on health check failures with version restoration
- **Environment Protection**: Frozen environment support to prevent accidental deployments

### 🔒 Security Features

- GPG commit signature validation (warning mode)
- Trivy container security scanning
- Bandit Python security analysis
- Secret management via GitHub Secrets

### 📊 Quality Assurance

- Automated testing with pytest
- Code coverage reporting
- SonarQube integration for code quality
- Smoke tests post-deployment

---

## Prerequisites

### Infrastructure Requirements

1. **Self-hosted GitHub Runner** with:
   - Docker installed
   - Python 3.11+
   - SSH client (`sshpass`)
   - Access to deployment servers

2. **Deployment Server** with:
   - Docker installed
   - SSH access configured
   - Network access to Docker registry

3. **Docker Registry** (private or public)

4. **Version Management Script** (`versionmanager.py`) installed at `/devops-tools/`

### Repository Setup

Your repository should have:

```
your-repo/
├── app/
│   └── _version.py          # For SKIP_BUILD mode
├── Dockerfile              # Your application Dockerfile. Can be anywhere as long as
|                           # you specify it when you launch the pipeline.
├── .env.example            # Environment template
├── requirements.txt        # Python dependencies
├── tests/
│   └── test_examples.py    # Your test files. Filaname can be different
└── deployment.sh           # Service-specific deployment script Can be anywhere as
                            # long as you specify it when you launch the pipeline.
```

---

## Quick Start

### 1. Create a Workflow in Your Repository

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy Application

on:
  push:
    branches:
      - develop
      - qa
      - stg
      - 'feature/**'
      - 'issue/**'
      - 'bugfix/**'
      - 'hotfix/**'
  pull_request:
    branches:
      - develop
      - main
      - qa
      - stg
jobs:
  deploy:
    uses: Infocontrol-AR/shared-workflows/.github/workflows/reusable-build-deploy.yml@v4
    with:
      DOCKER_REGISTRY: 'registry.example.com'
      DOCKER_REGISTRY_SHORT: 'registry.example.com'
      DOCKER_IMAGE_NAME: 'my-app'
      CONTAINER_NAME: 'my-app-container'
      CONTAINER_PORT: '8000'
      DEPLOYMENT_SCRIPT_PATH: './deployment.sh'
      VERSION_FILE_NAME: 'app/_version.py'
      REPOSITORY_NAME: 'my-app'
      environment: 'development'
    secrets:
      SSH_PASSWORD: ${{ secrets.SSH_PASSWORD }}
      SSH_IP: ${{ secrets.SSH_IP }}
      DOCKER_USERNAME: ${{ secrets.DOCKER_USERNAME }}
      DOCKER_PASSWORD: ${{ secrets.DOCKER_PASSWORD }}
      # ... other secrets
```

### 2. Configure GitHub Secrets

Go to **Settings → Secrets and variables → Actions** and add:

#### Required Secrets
- `SSH_PASSWORD` - SSH password for deployment server
- `SSH_IP` - IP address of deployment server
- `DOCKER_USERNAME` - Docker registry username
- `DOCKER_PASSWORD` - Docker registry password

#### Application Secrets
- API keys
- Cloud storage credentials
- Kafka credentials (if applicable)

### 3. Create Deployment Script

Create `deployment.sh` in your repository root:

```bash
#!/bin/bash
set -e

echo "Starting deployment..."

# Stop existing container
docker stop ${CONTAINER_NAME} || true
docker rm ${CONTAINER_NAME} || true

# Pull new image
docker pull ${DOCKER_REGISTRY}/${DOCKER_IMAGE_NAME}:${VERSION}

# Start new container
docker run -d \
  --name ${CONTAINER_NAME} \
  --network ${NETWORK_NAME} \
  -p ${CONTAINER_PORT}:${CONTAINER_PORT} \
  --env-file .env \
  --restart unless-stopped \
  ${DOCKER_REGISTRY}/${DOCKER_IMAGE_NAME}:${VERSION}

echo "Deployment completed successfully!"
```

### 4. Push to Your Branch

```bash
git add .
git commit -m "001: Add deployment workflow"
git push origin feature/001
```

The pipeline will automatically start!

---

## Configuration

### Input Parameters

#### Docker Configuration

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `DOCKER_REGISTRY` | ✅ | - | Full Docker registry URL (e.g., `registry.example.com`) |
| `DOCKER_REGISTRY_SHORT` | ✅ | - | Short registry name |
| `DOCKER_IMAGE_NAME` | ✅ | - | Name of Docker image. Sould begin with 'infocontrol/' |
| `DOCKERFILE_PATH` | ❌ | `./Dockerfile` | Path to Dockerfile |
| `DOCKER_CONTEXT_PATH` | ❌ | `.` | Docker build context path |

#### Deployment Configuration

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `CONTAINER_NAME` | ✅ | - | Name for the container |
| `CONTAINER_PORT` | ✅ | - | Port to expose |
| `DEPLOYMENT_SCRIPT_PATH` | ✅ | - | Path to deployment script |
| `environment` | ✅ | - | GitHub environment (development/staging/production) |

#### Version Management

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `VERSION_FILE_NAME` | ✅ | - | Version file path (e.g., `app/_version.py`) |
| `IMAGE_TAG` | ❌ | `None` | Override version with custom tag |
| `VERSION_NUMBER` | ❌ | `patch` | Version increment type: `major`, `minor`, or `patch` |
| `SKIP_BUILD` | ❌ | `false` | Skip build and deploy existing version from `app/_version.py` |

#### Pipeline Behavior

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `enable_tests` | ❌ | `true` | Enable tests and quality checks |
| `health_check_endpoint` | ❌ | `/health` | Health check HTTP endpoint |
| `health_check_timeout` | ❌ | `300` | Health check timeout (seconds) |
| `health_check_interval` | ❌ | `10` | Health check retry interval (seconds) |
| `FROZEN_ENVIRONMENT` | ❌ | `false` | Prevent deployments to environment |

### Required Secrets

#### SSH Access
```yaml
SSH_PASSWORD: <deployment-server-ssh-password>
SSH_IP: <deployment-server-ip-address>
```

#### Docker Registry
```yaml
DOCKER_USERNAME: <registry-username>
DOCKER_PASSWORD: <registry-password>
```


```

### Environment Variables

Set in **Settings → Environments → [environment] → Variables**:

```yaml
DEBUG: "true"  # or "false"
ENVIRONMENT_FROZEN: "false"  # Set to "true" to prevent deployments
```

---

## Branch Strategy

The pipeline behaves differently based on branch naming:

### Development Branches

**Pattern**: `develop`, `feature/XXX`, `issue/XXX`, `fix/XXX`

- **Version**: `latest-{run_id}` (e.g., `latest-12345`)
- **Version File**: Not modified
- **Git Tags**: Not created
- **Use Case**: Active development, testing

**Example**:
```bash
git checkout -b feature/123
# Version will be: latest-67890
```

### QA/Staging Branches

**Pattern**: `qa`, `staging`, `bugfix/XXX`

- **Version**: Incremented based on `VERSION_NUMBER` parameter
- **Version File**: Updated and committed
- **Git Tags**: Created automatically
- **Use Case**: Pre-production testing

**Example**:
```bash
git checkout -b bugfix/456
# With VERSION_NUMBER=minor
# Version: 1.2.0 → 1.3.0
```

### Hotfix Branches

**Pattern**: `hotfix/XXX`

- **Version**: Patch number always incremented (ignores `VERSION_NUMBER`)
- **Version File**: Updated and committed
- **Git Tags**: Created automatically
- **Use Case**: Emergency production fixes

**Example**:
```bash
git checkout -b hotfix/789
# Version: 1.3.4 → 1.3.5 (always patch)
```

### Branch Naming Requirements

For `feature/`, `issue/`, `fix/`, `hotfix/`, `bugfix/` branches:

- **XXX must be a 3-digit number** (e.g., `001`, `123`, `999`)
- Commit messages must start with `XXX:` (auto-corrected if not)

**Valid Examples**:
```
feature/001
issue/042
fix/123
hotfix/999
bugfix/456
```

**Invalid Examples**:
```
feature/1       ❌ (not 3 digits)
issue/abc       ❌ (not numeric)
fix/1234        ❌ (4 digits)
```

---

## Version Management

### Automatic Versioning

The pipeline automatically manages versions.

### Manual Version Override

Use `IMAGE_TAG` to specify an exact version:

```yaml
with:
  IMAGE_TAG: 'v1.5.0'
  # Skips all version calculation, uses v1.5.0
```

### Version File Format

Your `app/_version.py` should contain:

```python
__version__ = "1.2.3"
```

or

```python
__version__ = '1.2.3'
```

---

## Usage Examples

### Example 1: Standard Deployment

Deploy from a feature branch with automatic versioning:

```yaml
name: Deploy Feature

on:
  push:
    branches:
      - 'feature/**'

jobs:
  deploy:
    uses: Infocontrol-AR/shared-workflows/.github/workflows/reusable-build-deploy.yml@develop
    with:
      DOCKER_REGISTRY: 'registry.example.com'
      DOCKER_IMAGE_NAME: 'my-service'
      CONTAINER_NAME: 'my-service'
      CONTAINER_PORT: '8080'
      DEPLOYMENT_SCRIPT_PATH: './deploy.sh'
      VERSION_FILE_NAME: 'app/_version.py'
      REPOSITORY_NAME: ${{ github.event.repository.name }}
      environment: 'development'
    ...
```

### Example 2: Quick Redeploy (Skip Build)

Redeploy an existing image without rebuilding:

```yaml
name: Quick Redeploy

on:
  workflow_dispatch:

jobs:
  redeploy:
    uses: Infocontrol-AR/shared-workflows/.github/workflows/reusable-build-deploy.yml@develop
    with:
      DOCKER_REGISTRY: 'registry.example.com'
      DOCKER_IMAGE_NAME: 'my-service'
      SKIP_BUILD: true  # Uses version from app/_version.py
      CONTAINER_NAME: 'my-service'
      CONTAINER_PORT: '8080'
      DEPLOYMENT_SCRIPT_PATH: './deploy.sh'
      VERSION_FILE_NAME: 'app/_version.py'
      REPOSITORY_NAME: ${{ github.event.repository.name }}
      environment: 'staging'
      enable_tests: false
    secrets: inherit
```

---

## Pipeline Stages

### Stage 1: Get Version (Conditional)

**Runs**: Only when `SKIP_BUILD = true`

**Actions**:
- Reads version from `app/_version.py`
- Validates version format
- Outputs version for deployment

### Stage 2: Pre-build (Always Runs)

**Actions**:
1. ✅ Validate GPG commit signatures (warning if missing)
2. ✅ Check branch naming convention
3. ✅ Enforce commit message format (auto-fix if needed)
4. 📋 Get previous deployed version (for rollback)
5. 🔢 Compute new version (if not skipping build)

**Commit Message Enforcement**:
- Branch `feature/123` → Commit must start with `123:`
- If not, pipeline automatically amends: `"Add feature"` → `"123: Add feature"`

### Stage 3: Build (Conditional)

**Runs**: When `SKIP_BUILD = false`

**Actions**:
1. 🐳 Build Docker image
2. 📤 Push to registry with version tag and `latest`
3. 🔒 Run Trivy security scan
4. 📊 Upload security report as artifact

**Build Cache**:
- Uses registry cache for faster builds
- Cache key: `buildcache`

### Stage 4: Test and Quality (Conditional)

**Runs**: When `SKIP_BUILD = false` AND `enable_tests = true`

**Actions**:
1. 🧪 Run pytest with coverage
2. 🔍 Run Bandit security scan
3. 📈 SonarQube analysis (development environment only)
4. 📊 Upload test reports as artifacts

**Quality Gate**:
- Currently in warning mode (doesn't block deployment)
- Can be enforced by changing `exit 0` to `exit 1` in workflow

### Stage 5: Deploy

**Runs**: After successful build (or immediately if `SKIP_BUILD = true`)

**Actions**:
1. ✅ Check if environment is frozen
2. 📦 Transfer deployment scripts to server
3. 🚀 Execute deployment:
   - Clean Docker resources
   - Login to registry
   - Backup current deployment
   - Update `.env` file
   - Run service-specific deployment script
4. 💾 Save deployed version

**Environment Freezing**:
Set `ENVIRONMENT_FROZEN = true` to prevent deployments while keeping the pipeline green.

### Stage 6: Health Check

**Runs**: After successful deployment

**Actions**:
1. ⏳ Wait 30 seconds for container startup
2. 🏥 HTTP health checks (with retry logic):
   - Default: 300s timeout, 10s interval
   - Checks: `http://{server}:{port}/health`
   - Success: HTTP 200
3. 🧪 Run smoke tests (if healthy)
4. 📋 Collect container logs
5. 📤 Upload logs as artifact

**Health Check Configuration**:
```yaml
with:
  health_check_endpoint: '/api/health'
  health_check_timeout: 600
  health_check_interval: 15
```

### Stage 7: Rollback (Conditional)

**Runs**: When deployment fails OR health checks fail

**Requirements**:
- `rollback_enabled = true` in workflow call
- Previous version available

**Actions**:
1. 🔄 Determine rollback version
2. 🛑 Stop failed container
3. ♻️ Restore previous `.env` file
4. 📥 Pull previous Docker image
5. 🚀 Start container with previous version
6. ✅ Verify rollback health

**Rollback Logic**:
- Restores last known good deployment
- Reverts `.env` changes
- Updates version marker files

---


## Best Practices

### 1. Branch Naming

✅ **DO**:
```
feature/001-user-authentication
bugfix/042-fix-memory-leak
hotfix/999-critical-security-patch
```

❌ **DON'T**:
```
feature/user-auth          # Missing ticket number
bugfix/1                   # Not 3 digits  
hotfix/abcd                # Not numeric
```

### 2. Commit Messages

✅ **DO**:
```bash
git commit -m "123: Add user authentication endpoint"
git commit -m "456: Fix memory leak in data processor"
```

❌ **DON'T**:
```bash
git commit -m "Add feature"              # Missing ticket number
git commit -m "Fixed bug"                # Too vague
```

### 3. Version Management

✅ **DO**:
- Use semantic versioning (MAJOR.MINOR.PATCH)
- Let hotfix branches always increment patch
- Use `major` for breaking changes
- Use `minor` for new features
- Use `patch` for bug fixes

❌ **DON'T**:
- Manually edit version files on versioned branches
- Skip version increments
- Use inconsistent version formats

### 4. Deployment Scripts

✅ **DO**:
```bash
#!/bin/bash
set -e  # Exit on error

# Clear error handling
trap 'echo "Deployment failed at line $LINENO"' ERR

# Idempotent operations
docker stop ${CONTAINER_NAME} || true
docker rm ${CONTAINER_NAME} || true
```

❌ **DON'T**:
```bash
#!/bin/bash
# No error handling
docker stop ${CONTAINER_NAME}  # Fails if not running
# No cleanup on failure
```

### Blue-Green Deployments

Modify deployment script for zero-downtime:

```bash
#!/bin/bash
set -e

# Start new container (blue)
docker run -d \
  --name ${CONTAINER_NAME}-blue \
  --network ${NETWORK_NAME} \
  -p 8081:8080 \
  --env-file .env \
  ${DOCKER_REGISTRY}/${DOCKER_IMAGE_NAME}:${VERSION}

# Wait for health check
sleep 30
if curl -f http://localhost:8081/health; then
  # Switch traffic (update nginx/load balancer)
  # Stop old container (green)
  docker stop ${CONTAINER_NAME}-green || true
  docker rm ${CONTAINER_NAME}-green || true
  
  # Rename blue to green
  docker rename ${CONTAINER_NAME}-blue ${CONTAINER_NAME}-green
else
  # Rollback - remove blue
  docker stop ${CONTAINER_NAME}-blue
  docker rm ${CONTAINER_NAME}-blue
  exit 1
fi
```

### Multi-Container Applications

Deploy multiple containers:

```bash
#!/bin/bash
set -e


# Deploy application
docker run -d \
  --name ${CONTAINER_NAME} \
  --network ${NETWORK_NAME} \
  -p ${CONTAINER_PORT}:${CONTAINER_PORT} \
  --env-file .env \
  ${DOCKER_REGISTRY}/${DOCKER_IMAGE_NAME}:${VERSION}
```

### Scheduled Deployments

Deploy on a schedule:

```yaml
name: Scheduled Deployment

on:
  schedule:
    - cron: '0 2 * * 1'  # Every Monday at 2 AM

jobs:
  deploy:
    uses: Infocontrol-AR/shared-workflows/.github/workflows/reusable-build-deploy.yml@develop
    with:
      # ... configuration
    secrets: inherit
```

### Manual Approval for Production

Add manual approval step:

```yaml
name: Production Deploy with Approval

on:
  workflow_dispatch:

jobs:
  approval:
    runs-on: ubuntu-latest
    environment: 
      name: production-approval
    steps:
      - name: Wait for approval
        run: echo "Waiting for manual approval..."
  
  deploy:
    needs: approval
    uses: Infocontrol-AR/shared-workflows/.github/workflows/reusable-build-deploy.yml@develop
    with:
      environment: 'production'
      # ... other configuration
    secrets: inherit
```

## Security Considerations


### Image Scanning

Review Trivy reports:

- Check Actions → Workflow → Artifacts
- Download `trivy-report-{version}`
- Address CRITICAL and HIGH severity issues


---

**Last Updated**: January 30, 2024  
**Version**: 2.0.0  
**Maintained By**: Juanjo Leno