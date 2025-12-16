# Feature: Backend Debug Mode

## Feature Description
A comprehensive debug mode for the Keep Track NZ backend that provides detailed visibility into the scraping and deduplication processes. When enabled via a `--debug` command-line flag, the system will output detailed information about each scraped item including titles, first sentences, and a complete audit trail of the deduplication process showing exactly how duplicates are identified and removed.

## User Story
As a developer or system administrator
I want to see detailed debug information about the scraping and deduplication process
So that I can understand what data is being collected, troubleshoot issues, monitor data quality, and verify that the deduplication logic is working correctly

## Problem Statement
Currently, the Keep Track NZ backend provides only high-level logging about the number of items scraped and duplicates removed. When issues arise with data quality, missing items, or incorrect deduplication, there's no easy way to see exactly what was scraped, how items were compared, or why specific duplicates were identified. This makes troubleshooting difficult and reduces confidence in the system's data collection accuracy.

## Solution Statement
Implement a `--debug` mode that enhances the existing logging infrastructure to provide:
1. Detailed output for each scraped item (title + first sentence of summary/body)
2. Numbered listing of all items as they are processed
3. Complete deduplication audit trail showing:
   - When duplicates are found (exact, similar, or cross-source)
   - Both items being compared
   - Similarity scores and reasons for duplicate classification
   - Which item was kept and why
4. Summary statistics and processing insights

This solution leverages the existing processor pipeline and adds debug-specific output without modifying core business logic.

## Relevant Files
Use these files to implement the feature:

- `backend/src/keep_track_nz/main.py` - Main orchestrator where `--debug` flag will be added and debug mode coordinated
- `backend/src/keep_track_nz/processors/deduplicator.py` - Core deduplication logic that needs debug output enhancement
- `backend/src/keep_track_nz/processors/base.py` - Base processor class where debug logging infrastructure will be added
- `backend/src/keep_track_nz/scrapers/beehive.py` - Example scraper for implementing debug output pattern
- `backend/src/keep_track_nz/scrapers/parliament.py` - Parliament scraper for debug output
- `backend/src/keep_track_nz/scrapers/legislation.py` - Legislation scraper for debug output
- `backend/src/keep_track_nz/scrapers/gazette.py` - Gazette scraper for debug output
- `backend/tests/test_main.py` - Tests for main orchestrator including debug mode
- `backend/tests/test_deduplicator.py` - Tests for enhanced deduplicator debug functionality

### New Files
- `backend/src/keep_track_nz/debug/__init__.py` - Debug utility module
- `backend/src/keep_track_nz/debug/formatters.py` - Debug output formatting utilities
- `backend/tests/test_debug.py` - Tests for debug functionality

## Implementation Plan
### Phase 1: Foundation
Create the debug infrastructure and extend the argument parser to support the `--debug` flag. Establish debug output formatting utilities and modify the base processor to support debug mode context.

### Phase 2: Core Implementation
Implement debug output in the deduplicator to show detailed duplicate detection reasoning. Add numbered item listing in scrapers and enhance the main orchestrator to coordinate debug output across all processors.

### Phase 3: Integration
Integrate debug mode with all scrapers and processors, ensure consistent formatting, add comprehensive test coverage, and validate the feature works end-to-end with real data.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Create Debug Infrastructure
- Create debug module with output formatting utilities
- Add debug parameter support to BaseProcessor
- Extend argument parser in main.py to accept `--debug` flag
- Create debug context object for passing debug state through pipeline

### Enhance Deduplicator Debug Output
- Modify Deduplicator class to accept debug mode parameter
- Add detailed logging for exact duplicate detection (show both items, reason for duplicate classification)
- Add detailed logging for similar duplicate detection (show similarity scores, comparison criteria)
- Add detailed logging for cross-source duplicate detection (show source types, matching logic)
- For each duplicate found, show both the original and duplicate item with clear formatting

### Implement Scraper Debug Output
- Modify each scraper (beehive, parliament, legislation, gazette) to support debug mode
- Add numbered listing of scraped items with title and first sentence of summary/body
- Ensure consistent formatting across all scrapers
- Add item count summaries at the end of each scraper's debug output

### Integrate Debug Mode in Main Orchestrator
- Pass debug flag through to all processors and scrapers
- Add debug summary at the end showing total items processed, duplicates removed, and final counts
- Ensure debug output is coordinated and doesn't conflict with normal logging

### Add Comprehensive Testing
- Create unit tests for debug output formatting utilities
- Add tests for deduplicator debug functionality using controlled test data
- Create integration tests for full pipeline debug mode
- Add tests to verify debug output doesn't affect normal operation when disabled

### Validation and Documentation
- Test debug mode with real data from all sources
- Verify output is readable and useful for troubleshooting
- Update README with debug mode usage examples
- Run the `Validation Commands` to ensure zero regressions

## Testing Strategy
### Unit Tests
- Debug formatting utilities produce expected output format
- Deduplicator debug methods correctly identify and format duplicate information
- Main orchestrator properly propagates debug flag to all components
- Debug mode can be enabled and disabled without affecting core functionality

### Integration Tests
- Full pipeline with debug mode produces complete audit trail
- Debug output includes all expected elements (numbered items, similarity scores, duplicate reasoning)
- Debug mode works with all scrapers and shows expected item details
- Performance impact of debug mode is minimal

### Edge Cases
- Debug mode handles empty scraping results gracefully
- Debug output works when no duplicates are found
- Debug mode handles scraper errors and continues processing
- Very large similarity scores and edge case comparisons are displayed correctly

## Acceptance Criteria
- `--debug` flag is available in the command line interface
- Each scraped item is displayed with number, title, and first sentence of summary/body
- For every duplicate detected, both items are shown with clear formatting
- Exact duplicates show the specific matching criteria (ID, URL, etc.)
- Similar duplicates show similarity scores and date comparison results
- Cross-source duplicates show source types and matching reasoning
- Debug output is properly formatted and easy to read
- Debug mode has minimal performance impact (< 10% slowdown)
- All existing tests pass with debug mode enabled
- Debug mode can be enabled/disabled without affecting normal operation

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `cd backend && uv run pytest tests/` - Run all tests to ensure zero regressions
- `cd backend && uv run python -m keep_track_nz.main --debug --dry-run --limit 5` - Test debug mode with limited data
- `cd backend && uv run python -m keep_track_nz.main --help` - Verify --debug flag appears in help
- `cd backend && uv run python -m keep_track_nz.main --dry-run --limit 5` - Verify normal mode still works without debug output
- `cd backend && uv run python -m keep_track_nz.scrapers.beehive --debug` - Test scraper debug output (if scraper supports standalone testing)

## Notes
- The debug output should be sent to stdout/stderr and not interfere with normal log files or export files
- Consider implementing different debug verbosity levels in the future (--debug-level 1,2,3)
- Debug mode should be performance conscious - avoid expensive operations that aren't essential for debugging
- The first sentence extraction should handle various text formats gracefully (HTML, plain text, etc.)
- Consider adding color coding to debug output to improve readability
- Debug output should be deterministic and suitable for automated testing
- The feature sets foundation for future debugging and monitoring capabilities