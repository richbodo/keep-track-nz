# Feature: Fix Beehive Scraper

## Feature Description
Fix the existing Beehive scraper that is currently returning zero data from beehive.govt.nz government announcements. The scraper should reliably collect press releases, speeches, and ministerial announcements from the Beehive website using a robust RSS-first approach with HTML fallback and comprehensive error handling.

## User Story
As a developer maintaining the Keep Track NZ application
I want the Beehive scraper to reliably collect government announcements
So that users can access current New Zealand government press releases and speeches through our platform

## Problem Statement
The current Beehive scraper at `backend/src/keep_track_nz/scrapers/beehive.py` is failing to extract any data from beehive.govt.nz despite the website containing abundant recent content. Analysis shows the scraper has incorrect URL patterns, outdated HTML selectors, and lacks the robust RSS feed integration recommended in the comprehensive beehive-scraping-guide.md documentation.

## Solution Statement
Implement a comprehensive Beehive scraping strategy that prioritizes RSS feeds (the most reliable method) with HTML scraping fallback and browser automation as a last resort. Update all URL patterns, HTML selectors, and parsing logic to match the current website structure. Add comprehensive debugging, error handling, and data validation to ensure reliable long-term operation.

## Relevant Files
Use these files to implement the feature:

- `backend/src/keep_track_nz/scrapers/beehive.py` - Main Beehive scraper that needs complete refactoring using RSS-first approach
- `backend/src/keep_track_nz/scrapers/base.py` - Base scraper class that may need enhanced debug capabilities for RSS feed handling
- `docs/beehive-scraping-guide.md` - Comprehensive documentation detailing the exact implementation strategy including RSS feeds, HTML structures, and fallback methods
- `backend/src/keep_track_nz/debug/formatters.py` - Debug formatting utilities for enhanced logging
- `backend/tests/test_scrapers.py` - Test file for validating scraper functionality

### New Files
- `backend/requirements-scraping.txt` - Additional dependencies needed for RSS parsing (feedparser) and browser automation (playwright)

## Implementation Plan

### Phase 1: Foundation
Add RSS parsing capabilities and enhanced debugging infrastructure to support the RSS-first approach documented in the beehive-scraping-guide.md. Install required dependencies and update the base scraper class with RSS-specific debug methods.

### Phase 2: Core Implementation
Completely refactor the Beehive scraper to implement the comprehensive RSS-first strategy documented in beehive-scraping-guide.md. This includes RSS feed parsing, HTML fallback, data deduplication, validation, and enhanced metadata extraction.

### Phase 3: Integration
Integrate the new scraper with the existing data pipeline, ensuring compatibility with processors and exporters. Add comprehensive testing and validation to ensure reliable operation in production.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Install Required Dependencies
- Add `feedparser` dependency for RSS parsing using `uv add feedparser`
- Add `playwright` dependency for browser automation fallback using `uv add playwright`
- Install Playwright browser using `playwright install chromium`

### Step 2: Enhance Base Scraper with RSS Support
- Add `_debug_log_rss_feed()` method to base scraper for RSS feed parsing debug output
- Add `_parse_rss_date()` utility method for RSS date format normalization
- Add `_validate_rss_item()` method for RSS feed item validation
- Update base scraper headers to handle both HTML and RSS content types

### Step 3: Implement RSS Feed Infrastructure
- Create `_scrape_beehive_rss()` method that implements the RSS parsing strategy from beehive-scraping-guide.md
- Create `_extract_minister_from_content()` method for minister name extraction from RSS content
- Create `_extract_portfolio_from_content()` method for portfolio detection from RSS tags and content
- Create `deduplicate_beehive_items()` method using URL and title+date as deduplication keys

### Step 4: Implement HTML Fallback Infrastructure
- Update `_parse_announcements_page()` method with correct HTML selectors from the guide
- Update `_extract_announcement_from_element()` with proper article parsing for current Beehive structure
- Fix URL patterns from `/release` to `/releases` and `/speech` to `/speeches`
- Add enhanced date parsing for multiple Beehive date formats

### Step 5: Implement Browser Automation Fallback
- Create `_scrape_beehive_with_browser()` method using Playwright for JavaScript-rendered content
- Add `_parse_article_with_playwright()` method for browser-based HTML parsing
- Implement browser session management with proper error handling

### Step 6: Implement Comprehensive Scraping Strategy
- Create main `scrape_beehive_comprehensive()` method that orchestrates RSS-first → HTML fallback → browser automation
- Implement retry logic with exponential backoff for each scraping method
- Add comprehensive error handling and logging for each fallback level
- Implement data enhancement and validation pipeline

### Step 7: Update Data Processing and Validation
- Implement `enhance_beehive_items()` method for metadata enrichment
- Implement `validate_beehive_item()` method with comprehensive validation rules
- Implement `generate_beehive_id()` method for consistent ID generation
- Update `create_government_action()` method to handle enhanced data structure

### Step 8: Add Performance Monitoring
- Implement `monitor_beehive_health()` method for endpoint health checking
- Add performance metrics logging for each scraping method
- Add RSS feed availability monitoring
- Implement rate limiting and respectful crawling delays

### Step 9: Comprehensive Testing
- Create unit tests for RSS parsing functionality
- Create unit tests for HTML fallback parsing
- Create integration tests for the full scraping pipeline
- Add tests for data validation and deduplication logic

### Step 10: Validation and Integration Testing
- Test RSS scraping with `cd backend && uv run python -m keep_track_nz.scrapers.beehive --test --rss`
- Test HTML fallback with `cd backend && uv run python -m keep_track_nz.scrapers.beehive --test --html`
- Test browser automation with `cd backend && uv run python -m keep_track_nz.scrapers.beehive --test --browser`
- Run full pipeline validation using the validation commands

## Testing Strategy

### Unit Tests
- Test RSS feed parsing with mock RSS data
- Test HTML parsing with mock HTML responses
- Test date normalization with various date formats
- Test data validation with valid and invalid items
- Test deduplication logic with duplicate entries

### Integration Tests
- Test RSS feeds availability and structure from live endpoints
- Test HTML fallback against live Beehive pages
- Test browser automation with real website interaction
- Test data pipeline integration with processors and exporters

### Edge Cases
- Handle RSS feed unavailability or malformed XML
- Handle HTML structure changes and missing elements
- Handle bot protection and rate limiting responses
- Handle network timeouts and connection failures
- Handle empty or malformed date strings

## Acceptance Criteria
- Beehive scraper successfully collects at least 10 recent announcements in debug mode
- RSS feed parsing works for all major Beehive feeds (releases, speeches, features)
- HTML fallback successfully activates when RSS feeds fail
- Browser automation fallback works when HTML parsing fails
- Data validation rejects malformed entries and accepts valid ones
- Performance metrics show scraping completion within 30 seconds for normal operations
- Debug output provides clear visibility into each scraping method attempt
- All tests pass with zero regressions to existing functionality

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `cd backend && uv add feedparser && uv add playwright` - Install required dependencies
- `cd backend && playwright install chromium` - Install browser for automation
- `cd backend && uv run python -m keep_track_nz.scrapers.beehive --test` - Test comprehensive scraper
- `cd backend && uv run python -m keep_track_nz.scrapers.beehive --debug --limit 5` - Test with debug output
- `cd backend && uv run python -c "import feedparser; print('RSS parsing available')"` - Verify RSS capability
- `cd backend && uv run python -c "from playwright.sync_api import sync_playwright; print('Browser automation available')"` - Verify browser capability
- `cd backend && uv run python -m keep_track_nz.main --dry-run --debug --limit 10` - Test full pipeline integration
- `cd backend && uv run pytest tests/test_scrapers.py::test_beehive_scraper -v` - Run specific scraper tests
- `cd backend && uv run pytest tests/ -v` - Run full test suite for regressions

## Notes
- The beehive-scraping-guide.md provides comprehensive implementation details including exact code examples for RSS parsing, HTML fallback, and browser automation
- RSS feeds are the most reliable method as they're designed for automated consumption and less likely to change
- The scraper should gracefully degrade from RSS → HTML → Browser automation, only using more complex methods when necessary
- Comprehensive debug logging is essential for troubleshooting when government websites change their structure
- The implementation should be resilient to bot protection measures while respecting rate limits and server resources
- Consider adding RSS feed monitoring to detect when feeds become unavailable and alert for maintenance needs