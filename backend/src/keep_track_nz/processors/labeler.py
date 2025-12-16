"""Label classifier for automatically assigning labels to government actions."""

import re
import logging
from typing import List, Dict, Any, Set

from ..models import PREDEFINED_LABELS
from .base import BaseProcessor
from ..debug import DebugContext

logger = logging.getLogger(__name__)


class LabelClassifier(BaseProcessor):
    """Automatically assign classification labels to government actions."""

    def __init__(self, debug_context=None):
        """Initialize label classifier with keyword mappings."""
        super().__init__(debug_context)
        # Define keyword mappings for each label
        self.label_keywords = {
            'Housing': {
                'housing', 'homes', 'residential', 'property', 'rent', 'rental',
                'accommodation', 'tenancy', 'landlord', 'tenant', 'mortgage',
                'affordable housing', 'social housing', 'public housing',
                'kainga ora', 'kāinga ora', 'building consent', 'construction',
                'development', 'urban planning', 'zoning', 'density'
            },
            'Health': {
                'health', 'healthcare', 'medical', 'hospital', 'clinic', 'doctor',
                'nurse', 'patient', 'treatment', 'medicine', 'pharmaceutical',
                'mental health', 'public health', 'wellbeing', 'wellness',
                'health nz', 'te whatu ora', 'pharmac', 'covid', 'pandemic',
                'disability', 'aged care', 'elder care'
            },
            'Education': {
                'education', 'school', 'student', 'teacher', 'university',
                'college', 'learning', 'curriculum', 'scholarship', 'exam',
                'qualification', 'training', 'skill', 'literacy', 'numeracy',
                'early childhood', 'tertiary', 'vocational', 'apprenticeship',
                'education funding'
            },
            'Infrastructure': {
                'infrastructure', 'road', 'bridge', 'tunnel', 'highway',
                'motorway', 'rail', 'railway', 'public transport', 'water',
                'sewage', 'electricity', 'power', 'broadband', 'internet',
                'telecommunications', 'energy', 'utility', 'construction',
                'development', 'maintenance', 'upgrade', 'investment'
            },
            'Environment': {
                'environment', 'environmental', 'climate', 'carbon', 'emissions',
                'renewable', 'sustainability', 'conservation', 'biodiversity',
                'pollution', 'waste', 'recycling', 'water quality', 'air quality',
                'forest', 'marine', 'coastal', 'national park', 'reserve',
                'climate change', 'greenhouse gas', 'clean energy', 'green',
                'nature', 'wildlife', 'ecosystem'
            },
            'Economy': {
                'economy', 'economic', 'business', 'industry', 'commerce',
                'trade', 'export', 'import', 'investment', 'employment',
                'job', 'work', 'productivity', 'growth', 'development',
                'innovation', 'technology', 'digital', 'manufacturing',
                'tourism', 'agriculture', 'fisheries', 'forestry',
                'small business', 'enterprise'
            },
            'Justice': {
                'justice', 'court', 'judge', 'law', 'legal', 'crime', 'police',
                'prison', 'corrections', 'bail', 'sentence', 'trial', 'jury',
                'solicitor', 'barrister', 'lawyer', 'attorney', 'prosecution',
                'defence', 'civil', 'criminal', 'offence', 'penalty', 'fine',
                'legal aid', 'family court', 'youth justice'
            },
            'Immigration': {
                'immigration', 'migrant', 'visa', 'residence', 'citizenship',
                'border', 'refugee', 'asylum', 'deportation', 'work permit',
                'student visa', 'family reunion', 'skilled migrant',
                'points system', 'immigration nz', 'customs', 'passport'
            },
            'Defence': {
                'defence', 'defense', 'military', 'army', 'navy', 'air force',
                'nzdf', 'security', 'national security', 'peacekeeping',
                'veteran', 'deployment', 'equipment', 'training',
                'international relations', 'alliance', 'treaty'
            },
            'Transport': {
                'transport', 'transportation', 'road', 'rail', 'bus', 'ferry',
                'aviation', 'airport', 'port', 'shipping', 'logistics',
                'public transport', 'cycling', 'walking', 'safety',
                'traffic', 'vehicle', 'driver', 'license', 'registration',
                'waka kotahi', 'nzta'
            },
            'Social Welfare': {
                'welfare', 'benefit', 'pension', 'allowance', 'support',
                'social development', 'family', 'child', 'youth', 'senior',
                'disability', 'poverty', 'hardship', 'assistance', 'community',
                'social service', 'msd', 'work and income', 'winz',
                'superannuation', 'accommodation supplement'
            },
            'Tax': {
                'tax', 'taxation', 'gst', 'income tax', 'company tax',
                'ird', 'inland revenue', 'customs duty', 'excise',
                'tax credit', 'tax relief', 'tax rate', 'tax policy',
                'provisional tax', 'fringe benefit', 'working for families',
                'family boost', 'rates', 'levy'
            },
            'Local Government': {
                'local government', 'council', 'mayor', 'councillor', 'rates',
                'district', 'city', 'regional', 'local authority', 'bylaw',
                'planning', 'consent', 'resource management', 'three waters',
                'waste management', 'community facility', 'library', 'park',
                'local road', 'water supply', 'wastewater'
            },
            'Treaty of Waitangi': {
                'treaty', 'waitangi', 'iwi', 'māori', 'maori', 'tangata whenua',
                'settlement', 'claim', 'tribunal', 'partnership', 'sovereignty',
                'tino rangatiratanga', 'biculturalism', 'te tiriti',
                'indigenous rights', 'cultural heritage', 'land rights',
                'co-governance', 'co-management'
            },
            'Agriculture': {
                'agriculture', 'farming', 'farm', 'farmer', 'livestock',
                'dairy', 'beef', 'sheep', 'crop', 'harvest', 'rural',
                'primary sector', 'food production', 'meat', 'milk',
                'wool', 'horticulture', 'fruit', 'vegetable', 'wine',
                'viticulture', 'pastoral', 'irrigation', 'drought',
                'biosecurity', 'animal welfare'
            }
        }

        # Compile patterns for efficient matching
        self.compiled_patterns = {}
        for label, keywords in self.label_keywords.items():
            # Create regex pattern for each label
            pattern = r'\b(?:' + '|'.join(re.escape(keyword) for keyword in keywords) + r')\b'
            self.compiled_patterns[label] = re.compile(pattern, re.IGNORECASE)

    def process(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Assign labels to government actions based on content analysis.

        Args:
            data: List of action data dictionaries

        Returns:
            List of action data dictionaries with labels assigned
        """
        input_count = len(data)
        logger.info(f"Starting label classification for {input_count} actions")

        labeled_data = []
        total_labels_assigned = 0

        for item in data:
            try:
                labels = self._classify_action(item)
                item['labels'] = labels
                labeled_data.append(item)
                total_labels_assigned += len(labels)

            except Exception as e:
                logger.warning(f"Failed to classify action {item.get('id', 'unknown')}: {e}")
                # Still include the item but with empty labels
                item['labels'] = []
                labeled_data.append(item)

        avg_labels = total_labels_assigned / input_count if input_count > 0 else 0
        logger.info(f"Assigned {total_labels_assigned} labels across {input_count} actions "
                   f"(avg {avg_labels:.1f} labels per action)")

        self._log_processing_stats(input_count, len(labeled_data), "LabelClassifier")
        return labeled_data

    def _classify_action(self, action: Dict[str, Any]) -> List[str]:
        """Classify a single government action and return appropriate labels."""
        # Collect all text content for analysis
        text_content = self._extract_text_content(action)

        if not text_content:
            logger.debug(f"No text content found for action {action.get('id', 'unknown')}")
            return []

        # Find matching labels
        matched_labels = set()

        # Check each label pattern against the text
        for label, pattern in self.compiled_patterns.items():
            matches = pattern.findall(text_content)
            if matches:
                matched_labels.add(label)
                logger.debug(f"Action {action.get('id', 'unknown')} matched '{label}' "
                           f"with keywords: {matches[:3]}")  # Log first 3 matches

        # Apply additional business rules
        matched_labels = self._apply_business_rules(action, matched_labels)

        # Convert to sorted list for consistency
        return sorted(list(matched_labels))

    def _extract_text_content(self, action: Dict[str, Any]) -> str:
        """Extract all relevant text content from an action for classification."""
        text_parts = []

        # Title (weighted more heavily by repeating)
        title = action.get('title', '').strip()
        if title:
            text_parts.extend([title] * 3)  # Triple weight for title

        # Summary
        summary = action.get('summary', '').strip()
        if summary:
            text_parts.append(summary)

        # Primary entity (might indicate portfolio)
        primary_entity = action.get('primary_entity', '').strip()
        if primary_entity:
            text_parts.append(primary_entity)

        # Metadata fields
        metadata = action.get('metadata', {})
        if isinstance(metadata, dict):
            for key, value in metadata.items():
                if value and isinstance(value, str):
                    text_parts.append(value)

        # Portfolio from metadata
        portfolio = metadata.get('portfolio', '') if isinstance(metadata, dict) else ''
        if portfolio:
            text_parts.extend([portfolio] * 2)  # Double weight for portfolio

        return ' '.join(text_parts).lower()

    def _apply_business_rules(self, action: Dict[str, Any], labels: Set[str]) -> Set[str]:
        """Apply business logic rules to refine label assignments."""
        # Rule 1: Source-specific label inference
        source_system = action.get('source_system', '')

        if source_system == 'GAZETTE':
            # Gazette notices often contain appointments and regulatory changes
            title = action.get('title', '').lower()
            if any(word in title for word in ['appointment', 'appoint']):
                if 'judge' in title or 'court' in title:
                    labels.add('Justice')
                elif 'health' in title:
                    labels.add('Health')

        # Rule 2: Portfolio-based labeling
        metadata = action.get('metadata', {})
        portfolio = metadata.get('portfolio', '') if isinstance(metadata, dict) else ''

        portfolio_mappings = {
            'Finance': 'Economy',
            'Housing': 'Housing',
            'Health': 'Health',
            'Education': 'Education',
            'Transport': 'Transport',
            'Justice': 'Justice',
            'Environment': 'Environment',
            'Defence': 'Defence',
            'Immigration': 'Immigration',
            'Internal Affairs': 'Local Government',
            'Social Development': 'Social Welfare',
            'Agriculture': 'Agriculture',
            'Prime Minister': 'Economy',  # Often economic policy
        }

        if portfolio in portfolio_mappings:
            labels.add(portfolio_mappings[portfolio])

        # Rule 3: Title-based inference for common patterns
        title = action.get('title', '').lower()

        # Bills and Acts often have clear subject matter
        if 'taxation' in title or 'tax' in title:
            labels.add('Tax')

        if 'treaty principles' in title or 'waitangi' in title:
            labels.add('Treaty of Waitangi')

        if 'gang' in title and 'legislation' in title:
            labels.add('Justice')

        # Rule 4: Cross-label relationships
        # If it's about infrastructure and mentions housing, it's likely housing-related
        if 'Infrastructure' in labels and 'housing' in action.get('title', '').lower():
            labels.add('Housing')

        # If it's about economy and mentions specific sectors
        if 'Economy' in labels:
            title_lower = action.get('title', '').lower()
            summary_lower = action.get('summary', '').lower()
            combined = f"{title_lower} {summary_lower}"

            if any(word in combined for word in ['agriculture', 'farming', 'rural']):
                labels.add('Agriculture')
            if any(word in combined for word in ['tourism', 'hospitality']):
                # Tourism is often part of economic policy
                pass  # Keep just Economy for now

        # Rule 5: Ensure minimum labeling
        # If no labels were found but we have clear indicators, add a generic one
        if not labels:
            if source_system == 'LEGISLATION':
                # All legislation affects some area - try to infer from title
                title = action.get('title', '').lower()
                if 'amendment' in title:
                    # Amendment acts often modify existing policy areas
                    if any(word in title for word in ['health', 'education', 'housing']):
                        # Already handled by keyword matching
                        pass
                    else:
                        labels.add('Economy')  # Default for unclear amendments

        return labels

    def get_label_statistics(self, data: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get statistics about label distribution."""
        label_counts = {label: 0 for label in PREDEFINED_LABELS}

        for action in data:
            action_labels = action.get('labels', [])
            for label in action_labels:
                if label in label_counts:
                    label_counts[label] += 1

        return label_counts


def main():
    """Test the label classifier."""
    import sys

    logging.basicConfig(level=logging.INFO)

    # Create test data
    test_data = [
        {
            'id': 'test-001',
            'title': 'Fast-track Approvals Bill',
            'summary': 'A bill to provide a fast-track consenting process for major infrastructure and development projects, streamlining approvals under the Resource Management Act.',
            'source_system': 'PARLIAMENT',
            'metadata': {}
        },
        {
            'id': 'test-002',
            'title': 'Taxation Annual Rates Act 2024',
            'summary': 'Sets the annual rates of income tax and introduces tax policy changes.',
            'source_system': 'LEGISLATION',
            'metadata': {'portfolio': 'Finance'}
        },
        {
            'id': 'test-003',
            'title': 'Health New Zealand Board Appointments',
            'summary': 'Appointments to the Board of Health New Zealand.',
            'source_system': 'GAZETTE',
            'metadata': {'portfolio': 'Health'}
        }
    ]

    classifier = LabelClassifier()
    result = classifier.process(test_data)

    if '--test' in sys.argv:
        print("Label classification results:")
        for action in result:
            print(f"- {action['title']}")
            print(f"  Labels: {', '.join(action['labels'])}")
            print()

        # Show statistics
        stats = classifier.get_label_statistics(result)
        print("Label distribution:")
        for label, count in sorted(stats.items()):
            if count > 0:
                print(f"  {label}: {count}")


if __name__ == '__main__':
    main()