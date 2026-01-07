#!/usr/bin/env bash

# Monlam Doccano Run Script
# Based on official Doccano run.sh with minimal modifications

set -o errexit
set -o pipefail
set -o nounset

# Ensure we're in the correct directory
cd /doccano/backend

echo "📂 Working directory: $(pwd)"
echo "🐍 Python: $(python --version)"

# Simple database wait (without Django command)
echo "⏳ Waiting for database to accept connections..."
for i in {1..30}; do
  # Simple check: just wait a bit for PostgreSQL to be ready
  # The migrate command below will verify it works
  if [ $i -eq 1 ]; then
    sleep 5  # Give database a few seconds to start
    break
  fi
done
echo "✅ Proceeding with initialization..."

# Run migrations
echo "🔄 Running database migrations..."
python manage.py migrate --noinput

# Create admin user (use Doccano's actual command)
if [[ -n "${ADMIN_USERNAME:-}" ]] && [[ -n "${ADMIN_PASSWORD:-}" ]]; then
  echo "👤 Creating admin user..."
  python manage.py create_admin \
    --username="${ADMIN_USERNAME}" \
    --password="${ADMIN_PASSWORD}" \
    --email="${ADMIN_EMAIL:-admin@example.com}" \
    --noinput \
  || echo "⚠️ Admin user may already exist (this is OK)"
fi

# Start Celery worker in background (if CELERY_BROKER_URL is set)
if [[ -n "${CELERY_BROKER_URL:-}" ]]; then
  echo "🔧 Starting Celery worker in background..."
  celery --app=config worker \
    --loglevel=INFO \
    --concurrency=1 \
    --pool=solo &
  echo "✅ Celery worker started"
fi

# Start application with gunicorn
echo "🚀 Starting Doccano application..."
echo "🌐 Listening on port ${PORT:-8000}"

# Use sync workers (not uvicorn) - this is what Doccano uses
exec gunicorn \
  --bind="0.0.0.0:${PORT:-8000}" \
  --workers="${WEB_CONCURRENCY:-1}" \
  --timeout=300 \
  --graceful-timeout=120 \
  --access-logfile=- \
  --error-logfile=- \
  --log-level=info \
  config.wsgi:application

