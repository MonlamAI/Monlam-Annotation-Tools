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

FROM doccano/doccano:1.8.4

USER root

# ============================================
# BRANDING: Tibetan locale and assets
# ============================================
COPY branding/i18n/bo /doccano/frontend/i18n/bo
COPY branding/i18n/index.js /doccano/frontend/i18n/index.js
COPY branding/static/logo.png /doccano/frontend/assets/icon.png
COPY branding/static/favicon.png /doccano/backend/staticfiles/favicon.png
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

# Example JSONL files (required for import options to appear)
COPY patches/examples/speech_to_text/example.jsonl /doccano/backend/data_import/pipeline/examples/speech_to_text/example.jsonl
COPY patches/examples/image_classification/example.jsonl /doccano/backend/data_import/pipeline/examples/image_classification/example.jsonl

# ============================================
# FRONTEND PATCHES
# ============================================

# Custom index.html with:
# - Monlam Unicode font
# - Tibetan translations
# - Monlam branding colors
# - Review button styling (Red O / Green Check)
# - GitHub button hidden
COPY patches/frontend/index.html /doccano/backend/client/dist/index.html
COPY patches/frontend/200.html /doccano/backend/client/dist/200.html

# ============================================
# SET OWNERSHIP
# ============================================
RUN chown -R doccano:doccano /doccano/frontend/i18n/bo && \
    chown doccano:doccano /doccano/frontend/i18n/index.js && \
    chown doccano:doccano /doccano/frontend/assets/icon.png && \
    chown doccano:doccano /doccano/backend/staticfiles/favicon.png && \
    chown doccano:doccano /doccano/backend/staticfiles/_nuxt/img/icon.c360b38.png && \
    chown doccano:doccano /doccano/backend/staticfiles/_nuxt/img/6737785.30d4036.png && \
    chown doccano:doccano /doccano/backend/data_import/celery_tasks.py && \
    chown doccano:doccano /doccano/backend/examples/serializers.py && \
    chown doccano:doccano /doccano/backend/data_export/models.py && \
    chown doccano:doccano /doccano/backend/data_import/pipeline/catalog.py && \
    chown doccano:doccano /doccano/backend/data_import/datasets.py && \
    chown doccano:doccano /doccano/backend/data_import/pipeline/examples/speech_to_text/example.jsonl && \
    chown doccano:doccano /doccano/backend/data_import/pipeline/examples/image_classification/example.jsonl && \
    chown doccano:doccano /doccano/backend/client/dist/index.html && \
    chown doccano:doccano /doccano/backend/client/dist/200.html

USER doccano
WORKDIR /doccano/backend
