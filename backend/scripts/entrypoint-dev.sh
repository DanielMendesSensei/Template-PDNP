#!/bin/bash
set -e

PROJECT_NAME="${PROJECT_NAME:-Project}"

echo "🚀 Starting $PROJECT_NAME - Development"

# Function to wait for services
wait_for_service() {
    local host=$1
    local port=$2
    local service=$3
    
    echo "⏳ Waiting for $service..."
    while ! nc -z $host $port; do
        sleep 0.1
    done
    echo "✅ $service is ready!"
}

# Wait for dependent services
wait_for_service postgres 5432 "PostgreSQL"
wait_for_service redis 6379 "Redis"

# Wait a bit more to ensure DB is really ready
sleep 5

# Run migrations automatically in development
echo "🗃️ Running migrations..."
python manage.py migrate --noinput

# Create superuser if it doesn't exist (development only)
if [ "$DJANGO_ENVIRONMENT" = "development" ]; then
    echo "👤 Checking superuser..."
    python manage.py shell -c "
from django.contrib.auth.models import User
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser(
        '${DJANGO_SUPERUSER_USERNAME:-admin}',
        '${DJANGO_SUPERUSER_EMAIL:-admin@example.com}',
        '${DJANGO_SUPERUSER_PASSWORD:-admin123}'
    )
    print('✅ Superuser created')
else:
    print('ℹ️ Superuser already exists')
"
fi

# Check system health
echo "🏥 Checking system health..."
python -c "
import redis
import django
from django.db import connection

# Test Redis
try:
    r = redis.from_url('${REDIS_URL}')
    r.ping()
    print('✅ Redis connected')
except Exception as e:
    print(f'❌ Redis error: {e}')

# Test Database
try:
    with connection.cursor() as cursor:
        cursor.execute('SELECT 1')
    print('✅ PostgreSQL connected')
except Exception as e:
    print(f'❌ PostgreSQL error: {e}')
"

echo "🎉 Development setup complete!"
echo "🌐 Available services:"
echo "  📡 API Backend: http://localhost:${BACKEND_PORT:-8000}"
echo "  🔧 Django Admin: http://localhost:${BACKEND_PORT:-8000}/admin"
echo "  📊 Health Check: http://localhost:${BACKEND_PORT:-8000}/health"
echo ""
echo "  👤 Default superuser: ${DJANGO_SUPERUSER_USERNAME:-admin} / ${DJANGO_SUPERUSER_PASSWORD:-admin123}"

echo "🚀 Running command: $@"
exec "$@"