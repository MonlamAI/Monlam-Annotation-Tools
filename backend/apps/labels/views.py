"""
Label views for API.
"""

from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import (
    CategoryType, SpanType, RelationType,
    Category, Span, TextLabel, Relation, BoundingBox
)
from .serializers import (
    CategoryTypeSerializer, SpanTypeSerializer, RelationTypeSerializer,
    CategorySerializer, SpanSerializer, TextLabelSerializer,
    RelationSerializer, BoundingBoxSerializer
)
from apps.projects.models import Project
from apps.projects.permissions import IsProjectMember, IsProjectAdmin
from apps.examples.models import Example


# ============================================
# Label Type ViewSets
# ============================================

class CategoryTypeViewSet(viewsets.ModelViewSet):
    """ViewSet for managing category types."""
    serializer_class = CategoryTypeSerializer
    permission_classes = [IsAuthenticated, IsProjectMember]
    
    def get_queryset(self):
        project_id = self.kwargs.get('project_id')
        return CategoryType.objects.filter(project_id=project_id)
    
    def perform_create(self, serializer):
        project = get_object_or_404(Project, id=self.kwargs['project_id'])
        serializer.save(project=project)


class SpanTypeViewSet(viewsets.ModelViewSet):
    """ViewSet for managing span types."""
    serializer_class = SpanTypeSerializer
    permission_classes = [IsAuthenticated, IsProjectMember]
    
    def get_queryset(self):
        project_id = self.kwargs.get('project_id')
        return SpanType.objects.filter(project_id=project_id)
    
    def perform_create(self, serializer):
        project = get_object_or_404(Project, id=self.kwargs['project_id'])
        serializer.save(project=project)


class RelationTypeViewSet(viewsets.ModelViewSet):
    """ViewSet for managing relation types."""
    serializer_class = RelationTypeSerializer
    permission_classes = [IsAuthenticated, IsProjectMember]
    
    def get_queryset(self):
        project_id = self.kwargs.get('project_id')
        return RelationType.objects.filter(project_id=project_id)
    
    def perform_create(self, serializer):
        project = get_object_or_404(Project, id=self.kwargs['project_id'])
        serializer.save(project=project)


# ============================================
# Annotation ViewSets
# ============================================

class AnnotationViewSetMixin:
    """Common functionality for annotation viewsets."""
    permission_classes = [IsAuthenticated, IsProjectMember]
    
    def get_example(self):
        return get_object_or_404(
            Example,
            id=self.kwargs['example_id'],
            project_id=self.kwargs['project_id']
        )
    
    def perform_create(self, serializer):
        example = self.get_example()
        serializer.save(example=example, user=self.request.user)


class CategoryViewSet(AnnotationViewSetMixin, viewsets.ModelViewSet):
    """ViewSet for category annotations."""
    serializer_class = CategorySerializer
    
    def get_queryset(self):
        return Category.objects.filter(
            example_id=self.kwargs['example_id'],
            example__project_id=self.kwargs['project_id']
        )


class SpanViewSet(AnnotationViewSetMixin, viewsets.ModelViewSet):
    """ViewSet for span annotations."""
    serializer_class = SpanSerializer
    
    def get_queryset(self):
        return Span.objects.filter(
            example_id=self.kwargs['example_id'],
            example__project_id=self.kwargs['project_id']
        )


class TextLabelViewSet(AnnotationViewSetMixin, viewsets.ModelViewSet):
    """ViewSet for text label annotations."""
    serializer_class = TextLabelSerializer
    
    def get_queryset(self):
        return TextLabel.objects.filter(
            example_id=self.kwargs['example_id'],
            example__project_id=self.kwargs['project_id']
        )


class RelationViewSet(AnnotationViewSetMixin, viewsets.ModelViewSet):
    """ViewSet for relation annotations."""
    serializer_class = RelationSerializer
    
    def get_queryset(self):
        return Relation.objects.filter(
            example_id=self.kwargs['example_id'],
            example__project_id=self.kwargs['project_id']
        )


class BoundingBoxViewSet(AnnotationViewSetMixin, viewsets.ModelViewSet):
    """ViewSet for bounding box annotations."""
    serializer_class = BoundingBoxSerializer
    
    def get_queryset(self):
        return BoundingBox.objects.filter(
            example_id=self.kwargs['example_id'],
            example__project_id=self.kwargs['project_id']
        )

