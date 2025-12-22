"""
Patched datasets.py for Doccano with proper STT JSONL import support.

This file replaces /doccano/backend/data_import/datasets.py
Adds Speech2TextJsonlDataset for importing JSONL with audio URLs and transcripts.
"""

import abc
from typing import List, Type

from django.contrib.auth.models import User

from .models import DummyLabelType
from .pipeline.catalog import RELATION_EXTRACTION, Format
from .pipeline.data import BaseData, BinaryData, TextData
from .pipeline.examples import Examples
from .pipeline.exceptions import FileParseException
from .pipeline.factories import create_parser
from .pipeline.label import CategoryLabel, Label, RelationLabel, SpanLabel, TextLabel
from .pipeline.label_types import LabelTypes
from .pipeline.labels import Categories, Labels, Relations, Spans, Texts
from .pipeline.makers import BinaryExampleMaker, ExampleMaker, LabelMaker
from .pipeline.readers import (
    DEFAULT_LABEL_COLUMN,
    DEFAULT_TEXT_COLUMN,
    FileName,
    Reader,
)
from label_types.models import CategoryType, LabelType, RelationType, SpanType
from projects.models import Project, ProjectType

import pandas as pd
from pydantic import UUID4
from examples.models import Example


class Dataset(abc.ABC):
    def __init__(self, reader: Reader, project: Project, **kwargs):
        self.reader = reader
        self.project = project
        self.kwargs = kwargs

    def save(self, user: User, batch_size: int = 1000):
        raise NotImplementedError()

    @property
    def errors(self) -> List[FileParseException]:
        raise NotImplementedError()


class PlainDataset(Dataset):
    def __init__(self, reader: Reader, project: Project, **kwargs):
        super().__init__(reader, project, **kwargs)
        self.example_maker = ExampleMaker(project=project, data_class=TextData)

    def save(self, user: User, batch_size: int = 1000):
        for records in self.reader.batch(batch_size):
            examples = Examples(self.example_maker.make(records))
            examples.save()

    @property
    def errors(self) -> List[FileParseException]:
        return self.reader.errors + self.example_maker.errors


class DatasetWithSingleLabelType(Dataset):
    data_class: Type[BaseData]
    label_class: Type[Label]
    label_type = LabelType
    labels_class = Labels

    def __init__(self, reader: Reader, project: Project, **kwargs):
        super().__init__(reader, project, **kwargs)
        self.types = LabelTypes(self.label_type)
        self.example_maker = ExampleMaker(
            project=project,
            data_class=self.data_class,
            column_data=kwargs.get("column_data") or DEFAULT_TEXT_COLUMN,
            exclude_columns=[kwargs.get("column_label") or DEFAULT_LABEL_COLUMN],
        )
        self.label_maker = LabelMaker(
            column=kwargs.get("column_label") or DEFAULT_LABEL_COLUMN, label_class=self.label_class
        )

    def save(self, user: User, batch_size: int = 1000):
        for records in self.reader.batch(batch_size):
            # create examples
            examples = Examples(self.example_maker.make(records))
            examples.save()

            # create label types
            labels = self.labels_class(self.label_maker.make(records), self.types)
            labels.clean(self.project)
            labels.save_types(self.project)

            # create Labels
            labels.save(user, examples)

    @property
    def errors(self) -> List[FileParseException]:
        return self.reader.errors + self.example_maker.errors + self.label_maker.errors


class BinaryDataset(Dataset):
    def __init__(self, reader: Reader, project: Project, **kwargs):
        super().__init__(reader, project, **kwargs)
        self.example_maker = BinaryExampleMaker(project=project, data_class=BinaryData)

    def save(self, user: User, batch_size: int = 1000):
        for records in self.reader.batch(batch_size):
            examples = Examples(self.example_maker.make(records))
            examples.save()

    @property
    def errors(self) -> List[FileParseException]:
        return self.reader.errors + self.example_maker.errors


# ============================================================================
# MONLAM PATCH: Speech2Text JSONL Dataset
# ============================================================================

class Speech2TextData(BaseData):
    """Custom data class for STT that properly handles audio URL and transcript."""
    text: str = ""
    
    @classmethod
    def parse(cls, example_uuid: UUID4, filename: str, upload_name: str, text: str = "", **kwargs):
        """Parse STT record - filename is the audio URL, text is the transcript."""
        # Extract meta from remaining kwargs (excluding internal columns)
        meta = kwargs.pop('meta', {})
        # Also include any other fields as meta
        for key in list(kwargs.keys()):
            if key not in ['#line_number', 'label']:
                meta[key] = kwargs.pop(key, None)
        
        return cls(
            uuid=example_uuid,
            filename=filename,  # Audio URL
            upload_name=upload_name,
            text=text,  # Transcript text
            meta=meta
        )

    def create(self, project: Project) -> Example:
        return Example(
            uuid=self.uuid,
            project=project,
            filename=self.filename,  # Audio URL stored here
            upload_name=self.upload_name,
            text=self.text,  # Transcript stored here
            meta=self.meta,
        )


class Speech2TextExampleMaker:
    """
    Custom ExampleMaker for Speech2Text that:
    - Uses 'filename' field as audio URL (Example.filename)
    - Uses 'text' field as transcript (Example.text)
    - Does NOT remap columns like standard ExampleMaker
    """
    
    def __init__(self, project: Project):
        self.project = project
        self._errors: List[FileParseException] = []

    def make(self, df: pd.DataFrame) -> List[Example]:
        examples = []
        for row in df.to_dict(orient="records"):
            try:
                # Get uuid and upload_name from reader
                example_uuid = row.pop('example_uuid')
                upload_name = row.pop('upload_name', '')
                
                # Get audio URL - prefer 'filename' from JSONL, fallback to reader's filename
                audio_url = row.pop('filename', '')
                
                # Get transcript text
                transcript = row.pop('text', '')
                
                # Get meta if present
                meta = row.pop('meta', {})
                
                # Add remaining fields to meta (except internal ones)
                for key, value in row.items():
                    if key not in ['#line_number', 'label']:
                        meta[key] = value
                
                # Create data and example
                data = Speech2TextData(
                    uuid=example_uuid,
                    filename=audio_url,
                    upload_name=upload_name,
                    text=transcript,
                    meta=meta
                )
                example = data.create(self.project)
                examples.append(example)
                
            except Exception as e:
                from .pipeline.exceptions import FileParseException
                error = FileParseException(
                    row.get('upload_name', 'unknown'),
                    row.get('#line_number', 0),
                    str(e)
                )
                self._errors.append(error)
                
        return examples

    @property
    def errors(self) -> List[FileParseException]:
        return self._errors


class Speech2TextLabelMaker:
    """
    Custom LabelMaker for STT that creates TextLabels from the 'label' or 'text' field.
    """
    
    def __init__(self):
        self._errors: List[FileParseException] = []
    
    def make(self, df: pd.DataFrame) -> List[TextLabel]:
        labels = []
        
        for row in df.to_dict(orient="records"):
            example_uuid = row.get('example_uuid')
            
            # Prefer 'label' field, fallback to 'text'
            label_text = row.get('label') or row.get('text', '')
            
            if label_text and example_uuid:
                # TextLabel expects example_uuid, not uuid (uuid is auto-generated)
                label = TextLabel(example_uuid=example_uuid, text=label_text)
                labels.append(label)
        
        return labels
    
    @property
    def errors(self) -> List[FileParseException]:
        return self._errors


class Speech2TextJsonlDataset(Dataset):
    """
    Dataset for importing STT data from JSONL with the format:
    {"filename": "https://audio.url/file.wav", "text": "transcript", "label": "transcript", "meta": {...}}
    
    - 'filename': Audio URL (stored in Example.filename)
    - 'text': Transcript (stored in Example.text) 
    - 'label': Label text for TextLabel annotation (created by celery_tasks.py after import)
    - 'meta': Additional metadata
    
    Note: TextLabels are created automatically by the patched celery_tasks.py
    after the import completes successfully.
    """
    
    def __init__(self, reader: Reader, project: Project, **kwargs):
        super().__init__(reader, project, **kwargs)
        self.example_maker = Speech2TextExampleMaker(project=project)

    def save(self, user: User, batch_size: int = 1000):
        # Only create examples - TextLabels are created by celery_tasks.py patch
        for records in self.reader.batch(batch_size):
            examples = Examples(self.example_maker.make(records))
            examples.save()

    @property
    def errors(self) -> List[FileParseException]:
        return self.reader.errors + self.example_maker.errors


# ============================================================================
# MONLAM PATCH: Image Classification JSONL Dataset
# ============================================================================

class ImageClassificationData(BaseData):
    """Custom data class for Image Classification that handles image URLs."""
    
    @classmethod
    def parse(cls, example_uuid: UUID4, filename: str, upload_name: str, **kwargs):
        """Parse image record - filename is the image URL."""
        meta = kwargs.pop('meta', {})
        for key in list(kwargs.keys()):
            if key not in ['#line_number', 'label']:
                meta[key] = kwargs.pop(key, None)
        
        return cls(
            uuid=example_uuid,
            filename=filename,  # Image URL
            upload_name=upload_name,
            meta=meta
        )

    def create(self, project: Project) -> Example:
        return Example(
            uuid=self.uuid,
            project=project,
            filename=self.filename,  # Image URL stored here
            upload_name=self.upload_name,
            meta=self.meta,
        )


class ImageClassificationExampleMaker:
    """
    Custom ExampleMaker for Image Classification that:
    - Uses 'filename' field as image URL (Example.filename)
    """
    
    def __init__(self, project: Project):
        self.project = project
        self._errors: List[FileParseException] = []

    def make(self, df: pd.DataFrame) -> List[Example]:
        examples = []
        for row in df.to_dict(orient="records"):
            try:
                example_uuid = row.pop('example_uuid')
                upload_name = row.pop('upload_name', '')
                
                # Get image URL from 'filename' field
                image_url = row.pop('filename', '')
                
                meta = row.pop('meta', {})
                for key, value in row.items():
                    if key not in ['#line_number', 'label']:
                        meta[key] = value
                
                data = ImageClassificationData(
                    uuid=example_uuid,
                    filename=image_url,
                    upload_name=upload_name,
                    meta=meta
                )
                example = data.create(self.project)
                examples.append(example)
                
            except Exception as e:
                from .pipeline.exceptions import FileParseException
                error = FileParseException(
                    row.get('upload_name', 'unknown'),
                    row.get('#line_number', 0),
                    str(e)
                )
                self._errors.append(error)
                
        return examples

    @property
    def errors(self) -> List[FileParseException]:
        return self._errors


class ImageClassificationLabelMaker:
    """
    Custom LabelMaker for Image Classification that creates CategoryLabels from the 'label' field.
    """
    
    def __init__(self):
        self._errors: List[FileParseException] = []
    
    def make(self, df: pd.DataFrame) -> List[CategoryLabel]:
        labels = []
        
        # Explode label arrays
        df_labels = df.explode('label')
        
        for row in df_labels.to_dict(orient="records"):
            example_uuid = row.get('example_uuid')
            label_text = row.get('label', '')
            
            if label_text and example_uuid:
                label = CategoryLabel(example_uuid=example_uuid, label=label_text)
                labels.append(label)
        
        return labels
    
    @property
    def errors(self) -> List[FileParseException]:
        return self._errors


class ImageClassificationJsonlDataset(Dataset):
    """
    Dataset for importing Image Classification data from JSONL with format:
    {"filename": "https://image.url/file.jpg", "label": ["cat", "animal"], "meta": {...}}
    
    - 'filename': Image URL (stored in Example.filename)
    - 'label': Category labels (array of strings)
    - 'meta': Additional metadata
    """
    
    def __init__(self, reader: Reader, project: Project, **kwargs):
        super().__init__(reader, project, **kwargs)
        self.example_maker = ImageClassificationExampleMaker(project=project)
        self.label_maker = ImageClassificationLabelMaker()
        self.types = LabelTypes(CategoryType)

    def save(self, user: User, batch_size: int = 1000):
        for records in self.reader.batch(batch_size):
            # Create examples
            examples = Examples(self.example_maker.make(records))
            examples.save()
            
            # Create category labels
            labels = Categories(self.label_maker.make(records), self.types)
            labels.clean(self.project)
            labels.save_types(self.project)
            labels.save(user, examples)

    @property
    def errors(self) -> List[FileParseException]:
        return self.reader.errors + self.example_maker.errors + self.label_maker.errors


# ============================================================================
# END MONLAM PATCH
# ============================================================================


class TextClassificationDataset(DatasetWithSingleLabelType):
    data_class = TextData
    label_class = CategoryLabel
    label_type = CategoryType
    labels_class = Categories


class SequenceLabelingDataset(DatasetWithSingleLabelType):
    data_class = TextData
    label_class = SpanLabel
    label_type = SpanType
    labels_class = Spans


class Seq2seqDataset(DatasetWithSingleLabelType):
    data_class = TextData
    label_class = TextLabel
    label_type = DummyLabelType
    labels_class = Texts


class RelationExtractionDataset(Dataset):
    def __init__(self, reader: Reader, project: Project, **kwargs):
        super().__init__(reader, project, **kwargs)
        self.span_types = LabelTypes(SpanType)
        self.relation_types = LabelTypes(RelationType)
        self.example_maker = ExampleMaker(
            project=project,
            data_class=TextData,
            column_data=kwargs.get("column_data") or DEFAULT_TEXT_COLUMN,
            exclude_columns=["entities", "relations"],
        )
        self.span_maker = LabelMaker(column="entities", label_class=SpanLabel)
        self.relation_maker = LabelMaker(column="relations", label_class=RelationLabel)

    def save(self, user: User, batch_size: int = 1000):
        for records in self.reader.batch(batch_size):
            # create examples
            examples = Examples(self.example_maker.make(records))
            examples.save()

            # create label types
            spans = Spans(self.span_maker.make(records), self.span_types)
            spans.clean(self.project)
            spans.save_types(self.project)

            relations = Relations(self.relation_maker.make(records), self.relation_types)
            relations.clean(self.project)
            relations.save_types(self.project)

            # create Labels
            spans.save(user, examples)
            relations.save(user, examples, spans=spans)

    @property
    def errors(self) -> List[FileParseException]:
        return self.reader.errors + self.example_maker.errors + self.span_maker.errors + self.relation_maker.errors


class CategoryAndSpanDataset(Dataset):
    def __init__(self, reader: Reader, project: Project, **kwargs):
        super().__init__(reader, project, **kwargs)
        self.category_types = LabelTypes(CategoryType)
        self.span_types = LabelTypes(SpanType)
        self.example_maker = ExampleMaker(
            project=project,
            data_class=TextData,
            column_data=kwargs.get("column_data") or DEFAULT_TEXT_COLUMN,
            exclude_columns=["cats", "entities"],
        )
        self.category_maker = LabelMaker(column="cats", label_class=CategoryLabel)
        self.span_maker = LabelMaker(column="entities", label_class=SpanLabel)

    def save(self, user: User, batch_size: int = 1000):
        for records in self.reader.batch(batch_size):
            # create examples
            examples = Examples(self.example_maker.make(records))
            examples.save()

            # create label types
            categories = Categories(self.category_maker.make(records), self.category_types)
            categories.clean(self.project)
            categories.save_types(self.project)

            spans = Spans(self.span_maker.make(records), self.span_types)
            spans.clean(self.project)
            spans.save_types(self.project)

            # create Labels
            categories.save(user, examples)
            spans.save(user, examples)

    @property
    def errors(self) -> List[FileParseException]:
        return self.reader.errors + self.example_maker.errors + self.category_maker.errors + self.span_maker.errors


def select_dataset(project: Project, task: str, file_format: Format) -> Type[Dataset]:
    mapping = {
        ProjectType.DOCUMENT_CLASSIFICATION: TextClassificationDataset,
        ProjectType.SEQUENCE_LABELING: SequenceLabelingDataset,
        RELATION_EXTRACTION: RelationExtractionDataset,
        ProjectType.SEQ2SEQ: Seq2seqDataset,
        ProjectType.INTENT_DETECTION_AND_SLOT_FILLING: CategoryAndSpanDataset,
        ProjectType.IMAGE_CLASSIFICATION: BinaryDataset,
        ProjectType.IMAGE_CAPTIONING: BinaryDataset,
        ProjectType.BOUNDING_BOX: BinaryDataset,
        ProjectType.SEGMENTATION: BinaryDataset,
        ProjectType.SPEECH2TEXT: BinaryDataset,
    }
    if task not in mapping:
        task = project.project_type
    
    # MONLAM PATCH: Use Speech2TextJsonlDataset for STT with JSONL format
    if project.project_type == ProjectType.SPEECH2TEXT and file_format.name == 'JSONL':
        return Speech2TextJsonlDataset
    
    # MONLAM PATCH: Use ImageClassificationJsonlDataset for Image Classification with JSONL format
    if project.project_type == ProjectType.IMAGE_CLASSIFICATION and file_format.name == 'JSONL':
        return ImageClassificationJsonlDataset
    
    if project.is_text_project and file_format.is_plain_text():
        return PlainDataset
    return mapping[task]


def load_dataset(task: str, file_format: Format, data_files: List[FileName], project: Project, **kwargs) -> Dataset:
    parser = create_parser(file_format, **kwargs)
    reader = Reader(data_files, parser)
    dataset_class = select_dataset(project, task, file_format)
    return dataset_class(reader, project, **kwargs)

