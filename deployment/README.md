# VCP ML Platform - Autonomous Deployment System

Complete autonomous deployment automation for the VCP ML Platform.

## Overview

This deployment system provides **zero-touch deployment** from validation to production with automatic rollback on failure.

### Features

- **Pre-Deployment Validation** - Automated tests, Docker build, environment checks
- **Staging Deployment** - Safe staging environment for testing
- **Smoke Tests** - Critical endpoint verification
- **Production Deployment** - Blue-green deployment with monitoring
- **Automatic Rollback** - Instant rollback on health degradation
- **Notifications** - Slack/Email alerts for deployment events
- **Monitoring** - Real-time health checks and metrics

## Directory Structure

```
deployment/
├── agents/                          # Autonomous deployment agents
│   ├── pre_deployment_validator.py  # Validates system readiness
│   ├── deployment_orchestrator.py   # Coordinates deployment
│   ├── smoke_test_runner.py         # Runs critical tests
│   ├── deployment_monitor.py        # Monitors health
│   └── rollback_agent.py            # Handles rollbacks
│
├── tools/                           # Deployment utilities
│   ├── docker_manager.py            # Docker operations
│   ├── environment_manager.py       # Environment config
│   └── notification_manager.py      # Alerts & notifications
│
├── scripts/                         # Deployment scripts
│   ├── deploy_staging.py            # Deploy to staging
│   ├── deploy_production.py         # Deploy to production
│   └── deploy_all.sh                # One-click full deployment
│
└── config/                          # Configuration files
    ├── .env.staging                 # Staging environment
    ├── .env.production              # Production environment
    └── deployment.yaml              # Deployment config
```

## Quick Start

### Prerequisites

1. **Docker** installed and running
2. **Python 3.10+** installed
3. **All tests passing** (141/141)
4. **Data directories** populated

### One-Click Deployment

Deploy to both staging and production with full monitoring:

```bash
./deployment/scripts/deploy_all.sh
```

This will:
1. ✅ Validate pre-deployment requirements
2. 🔧 Deploy to staging
3. 🧪 Run smoke tests
4. 🎯 Deploy to production (with confirmation)
5. 👀 Monitor production for 5 minutes

### Deploy to Staging Only

```bash
python3 deployment/scripts/deploy_staging.py
```

Access staging at: http://localhost:8001

### Deploy to Production Only

```bash
python3 deployment/scripts/deploy_production.py
```

Access production at: http://localhost:8000

## Deployment Workflow

### 1. Pre-Deployment Validation

Validates:
- ✅ All tests passing (141/141)
- ✅ Docker build succeeds
- ✅ Environment variables set
- ✅ Database connections valid
- ✅ Model registry has models

Run validation independently:
```bash
python3 deployment/agents/pre_deployment_validator.py
```

### 2. Staging Deployment

Deploys to isolated staging environment:
- Port: 8001
- Workers: 2
- Log Level: DEBUG
- Auto-scaling: Disabled

### 3. Smoke Tests

Tests critical endpoints:
- ✅ Health check (`/api/v1/health`)
- ✅ Single prediction (`/api/v1/predict`)
- ✅ Batch prediction (`/api/v1/batch_predict`)
- ✅ Metrics (`/api/v1/metrics`)

Run smoke tests independently:
```bash
python3 deployment/agents/smoke_test_runner.py http://localhost:8001
```

### 4. Production Deployment

Deploys to production with:
- Port: 8000
- Workers: 4
- Log Level: INFO
- Auto-scaling: Enabled
- Monitoring: 5 minutes

### 5. Monitoring & Rollback

Monitors deployment health:
- Health checks every 30 seconds
- Automatic rollback if health < 95%
- Alert notifications via Slack/Email

Run monitoring independently:
```bash
python3 deployment/agents/deployment_monitor.py http://localhost:8000 300
```

## Configuration

### Environment Variables

Edit `.env.staging` or `.env.production`:

```bash
ENVIRONMENT=production
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
DATABASE_PATH=/app/data/vcp_trading_local.db
MODEL_REGISTRY_PATH=/app/data/models/registry/model_registry.db
```

### Deployment Configuration

Edit `deployment.yaml` for advanced settings:

```yaml
deployment:
  production:
    replicas: 2
    cpu_limit: "4000m"
    memory_limit: "8Gi"
    autoscaling: true
    rollback_threshold: 0.95
```

## Agents

### 1. PreDeploymentValidator

Validates system readiness before deployment.

**Usage:**
```python
from deployment.agents import PreDeploymentValidator

validator = PreDeploymentValidator()
report = validator.validate_all()

if report.overall_passed:
    print("Ready for deployment!")
```

### 2. DeploymentOrchestrator

Coordinates complete deployment workflow.

**Usage:**
```python
from deployment.agents import DeploymentOrchestrator

orchestrator = DeploymentOrchestrator(environment="production")
result = orchestrator.deploy()

if result.success:
    print(f"Deployed to {result.url}")
```

### 3. SmokeTestRunner

Runs critical smoke tests after deployment.

**Usage:**
```python
from deployment.agents import SmokeTestRunner

runner = SmokeTestRunner(base_url="http://localhost:8000")
report = runner.run_all_smoke_tests()

if report.overall_passed:
    print("All smoke tests passed!")
```

### 4. DeploymentMonitor

Monitors deployment health in real-time.

**Usage:**
```python
from deployment.agents import DeploymentMonitor

monitor = DeploymentMonitor(base_url="http://localhost:8000")
result = monitor.monitor_deployment(
    deployment_id="deploy_123",
    duration=300  # 5 minutes
)
```

### 5. RollbackAgent

Handles deployment rollbacks safely.

**Usage:**
```python
from deployment.agents import RollbackAgent

agent = RollbackAgent()

# Save state before deployment
agent.save_deployment_state(
    version="v1.0.0",
    image_tag="vcp-ml:v1.0.0"
)

# Rollback if needed
result = agent.execute_rollback(target_version="v1.0.0")
```

## Tools

### DockerManager

Manages Docker operations:

```python
from deployment.tools import DockerManager

docker = DockerManager()

# Build image
image_id = docker.build_image(tag="vcp-ml:latest")

# Deploy container
container_id = docker.deploy_container(
    tag="vcp-ml:latest",
    port=8000
)

# Stop container
docker.stop_container(container_id)
```

### EnvironmentManager

Manages environment configuration:

```python
from deployment.tools import EnvironmentManager

env = EnvironmentManager()

# Load environment file
vars = env.load_env_file("production")

# Set environment variables
env.set_env_vars(vars)

# Validate required variables
env.validate_env_vars(['API_HOST', 'API_PORT'])
```

### NotificationManager

Sends deployment notifications:

```python
from deployment.tools import NotificationManager

notifier = NotificationManager()

# Notify deployment start
notifier.notify_deployment_start(
    environment="production",
    deployment_id="deploy_123",
    version="v1.0.0"
)

# Notify deployment success
notifier.notify_deployment_success(
    environment="production",
    deployment_id="deploy_123",
    version="v1.0.0",
    duration=120.5,
    url="http://localhost:8000"
)
```

## Rollback

### Automatic Rollback

Automatically triggered when:
- Smoke tests fail
- Health checks fail
- Health rate < 95%

### Manual Rollback

```bash
python3 deployment/agents/rollback_agent.py <version>
```

Example:
```bash
python3 deployment/agents/rollback_agent.py v1.0.0
```

## Notifications

### Slack

Configure Slack webhook in `.env.production`:

```bash
ALERT_SLACK_WEBHOOK=https://hooks.slack.com/services/YOUR/WEBHOOK/HERE
```

### Email

Configure SMTP settings in `deployment.yaml`:

```yaml
notifications:
  email:
    smtp_server: "smtp.gmail.com"
    smtp_port: 587
    to_addresses:
      - "ops@yourcompany.com"
```

## Monitoring

### Health Checks

Check API health:
```bash
curl http://localhost:8000/api/v1/health
```

Response:
```json
{
  "status": "healthy",
  "model_loaded": true,
  "uptime_seconds": 3600,
  "requests_processed": 1000,
  "avg_latency_ms": 45.2,
  "error_rate": 0.01
}
```

### Metrics

View Prometheus metrics:
```bash
curl http://localhost:8000/api/v1/metrics
```

### Logs

View container logs:
```bash
docker logs vcp-ml-production
```

## Troubleshooting

### Deployment Fails

1. Check validation report:
   ```bash
   python3 deployment/agents/pre_deployment_validator.py
   ```

2. Verify Docker is running:
   ```bash
   docker ps
   ```

3. Check logs:
   ```bash
   docker logs vcp-ml-staging
   ```

### Smoke Tests Fail

1. Verify container is running:
   ```bash
   docker ps | grep vcp-ml
   ```

2. Check health endpoint:
   ```bash
   curl http://localhost:8001/api/v1/health
   ```

3. View container logs:
   ```bash
   docker logs vcp-ml-staging
   ```

### Rollback Fails

1. Check available versions:
   ```bash
   ls deployment/state/
   ```

2. Verify Docker images:
   ```bash
   docker images | grep vcp-ml
   ```

3. Manual container restart:
   ```bash
   docker restart vcp-ml-production
   ```

## Performance

### Deployment Times

- **Validation**: ~30 seconds
- **Docker Build**: ~60 seconds
- **Staging Deployment**: ~45 seconds
- **Smoke Tests**: ~10 seconds
- **Production Deployment**: ~45 seconds
- **Monitoring**: 5 minutes

**Total**: ~7-8 minutes for full deployment

### Resource Requirements

**Staging:**
- CPU: 2 cores
- Memory: 4 GB
- Disk: 10 GB

**Production:**
- CPU: 4 cores
- Memory: 8 GB
- Disk: 20 GB

## Security

### Best Practices

1. **Non-root user** - Containers run as `mluser`
2. **Environment variables** - Sensitive data in .env files (not committed)
3. **CORS** - Configure allowed origins for production
4. **Rate limiting** - Built into API
5. **Health checks** - Automatic container health monitoring

### Secrets Management

DO NOT commit:
- `.env.staging`
- `.env.production`
- Slack webhook URLs
- API keys

Add to `.gitignore`:
```
deployment/config/.env.*
deployment/state/*
deployment/logs/*
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to Production
        run: ./deployment/scripts/deploy_all.sh
```

### GitLab CI

```yaml
deploy:
  stage: deploy
  script:
    - ./deployment/scripts/deploy_all.sh
  only:
    - main
```

## Support

For issues or questions:
1. Check troubleshooting section
2. Review logs: `docker logs vcp-ml-production`
3. Check health: `curl http://localhost:8000/api/v1/health`
4. Review deployment events: `cat deployment/logs/deployment_events.jsonl`

## License

VCP Financial Research Team - 2025
