"""
URL Patch for Review API

This file shows how to add the review endpoint to Doccano's URL configuration.
Since Doccano uses Django REST Framework routers, we can add this endpoint
by patching the examples app's URLs.

To integrate:
1. Copy this file to: /doccano/backend/examples/urls_patch.py
2. Modify /doccano/backend/examples/urls.py to include:
   from .urls_patch import add_review_urls
   add_review_urls(urlpatterns)

OR use Django's URL include pattern in the main config/urls.py:
   from examples.review_api import review_current_example_simple
   path('v1/projects/<int:project_id>/review-current/', review_current_example_simple, name='review-current'),
"""

def add_review_urls(urlpatterns):
    """Add review API URLs to existing urlpatterns"""
    from examples.review_api import review_current_example_simple, get_current_example
    
    # Add review endpoint
    urlpatterns.append(
        ('v1/projects/<int:project_id>/review-current/', review_current_example_simple, 'review-current')
    )
    
    # Optional: Add current example endpoint
    urlpatterns.append(
        ('v1/projects/<int:project_id>/current-example/', get_current_example, 'current-example')
    )
    
    return urlpatterns

