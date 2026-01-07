"""
Debug middleware to log all incoming requests.
"""

import logging

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware:
    """
    Middleware that logs every incoming request.
    This helps debug which requests are actually reaching Django.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Log the incoming request
        logger.warning(f"INCOMING REQUEST: {request.method} {request.path} (full: {request.get_full_path()})")
        
        response = self.get_response(request)
        
        # Log the response
        logger.warning(f"RESPONSE: {request.path} -> {response.status_code} {response.get('Content-Type', 'unknown')}")
        
        return response

