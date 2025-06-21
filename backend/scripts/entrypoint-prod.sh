#!/bin/bash
set -e

PROJECT_NAME="${PROJECT_NAME:-Project}"

echo "🚀 Starting $PROJECT_NAME - Production"

# Function to wait for services
wait_for_service() {
    local host=$1
    local port=$2
    local service=$3
    local max_attempts=30
    local attempt=0
    
    echo "⏳ Waiting for $service..."
    while ! nc -z $host $port; do
        attempt=$((attempt+1))
        if [ $attempt -eq $max_attempts ]; then
            echo "❌ $service failed to start after $max_attempts attempts"
            exit 1
        fi
        sleep 1
    done
    echo "✅ $service is ready!"
}

# Wait for dependent services
wait_for_service postgres 5432 "PostgreSQL"
wait_for_service redis 6379 "Redis"

# Run migrations
echo "🗃️ Running migrations..."
python manage.py migrate --noinput

# Collect static files (if not already done in Dockerfile)
echo "📦 Collecting static files..."
python manage.py collectstatic --noinput

# Check system health
echo "🏥 Checking system health..."
python manage.py check --deploy

echo "🎉 Production setup complete!"
echo "🚀 Starting Gunicorn..."

# Execute the command
exec "$@"