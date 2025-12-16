"""Debug output formatting utilities for Keep Track NZ."""

import re
from typing import Dict, Any, Optional
from datetime import datetime


class DebugContext:
    """Context object for passing debug state through the pipeline."""

    def __init__(self, enabled: bool = False):
        self.enabled = enabled
        self.item_counter = 0

    def next_item_number(self) -> int:
        """Get next item number for debugging."""
        self.item_counter += 1
        return self.item_counter


class DebugFormatter:
    """Utilities for formatting debug output."""

    @staticmethod
    def format_item_header(item_number: int, title: str, source_system: str) -> str:
        """Format a header for a scraped item."""
        return f"\n[{item_number:03d}] {source_system} | {title}"

    @staticmethod
    def format_first_sentence(text: str, max_length: int = 200) -> str:
        """Extract and format the first sentence from text content."""
        if not text:
            return "[No content]"

        # Clean HTML tags if present
        clean_text = re.sub(r'<[^>]+>', ' ', text)
        # Normalize whitespace
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()

        if not clean_text:
            return "[No readable content]"

        # Find first sentence (simple approach)
        sentences = re.split(r'[.!?]+', clean_text)
        first_sentence = sentences[0].strip() if sentences else clean_text

        # Truncate if too long
        if len(first_sentence) > max_length:
            first_sentence = first_sentence[:max_length-3] + "..."

        return first_sentence or "[Empty content]"

    @staticmethod
    def format_item_summary(item: Dict[str, Any]) -> str:
        """Format a complete item summary for debug output."""
        title = item.get('title', '[No title]')
        source = item.get('source_system', 'UNKNOWN')
        url = item.get('url', '[No URL]')
        date = item.get('date', '[No date]')

        # Get content for first sentence
        content_fields = ['summary', 'description', 'content', 'body']
        content = ""
        for field in content_fields:
            if field in item and item[field]:
                content = item[field]
                break

        first_sentence = DebugFormatter.format_first_sentence(content)

        return f"""     Title: {title}
     First sentence: {first_sentence}
     Date: {date}
     URL: {url[:80]}{'...' if len(url) > 80 else ''}"""

    @staticmethod
    def format_scraper_summary(source_name: str, count: int) -> str:
        """Format scraper completion summary."""
        return f"\n✅ {source_name} scraping complete: {count} items collected"

    @staticmethod
    def format_section_header(section_name: str) -> str:
        """Format a debug section header."""
        border = "=" * (len(section_name) + 4)
        return f"\n{border}\n  {section_name.upper()}\n{border}"

    @staticmethod
    def _indent_text(text: str, spaces: int) -> str:
        """Indent all lines of text by specified number of spaces."""
        indent = " " * spaces
        return "\n".join(f"{indent}{line}" for line in text.split("\n"))

    @staticmethod
    def format_pipeline_debug_summary(
        total_scraped: int,
        total_processed: int,
        source_stats: Dict[str, Dict[str, Any]],
        debug_stats: Dict[str, Any]
    ) -> str:
        """Format final pipeline debug summary."""
        summary = f"""
{DebugFormatter.format_section_header("DEBUG PIPELINE SUMMARY")}

📈 OVERALL STATISTICS:
   Total scraped: {total_scraped}
   Total processed: {total_processed}
   Items removed: {total_scraped - total_processed}

📋 SOURCE BREAKDOWN:"""

        for source, stats in source_stats.items():
            scraped = stats.get('scraped', 0)
            success = stats.get('success', False)
            status = "✓" if success else "✗"
            summary += f"\n   {status} {source}: {scraped} items"

        # No longer displaying deduplication statistics

        return summary