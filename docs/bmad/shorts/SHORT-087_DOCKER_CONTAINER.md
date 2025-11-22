# SHORT-087: Docker Container

**Status**: 🔲 Not Started
**TDD Status**: N/A (Infrastructure)
**Iteration**: 1
**Category**: Production Deployment

## Problem
Need containerized deployment for consistency across environments.

## Solution
Docker container with multi-stage build and production optimizations.

## Implementation

### Dockerfile

```dockerfile
# Build stage
FROM python:3.10-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.10-slim

WORKDIR /app

# Copy dependencies from builder
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages

# Copy application
COPY src/ ./src/
COPY .env.production .env

# Non-root user
RUN useradd -m vcp
USER vcp

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "from src.deployment.health_check import HealthChecker; exit(0 if HealthChecker().check_health()['status'] == 'healthy' else 1)"

# Run application
CMD ["python", "-m", "src.main"]
```

### Usage

```bash
# Build image
docker build -t vcp-trading:latest .

# Run container
docker run -d \
  --name vcp-trading \
  --env-file .env.production \
  -v /opt/vcp/data:/app/data \
  --restart unless-stopped \
  vcp-trading:latest

# Check logs
docker logs -f vcp-trading

# Health check
docker ps --filter health=healthy
```

## Test Requirements
- Image builds successfully
- Container starts
- Health check works
- Volumes mounted
- Environment loaded

## Dependencies
- Docker
- Docker Compose (optional)

## Acceptance Criteria
- 🔲 Multi-stage Dockerfile
- 🔲 Non-root user
- 🔲 Health check integrated
- 🔲 Volume support
- N/A test coverage (infrastructure)

## Files
- Dockerfile: `/Users/srijan/Desktop/aksh/Dockerfile` (to create)
- Compose: `/Users/srijan/Desktop/aksh/docker-compose.yml` (to create)
- Docs: `/Users/srijan/Desktop/aksh/deployment/DOCKER.md` (to create)
