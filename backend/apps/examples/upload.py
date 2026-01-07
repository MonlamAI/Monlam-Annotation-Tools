"""
JSON Upload handler for importing examples with S3 audio links.
Supports various JSON formats including:
- Array of objects with 'text', 'audio_url', 'data' fields
- JSONL format (one JSON object per line)
"""

import json
import uuid
from typing import Any, Dict, List, Optional
from django.db import transaction
from django.utils import timezone


class JSONUploadHandler:
    """Handles JSON file uploads for importing examples."""
    
    SUPPORTED_FORMATS = ['json', 'jsonl']
    
    def __init__(self, project):
        self.project = project
        self.errors = []
        self.imported_count = 0
    
    def parse_file(self, file_content: str, format: str = 'json') -> List[Dict[str, Any]]:
        """Parse uploaded file content based on format."""
        records = []
        
        if format == 'jsonl':
            for line_num, line in enumerate(file_content.strip().split('\n'), 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    records.append(record)
                except json.JSONDecodeError as e:
                    self.errors.append(f"Line {line_num}: Invalid JSON - {str(e)}")
        else:  # json
            try:
                data = json.loads(file_content)
                if isinstance(data, list):
                    records = data
                elif isinstance(data, dict):
                    # Single record or wrapped format
                    if 'examples' in data:
                        records = data['examples']
                    elif 'data' in data and isinstance(data['data'], list):
                        records = data['data']
                    else:
                        records = [data]
            except json.JSONDecodeError as e:
                self.errors.append(f"Invalid JSON file: {str(e)}")
        
        return records
    
    def validate_record(self, record: Dict[str, Any], index: int) -> Optional[Dict[str, Any]]:
        """Validate and normalize a single record."""
        # Handle different field names for text
        text = record.get('text') or record.get('sentence') or record.get('content') or record.get('label', '')
        
        # Handle different field names for audio URL
        # Note: 'filename' is commonly used in Doccano STT format for remote URLs
        audio_url = (
            record.get('audio_url') or 
            record.get('audio') or 
            record.get('audio_link') or 
            record.get('filename') or  # Doccano STT format uses 'filename' for remote URLs
            record.get('file_name') or
            record.get('s3_url') or
            ''
        )
        
        # Meta can contain additional fields
        meta = record.get('meta', {})
        if not isinstance(meta, dict):
            meta = {}
        
        # Add any extra fields to meta
        excluded_fields = {'text', 'sentence', 'content', 'audio_url', 'audio', 
                          'audio_link', 'file_name', 'meta', 'annotations', 'label', 'labels'}
        for key, value in record.items():
            if key not in excluded_fields:
                meta[key] = value
        
        # Store audio_url in meta for easy access
        if audio_url:
            meta['audio_url'] = audio_url
        
        if not text and not audio_url:
            self.errors.append(f"Record {index + 1}: Must have either 'text' or 'audio_url'")
            return None
        
        return {
            'text': text or '',
            'meta': meta,
            'uuid': str(uuid.uuid4()),
            'created_at': timezone.now(),
            'updated_at': timezone.now(),
        }
    
    @transaction.atomic
    def import_examples(self, file_content: str, format: str = 'json', user=None) -> Dict[str, Any]:
        """Import examples from file content."""
        from .models import Example
        
        records = self.parse_file(file_content, format)
        
        if not records:
            return {
                'success': False,
                'imported': 0,
                'errors': self.errors or ['No valid records found in file']
            }
        
        examples_to_create = []
        
        for index, record in enumerate(records):
            validated = self.validate_record(record, index)
            if validated:
                example = Example(
                    project=self.project,
                    text=validated['text'],
                    meta=validated['meta'],
                    uuid=validated['uuid'],
                    created_at=validated['created_at'],
                    updated_at=validated['updated_at'],
                )
                examples_to_create.append(example)
        
        if examples_to_create:
            Example.objects.bulk_create(examples_to_create)
            self.imported_count = len(examples_to_create)
            
            # Auto-create TextLabels for STT projects
            if self.project.project_type in ['speech_to_text', 'Speech2text']:
                try:
                    from .auto_labels import bulk_create_text_labels_for_project
                    labels_created = bulk_create_text_labels_for_project(self.project, user)
                    if labels_created > 0:
                        print(f"[Monlam] Auto-created {labels_created} TextLabels for STT import")
                except Exception as e:
                    print(f"[Monlam] Failed to auto-create TextLabels: {e}")
        
        return {
            'success': self.imported_count > 0,
            'imported': self.imported_count,
            'total_records': len(records),
            'errors': self.errors
        }


def get_audio_url_from_example(example) -> Optional[str]:
    """
    Extract audio URL from example metadata.
    Supports various S3 URL formats and local paths.
    """
    meta = example.meta or {}
    
    # Check various possible field names for audio URL
    audio_url = (
        meta.get('audio_url') or 
        meta.get('audio') or 
        meta.get('audio_link') or 
        meta.get('file_name') or
        meta.get('s3_url') or
        meta.get('media_url') or
        meta.get('sound_url')
    )
    
    return audio_url


def validate_s3_audio_url(url: str) -> bool:
    """Validate that URL is a valid S3 or audio URL."""
    if not url:
        return False
    
    # Accept S3 URLs, CloudFront URLs, and common audio formats
    valid_patterns = [
        's3.amazonaws.com',
        's3-',  # Regional S3 endpoints
        'cloudfront.net',
        '.mp3',
        '.wav',
        '.ogg',
        '.m4a',
        '.flac',
        '.webm',
        'audio/',  # Content-type style paths
    ]
    
    url_lower = url.lower()
    return any(pattern in url_lower for pattern in valid_patterns) or url.startswith(('http://', 'https://'))

