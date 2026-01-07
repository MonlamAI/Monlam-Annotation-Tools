"""
Upload API views for JSON file imports.
"""

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from apps.projects.models import Project
from apps.projects.permissions import IsProjectMember
from .upload import JSONUploadHandler


class ExampleUploadView(APIView):
    """
    API endpoint for uploading JSON files to import examples.
    
    POST /api/v1/projects/{project_id}/examples/upload
    
    Request body (multipart/form-data):
        - file: JSON or JSONL file
        - format: 'json' or 'jsonl' (default: 'json')
    
    JSON file format examples:
    
    1. Array format:
    [
        {"text": "Hello", "audio_url": "https://s3.amazonaws.com/bucket/audio.mp3"},
        {"sentence": "World", "audio": "https://s3.amazonaws.com/bucket/audio2.mp3"}
    ]
    
    2. Wrapped format:
    {
        "examples": [
            {"text": "Hello", "audio_url": "https://s3.amazonaws.com/bucket/audio.mp3"}
        ]
    }
    
    3. JSONL format (one object per line):
    {"text": "Hello", "audio_url": "https://s3.amazonaws.com/bucket/audio.mp3"}
    {"text": "World", "audio_url": "https://s3.amazonaws.com/bucket/audio2.mp3"}
    """
    
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated, IsProjectMember]
    
    def post(self, request, project_id):
        """Handle file upload."""
        project = get_object_or_404(Project, pk=project_id)
        
        # Check permission
        self.check_object_permissions(request, project)
        
        # Get uploaded file
        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            return Response(
                {'error': 'No file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate file extension
        filename = uploaded_file.name.lower()
        if not (filename.endswith('.json') or filename.endswith('.jsonl')):
            return Response(
                {'error': 'Invalid file format. Please upload a .json or .jsonl file'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Determine format
        file_format = request.data.get('format', 'json')
        if filename.endswith('.jsonl'):
            file_format = 'jsonl'
        
        # Read file content
        try:
            file_content = uploaded_file.read().decode('utf-8')
        except UnicodeDecodeError:
            return Response(
                {'error': 'File encoding error. Please ensure the file is UTF-8 encoded'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Process upload
        handler = JSONUploadHandler(project)
        result = handler.import_examples(file_content, file_format, user=request.user)
        
        if result['success']:
            return Response({
                'message': f"Successfully imported {result['imported']} examples",
                'imported': result['imported'],
                'total_records': result.get('total_records', result['imported']),
                'errors': result['errors']
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'error': 'Import failed',
                'imported': result['imported'],
                'errors': result['errors']
            }, status=status.HTTP_400_BAD_REQUEST)


class ExampleUploadPreviewView(APIView):
    """
    Preview JSON file content before importing.
    
    POST /api/v1/projects/{project_id}/examples/upload/preview
    """
    
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated, IsProjectMember]
    
    def post(self, request, project_id):
        """Preview file upload without importing."""
        project = get_object_or_404(Project, pk=project_id)
        self.check_object_permissions(request, project)
        
        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            return Response(
                {'error': 'No file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Determine format
        filename = uploaded_file.name.lower()
        file_format = 'jsonl' if filename.endswith('.jsonl') else 'json'
        
        try:
            file_content = uploaded_file.read().decode('utf-8')
        except UnicodeDecodeError:
            return Response(
                {'error': 'File encoding error'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        handler = JSONUploadHandler(project)
        records = handler.parse_file(file_content, file_format)
        
        # Return preview (first 10 records)
        preview_records = []
        for i, record in enumerate(records[:10]):
            validated = handler.validate_record(record, i)
            if validated:
                preview_records.append({
                    'text': validated['text'][:200] + ('...' if len(validated['text']) > 200 else ''),
                    'audio_url': validated['meta'].get('audio_url', ''),
                    'meta_keys': list(validated['meta'].keys())
                })
        
        return Response({
            'total_records': len(records),
            'preview': preview_records,
            'errors': handler.errors,
            'format': file_format
        })

