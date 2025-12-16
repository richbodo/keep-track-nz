"""Debug output formatting utilities for Keep Track NZ."""

import re
from typing import Dict, Any, Optional
from datetime import datetime


class DebugContext:
    """Context object for passing debug state through the pipeline."""

    def __init__(self, enabled: bool = False):
        self.enabled = enabled
        self.item_counter = 0
        self.duplicate_counter = 0

    def next_item_number(self) -> int:
        """Get next item number for debugging."""
        self.item_counter += 1
        return self.item_counter

    def next_duplicate_number(self) -> int:
        """Get next duplicate number for debugging."""
        self.duplicate_counter += 1
        return self.duplicate_counter


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
    def format_duplicate_comparison(
        dup_number: int,
        item1: Dict[str, Any],
        item2: Dict[str, Any],
        duplicate_type: str,
        reason: str,
        similarity_score: Optional[float] = None
    ) -> str:
        """Format a duplicate comparison for debug output."""
        header = f"\n🔍 DUPLICATE #{dup_number:02d} - {duplicate_type.upper()}"
        if similarity_score is not None:
            header += f" (similarity: {similarity_score:.1f}%)"

        reason_text = f"\n   Reason: {reason}"

        item1_text = f"\n   Original:\n{DebugFormatter._indent_text(DebugFormatter.format_item_summary(item1), 6)}"
        item2_text = f"\n   Duplicate:\n{DebugFormatter._indent_text(DebugFormatter.format_item_summary(item2), 6)}"

        return f"{header}{reason_text}{item1_text}{item2_text}"

    @staticmethod
    def format_dedup_summary(
        input_count: int,
        output_count: int,
        exact_removed: int,
        similar_removed: int,
        cross_source_removed: int
    ) -> str:
        """Format deduplication summary."""
        total_removed = input_count - output_count
        return f"""
📊 DEDUPLICATION SUMMARY:
   Input items: {input_count}
   Output items: {output_count}
   Total removed: {total_removed}
   - Exact duplicates: {exact_removed}
   - Similar duplicates: {similar_removed}
   - Cross-source duplicates: {cross_source_removed}"""

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

        if debug_stats:
            summary += f"\n\n🔍 DEBUG STATISTICS:"
            summary += f"\n   Total duplicates found: {debug_stats.get('total_duplicates', 0)}"
            summary += f"\n   Exact duplicates: {debug_stats.get('exact_duplicates', 0)}"
            summary += f"\n   Similar duplicates: {debug_stats.get('similar_duplicates', 0)}"
            summary += f"\n   Cross-source duplicates: {debug_stats.get('cross_source_duplicates', 0)}"

        return summary