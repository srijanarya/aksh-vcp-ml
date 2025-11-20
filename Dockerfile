# ============================================================================
# Story 4.5: Docker Containerization
#
# Multi-stage Dockerfile for VCP ML Prediction API
#
# Features:
# - Multi-stage build for size optimization
# - Python 3.10 slim base image
# - Non-root user for security
# - Health checks built-in
# - Optimized layer caching
# - Target image size: <500MB
#
# Author: VCP Financial Research Team
# Created: 2025-11-14
# ============================================================================

# ============================================================================
# Stage 1: Builder
# ============================================================================
FROM python:3.10-slim AS builder

# Set working directory
WORKDIR /build

# Install system dependencies needed for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for layer caching
COPY requirements.txt .

# Install Python dependencies to user directory
RUN pip install --no-cache-dir --user -r requirements.txt


# ============================================================================
# Stage 2: Runtime
# ============================================================================
FROM python:3.10-slim

# Metadata
LABEL maintainer="VCP Financial Research Team"
LABEL description="VCP Upper Circuit Prediction API"
LABEL version="1.0.0"

# Create non-root user (AC4.5.2)
RUN useradd -m -u 1000 mluser && \
    mkdir -p /app/data /app/logs && \
    chown -R mluser:mluser /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/mluser/.local

# Set PATH to include user-installed packages
ENV PATH=/home/mluser/.local/bin:$PATH

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=mluser:mluser agents/ ./agents/
COPY --chown=mluser:mluser api/ ./api/
COPY --chown=mluser:mluser tests/ ./tests/
COPY --chown=mluser:mluser tools/ ./tools/

# Copy data directory structure (empty, mounted at runtime)
RUN mkdir -p data/models/registry data/features && \
    chown -R mluser:mluser data/

# Switch to non-root user
USER mluser

# Environment variables (AC4.5.4)
ENV MODEL_REGISTRY_PATH=/app/data/models/registry
ENV LOG_LEVEL=INFO
ENV API_PORT=8000
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Expose port
EXPOSE 8000

# Health check (AC4.5.5)
# Check every 30 seconds, timeout 3 seconds, start checking after 40 seconds, 3 retries
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Run application (AC4.5.7)
# Use uvicorn with production settings
CMD ["uvicorn", "api.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "4", \
     "--log-level", "info"]
