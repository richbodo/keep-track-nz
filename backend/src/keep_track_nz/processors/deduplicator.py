"""Deduplication processor for handling versioned government actions."""

import logging
from typing import List, Dict, Set
from collections import defaultdict

from ..models import GovernmentAction
from .base import BaseProcessor

logger = logging.getLogger(__name__)


class DeduplicationProcessor(BaseProcessor):
    """
    Processor that handles deduplication of versioned government actions.

    This processor identifies actions that are different versions of the same base action
    and ensures they are properly organized while preserving version history.
    """

    def __init__(self, debug_context=None):
        """Initialize the deduplication processor."""
        super().__init__(debug_context)
        self.stats = {
            'total_processed': 0,
            'duplicates_found': 0,
            'versions_preserved': 0,
            'base_actions': 0
        }

    def process(self, actions: List[GovernmentAction]) -> List[GovernmentAction]:
        """
        Process actions to handle version-based deduplication.

        Args:
            actions: List of government actions to process

        Returns:
            List of deduplicated actions with proper version relationships
        """
        logger.info(f"Starting deduplication processing for {len(actions)} actions")
        self.stats['total_processed'] = len(actions)

        # Group actions by base_id
        base_id_groups = self._group_actions_by_base_id(actions)

        # Process each group to handle versioning
        processed_actions = []
        for base_id, action_group in base_id_groups.items():
            processed_group = self._process_version_group(base_id, action_group)
            processed_actions.extend(processed_group)

        # Log statistics
        self._log_deduplication_stats()

        logger.info(f"Deduplication complete: {len(processed_actions)} actions after processing")
        return processed_actions

    def _group_actions_by_base_id(self, actions: List[GovernmentAction]) -> Dict[str, List[GovernmentAction]]:
        """Group actions by their base_id."""
        groups = defaultdict(list)

        for action in actions:
            # Use base_id if available, otherwise fall back to generating from id
            base_id = action.base_id
            if not base_id:
                # Generate base_id by removing version suffix from id
                if '-v' in action.id:
                    base_id = action.id.rsplit('-v', 1)[0]
                else:
                    base_id = action.id
                # Update the action with the computed base_id
                action.base_id = base_id

            groups[base_id].append(action)

        return dict(groups)

    def _process_version_group(self, base_id: str, actions: List[GovernmentAction]) -> List[GovernmentAction]:
        """
        Process a group of actions that share the same base_id.

        Args:
            base_id: The base identifier shared by all actions in the group
            actions: List of actions with the same base_id

        Returns:
            List of processed actions (all versions preserved)
        """
        if len(actions) == 1:
            # Single action, no deduplication needed
            return actions

        # Multiple versions detected
        self.stats['duplicates_found'] += len(actions) - 1
        self.stats['base_actions'] += 1

        # Sort actions by version (latest first)
        sorted_actions = self._sort_actions_by_version(actions)

        # Ensure all actions have proper version relationships
        processed_actions = []
        for action in sorted_actions:
            # Ensure base_id is set
            if not action.base_id:
                action.base_id = base_id

            processed_actions.append(action)
            self.stats['versions_preserved'] += 1

        logger.debug(f"Processed version group {base_id}: {len(processed_actions)} versions")

        # Log version information if in debug mode
        if self.debug_context:
            version_info = [f"v{action.version or '1'}" for action in processed_actions]
            logger.debug(f"Versions for {base_id}: {', '.join(version_info)}")

        return processed_actions

    def _sort_actions_by_version(self, actions: List[GovernmentAction]) -> List[GovernmentAction]:
        """
        Sort actions by version number (latest first).

        Args:
            actions: List of actions to sort

        Returns:
            List of actions sorted by version (descending)
        """
        def version_key(action: GovernmentAction) -> int:
            """Extract numeric version for sorting."""
            version = action.version or '1'
            try:
                # Remove 'v' prefix if present and convert to int
                if version.startswith('v'):
                    version = version[1:]
                return int(version)
            except (ValueError, AttributeError):
                # Default to version 1 if parsing fails
                return 1

        return sorted(actions, key=version_key, reverse=True)

    def _detect_true_duplicates(self, actions: List[GovernmentAction]) -> List[GovernmentAction]:
        """
        Detect true duplicates (same URL, same content) vs different versions.

        This method identifies actions that are actual duplicates rather than
        legitimate different versions.

        Args:
            actions: List of actions to check for true duplicates

        Returns:
            List of actions with true duplicates removed
        """
        seen_urls = set()
        unique_actions = []

        for action in actions:
            # Consider it a duplicate if URL is exactly the same
            if action.url in seen_urls:
                logger.debug(f"Removing true duplicate: {action.id} (same URL)")
                continue

            seen_urls.add(action.url)
            unique_actions.append(action)

        return unique_actions

    def _update_version_relationships(self, actions: List[GovernmentAction]) -> None:
        """
        Update actions to ensure proper version relationships are maintained.

        This could be extended in the future to add fields like 'related_versions',
        'is_latest_version', etc.
        """
        if not actions:
            return

        # Sort by version to identify latest
        sorted_actions = self._sort_actions_by_version(actions)

        # Could add additional relationship fields here
        # For now, just ensure all have the same base_id
        base_id = sorted_actions[0].base_id
        for action in actions:
            action.base_id = base_id

    def _log_deduplication_stats(self) -> None:
        """Log deduplication processing statistics."""
        stats_msg = (
            f"Deduplication Stats: "
            f"Processed: {self.stats['total_processed']}, "
            f"Duplicates found: {self.stats['duplicates_found']}, "
            f"Versions preserved: {self.stats['versions_preserved']}, "
            f"Base actions: {self.stats['base_actions']}"
        )
        logger.info(stats_msg)

    def get_processing_stats(self) -> Dict[str, int]:
        """
        Get processing statistics for this processor.

        Returns:
            Dictionary containing processing statistics
        """
        return self.stats.copy()