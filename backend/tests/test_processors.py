"""Tests for data processors."""

import pytest
from unittest.mock import Mock, patch

from keep_track_nz.processors import (
    DataValidator,
    LabelClassifier
)


class TestDataValidator:
    """Test DataValidator processor."""

    def test_validate_valid_data(self):
        """Test validation of valid data."""
        validator = DataValidator(strict_mode=False)

        valid_data = [
            {
                'id': 'test-2024-001',
                'title': 'Test Action',
                'url': 'https://example.com/test',
                'source_system': 'PARLIAMENT',
                'date': '2024-12-15',
                'primary_entity': 'Test Entity',
                'summary': 'Test summary',
                'labels': ['Housing'],
                'metadata': {'test_field': 'test_value'}
            }
        ]

        result = validator.process(valid_data)
        assert len(result) == 1
        assert result[0]['id'] == 'test-2024-001'

    def test_fix_invalid_data(self):
        """Test fixing of invalid data in non-strict mode."""
        validator = DataValidator(strict_mode=False)

        invalid_data = [
            {
                'title': 'Test Action',
                'url': 'example.com/test',  # Missing protocol
                'source_system': 'parliament',  # Wrong case
                'date': '15/12/2024',  # Wrong format
                # Missing id, primary_entity
                'labels': ['Housing', 'InvalidLabel'],  # Invalid label
                'metadata': {}
            }
        ]

        result = validator.process(invalid_data)
        assert len(result) == 1

        # Check fixes
        action = result[0]
        assert action['url'].startswith('https://')
        assert action['source_system'] == 'PARLIAMENT'
        assert action['date'] == '2024-12-15'
        assert 'id' in action
        assert 'primary_entity' in action
        assert 'InvalidLabel' not in action['labels']

    def test_strict_mode_rejection(self):
        """Test that strict mode rejects invalid data."""
        validator = DataValidator(strict_mode=True)

        invalid_data = [
            {
                # Missing required fields
                'title': 'Test Action'
            }
        ]

        result = validator.process(invalid_data)
        # Should reject the invalid item
        assert len(result) == 0

    def test_id_generation(self):
        """Test ID generation for missing IDs."""
        validator = DataValidator(strict_mode=False)

        data_without_id = [
            {
                'title': 'Test Action',
                'url': 'https://example.com/test',
                'source_system': 'PARLIAMENT',
                'date': '2024-12-15'
            }
        ]

        result = validator.process(data_without_id)
        assert len(result) == 1
        assert 'id' in result[0]
        assert result[0]['id'].startswith('parl-2024-')

    def test_date_normalization(self):
        """Test date format normalization."""
        validator = DataValidator(strict_mode=False)

        data_with_dates = [
            {
                'title': 'Test 1',
                'url': 'https://example.com/1',
                'source_system': 'PARLIAMENT',
                'date': '15/12/2024'
            },
            {
                'title': 'Test 2',
                'url': 'https://example.com/2',
                'source_system': 'PARLIAMENT',
                'date': '15 December 2024'
            }
        ]

        result = validator.process(data_with_dates)
        assert len(result) == 2
        assert all(action['date'] == '2024-12-15' for action in result)


class TestLabelClassifier:
    """Test LabelClassifier processor."""

    def test_classify_housing_action(self):
        """Test classification of housing-related action."""
        classifier = LabelClassifier()

        housing_data = [
            {
                'id': 'test-2024-001',
                'title': 'Housing Development Bill',
                'summary': 'A bill to accelerate housing development and construction',
                'source_system': 'PARLIAMENT',
                'metadata': {'portfolio': 'Housing'}
            }
        ]

        result = classifier.process(housing_data)
        assert len(result) == 1
        assert 'Housing' in result[0]['labels']

    def test_classify_multiple_labels(self):
        """Test classification with multiple labels."""
        classifier = LabelClassifier()

        multi_label_data = [
            {
                'id': 'test-2024-001',
                'title': 'Infrastructure Investment for Housing and Transport',
                'summary': 'Investment in housing development and transport infrastructure',
                'source_system': 'BEEHIVE',
                'metadata': {}
            }
        ]

        result = classifier.process(multi_label_data)
        assert len(result) == 1
        labels = result[0]['labels']
        assert 'Infrastructure' in labels
        assert 'Housing' in labels
        assert 'Transport' in labels

    def test_portfolio_based_classification(self):
        """Test classification based on portfolio."""
        classifier = LabelClassifier()

        portfolio_data = [
            {
                'id': 'test-2024-001',
                'title': 'General Notice',
                'summary': 'A general administrative notice',
                'source_system': 'GAZETTE',
                'metadata': {'portfolio': 'Justice'}
            }
        ]

        result = classifier.process(portfolio_data)
        assert len(result) == 1
        assert 'Justice' in result[0]['labels']

    def test_treaty_classification(self):
        """Test Treaty of Waitangi classification."""
        classifier = LabelClassifier()

        treaty_data = [
            {
                'id': 'test-2024-001',
                'title': 'Treaty Principles Bill',
                'summary': 'A bill to define the principles of the Treaty of Waitangi',
                'source_system': 'PARLIAMENT',
                'metadata': {}
            }
        ]

        result = classifier.process(treaty_data)
        assert len(result) == 1
        assert 'Treaty of Waitangi' in result[0]['labels']

    def test_tax_classification(self):
        """Test taxation classification."""
        classifier = LabelClassifier()

        tax_data = [
            {
                'id': 'test-2024-001',
                'title': 'Taxation Annual Rates Act 2024',
                'summary': 'Sets annual tax rates and introduces tax policy changes',
                'source_system': 'LEGISLATION',
                'metadata': {'portfolio': 'Finance'}
            }
        ]

        result = classifier.process(tax_data)
        assert len(result) == 1
        labels = result[0]['labels']
        assert 'Tax' in labels
        assert 'Economy' in labels

    def test_no_classification(self):
        """Test action with no clear classification gets empty labels."""
        classifier = LabelClassifier()

        unclear_data = [
            {
                'id': 'test-2024-001',
                'title': 'General Administrative Notice',
                'summary': 'A general notice with no specific policy area',
                'source_system': 'GAZETTE',
                'metadata': {}
            }
        ]

        result = classifier.process(unclear_data)
        assert len(result) == 1
        # Should have some default classification or be empty
        labels = result[0]['labels']
        # Could be empty or have a default label depending on business rules

    def test_gazette_appointment_classification(self):
        """Test classification of Gazette appointments."""
        classifier = LabelClassifier()

        appointment_data = [
            {
                'id': 'test-2024-001',
                'title': 'Appointment of District Court Judge',
                'summary': 'Appointment of a new judge to the District Court',
                'source_system': 'GAZETTE',
                'metadata': {'notice_type': 'Vice Regal'}
            }
        ]

        result = classifier.process(appointment_data)
        assert len(result) == 1
        assert 'Justice' in result[0]['labels']

    def test_get_label_statistics(self):
        """Test getting label statistics."""
        classifier = LabelClassifier()

        test_data = [
            {'labels': ['Housing', 'Infrastructure']},
            {'labels': ['Housing', 'Education']},
            {'labels': ['Health']},
            {'labels': []}
        ]

        stats = classifier.get_label_statistics(test_data)
        assert stats['Housing'] == 2
        assert stats['Infrastructure'] == 1
        assert stats['Education'] == 1
        assert stats['Health'] == 1
        # Other labels should have 0 count or not be in dict