# URL Patch for Assignment and Completion Tracking
# Add this to your main urls.py to register the assignment app endpoints

from django.urls import path, include

# Add to urlpatterns:
urlpatterns += [
    # Assignment and Completion Tracking APIs
    path('v1/projects/<int:project_id>/assignments/', include('assignment.urls')),
    
    # Tracking API (approve/reject/status/lock)
    path('v1/projects/<int:project_id>/tracking/', include('assignment.tracking_urls')),
]

