"""Deduplicator for removing duplicate government actions."""

import logging
from typing import List, Dict, Any, Set, Tuple
from fuzzywuzzy import fuzz
from urllib.parse import urlparse

from ..models import GovernmentAction
from .base import BaseProcessor
from ..debug import DebugContext, DebugFormatter

logger = logging.getLogger(__name__)


class Deduplicator(BaseProcessor):
    """Remove duplicate government actions using multiple strategies."""

    def __init__(
        self,
        debug_context: DebugContext = None,
        title_similarity_threshold: int = 85,
        url_similarity_threshold: int = 90,
        exact_match_threshold: int = 95,
    ):
        """
        Initialize deduplicator with similarity thresholds.

        Args:
            debug_context: Debug context for detailed output
            title_similarity_threshold: Minimum fuzzy match score for title similarity
            url_similarity_threshold: Minimum fuzzy match score for URL similarity
            exact_match_threshold: Threshold for considering items exact duplicates
        """
        super().__init__(debug_context)
        self.title_similarity_threshold = title_similarity_threshold
        self.url_similarity_threshold = url_similarity_threshold
        self.exact_match_threshold = exact_match_threshold

        # Debug tracking
        self.debug_stats = {
            'exact_duplicates': 0,
            'similar_duplicates': 0,
            'cross_source_duplicates': 0,
            'total_duplicates': 0
        }

    def process(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicate government actions from the data.

        Args:
            data: List of raw action data dictionaries

        Returns:
            List of deduplicated action data dictionaries
        """
        input_count = len(data)
        logger.info(f"Starting deduplication of {input_count} actions")

        if self.debug_context and self.debug_context.enabled:
            print(DebugFormatter.format_section_header("DEDUPLICATION PROCESS"))
            print(f"📥 Input: {input_count} actions to process")

        if not data:
            return data

        # Convert to actions for easier comparison
        actions = []
        for item in data:
            try:
                if isinstance(item, dict):
                    actions.append(item)
                else:
                    logger.warning(f"Unexpected data type in deduplication: {type(item)}")
            except Exception as e:
                logger.warning(f"Failed to process item during deduplication: {e}")

        # Reset debug stats
        self.debug_stats = {
            'exact_duplicates': 0,
            'similar_duplicates': 0,
            'cross_source_duplicates': 0,
            'total_duplicates': 0
        }

        # Remove exact duplicates first (same ID or URL)
        before_exact = len(actions)
        actions = self._remove_exact_duplicates(actions)
        self.debug_stats['exact_duplicates'] = before_exact - len(actions)

        # Remove similar duplicates using fuzzy matching
        before_similar = len(actions)
        actions = self._remove_similar_duplicates(actions)
        self.debug_stats['similar_duplicates'] = before_similar - len(actions)

        # Remove cross-source duplicates (same content from different sources)
        before_cross = len(actions)
        actions = self._remove_cross_source_duplicates(actions)
        self.debug_stats['cross_source_duplicates'] = before_cross - len(actions)

        # Calculate total
        self.debug_stats['total_duplicates'] = input_count - len(actions)

        if self.debug_context and self.debug_context.enabled:
            print(DebugFormatter.format_dedup_summary(
                input_count, len(actions),
                self.debug_stats['exact_duplicates'],
                self.debug_stats['similar_duplicates'],
                self.debug_stats['cross_source_duplicates']
            ))

        self._log_processing_stats(input_count, len(actions), "Deduplicator")
        return actions

    def _remove_exact_duplicates(self, actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove actions with identical IDs or URLs."""
        if self.debug_context and self.debug_context.enabled:
            print("\n🔍 CHECKING FOR EXACT DUPLICATES...")

        seen_ids: Set[str] = set()
        seen_urls: Set[str] = set()
        seen_items: Dict[str, Dict[str, Any]] = {}  # For debug comparison
        unique_actions = []

        for action in actions:
            action_id = action.get('id', '')
            url = action.get('url', '')

            # Normalize URL for comparison
            normalized_url = self._normalize_url(url)

            # Check for duplicate ID
            if action_id and action_id in seen_ids:
                if self.debug_context and self.debug_context.enabled:
                    original_item = seen_items.get(f"id:{action_id}")
                    if original_item:
                        dup_num = self.debug_context.next_duplicate_number()
                        print(DebugFormatter.format_duplicate_comparison(
                            dup_num, original_item, action, "exact",
                            f"Identical ID: {action_id}"
                        ))
                logger.debug(f"Removing duplicate action with ID: {action_id}")
                continue

            # Check for duplicate URL
            if normalized_url and normalized_url in seen_urls:
                if self.debug_context and self.debug_context.enabled:
                    original_item = seen_items.get(f"url:{normalized_url}")
                    if original_item:
                        dup_num = self.debug_context.next_duplicate_number()
                        print(DebugFormatter.format_duplicate_comparison(
                            dup_num, original_item, action, "exact",
                            f"Identical URL: {normalized_url}"
                        ))
                logger.debug(f"Removing duplicate action with URL: {url}")
                continue

            # Add to seen sets and store for debug comparison
            if action_id:
                seen_ids.add(action_id)
                seen_items[f"id:{action_id}"] = action
            if normalized_url:
                seen_urls.add(normalized_url)
                seen_items[f"url:{normalized_url}"] = action

            unique_actions.append(action)

        logger.info(f"Removed {len(actions) - len(unique_actions)} exact duplicates")
        return unique_actions

    def _remove_similar_duplicates(self, actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove actions that are similar based on title and date."""
        if self.debug_context and self.debug_context.enabled:
            print("\n🔍 CHECKING FOR SIMILAR DUPLICATES...")

        unique_actions = []
        processed_indices: Set[int] = set()

        for i, action1 in enumerate(actions):
            if i in processed_indices:
                continue

            # Find all similar actions
            similar_indices = [i]
            for j, action2 in enumerate(actions[i + 1:], start=i + 1):
                if j in processed_indices:
                    continue

                similarity_info = self._are_similar_actions_debug(action1, action2)
                if similarity_info['is_similar']:
                    similar_indices.append(j)
                    if self.debug_context and self.debug_context.enabled:
                        dup_num = self.debug_context.next_duplicate_number()
                        print(DebugFormatter.format_duplicate_comparison(
                            dup_num, action1, action2, "similar",
                            similarity_info['reason'],
                            similarity_info.get('title_similarity')
                        ))

            # Choose the best action from the similar group
            best_action = self._choose_best_action([actions[idx] for idx in similar_indices])
            unique_actions.append(best_action)

            # Mark all indices as processed
            processed_indices.update(similar_indices)

        removed_count = len(actions) - len(unique_actions)
        if removed_count > 0:
            logger.info(f"Removed {removed_count} similar duplicates")

        return unique_actions

    def _remove_cross_source_duplicates(self, actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicates that appear across different source systems."""
        if self.debug_context and self.debug_context.enabled:
            print("\n🔍 CHECKING FOR CROSS-SOURCE DUPLICATES...")

        unique_actions = []
        processed_indices: Set[int] = set()

        for i, action1 in enumerate(actions):
            if i in processed_indices:
                continue

            # Look for the same content across different sources
            cross_source_indices = [i]
            for j, action2 in enumerate(actions[i + 1:], start=i + 1):
                if j in processed_indices:
                    continue

                # Only consider cross-source if they're from different systems
                if action1.get('source_system') != action2.get('source_system'):
                    cross_source_info = self._are_cross_source_duplicates_debug(action1, action2)
                    if cross_source_info['is_duplicate']:
                        cross_source_indices.append(j)
                        if self.debug_context and self.debug_context.enabled:
                            dup_num = self.debug_context.next_duplicate_number()
                            print(DebugFormatter.format_duplicate_comparison(
                                dup_num, action1, action2, "cross-source",
                                cross_source_info['reason']
                            ))

            # If we found cross-source duplicates, choose the best one
            if len(cross_source_indices) > 1:
                best_action = self._choose_best_cross_source_action(
                    [actions[idx] for idx in cross_source_indices]
                )
                unique_actions.append(best_action)
            else:
                unique_actions.append(action1)

            # Mark all indices as processed
            processed_indices.update(cross_source_indices)

        removed_count = len(actions) - len(unique_actions)
        if removed_count > 0:
            logger.info(f"Removed {removed_count} cross-source duplicates")

        return unique_actions

    def _are_similar_actions(self, action1: Dict[str, Any], action2: Dict[str, Any]) -> bool:
        """Check if two actions are similar enough to be considered duplicates."""
        # Check title similarity
        title1 = action1.get('title', '').lower().strip()
        title2 = action2.get('title', '').lower().strip()

        if not title1 or not title2:
            return False

        title_similarity = fuzz.ratio(title1, title2)

        # Check date proximity (same day or very close)
        date1 = action1.get('date', '')
        date2 = action2.get('date', '')
        date_match = self._dates_are_similar(date1, date2)

        # Check URL similarity (might be different versions of same document)
        url1 = action1.get('url', '')
        url2 = action2.get('url', '')
        url_similarity = fuzz.ratio(url1, url2) if url1 and url2 else 0

        # Consider similar if:
        # 1. High title similarity and same/similar dates
        # 2. Very high title similarity regardless of date
        # 3. High URL similarity
        if title_similarity >= self.exact_match_threshold:
            return True
        elif title_similarity >= self.title_similarity_threshold and date_match:
            return True
        elif url_similarity >= self.url_similarity_threshold:
            return True

        return False

    def _are_similar_actions_debug(self, action1: Dict[str, Any], action2: Dict[str, Any]) -> Dict[str, Any]:
        """Check if two actions are similar and provide debug information."""
        # Check title similarity
        title1 = action1.get('title', '').lower().strip()
        title2 = action2.get('title', '').lower().strip()

        if not title1 or not title2:
            return {'is_similar': False, 'reason': 'Missing titles'}

        title_similarity = fuzz.ratio(title1, title2)

        # Check date proximity (same day or very close)
        date1 = action1.get('date', '')
        date2 = action2.get('date', '')
        date_match = self._dates_are_similar(date1, date2)

        # Check URL similarity (might be different versions of same document)
        url1 = action1.get('url', '')
        url2 = action2.get('url', '')
        url_similarity = fuzz.ratio(url1, url2) if url1 and url2 else 0

        # Consider similar if:
        # 1. High title similarity and same/similar dates
        # 2. Very high title similarity regardless of date
        # 3. High URL similarity
        if title_similarity >= self.exact_match_threshold:
            return {
                'is_similar': True,
                'reason': f'Very high title similarity: {title_similarity}%',
                'title_similarity': title_similarity
            }
        elif title_similarity >= self.title_similarity_threshold and date_match:
            return {
                'is_similar': True,
                'reason': f'High title similarity ({title_similarity}%) + similar dates',
                'title_similarity': title_similarity
            }
        elif url_similarity >= self.url_similarity_threshold:
            return {
                'is_similar': True,
                'reason': f'High URL similarity: {url_similarity}%',
                'title_similarity': title_similarity
            }

        return {
            'is_similar': False,
            'reason': f'Low similarity (title: {title_similarity}%, URL: {url_similarity}%)',
            'title_similarity': title_similarity
        }

    def _are_cross_source_duplicates(self, action1: Dict[str, Any], action2: Dict[str, Any]) -> bool:
        """Check if actions from different sources represent the same thing."""
        # For cross-source duplicates, be more strict
        title1 = action1.get('title', '').lower().strip()
        title2 = action2.get('title', '').lower().strip()

        if not title1 or not title2:
            return False

        # Check for common patterns that indicate same content
        # 1. One is a bill and another is the resulting act
        is_bill_and_act = self._is_bill_and_corresponding_act(action1, action2)

        # 2. Similar titles with high similarity
        title_similarity = fuzz.ratio(title1, title2)

        # 3. Check if one is announcement and another is formal document
        is_announcement_and_formal = self._is_announcement_and_formal_document(action1, action2)

        return (
            is_bill_and_act or
            title_similarity >= self.exact_match_threshold or
            is_announcement_and_formal
        )

    def _are_cross_source_duplicates_debug(self, action1: Dict[str, Any], action2: Dict[str, Any]) -> Dict[str, Any]:
        """Check if actions from different sources represent the same thing and provide debug info."""
        # For cross-source duplicates, be more strict
        title1 = action1.get('title', '').lower().strip()
        title2 = action2.get('title', '').lower().strip()
        source1 = action1.get('source_system', '')
        source2 = action2.get('source_system', '')

        if not title1 or not title2:
            return {'is_duplicate': False, 'reason': 'Missing titles'}

        # Check for common patterns that indicate same content
        # 1. One is a bill and another is the resulting act
        is_bill_and_act = self._is_bill_and_corresponding_act(action1, action2)

        # 2. Similar titles with high similarity
        title_similarity = fuzz.ratio(title1, title2)

        # 3. Check if one is announcement and another is formal document
        is_announcement_and_formal = self._is_announcement_and_formal_document(action1, action2)

        if is_bill_and_act:
            return {
                'is_duplicate': True,
                'reason': f'Bill-to-Act match ({source1} → {source2}, similarity: {title_similarity}%)'
            }
        elif title_similarity >= self.exact_match_threshold:
            return {
                'is_duplicate': True,
                'reason': f'Very high cross-source title similarity: {title_similarity}%'
            }
        elif is_announcement_and_formal:
            return {
                'is_duplicate': True,
                'reason': f'Announcement-to-formal match ({source1} → {source2}, similarity: {title_similarity}%)'
            }

        return {
            'is_duplicate': False,
            'reason': f'Low cross-source similarity ({source1} vs {source2}: {title_similarity}%)'
        }

    def _is_bill_and_corresponding_act(self, action1: Dict[str, Any], action2: Dict[str, Any]) -> bool:
        """Check if one action is a bill and the other is the corresponding act."""
        title1 = action1.get('title', '').lower()
        title2 = action2.get('title', '').lower()

        source1 = action1.get('source_system', '')
        source2 = action2.get('source_system', '')

        # Check if one is from Parliament (bills) and other is from Legislation (acts)
        if not ((source1 == 'PARLIAMENT' and source2 == 'LEGISLATION') or
                (source1 == 'LEGISLATION' and source2 == 'PARLIAMENT')):
            return False

        # Remove common suffixes/prefixes to compare core titles
        clean_title1 = self._clean_title_for_comparison(title1)
        clean_title2 = self._clean_title_for_comparison(title2)

        # Check similarity of cleaned titles
        similarity = fuzz.ratio(clean_title1, clean_title2)
        return similarity >= self.title_similarity_threshold

    def _is_announcement_and_formal_document(self, action1: Dict[str, Any], action2: Dict[str, Any]) -> bool:
        """Check if one is an announcement and the other is the formal document."""
        source1 = action1.get('source_system', '')
        source2 = action2.get('source_system', '')

        # Check if one is from Beehive (announcements) and another is formal
        announcement_sources = {'BEEHIVE'}
        formal_sources = {'PARLIAMENT', 'LEGISLATION', 'GAZETTE'}

        is_announcement_formal = (
            (source1 in announcement_sources and source2 in formal_sources) or
            (source1 in formal_sources and source2 in announcement_sources)
        )

        if not is_announcement_formal:
            return False

        # Check title similarity
        title1 = self._clean_title_for_comparison(action1.get('title', '').lower())
        title2 = self._clean_title_for_comparison(action2.get('title', '').lower())

        similarity = fuzz.ratio(title1, title2)
        return similarity >= self.title_similarity_threshold

    def _clean_title_for_comparison(self, title: str) -> str:
        """Clean title for cross-source comparison."""
        # Remove common prefixes and suffixes
        import re

        title = re.sub(r'\s+bill\s*$', '', title, flags=re.IGNORECASE)
        title = re.sub(r'\s+act\s+\d{4}.*$', '', title, flags=re.IGNORECASE)
        title = re.sub(r'^\s*government\s+', '', title, flags=re.IGNORECASE)
        title = re.sub(r'^\s*new\s+', '', title, flags=re.IGNORECASE)
        title = re.sub(r'\s+amendment\s*$', '', title, flags=re.IGNORECASE)

        # Remove extra whitespace
        title = re.sub(r'\s+', ' ', title).strip()

        return title

    def _dates_are_similar(self, date1: str, date2: str, max_days_diff: int = 7) -> bool:
        """Check if two dates are within a reasonable timeframe."""
        if not date1 or not date2:
            return False

        try:
            from datetime import datetime, timedelta

            # Parse dates
            d1 = datetime.strptime(date1, '%Y-%m-%d')
            d2 = datetime.strptime(date2, '%Y-%m-%d')

            # Check if within max_days_diff
            diff = abs((d1 - d2).days)
            return diff <= max_days_diff

        except ValueError:
            # If date parsing fails, consider them not similar
            return False

    def _choose_best_action(self, actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Choose the best action from a group of similar actions."""
        if len(actions) == 1:
            return actions[0]

        # Scoring criteria:
        # 1. More complete summary/content
        # 2. More recent scraping date
        # 3. More complete metadata
        # 4. Prefer certain sources (Parliament > Legislation > Beehive > Gazette)

        source_priority = {
            'PARLIAMENT': 4,
            'LEGISLATION': 3,
            'BEEHIVE': 2,
            'GAZETTE': 1
        }

        best_action = actions[0]
        best_score = self._score_action(best_action, source_priority)

        for action in actions[1:]:
            score = self._score_action(action, source_priority)
            if score > best_score:
                best_action = action
                best_score = score

        return best_action

    def _choose_best_cross_source_action(self, actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Choose the best action from cross-source duplicates."""
        # For cross-source duplicates, prefer formal documents over announcements
        source_priority = {
            'LEGISLATION': 4,  # Acts are most authoritative
            'PARLIAMENT': 3,   # Bills are formal
            'GAZETTE': 2,      # Official notices
            'BEEHIVE': 1       # Announcements are least formal
        }

        best_action = actions[0]
        best_score = self._score_action(best_action, source_priority)

        for action in actions[1:]:
            score = self._score_action(action, source_priority)
            if score > best_score:
                best_action = action
                best_score = score

        return best_action

    def _score_action(self, action: Dict[str, Any], source_priority: Dict[str, int]) -> float:
        """Score an action for quality/completeness."""
        score = 0.0

        # Source priority
        source = action.get('source_system', '')
        score += source_priority.get(source, 0) * 10

        # Summary completeness
        summary = action.get('summary', '')
        if summary:
            score += min(len(summary) / 100, 5)  # Up to 5 points for summary

        # Title completeness
        title = action.get('title', '')
        if title:
            score += min(len(title) / 50, 3)  # Up to 3 points for title

        # Metadata completeness
        metadata = action.get('metadata', {})
        if isinstance(metadata, dict):
            score += len([v for v in metadata.values() if v is not None])

        # Recent scraping (prefer more recently scraped)
        last_scraped = action.get('last_scraped', '')
        if last_scraped:
            score += 1

        return score

    def _normalize_url(self, url: str) -> str:
        """Normalize URL for comparison."""
        if not url:
            return ''

        try:
            parsed = urlparse(url.lower())
            # Remove common variations
            path = parsed.path.rstrip('/')
            # Remove common parameters that don't affect content
            return f"{parsed.netloc}{path}"
        except Exception:
            return url.lower()


def main():
    """Test the deduplicator."""
    import sys

    logging.basicConfig(level=logging.INFO)

    # Create test data with duplicates
    test_data = [
        {
            'id': 'test-001',
            'title': 'Fast-track Approvals Bill',
            'url': 'https://example.com/bill1',
            'date': '2024-12-05',
            'source_system': 'PARLIAMENT',
            'summary': 'A bill to provide fast-track approvals'
        },
        {
            'id': 'test-002',
            'title': 'Fast-track Approvals Bill',
            'url': 'https://example.com/bill1',
            'date': '2024-12-05',
            'source_system': 'PARLIAMENT',
            'summary': 'A bill to provide fast-track approvals'
        },
        {
            'id': 'test-003',
            'title': 'Fast-Track Approvals Act 2024',
            'url': 'https://example.com/act1',
            'date': '2024-12-06',
            'source_system': 'LEGISLATION',
            'summary': 'An act to provide fast-track approvals'
        }
    ]

    deduplicator = Deduplicator()
    result = deduplicator.process(test_data)

    if '--test' in sys.argv:
        print(f"Original: {len(test_data)} items")
        print(f"After deduplication: {len(result)} items")
        for item in result:
            print(f"- {item['title']} ({item['source_system']})")


if __name__ == '__main__':
    main()