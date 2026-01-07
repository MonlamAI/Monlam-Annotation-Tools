#!/usr/bin/env bash

# Monlam Doccano Run Script
# Wrapper for Doccano's run.sh with wait_for_db handled

set -o errexit
set -o pipefail
set -o nounset

# Wait for database to be ready (simple implementation)
echo "Waiting for database..."
for i in {1..30}; do
  if python manage.py migrate --check >/dev/null 2>&1; then
    echo "✅ Database is ready!"
    break
  fi
  echo "Database not ready, waiting... (attempt $i/30)"
  sleep 1
done

# Run collectstatic
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Run migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Create admin user if needed
if [[ -n "${ADMIN_USERNAME:-}" ]] && [[ -n "${ADMIN_PASSWORD:-}" ]]; then
  python manage.py create_admin \
    --username="${ADMIN_USERNAME}" \
    --password="${ADMIN_PASSWORD}" \
    --email="${ADMIN_EMAIL:-admin@example.com}" \
    --noinput \
  || true
fi

# Start application
echo "Starting application..."
if [[ "${DEBUG:-False}" == "True" ]]; then
  echo "🐛 Debug mode enabled"
  python manage.py runserver 0.0.0.0:${PORT:-8000}
else
  echo "🚀 Production mode"
  gunicorn \
    --bind="0.0.0.0:${PORT:-8000}" \
    --workers="${WEB_CONCURRENCY:-1}" \
    --timeout=300 \
    --graceful-timeout=120 \
    --access-logfile=- \
    --error-logfile=- \
    config.wsgi
fi

