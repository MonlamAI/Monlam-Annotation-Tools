"""
Label serializers for API.
"""

from rest_framework import serializers

from .models import (
    CategoryType, SpanType, RelationType,
    Category, Span, TextLabel, Relation, BoundingBox
)


# ============================================
# Label Type Serializers
# ============================================

class CategoryTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoryType
        fields = [
            'id', 'text', 'tibetan_text', 'prefix_key', 'suffix_key',
            'background_color', 'text_color', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class SpanTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpanType
        fields = [
            'id', 'text', 'tibetan_text', 'prefix_key', 'suffix_key',
            'background_color', 'text_color', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class RelationTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = RelationType
        fields = [
            'id', 'text', 'tibetan_text', 'prefix_key', 'suffix_key',
            'background_color', 'text_color', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# ============================================
# Annotation Serializers
# ============================================

class CategorySerializer(serializers.ModelSerializer):
    label_text = serializers.CharField(source='label.text', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Category
        fields = [
            'id', 'example', 'label', 'label_text', 
            'user', 'username', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'created_at']


class SpanSerializer(serializers.ModelSerializer):
    label_text = serializers.CharField(source='label.text', read_only=True)
    label_color = serializers.CharField(source='label.background_color', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Span
        fields = [
            'id', 'example', 'label', 'label_text', 'label_color',
            'start_offset', 'end_offset',
            'user', 'username', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'created_at']


class TextLabelSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = TextLabel
        fields = [
            'id', 'example', 'text',
            'user', 'username', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'created_at']


class RelationSerializer(serializers.ModelSerializer):
    label_text = serializers.CharField(source='label.text', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Relation
        fields = [
            'id', 'example', 'label', 'label_text',
            'from_span', 'to_span',
            'user', 'username', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'created_at']


class BoundingBoxSerializer(serializers.ModelSerializer):
    label_text = serializers.CharField(source='label.text', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = BoundingBox
        fields = [
            'id', 'example', 'label', 'label_text',
            'x', 'y', 'width', 'height',
            'user', 'username', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'created_at']

