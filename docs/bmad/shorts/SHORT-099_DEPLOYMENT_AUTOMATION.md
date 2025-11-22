# SHORT-099: Deployment Automation

**Status**: 🔲 Not Started
**TDD Status**: N/A (Infrastructure)
**Iteration**: 1
**Category**: Production Deployment

## Problem
Manual deployments are error-prone and time-consuming.

## Solution
Automated deployment pipeline with CI/CD integration.

## Implementation

### Deployment Pipeline
1. **Build**: Run tests, lint, type check
2. **Package**: Create Docker image or binary
3. **Deploy**: Push to production server
4. **Verify**: Run health checks
5. **Rollback**: Automatic rollback on failure

### GitHub Actions Workflow

```yaml
name: Deploy to Production

on:
  push:
    tags:
      - 'v*'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: |
          pip install -r requirements.txt
          pytest tests/ --cov=src --cov-report=xml

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Build Docker image
        run: docker build -t vcp-trading:${{ github.ref_name }} .

      - name: Push to registry
        run: docker push vcp-trading:${{ github.ref_name }}

      - name: Deploy to production
        run: |
          ssh production "docker pull vcp-trading:${{ github.ref_name }}"
          ssh production "docker-compose up -d"

      - name: Health check
        run: |
          sleep 10
          curl -f http://production/health || exit 1

      - name: Rollback on failure
        if: failure()
        run: ssh production "docker-compose down && docker-compose up -d"
```

### Deployment Script

```bash
#!/bin/bash
# deploy.sh

set -e

VERSION=$1
if [ -z "$VERSION" ]; then
  echo "Usage: ./deploy.sh <version>"
  exit 1
fi

echo "Deploying version $VERSION..."

# Backup current state
ssh production "/opt/vcp/scripts/backup.sh"

# Pull new version
ssh production "cd /opt/vcp && git pull && git checkout $VERSION"

# Install dependencies
ssh production "cd /opt/vcp && pip install -r requirements.txt"

# Run migrations
ssh production "cd /opt/vcp && python -m src.deployment.migrations migrate"

# Restart service
ssh production "systemctl restart vcp-trading"

# Wait for health check
sleep 10
if curl -f http://production:8080/health; then
  echo "Deployment successful!"
else
  echo "Health check failed, rolling back..."
  ssh production "systemctl stop vcp-trading"
  ssh production "/opt/vcp/scripts/restore_backup.sh"
  ssh production "systemctl start vcp-trading"
  exit 1
fi
```

## Test Requirements
- Deployment script execution
- Rollback on failure
- Health check validation
- Version tagging

## Dependencies
- GitHub Actions or GitLab CI
- Docker (optional)
- SSH access to production

## Acceptance Criteria
- 🔲 Automated pipeline
- 🔲 Test gate
- 🔲 Health check
- 🔲 Rollback capability
- N/A test coverage (infrastructure)

## Files
- Workflow: `/Users/srijan/Desktop/aksh/.github/workflows/deploy.yml` (to create)
- Script: `/Users/srijan/Desktop/aksh/deployment/deploy.sh` (to create)
- Docs: `/Users/srijan/Desktop/aksh/deployment/DEPLOYMENT.md` (to create)
