# Multi-stage build for Monlam Doccano

# ============================================
# Stage 1: Build Frontend
# ============================================
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy frontend files and install dependencies
COPY frontend/package.json ./
RUN npm install --legacy-peer-deps

COPY frontend/ ./
RUN npm run build

# ============================================
# Stage 2: Python Backend
# ============================================
FROM python:3.11-slim AS backend

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# Override any existing DJANGO_SETTINGS_MODULE from old Doccano
ENV DJANGO_SETTINGS_MODULE=config.settings

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./

# Copy built frontend from Stage 1
COPY --from=frontend-builder /app/frontend/dist ./static/dist/

# Create necessary directories
RUN mkdir -p static staticfiles media templates

# Copy static assets (fonts, images, etc.)
COPY backend/static/ ./static/

# Collect static files
RUN python manage.py collectstatic --noinput

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port (Render uses PORT env var, default 8000 for local)
EXPOSE 8000

# Health check disabled - Render handles this via healthCheckPath
# HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
#     CMD curl -f http://localhost:${PORT:-8000}/health/ || exit 1

# Start command - use PORT env var (Render sets this to 10000)
CMD gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 2 --threads 2

