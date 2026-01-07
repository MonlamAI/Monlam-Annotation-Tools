"""
Project views for API.
"""

from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q

from .models import Project, Member, MemberRole
from .serializers import (
    ProjectSerializer, ProjectCreateSerializer, 
    MemberSerializer, MemberCreateSerializer
)
from .permissions import IsProjectMember, IsProjectAdmin, CanManageProject


class ProjectViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing projects.
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # Superusers can see all projects
        if user.is_superuser:
            return Project.objects.all()
        
        # Regular users see only their projects
        return Project.objects.filter(members__user=user).distinct()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ProjectCreateSerializer
        return ProjectSerializer
    
    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsProjectAdmin()]
        return [IsAuthenticated()]
    
    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        """List all members of a project."""
        project = self.get_object()
        members = project.members.all()
        serializer = MemberSerializer(members, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsProjectAdmin])
    def add_member(self, request, pk=None):
        """Add a member to the project."""
        project = self.get_object()
        serializer = MemberCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user_id = serializer.validated_data['user_id']
        
        # Check if already a member
        if Member.objects.filter(project=project, user_id=user_id).exists():
            return Response(
                {'error': 'User is already a member of this project.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer.save(project=project)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['delete'], url_path='remove-member/(?P<user_id>[^/.]+)',
            permission_classes=[IsAuthenticated, IsProjectAdmin])
    def remove_member(self, request, pk=None, user_id=None):
        """Remove a member from the project."""
        project = self.get_object()
        
        try:
            member = Member.objects.get(project=project, user_id=user_id)
            member.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Member.DoesNotExist:
            return Response(
                {'error': 'User is not a member of this project.'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['patch'], url_path='update-role/(?P<user_id>[^/.]+)',
            permission_classes=[IsAuthenticated, IsProjectAdmin])
    def update_role(self, request, pk=None, user_id=None):
        """Update a member's role."""
        project = self.get_object()
        new_role = request.data.get('role')
        
        if not new_role or new_role not in MemberRole.values:
            return Response(
                {'error': 'Invalid role.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            member = Member.objects.get(project=project, user_id=user_id)
            member.role = new_role
            member.save()
            serializer = MemberSerializer(member)
            return Response(serializer.data)
        except Member.DoesNotExist:
            return Response(
                {'error': 'User is not a member of this project.'},
                status=status.HTTP_404_NOT_FOUND
            )

