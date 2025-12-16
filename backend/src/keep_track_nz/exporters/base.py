"""Base exporter class for data export operations."""

from abc import ABC, abstractmethod
from typing import List, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class BaseExporter(ABC):
    """Abstract base class for all data exporters."""

    def __init__(self, output_path: Path):
        """Initialize exporter with output path."""
        self.output_path = output_path

    @abstractmethod
    def export(self, data: List[Any], **kwargs) -> None:
        """
        Export processed data to the target format.

        Args:
            data: List of processed government actions
            **kwargs: Additional export options
        """
        pass

    def _ensure_output_directory(self) -> None:
        """Ensure the output directory exists."""
        self.output_path.parent.mkdir(parents=True, exist_ok=True)