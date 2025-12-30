# Monlam Doccano - Custom Doccano with Tibetan Language Support
# Based on official doccano image with Monlam branding and enhancements
#
# Features:
# - Tibetan language (བོད་སྐད་) support
# - Monlam branding and styling
# - Auto TextLabel creation for STT projects
# - JSONL import with external URLs for STT and Image Classification
# - Pre-filled labels for annotation review workflow
# - Review button styling (Red O / Green Check)
# - Approve/Reject buttons for reviewers (saves to database)

FROM doccano/doccano:1.8.4

USER root

# ============================================
# BRANDING: Tibetan locale and assets
# ============================================
COPY branding/i18n/bo /doccano/frontend/i18n/bo
COPY branding/i18n/index.js /doccano/frontend/i18n/index.js
COPY branding/static/logo.png /doccano/frontend/assets/icon.png
# Favicon - proper ICO format for browser compatibility
COPY branding/static/favicon.ico /doccano/backend/staticfiles/favicon.ico
COPY branding/static/favicon.png /doccano/backend/staticfiles/favicon.png
COPY branding/static/favicon.ico /doccano/backend/client/dist/favicon.ico
COPY branding/static/favicon.png /doccano/backend/client/dist/favicon.png
COPY branding/static/favicon.ico /doccano/backend/client/dist/static/favicon.ico
COPY branding/static/favicon.png /doccano/backend/client/dist/static/favicon.png
# Root favicon.ico for browsers that look at site root
COPY branding/static/favicon.ico /doccano/backend/favicon.ico
COPY branding/fonts /doccano/backend/staticfiles/fonts
COPY branding/static/logo.png /doccano/backend/staticfiles/_nuxt/img/icon.c360b38.png
COPY branding/static/logo.png /doccano/backend/staticfiles/_nuxt/img/6737785.30d4036.png

# ============================================
# BACKEND PATCHES
# ============================================

# Auto-create TextLabels for STT projects after import
COPY patches/backend/celery_tasks.py /doccano/backend/data_import/celery_tasks.py

# Fix external audio/image URLs (don't prepend /media/)
COPY patches/backend/serializers.py /doccano/backend/examples/serializers.py

# Export correct audio URL instead of upload filename
COPY patches/backend/export_models.py /doccano/backend/data_export/models.py

# Enable JSONL import for STT and Image Classification
COPY patches/backend/catalog.py /doccano/backend/data_import/pipeline/catalog.py

# Custom dataset classes for STT & Image Classification with pre-filled labels
COPY patches/backend/datasets.py /doccano/backend/data_import/datasets.py

# Review API for approve/reject workflow (used by frontend)
COPY patches/backend/review_api.py /doccano/backend/examples/review_api.py

# Example JSONL files (required for import options to appear)
COPY patches/examples/speech_to_text/example.jsonl /doccano/backend/data_import/pipeline/examples/speech_to_text/example.jsonl
COPY patches/examples/image_classification/example.jsonl /doccano/backend/data_import/pipeline/examples/image_classification/example.jsonl

# ============================================
# ASSIGNMENT & COMPLETION TRACKING SYSTEM
# ============================================
# Copy the entire assignment app to doccano backend
COPY patches/assignment /doccano/backend/assignment

# Register the assignment app in settings
RUN echo "INSTALLED_APPS += ['assignment']" >> /doccano/backend/config/settings/base.py || true

# Configure WhiteNoise MIME types for JavaScript files
RUN echo "" >> /doccano/backend/config/settings/base.py && \
    echo "# Monlam: Ensure JavaScript files are served with correct MIME type" >> /doccano/backend/config/settings/base.py && \
    echo "import mimetypes" >> /doccano/backend/config/settings/base.py && \
    echo "mimetypes.add_type('application/javascript', '.js', True)" >> /doccano/backend/config/settings/base.py

# ============================================
# FRONTEND PATCHES
# ============================================

# Custom index.html with:
# - Monlam Unicode font
# - Tibetan translations
# - Monlam branding colors
# - Review button styling (Red O / Green Check)
# - GitHub button hidden
# - Monlam enhancement script tags (audio loop, completion tracking UI)
COPY patches/frontend/index.html /doccano/backend/client/dist/index.html
COPY patches/frontend/200.html /doccano/backend/client/dist/200.html

# ============================================
# DELETE ROBOTO FONTS - Force fallback to MonlamTBslim
# ============================================
RUN rm -rf /doccano/backend/staticfiles/_nuxt/fonts/Roboto* && \
    rm -rf /doccano/backend/client/dist/_nuxt/fonts/Roboto* && \
    rm -rf /doccano/backend/client/dist/static/_nuxt/fonts/Roboto* || true

# ============================================
# SET OWNERSHIP
# ============================================
RUN chown -R doccano:doccano /doccano/frontend/i18n/bo && \
    chown doccano:doccano /doccano/frontend/i18n/index.js && \
    chown doccano:doccano /doccano/frontend/assets/icon.png && \
    chown doccano:doccano /doccano/backend/staticfiles/favicon.png && \
    chown doccano:doccano /doccano/backend/staticfiles/favicon.ico && \
    chown -R doccano:doccano /doccano/backend/staticfiles/fonts && \
    chown doccano:doccano /doccano/backend/staticfiles/_nuxt/img/icon.c360b38.png && \
    chown doccano:doccano /doccano/backend/staticfiles/_nuxt/img/6737785.30d4036.png && \
    chown doccano:doccano /doccano/backend/favicon.ico && \
    chown doccano:doccano /doccano/backend/client/dist/favicon.ico && \
    chown doccano:doccano /doccano/backend/client/dist/favicon.png && \
    chown doccano:doccano /doccano/backend/client/dist/static/favicon.ico && \
    chown doccano:doccano /doccano/backend/client/dist/static/favicon.png && \
    chown doccano:doccano /doccano/backend/data_import/celery_tasks.py && \
    chown doccano:doccano /doccano/backend/examples/serializers.py && \
    chown doccano:doccano /doccano/backend/examples/review_api.py && \
    chown doccano:doccano /doccano/backend/data_export/models.py && \
    chown doccano:doccano /doccano/backend/data_import/pipeline/catalog.py && \
    chown doccano:doccano /doccano/backend/data_import/datasets.py && \
    chown doccano:doccano /doccano/backend/data_import/pipeline/examples/speech_to_text/example.jsonl && \
    chown doccano:doccano /doccano/backend/data_import/pipeline/examples/image_classification/example.jsonl && \
    chown doccano:doccano /doccano/backend/client/dist/index.html && \
    chown doccano:doccano /doccano/backend/client/dist/200.html && \
    chown -R doccano:doccano /doccano/backend/assignment

# ============================================
# RUN MIGRATIONS
# ============================================
# Run migrations for assignment and completion tracking
RUN python manage.py makemigrations assignment || true && \
    python manage.py migrate assignment || true

# ============================================
# COPY MONLAM JS FILES AND COMPRESS THEM
# ============================================
# Copy JS files to staticfiles
COPY --chown=doccano:doccano patches/frontend/audio-loop-enhanced.js /doccano/backend/staticfiles/_nuxt/
COPY --chown=doccano:doccano patches/frontend/enhance-members-progress.js /doccano/backend/staticfiles/_nuxt/
COPY --chown=doccano:doccano patches/frontend/dataset-completion-columns.js /doccano/backend/staticfiles/_nuxt/

# Compress files for WhiteNoise (it requires .gz versions)
RUN gzip -k -f /doccano/backend/staticfiles/_nuxt/audio-loop-enhanced.js && \
    gzip -k -f /doccano/backend/staticfiles/_nuxt/enhance-members-progress.js && \
    gzip -k -f /doccano/backend/staticfiles/_nuxt/dataset-completion-columns.js

USER doccano
WORKDIR /doccano/backend
