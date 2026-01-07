#!/bin/bash

# Run Django migrations
# Usage: ./scripts/migrate.sh

set -e

echo "🗃️ Running database migrations..."

cd backend

if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

python manage.py makemigrations
python manage.py migrate

echo "✅ Migrations complete!"

