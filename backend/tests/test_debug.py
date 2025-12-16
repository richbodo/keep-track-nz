"""Tests for debug functionality."""

import pytest
from unittest.mock import Mock, patch
from io import StringIO
import sys

from keep_track_nz.debug import DebugContext, DebugFormatter


class TestDebugContext:
    """Test DebugContext functionality."""

    def test_debug_context_enabled(self):
        """Test debug context when enabled."""
        context = DebugContext(enabled=True)
        assert context.enabled is True
        assert context.item_counter == 0

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


if __name__ == '__main__':
    pytest.main([__file__])