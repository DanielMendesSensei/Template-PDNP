# Multi-stage build for Django application

# Base stage with common dependencies
FROM python:3.13-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    postgresql-client \
    curl \
    netcat-traditional \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Development stage
FROM base as development

# Install additional dev tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    vim \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements/ requirements/

# Install Python dependencies (including dev)
RUN pip install --upgrade pip setuptools wheel \
    && pip install -r requirements/development.txt \
    && pip install watchdog

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs /app/media /app/staticfiles \
    && chown -R appuser:appuser /app

# Copy and set permissions for scripts
COPY scripts/entrypoint-dev.sh /app/scripts/
RUN chmod +x /app/scripts/entrypoint-dev.sh

USER appuser

EXPOSE 8000

ENTRYPOINT ["/app/scripts/entrypoint-dev.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# Production stage
FROM base as production

# Copy requirements
COPY requirements/ requirements/

# Install Python dependencies (production only)
RUN pip install --upgrade pip setuptools wheel \
    && pip install -r requirements/production.txt \
    && pip install gunicorn

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs /app/media /app/staticfiles \
    && chown -R appuser:appuser /app

# Copy and set permissions for scripts
COPY scripts/entrypoint-prod.sh /app/scripts/
RUN chmod +x /app/scripts/entrypoint-prod.sh

# Collect static files
RUN python manage.py collectstatic --noinput

USER appuser

EXPOSE 8000

ENTRYPOINT ["/app/scripts/entrypoint-prod.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4"]