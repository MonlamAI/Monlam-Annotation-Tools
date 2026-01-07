"""
Label URL patterns.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    CategoryTypeViewSet, SpanTypeViewSet, RelationTypeViewSet,
    CategoryViewSet, SpanViewSet, TextLabelViewSet,
    RelationViewSet, BoundingBoxViewSet
)

# Label types router
label_type_router = DefaultRouter()
label_type_router.register('category-types', CategoryTypeViewSet, basename='category-type')
label_type_router.register('span-types', SpanTypeViewSet, basename='span-type')
label_type_router.register('relation-types', RelationTypeViewSet, basename='relation-type')

# Annotations router
annotation_router = DefaultRouter()
annotation_router.register('categories', CategoryViewSet, basename='category')
annotation_router.register('spans', SpanViewSet, basename='span')
annotation_router.register('text-labels', TextLabelViewSet, basename='text-label')
annotation_router.register('relations', RelationViewSet, basename='relation')
annotation_router.register('bounding-boxes', BoundingBoxViewSet, basename='bounding-box')

urlpatterns = [
    # Label types
    path('projects/<int:project_id>/', include(label_type_router.urls)),
    
    # Annotations on examples
    path('projects/<int:project_id>/examples/<int:example_id>/', include(annotation_router.urls)),
]

