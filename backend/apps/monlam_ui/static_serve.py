"""
Custom static file serving for Vue.js assets.
This ensures files are served with correct MIME types.
"""

import os
import mimetypes
import logging
from pathlib import Path

from django.http import HttpResponse, Http404, FileResponse
from django.conf import settings

logger = logging.getLogger(__name__)

# Initialize mimetypes with common web types
mimetypes.add_type('application/javascript', '.js')
mimetypes.add_type('application/javascript', '.mjs')
mimetypes.add_type('text/css', '.css')
mimetypes.add_type('font/woff', '.woff')
mimetypes.add_type('font/woff2', '.woff2')
mimetypes.add_type('font/ttf', '.ttf')
mimetypes.add_type('font/eot', '.eot')
mimetypes.add_type('image/svg+xml', '.svg')
mimetypes.add_type('image/png', '.png')
mimetypes.add_type('image/x-icon', '.ico')


def get_vue_dist_path():
    """Get the Vue dist directory path."""
    return Path(settings.BASE_DIR) / 'static' / 'dist'


def try_serve_static(request):
    """
    Try to serve a static file from Vue dist.
    Returns None if file doesn't exist.
    """
    vue_dist = get_vue_dist_path()
    request_path = request.path.lstrip('/')
    
    logger.info(f"try_serve_static: request.path={request.path}, request_path={request_path}")
    
    file_path = vue_dist / request_path
    
    # Security: prevent directory traversal
    try:
        file_path = file_path.resolve()
        vue_dist_resolved = vue_dist.resolve()
        if not str(file_path).startswith(str(vue_dist_resolved)):
            logger.warning(f"Directory traversal attempt: {request_path}")
            return None
    except (ValueError, OSError):
        return None
    
    if not file_path.exists() or not file_path.is_file():
        logger.info(f"File not found: {file_path}")
        return None
    
    # Determine content type
    content_type, _ = mimetypes.guess_type(str(file_path))
    if content_type is None:
        content_type = 'application/octet-stream'
    
    logger.info(f"Serving {file_path} as {content_type}")
    
    # Serve the file
    response = FileResponse(open(file_path, 'rb'), content_type=content_type)
    response['Content-Length'] = file_path.stat().st_size
    
    # Cache headers for production
    if not settings.DEBUG:
        response['Cache-Control'] = 'public, max-age=31536000, immutable'
    
    return response


def serve_vue_asset(request, path, subdir=''):
    """
    Serve a file from the Vue dist directory.
    
    Args:
        request: Django request
        path: File path relative to the subdir
        subdir: Subdirectory within Vue dist (e.g., 'assets', 'fonts')
    """
    logger.info(f"serve_vue_asset called: path={path}, subdir={subdir}")
    vue_dist = get_vue_dist_path()
    logger.info(f"Vue dist path: {vue_dist}, exists: {vue_dist.exists()}")
    
    if subdir:
        file_path = vue_dist / subdir / path
    else:
        file_path = vue_dist / path
    
    # Security: prevent directory traversal
    try:
        file_path = file_path.resolve()
        vue_dist_resolved = vue_dist.resolve()
        if not str(file_path).startswith(str(vue_dist_resolved)):
            raise Http404("File not found")
    except (ValueError, OSError):
        raise Http404("File not found")
    
    if not file_path.exists() or not file_path.is_file():
        raise Http404(f"File not found: {path}")
    
    # Determine content type
    content_type, _ = mimetypes.guess_type(str(file_path))
    if content_type is None:
        content_type = 'application/octet-stream'
    
    # Serve the file
    response = FileResponse(open(file_path, 'rb'), content_type=content_type)
    response['Content-Length'] = file_path.stat().st_size
    
    # Cache headers for production
    if not settings.DEBUG:
        # Cache for 1 year (files are hashed by Vite)
        response['Cache-Control'] = 'public, max-age=31536000, immutable'
    
    return response


def serve_assets(request, path):
    """Serve files from /assets/"""
    return serve_vue_asset(request, path, subdir='assets')


def serve_fonts(request, path):
    """Serve files from /fonts/"""
    return serve_vue_asset(request, path, subdir='fonts')


def serve_root_file(request, path):
    """Serve files from Vue dist root (favicon, logo, etc.)"""
    return serve_vue_asset(request, path, subdir='')

