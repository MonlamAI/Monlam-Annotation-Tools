#!/bin/bash
# Startup script for Doccano with Assignment System
# Runs migrations before starting the server

set -e

echo "============================================"
echo "Monlam Doccano - Starting up..."
echo "============================================"

cd /doccano/backend

# Run the URL patcher to add assignment routes
echo "Patching URL routes..."
python patch_urls.py || echo "URL patching skipped (may already be applied)"

# Run migrations
echo "Running database migrations..."
python manage.py migrate --noinput || echo "Migration failed or already applied"

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput || echo "Static collection skipped"

echo "============================================"
echo "Starting Doccano server..."
echo "============================================"

# Start with gunicorn (production server) like doccano normally does
# If gunicorn is available, use it; otherwise fall back to runserver
if command -v gunicorn &> /dev/null; then
    exec gunicorn --bind 0.0.0.0:${PORT:-8000} \
        --workers ${WORKERS:-2} \
        --timeout 300 \
        config.wsgi:application
else
    exec python manage.py runserver 0.0.0.0:${PORT:-8000}
fi
