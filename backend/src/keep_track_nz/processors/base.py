"""Base processor class for data processing operations."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import logging

from ..debug import DebugContext

logger = logging.getLogger(__name__)


class BaseProcessor(ABC):
    """Abstract base class for all data processors."""

    def __init__(self, debug_context: Optional[DebugContext] = None):
        """
        Initialize processor with optional debug context.

        Args:
            debug_context: Debug context for detailed output
        """
        self.debug_context = debug_context

    @abstractmethod
    def process(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process raw data from scrapers.

        Args:
            data: List of raw data dictionaries

        Returns:
            List of processed data dictionaries
        """
        pass

    def _log_processing_stats(self, input_count: int, output_count: int, processor_name: str) -> None:
        """Log processing statistics."""
        logger.info(
            f"{processor_name}: Processed {input_count} items, output {output_count} items "
            f"({output_count - input_count:+d})"
        )