#!/bin/bash

# Monlam Doccano Setup Script
# Usage: ./scripts/setup.sh

set -e

echo "🚀 Setting up Monlam Doccano..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required but not installed."
    exit 1
fi

# Create virtual environment
echo "📦 Creating Python virtual environment..."
cd backend
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r ../requirements.txt

# Run migrations
echo "🗃️ Running database migrations..."
python manage.py migrate

# Create static directory
mkdir -p static/fonts

echo "⚠️  Remember to add MonlamTBslim font files to backend/static/fonts/"

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Deactivate virtual environment
deactivate

# Frontend setup
echo "📦 Setting up frontend..."
cd ../frontend
npm install

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start development:"
echo "  Backend:  cd backend && source venv/bin/activate && python manage.py runserver"
echo "  Frontend: cd frontend && npm run dev"
echo ""
echo "To create a superuser:"
echo "  cd backend && source venv/bin/activate && python manage.py createsuperuser"
echo ""

