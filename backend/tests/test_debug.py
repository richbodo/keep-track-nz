"""Tests for debug functionality."""

import pytest
from unittest.mock import Mock, patch
from io import StringIO
import sys

from keep_track_nz.debug import DebugContext, DebugFormatter
from keep_track_nz.processors.deduplicator import Deduplicator


class TestDebugContext:
    """Test DebugContext functionality."""

    def test_debug_context_enabled(self):
        """Test debug context when enabled."""
        context = DebugContext(enabled=True)
        assert context.enabled is True
        assert context.item_counter == 0
        assert context.duplicate_counter == 0

    def test_debug_context_disabled(self):
        """Test debug context when disabled."""
        context = DebugContext(enabled=False)
        assert context.enabled is False

    def test_item_counter_increment(self):
        """Test item counter increments correctly."""
        context = DebugContext(enabled=True)
        assert context.next_item_number() == 1
        assert context.next_item_number() == 2
        assert context.next_item_number() == 3

    def test_duplicate_counter_increment(self):
        """Test duplicate counter increments correctly."""
        context = DebugContext(enabled=True)
        assert context.next_duplicate_number() == 1
        assert context.next_duplicate_number() == 2


class TestDebugFormatter:
    """Test DebugFormatter functionality."""

    def test_format_item_header(self):
        """Test formatting of item headers."""
        result = DebugFormatter.format_item_header(1, "Test Title", "PARLIAMENT")
        assert "[001] PARLIAMENT | Test Title" in result

    def test_format_first_sentence(self):
        """Test first sentence extraction."""
        text = "This is the first sentence. This is the second sentence."
        result = DebugFormatter.format_first_sentence(text)
        assert result == "This is the first sentence"

    def test_format_first_sentence_with_html(self):
        """Test first sentence extraction with HTML."""
        text = "<p>This is the <b>first</b> sentence.</p> This is the second."
        result = DebugFormatter.format_first_sentence(text)
        assert "This is the first sentence" in result

    def test_format_first_sentence_empty(self):
        """Test first sentence extraction with empty text."""
        result = DebugFormatter.format_first_sentence("")
        assert result == "[No content]"

    def test_format_first_sentence_truncation(self):
        """Test first sentence truncation."""
        long_text = "A" * 300
        result = DebugFormatter.format_first_sentence(long_text, max_length=100)
        assert len(result) <= 100
        assert result.endswith("...")

    def test_format_item_summary(self):
        """Test formatting of item summary."""
        item = {
            'title': 'Test Bill',
            'url': 'https://example.com/test',
            'date': '2024-12-16',
            'summary': 'This is a test bill summary.'
        }
        result = DebugFormatter.format_item_summary(item)
        assert "Title: Test Bill" in result
        assert "Date: 2024-12-16" in result
        assert "URL: https://example.com/test" in result
        assert "First sentence: This is a test bill summary" in result

    def test_format_duplicate_comparison(self):
        """Test formatting of duplicate comparison."""
        item1 = {'title': 'Bill A', 'url': 'http://example.com/a', 'date': '2024-01-01'}
        item2 = {'title': 'Bill A', 'url': 'http://example.com/b', 'date': '2024-01-01'}

        result = DebugFormatter.format_duplicate_comparison(
            1, item1, item2, "exact", "Identical titles", 95.0
        )
        assert "DUPLICATE #01" in result
        assert "EXACT" in result
        assert "similarity: 95.0%" in result
        assert "Identical titles" in result

    def test_format_dedup_summary(self):
        """Test formatting of deduplication summary."""
        result = DebugFormatter.format_dedup_summary(100, 80, 10, 5, 5)
        assert "Input items: 100" in result
        assert "Output items: 80" in result
        assert "Total removed: 20" in result
        assert "Exact duplicates: 10" in result
        assert "Similar duplicates: 5" in result
        assert "Cross-source duplicates: 5" in result


class TestDeduplicatorDebug:
    """Test deduplicator debug output."""

    def test_deduplicator_with_debug_context(self):
        """Test deduplicator with debug context enabled."""
        context = DebugContext(enabled=True)
        dedup = Deduplicator(debug_context=context)
        assert dedup.debug_context is context

    def test_deduplicator_debug_exact_duplicates(self):
        """Test debug output for exact duplicates."""
        context = DebugContext(enabled=True)
        dedup = Deduplicator(debug_context=context)

        test_data = [
            {
                'id': 'test-001',
                'title': 'Test Bill',
                'url': 'https://example.com/bill1',
                'date': '2024-12-05',
                'source_system': 'PARLIAMENT'
            },
            {
                'id': 'test-001',  # Exact duplicate ID
                'title': 'Test Bill',
                'url': 'https://example.com/bill1',
                'date': '2024-12-05',
                'source_system': 'PARLIAMENT'
            }
        ]

        # Capture stdout
        captured_output = StringIO()
        with patch('sys.stdout', captured_output):
            result = dedup.process(test_data)

        output = captured_output.getvalue()
        assert "DEDUPLICATION PROCESS" in output
        assert "CHECKING FOR EXACT DUPLICATES" in output
        assert len(result) == 1  # One duplicate should be removed

    def test_deduplicator_debug_disabled(self):
        """Test deduplicator with debug disabled."""
        # No debug context (disabled by default)
        dedup = Deduplicator()

        test_data = [
            {'id': 'test-001', 'title': 'Test Bill', 'source_system': 'PARLIAMENT'},
            {'id': 'test-002', 'title': 'Another Bill', 'source_system': 'PARLIAMENT'}
        ]

        # Should not produce debug output
        captured_output = StringIO()
        with patch('sys.stdout', captured_output):
            result = dedup.process(test_data)

        output = captured_output.getvalue()
        assert "DEDUPLICATION PROCESS" not in output
        assert len(result) == 2  # No duplicates to remove

    @patch('keep_track_nz.processors.deduplicator.fuzz.ratio')
    def test_similar_duplicates_debug(self, mock_fuzz_ratio):
        """Test debug output for similar duplicates."""
        mock_fuzz_ratio.return_value = 90  # High similarity

        context = DebugContext(enabled=True)
        dedup = Deduplicator(debug_context=context)

        test_data = [
            {
                'id': 'test-001',
                'title': 'Climate Change Bill',
                'date': '2024-12-05',
                'source_system': 'PARLIAMENT'
            },
            {
                'id': 'test-002',
                'title': 'Climate Change Act',  # Similar title
                'date': '2024-12-05',
                'source_system': 'PARLIAMENT'
            }
        ]

        captured_output = StringIO()
        with patch('sys.stdout', captured_output):
            result = dedup.process(test_data)

        output = captured_output.getvalue()
        assert "CHECKING FOR SIMILAR DUPLICATES" in output


if __name__ == '__main__':
    pytest.main([__file__])