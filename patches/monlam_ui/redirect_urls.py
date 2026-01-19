"""
URL Redirects for Doccano Menu Items

DEPRECATED: This file is no longer used. Redirects are handled client-side in index.html.

All redirects are now handled by JavaScript in patches/frontend/index.html
which can check user roles and decide whether to redirect.

This file is kept for backwards compatibility with Dockerfile, but redirect_patterns
is empty and no longer used.
"""

from django.urls import path

# SERVER-SIDE REDIRECTS DISABLED
# Reason: Server-side redirects can't "pass through" to Doccano's original views
#         This breaks Project Admins who need the original dataset page
#
# Solution: Client-side redirects ONLY (in index.html)
#          Client-side can check user roles and decide whether to redirect
#
redirect_patterns = [
    # Empty list - no server-side redirects
    # All redirects handled by JavaScript in patches/frontend/index.html
]

