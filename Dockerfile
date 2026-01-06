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
# - Simple annotation tracking (who annotated, who reviewed)
# - Example visibility filtering (annotated examples hidden from others)
# - Example locking (prevents simultaneous edits)
# - Approve/Reject buttons on annotation page (saves to database)
# - Auto-advance after approve/reject
# - Dataset columns show tracking data from PostgreSQL

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

# Visibility filtering mixin (will be imported in views.py)
COPY patches/backend/examples_views_patch.py /doccano/backend/examples/visibility_mixin.py

# Runtime monkey-patch to apply visibility filtering
COPY patches/backend/apply_visibility_filter.py /doccano/backend/config/apply_visibility_filter.py

# Auto-tracking of annotations (signal handlers)
COPY patches/backend/auto_track_annotations.py /doccano/backend/config/auto_track_annotations.py

# Import the visibility filter and auto-tracking at Django startup
RUN echo "# Monlam: Apply visibility filtering and auto-tracking at startup" >> /doccano/backend/config/settings/base.py && \
    echo "try:" >> /doccano/backend/config/settings/base.py && \
    echo "    from config.apply_visibility_filter import apply_visibility_filtering" >> /doccano/backend/config/settings/base.py && \
    echo "    from config.auto_track_annotations import setup_auto_tracking" >> /doccano/backend/config/settings/base.py && \
    echo "    apply_visibility_filtering()" >> /doccano/backend/config/settings/base.py && \
    echo "    setup_auto_tracking()" >> /doccano/backend/config/settings/base.py && \
    echo "except Exception as e:" >> /doccano/backend/config/settings/base.py && \
    echo "    print(f'[Monlam] Visibility filter/auto-tracking not applied: {e}')" >> /doccano/backend/config/settings/base.py

# Export correct audio URL instead of upload filename
COPY patches/backend/export_models.py /doccano/backend/data_export/models.py

# Enable JSONL import for STT and Image Classification
COPY patches/backend/catalog.py /doccano/backend/data_import/pipeline/catalog.py

# Custom dataset classes for STT & Image Classification with pre-filled labels
COPY patches/backend/datasets.py /doccano/backend/data_import/datasets.py

# Review API for approve/reject workflow (used by frontend)
COPY patches/backend/review_api.py /doccano/backend/examples/review_api.py

# Custom WhiteNoise storage with proper MIME types
COPY patches/backend/whitenoise_config.py /doccano/backend/config/whitenoise_config.py

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

# Integrate assignment URLs into main urls.py
# Add the assignment URL pattern to urlpatterns
RUN if ! grep -q "assignment.urls" /doccano/backend/config/urls.py; then \
        sed -i "s|urlpatterns = \[|urlpatterns = [\n    # Monlam: Assignment and Completion Tracking APIs\n    path('v1/projects/<int:project_id>/assignments/', include('assignment.urls')),|" /doccano/backend/config/urls.py; \
    fi

# Integrate tracking URLs (for simple tracking system)
RUN if ! grep -q "assignment.tracking_urls" /doccano/backend/config/urls.py; then \
        sed -i "s|path('v1/projects/<int:project_id>/assignments/', include('assignment.urls')),|path('v1/projects/<int:project_id>/assignments/', include('assignment.urls')),\n    # Monlam: Simple Tracking API (approve/reject, visibility)\n    path('v1/projects/<int:project_id>/tracking/', include('assignment.tracking_urls')),|" /doccano/backend/config/urls.py; \
    fi

# NOTE: Visibility filtering not auto-applied (requires manual patch to Doccano's views.py)
# For now, visibility will be handled client-side via JavaScript
# TODO: Create proper Python patch file for examples/views.py

# ============================================
# MONLAM UI - PROFESSIONAL DJANGO INTEGRATION
# ============================================
# Copy the Monlam UI app (Django views and templates)
COPY patches/monlam_ui /doccano/backend/monlam_ui

# Register the Monlam UI app in settings
RUN echo "INSTALLED_APPS += ['monlam_ui']" >> /doccano/backend/config/settings/base.py || true

# Integrate Monlam UI URLs into main urls.py
RUN if ! grep -q "monlam_ui.urls" /doccano/backend/config/urls.py; then \
        sed -i "s|urlpatterns = \[|urlpatterns = [\n    # Monlam: Enhanced UI for Completion Tracking\n    path('monlam/', include('monlam_ui.urls')),|" /doccano/backend/config/urls.py; \
    fi

# Add Monlam redirects for Doccano menu items (must be before Doccano's URLs)
# This redirects /projects/{id}/dataset → /monlam/{id}/dataset-enhanced/
# and /projects/{id}/metrics → /monlam/{id}/completion/
RUN if ! grep -q "monlam_ui.redirect_urls" /doccano/backend/config/urls.py; then \
        sed -i '1i from monlam_ui.redirect_urls import redirect_patterns' /doccano/backend/config/urls.py && \
        sed -i "s|urlpatterns = \[|urlpatterns = [\n    # Monlam: Redirect standard menu items to enhanced views\n    *redirect_patterns,|" /doccano/backend/config/urls.py; \
    fi

# Add MIME type configuration at the VERY START of base.py (before any imports)
RUN sed -i '1i # Monlam: Configure MIME types for JavaScript files BEFORE WhiteNoise loads\nimport mimetypes\nmimetypes.add_type("application/javascript", ".js", True)\n' /doccano/backend/config/settings/base.py

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
    chown doccano:doccano /doccano/backend/examples/visibility_mixin.py && \
    chown doccano:doccano /doccano/backend/config/whitenoise_config.py && \
    chown doccano:doccano /doccano/backend/config/apply_visibility_filter.py && \
    chown doccano:doccano /doccano/backend/config/auto_track_annotations.py && \
    chown doccano:doccano /doccano/backend/data_export/models.py && \
    chown doccano:doccano /doccano/backend/data_import/pipeline/catalog.py && \
    chown doccano:doccano /doccano/backend/data_import/datasets.py && \
    chown doccano:doccano /doccano/backend/data_import/pipeline/examples/speech_to_text/example.jsonl && \
    chown doccano:doccano /doccano/backend/data_import/pipeline/examples/image_classification/example.jsonl && \
    chown doccano:doccano /doccano/backend/client/dist/index.html && \
    chown doccano:doccano /doccano/backend/client/dist/200.html && \
    chown -R doccano:doccano /doccano/backend/assignment && \
    chown -R doccano:doccano /doccano/backend/monlam_ui

# ============================================
# MIGRATIONS NOTE
# ============================================
# Migrations cannot run during Docker build (no database connection)
# After deployment, run ONCE via Render Shell:
#   python manage.py migrate assignment --noinput
# 
# This will create:
# - assignment_assignment table (legacy)
# - annotation_tracking table (NEW - simple tracking system)
#   Tracks: who annotated, who reviewed, status, locking
# 
# Or use the manual migration command documented in README

# ============================================
# MONLAM FEATURES ARCHITECTURE
# ============================================
# Monlam UI provides a professional Django app integration:
# - Native Django views (not HTML injection)
# - Vue.js + Vuetify templates
# - RESTful APIs for data
# - Completion dashboard, enhanced dataset, annotation approval
# - Production-grade, maintainable, upgradeable
#
# Simple Tracking System (assignment/simple_tracking.py):
# - First-come-first-serve annotation (no complex assignments)
# - Example visibility filtering (hide annotated examples from others)
# - Example locking (5-minute lock to prevent conflicts)
# - Approve/reject workflow with database tracking
# - Dataset columns show tracking data (4th & 5th columns)
#
# Frontend enhancements in index.html/200.html:
# - Audio auto-loop (annotation pages only)
# - Dataset table enhancement (assignment columns)
# - Metrics page redirect (works on first click)
# - Approve/reject buttons (underneath label box)

USER doccano
WORKDIR /doccano/backend
