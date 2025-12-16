"""Data validator for ensuring government actions meet schema requirements."""

import logging
from typing import List, Dict, Any, Set
from datetime import datetime
import re

from ..models import GovernmentAction, SourceSystem
from .base import BaseProcessor
from ..debug import DebugContext

logger = logging.getLogger(__name__)


class DataValidator(BaseProcessor):
    """Validate government action data against schema requirements."""

    def __init__(self, debug_context=None, strict_mode: bool = False):
        """
        Initialize data validator.

        Args:
            debug_context: Debug context for detailed output
            strict_mode: If True, reject actions that don't meet all requirements.
                        If False, attempt to fix/normalize data where possible.
        """
        super().__init__(debug_context)
        self.strict_mode = strict_mode
        self.validation_errors = []
        self.fixed_items = []

    def process(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validate and optionally fix government action data.

        Args:
            data: List of raw action data dictionaries

        Returns:
            List of validated and potentially fixed action data dictionaries
        """
        input_count = len(data)
        logger.info(f"Starting data validation for {input_count} actions (strict_mode={self.strict_mode})")

        self.validation_errors = []
        self.fixed_items = []
        valid_data = []

        for i, item in enumerate(data):
            try:
                validated_item = self._validate_action(item, i)
                if validated_item is not None:
                    valid_data.append(validated_item)
            except Exception as e:
                logger.error(f"Validation failed for item {i}: {e}")
                if not self.strict_mode:
                    # In non-strict mode, include the item as-is
                    valid_data.append(item)

        # Log validation results
        rejected_count = input_count - len(valid_data)
        if rejected_count > 0:
            logger.warning(f"Rejected {rejected_count} actions due to validation errors")

        if self.fixed_items:
            logger.info(f"Fixed validation issues in {len(self.fixed_items)} actions")

        if self.validation_errors:
            logger.info(f"Found {len(self.validation_errors)} validation errors")
            for error in self.validation_errors[:5]:  # Log first 5 errors
                logger.debug(f"Validation error: {error}")

        self._log_processing_stats(input_count, len(valid_data), "DataValidator")
        return valid_data

    def _validate_action(self, action: Dict[str, Any], index: int) -> Dict[str, Any] | None:
        """Validate a single government action."""
        original_action = action.copy()
        errors = []
        fixed = False

        # 1. Validate required fields
        required_fields = ['title', 'url', 'source_system']
        for field in required_fields:
            if not action.get(field):
                error = f"Item {index}: Missing required field '{field}'"
                errors.append(error)
                if self.strict_mode:
                    self.validation_errors.append(error)
                    return None

        # 2. Validate and fix source_system
        source_system = action.get('source_system')
        if source_system:
            fixed_source = self._validate_source_system(source_system, index, errors)
            if fixed_source != source_system:
                action['source_system'] = fixed_source
                fixed = True
        else:
            # Try to infer from URL
            inferred_source = self._infer_source_from_url(action.get('url', ''))
            if inferred_source:
                action['source_system'] = inferred_source
                fixed = True
                logger.debug(f"Item {index}: Inferred source_system as {inferred_source}")

        # 3. Validate and fix ID
        action_id = action.get('id')
        if not action_id:
            generated_id = self._generate_id(action, index)
            action['id'] = generated_id
            fixed = True
            logger.debug(f"Item {index}: Generated ID {generated_id}")
        else:
            validated_id = self._validate_id_format(action_id, index, errors)
            if validated_id != action_id:
                action['id'] = validated_id
                fixed = True

        # 4. Validate and fix date
        date_str = action.get('date')
        if not date_str:
            action['date'] = datetime.now().strftime('%Y-%m-%d')
            fixed = True
            logger.debug(f"Item {index}: Set default date")
        else:
            validated_date = self._validate_date_format(date_str, index, errors)
            if validated_date != date_str:
                action['date'] = validated_date
                fixed = True

        # 5. Validate URL
        url = action.get('url', '')
        if url:
            validated_url = self._validate_url_format(url, index, errors)
            if validated_url != url:
                action['url'] = validated_url
                fixed = True

        # 6. Validate and fix title
        title = action.get('title', '')
        if title:
            cleaned_title = self._clean_title(title)
            if cleaned_title != title:
                action['title'] = cleaned_title
                fixed = True

        # 7. Validate and fix primary_entity
        primary_entity = action.get('primary_entity', '')
        if not primary_entity:
            inferred_entity = self._infer_primary_entity(action)
            action['primary_entity'] = inferred_entity
            fixed = True

        # 8. Validate summary
        summary = action.get('summary', '')
        if summary:
            cleaned_summary = self._clean_summary(summary)
            if cleaned_summary != summary:
                action['summary'] = cleaned_summary
                fixed = True

        # 9. Validate labels
        labels = action.get('labels', [])
        if labels:
            validated_labels = self._validate_labels(labels, index, errors)
            if validated_labels != labels:
                action['labels'] = validated_labels
                fixed = True
        else:
            action['labels'] = []

        # 10. Validate metadata
        metadata = action.get('metadata', {})
        if metadata:
            validated_metadata = self._validate_metadata(metadata, action['source_system'], index, errors)
            if validated_metadata != metadata:
                action['metadata'] = validated_metadata
                fixed = True
        else:
            action['metadata'] = {}

        # Record if item was fixed
        if fixed:
            self.fixed_items.append(index)

        # In strict mode, reject if there were errors
        if self.strict_mode and errors:
            self.validation_errors.extend(errors)
            return None

        return action

    def _validate_source_system(self, source_system: str, index: int, errors: List[str]) -> str:
        """Validate and normalize source system."""
        if source_system in [s.value for s in SourceSystem]:
            return source_system

        # Try to normalize common variations
        source_mapping = {
            'parliament': 'PARLIAMENT',
            'legislation': 'LEGISLATION',
            'gazette': 'GAZETTE',
            'beehive': 'BEEHIVE',
            'bills': 'PARLIAMENT',
            'acts': 'LEGISLATION',
            'notices': 'GAZETTE',
            'announcements': 'BEEHIVE',
            'press releases': 'BEEHIVE'
        }

        normalized = source_mapping.get(source_system.lower())
        if normalized:
            logger.debug(f"Item {index}: Normalized source_system '{source_system}' to '{normalized}'")
            return normalized

        error = f"Item {index}: Invalid source_system '{source_system}'"
        errors.append(error)
        # Default to BEEHIVE for unknown sources
        return 'BEEHIVE'

    def _infer_source_from_url(self, url: str) -> str:
        """Infer source system from URL."""
        if not url:
            return 'BEEHIVE'  # Default

        url_lower = url.lower()

        if 'bills.parliament.nz' in url_lower or 'parliament.nz' in url_lower:
            return 'PARLIAMENT'
        elif 'legislation.govt.nz' in url_lower:
            return 'LEGISLATION'
        elif 'gazette.govt.nz' in url_lower:
            return 'GAZETTE'
        elif 'beehive.govt.nz' in url_lower:
            return 'BEEHIVE'

        return 'BEEHIVE'  # Default

    def _validate_id_format(self, action_id: str, index: int, errors: List[str]) -> str:
        """Validate ID follows expected pattern."""
        # Expected pattern: {source_prefix}-{year}-{number}
        if re.match(r'^[a-z]{3,8}-\d{4}-\d{3,6}$', action_id):
            return action_id

        # Try to fix common issues
        # Remove invalid characters
        clean_id = re.sub(r'[^a-zA-Z0-9-]', '', action_id)

        # Check if it matches after cleaning
        if re.match(r'^[a-z]{3,8}-\d{4}-\d{3,6}$', clean_id.lower()):
            return clean_id.lower()

        error = f"Item {index}: Invalid ID format '{action_id}'"
        errors.append(error)

        # Keep original ID if we can't fix it
        return action_id

    def _generate_id(self, action: Dict[str, Any], index: int) -> str:
        """Generate ID for action missing one."""
        source = action.get('source_system', 'BEEHIVE')
        source_prefix = {
            'PARLIAMENT': 'parl',
            'LEGISLATION': 'leg',
            'GAZETTE': 'gaz',
            'BEEHIVE': 'bee'
        }.get(source, 'unknown')

        # Extract year from date or use current year
        date_str = action.get('date', '')
        if date_str and len(date_str) >= 4:
            year = date_str[:4]
        else:
            year = str(datetime.now().year)

        # Generate number based on index and timestamp
        number = f"{index:03d}{datetime.now().microsecond // 1000:03d}"

        return f"{source_prefix}-{year}-{number}"

    def _validate_date_format(self, date_str: str, index: int, errors: List[str]) -> str:
        """Validate and normalize date format."""
        # Try to parse and reformat
        try:
            # Handle common formats
            formats = [
                '%Y-%m-%d',
                '%d/%m/%Y',
                '%d-%m-%Y',
                '%Y/%m/%d',
                '%d %B %Y',
                '%d %b %Y',
                '%B %d, %Y'
            ]

            for fmt in formats:
                try:
                    date_obj = datetime.strptime(date_str.strip(), fmt)
                    return date_obj.strftime('%Y-%m-%d')
                except ValueError:
                    continue

            # If no format worked, check if it's already in correct format
            if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str.strip()):
                return date_str.strip()

            error = f"Item {index}: Invalid date format '{date_str}'"
            errors.append(error)

        except Exception as e:
            error = f"Item {index}: Date validation error '{date_str}': {e}"
            errors.append(error)

        # Return current date as fallback
        return datetime.now().strftime('%Y-%m-%d')

    def _validate_url_format(self, url: str, index: int, errors: List[str]) -> str:
        """Validate and clean URL format."""
        url = url.strip()

        # Basic URL validation
        if not url.startswith(('http://', 'https://')):
            if url.startswith('www.'):
                url = 'https://' + url
            elif '.' in url and not url.startswith('/'):
                url = 'https://' + url

        # Check for valid URL pattern
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)

        if not url_pattern.match(url):
            error = f"Item {index}: Invalid URL format '{url}'"
            errors.append(error)

        return url

    def _clean_title(self, title: str) -> str:
        """Clean and normalize title."""
        # Remove extra whitespace
        title = re.sub(r'\s+', ' ', title.strip())

        # Remove common prefixes that might have been duplicated
        title = re.sub(r'^(New Zealand |NZ |Government |Official )+', '', title, flags=re.IGNORECASE)

        return title

    def _clean_summary(self, summary: str) -> str:
        """Clean and normalize summary."""
        if not summary:
            return ''

        # Remove extra whitespace
        summary = re.sub(r'\s+', ' ', summary.strip())

        # Truncate if too long (keep reasonable length)
        if len(summary) > 1000:
            summary = summary[:997] + '...'

        return summary

    def _infer_primary_entity(self, action: Dict[str, Any]) -> str:
        """Infer primary entity if missing."""
        # Check metadata first
        metadata = action.get('metadata', {})
        if isinstance(metadata, dict):
            portfolio = metadata.get('portfolio', '')
            if portfolio:
                # Map portfolio to likely minister
                portfolio_ministers = {
                    'Prime Minister': 'Rt Hon Christopher Luxon',
                    'Finance': 'Hon Nicola Willis',
                    'Housing': 'Hon Chris Bishop',
                    'Health': 'Hon Dr Shane Reti',
                    'Education': 'Hon Erica Stanford',
                    'Transport': 'Hon Simeon Brown',
                    'Justice': 'Hon Mark Mitchell',
                }
                if portfolio in portfolio_ministers:
                    return portfolio_ministers[portfolio]

        # Check source system
        source_system = action.get('source_system', '')
        if source_system == 'GAZETTE':
            # Many gazette notices are by Governor-General
            title = action.get('title', '').lower()
            if 'appointment' in title:
                return 'Governor-General'

        # Default based on source
        source_defaults = {
            'PARLIAMENT': 'Parliament',
            'LEGISLATION': 'Parliament',
            'GAZETTE': 'Government',
            'BEEHIVE': 'Government'
        }

        return source_defaults.get(source_system, 'Government')

    def _validate_labels(self, labels: List[str], index: int, errors: List[str]) -> List[str]:
        """Validate labels against predefined list."""
        from ..models import PREDEFINED_LABELS

        if not isinstance(labels, list):
            error = f"Item {index}: Labels must be a list, got {type(labels)}"
            errors.append(error)
            return []

        valid_labels = []
        for label in labels:
            if label in PREDEFINED_LABELS:
                valid_labels.append(label)
            else:
                error = f"Item {index}: Unknown label '{label}'"
                errors.append(error)

        # Remove duplicates and sort
        return sorted(list(set(valid_labels)))

    def _validate_metadata(self, metadata: Dict[str, Any], source_system: str, index: int, errors: List[str]) -> Dict[str, Any]:
        """Validate metadata based on source system requirements."""
        if not isinstance(metadata, dict):
            error = f"Item {index}: Metadata must be a dict, got {type(metadata)}"
            errors.append(error)
            return {}

        validated_metadata = {}

        # Clean and validate each field
        for key, value in metadata.items():
            if value is not None and value != '':
                if isinstance(value, str):
                    validated_metadata[key] = value.strip()
                elif isinstance(value, (int, list)):
                    validated_metadata[key] = value
                else:
                    validated_metadata[key] = str(value)

        return validated_metadata

    def get_validation_summary(self) -> Dict[str, Any]:
        """Get summary of validation results."""
        return {
            'total_errors': len(self.validation_errors),
            'items_fixed': len(self.fixed_items),
            'errors': self.validation_errors,
            'fixed_items': self.fixed_items
        }


def main():
    """Test the data validator."""
    import sys

    logging.basicConfig(level=logging.INFO)

    # Create test data with various validation issues
    test_data = [
        {
            'title': '   Fast-track Approvals Bill   ',
            'url': 'bills.parliament.nz/bill1',  # Missing protocol
            'source_system': 'parliament',  # Wrong case
            'date': '05/12/2024',  # Wrong format
            'summary': '  A bill to provide fast-track approvals.  ',
            'labels': ['Infrastructure', 'InvalidLabel'],
            'metadata': {'bill_number': '123456'}
        },
        {
            'title': 'Health Act 2024',
            'url': 'https://legislation.govt.nz/act1',
            'source_system': 'LEGISLATION',
            # Missing date, id, primary_entity
            'summary': '',
            'labels': [],
            'metadata': {}
        }
    ]

    validator = DataValidator(strict_mode=False)
    result = validator.process(test_data)

    if '--test' in sys.argv:
        print(f"Validation results:")
        print(f"Input: {len(test_data)} actions")
        print(f"Output: {len(result)} actions")

        summary = validator.get_validation_summary()
        print(f"Errors: {summary['total_errors']}")
        print(f"Fixed items: {summary['items_fixed']}")

        for action in result:
            print(f"\n- {action['title']}")
            print(f"  ID: {action.get('id', 'None')}")
            print(f"  Date: {action.get('date', 'None')}")
            print(f"  URL: {action.get('url', 'None')}")
            print(f"  Source: {action.get('source_system', 'None')}")
            print(f"  Primary Entity: {action.get('primary_entity', 'None')}")
            print(f"  Labels: {action.get('labels', [])}")


if __name__ == '__main__':
    main()