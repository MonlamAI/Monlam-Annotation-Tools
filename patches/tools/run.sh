#!/usr/bin/env bash

# Monlam Doccano Run Script
# Wrapper for Doccano's run.sh with proper error handling

set -o errexit
set -o pipefail
set -o nounset

# Ensure we're in the correct directory
cd /doccano/backend || cd /app || exit 1

echo "📂 Working directory: $(pwd)"
echo "🐍 Python: $(python --version)"

# Wait for database to be ready (simple implementation)
echo "⏳ Waiting for database..."
for i in {1..30}; do
  # Try to connect using Django's check command
  if python manage.py check --database default >/dev/null 2>&1; then
    echo "✅ Database is ready!"
    break
  fi
  
  if [ $i -eq 30 ]; then
    echo "❌ Database failed to become ready after 30 attempts"
    echo "🔍 Checking DATABASE_URL..."
    echo "DATABASE_URL is set: ${DATABASE_URL:+yes}"
    exit 1
  fi
  
  echo "⏳ Database not ready, waiting... (attempt $i/30)"
  sleep 1
done

# Run migrations
echo "🔄 Running migrations..."
python manage.py migrate --noinput || echo "⚠️ Some migrations may have failed (might be OK)"

# Create admin user if needed
if [[ -n "${ADMIN_USERNAME:-}" ]] && [[ -n "${ADMIN_PASSWORD:-}" ]]; then
  echo "👤 Creating admin user..."
  python manage.py create_admin \
    --username="${ADMIN_USERNAME}" \
    --password="${ADMIN_PASSWORD}" \
    --email="${ADMIN_EMAIL:-admin@example.com}" \
    --noinput \
  || echo "⚠️ Admin user may already exist"
fi

# Start Celery worker in background (if CELERY_BROKER_URL is set)
if [[ -n "${CELERY_BROKER_URL:-}" ]]; then
  echo "🔧 Starting Celery worker..."
  celery --app=config worker \
    --loglevel=INFO \
    --concurrency=1 \
    --pool=solo &
fi

# Start application
echo "🚀 Starting application..."
if [[ "${DEBUG:-False}" == "True" ]]; then
  echo "🐛 Debug mode enabled"
  python manage.py runserver 0.0.0.0:${PORT:-8000}
else
  echo "🚀 Production mode"
  gunicorn \
    --bind="0.0.0.0:${PORT:-8000}" \
    --workers="${WEB_CONCURRENCY:-1}" \
    --worker-class=uvicorn.workers.UvicornWorker \
    --timeout=300 \
    --graceful-timeout=120 \
    --access-logfile=- \
    --error-logfile=- \
    config.wsgi
fi

