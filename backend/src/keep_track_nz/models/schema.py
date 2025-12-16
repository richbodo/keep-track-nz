"""Data models that mirror the TypeScript schema for government actions."""

from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
import re


class SourceSystem(str, Enum):
    """Source system enum matching TypeScript SourceSystem."""
    PARLIAMENT = "PARLIAMENT"
    LEGISLATION = "LEGISLATION"
    GAZETTE = "GAZETTE"
    BEEHIVE = "BEEHIVE"


class StageHistory(BaseModel):
    """Stage history for parliamentary bills."""
    stage: str = Field(..., min_length=1, description="Name of the parliamentary stage")
    date: str = Field(..., description="Date of the stage in YYYY-MM-DD format")

    @field_validator('date')
    @classmethod
    def validate_date_format(cls, v):
        """Validate date is in correct format."""
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError('Date must be in YYYY-MM-DD format')


class ActionMetadata(BaseModel):
    """Metadata for government actions, varying by source system."""
    # Parliament-specific fields
    bill_number: Optional[str] = Field(None, description="Bill number for Parliament actions")
    parliament_number: Optional[int] = Field(None, description="Parliament number")
    stage_history: Optional[List[StageHistory]] = Field(None, description="Bill stage progression")

    # Legislation-specific fields
    act_number: Optional[str] = Field(None, description="Act number for legislation")
    commencement_date: Optional[str] = Field(None, description="Date act commenced")

    # Gazette-specific fields
    notice_number: Optional[str] = Field(None, description="Gazette notice number")
    notice_type: Optional[str] = Field(None, description="Type of gazette notice")

    # Common fields
    document_type: Optional[str] = Field(None, description="Type of document")
    portfolio: Optional[str] = Field(None, description="Government portfolio")

    @field_validator('commencement_date')
    @classmethod
    def validate_commencement_date(cls, v):
        """Validate commencement date format."""
        if v is not None:
            try:
                datetime.strptime(v, '%Y-%m-%d')
                return v
            except ValueError:
                raise ValueError('Commencement date must be in YYYY-MM-DD format')
        return v


class GovernmentAction(BaseModel):
    """Main model for government actions, matching TypeScript interface."""
    id: str = Field(..., description="Unique identifier for the action")
    title: str = Field(..., description="Title of the government action")
    date: str = Field(..., description="Date of the action in YYYY-MM-DD format")
    source_system: SourceSystem = Field(..., description="Source system that provided this action")
    url: str = Field(..., description="URL to the original source document")
    primary_entity: str = Field(..., description="Primary person or entity responsible")
    summary: str = Field(..., description="Summary of the action")
    labels: List[str] = Field(default_factory=list, description="Classification labels")
    metadata: ActionMetadata = Field(default_factory=ActionMetadata, description="Source-specific metadata")

    @field_validator('date')
    @classmethod
    def validate_date_format(cls, v):
        """Validate date is in correct format."""
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError('Date must be in YYYY-MM-DD format')

    @field_validator('url')
    @classmethod
    def validate_url(cls, v):
        """Validate URL format."""
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        if not url_pattern.match(v):
            raise ValueError('Invalid URL format')
        return v

    @field_validator('id')
    @classmethod
    def validate_id_format(cls, v):
        """Validate ID follows expected pattern."""
        # ID should be in format: {source_prefix}-{year}-{number}
        if not re.match(r'^[a-z]{3,8}-\d{4}-\d{3,6}$', v):
            raise ValueError('ID must follow pattern: {prefix}-{year}-{number}')
        return v

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for export."""
        return self.model_dump()

    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, Any], source_system: SourceSystem) -> "GovernmentAction":
        """Create GovernmentAction from raw scraped data."""
        # This will be implemented by specific scrapers
        raise NotImplementedError("Must be implemented by specific scraper")


# Predefined labels matching the TypeScript schema
PREDEFINED_LABELS = [
    'Housing',
    'Health',
    'Education',
    'Infrastructure',
    'Environment',
    'Economy',
    'Justice',
    'Immigration',
    'Defence',
    'Transport',
    'Social Welfare',
    'Tax',
    'Local Government',
    'Treaty of Waitangi',
    'Agriculture',
]


class ActionCollection(BaseModel):
    """Collection of government actions with metadata."""
    actions: List[GovernmentAction] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=datetime.now)
    total_count: int = Field(default=0)
    source_counts: Dict[str, int] = Field(default_factory=dict)

    def add_action(self, action: GovernmentAction) -> None:
        """Add an action to the collection."""
        self.actions.append(action)
        self.total_count = len(self.actions)
        self._update_source_counts()

    def _update_source_counts(self) -> None:
        """Update source system counts."""
        self.source_counts = {}
        for action in self.actions:
            source = action.source_system.value
            self.source_counts[source] = self.source_counts.get(source, 0) + 1

    def to_typescript_export(self) -> Dict[str, Any]:
        """Export in format compatible with TypeScript frontend."""
        return {
            "labels": PREDEFINED_LABELS,
            "actions": [action.to_dict() for action in self.actions]
        }