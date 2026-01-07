"""
Project serializers for API.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import Project, Member, MemberRole

User = get_user_model()


class MemberSerializer(serializers.ModelSerializer):
    """Serializer for project members."""
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    
    class Meta:
        model = Member
        fields = ['id', 'user_id', 'username', 'email', 'role', 
                  'can_annotate', 'can_review', 'can_see_all', 
                  'can_manage', 'is_admin', 'created_at']
        read_only_fields = ['id', 'created_at']


class MemberCreateSerializer(serializers.ModelSerializer):
    """Serializer for adding members to a project."""
    user_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Member
        fields = ['user_id', 'role']
    
    def validate_user_id(self, value):
        if not User.objects.filter(id=value).exists():
            raise serializers.ValidationError('User does not exist.')
        return value
    
    def create(self, validated_data):
        user_id = validated_data.pop('user_id')
        user = User.objects.get(id=user_id)
        return Member.objects.create(user=user, **validated_data)


class ProjectSerializer(serializers.ModelSerializer):
    """Serializer for project details."""
    created_by_username = serializers.CharField(
        source='created_by.username', 
        read_only=True
    )
    member_count = serializers.SerializerMethodField()
    current_user_role = serializers.SerializerMethodField()
    
    class Meta:
        model = Project
        fields = [
            'id', 'name', 'tibetan_name', 'description', 'project_type',
            'guideline', 'random_order', 'collaborative_annotation',
            'single_class_classification', 'allow_overlapping', 'grapheme_mode',
            'is_stt_project', 'created_at', 'updated_at', 
            'created_by', 'created_by_username', 'member_count',
            'current_user_role'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']
    
    def get_member_count(self, obj):
        return obj.members.count()
    
    def get_current_user_role(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        
        if request.user.is_superuser:
            return MemberRole.PROJECT_ADMIN
        
        member = obj.members.filter(user=request.user).first()
        return member.role if member else None


class ProjectCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new project."""
    
    class Meta:
        model = Project
        fields = [
            'name', 'tibetan_name', 'description', 'project_type',
            'guideline', 'random_order', 'collaborative_annotation',
            'single_class_classification', 'allow_overlapping', 'grapheme_mode'
        ]
    
    def create(self, validated_data):
        user = self.context['request'].user
        project = Project.objects.create(created_by=user, **validated_data)
        
        # Creator becomes Project Admin
        Member.objects.create(
            project=project,
            user=user,
            role=MemberRole.PROJECT_ADMIN
        )
        
        return project


class ProjectMinimalSerializer(serializers.ModelSerializer):
    """Minimal project serializer for embedding."""
    
    class Meta:
        model = Project
        fields = ['id', 'name', 'tibetan_name', 'project_type']

