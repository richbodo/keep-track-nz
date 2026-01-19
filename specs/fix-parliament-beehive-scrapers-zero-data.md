# Bug: Parliament and Beehive scrapers gathering zero data

## Bug Description
The Parliament and Beehive scrapers are returning zero items during scraping operations. The debug output shows that both scrapers complete successfully but collect 0 items, while the Legislation and Gazette scrapers work correctly and collect 145 and 100 items respectively. This indicates a fundamental issue with the HTML parsing logic and URL targeting in both scrapers.

## Problem Statement
The Parliament scraper at `backend/src/keep_track_nz/scrapers/parliament.py` and Beehive scraper at `backend/src/keep_track_nz/scrapers/beehive.py` are failing to extract any data from their respective government websites despite the websites containing current, accessible data.

## Solution Statement
Fix the scrapers by updating their URL targets, HTML selectors, and parsing logic to match the current website structures. Add comprehensive debug logging to provide visibility into each scraping step. Update the scrapers to handle the JavaScript-heavy Parliament site and the correct HTML structure of the Beehive releases page.

## Steps to Reproduce
1. Run the backend scraper in debug mode: `cd backend && uv run python -m keep_track_nz.main --dry-run --debug`
2. Observe in the output that Parliament scraper reports "0 items collected"
3. Observe in the output that Beehive scraper reports "0 items collected"
4. Compare with Legislation (145 items) and Gazette (100 items) which work correctly

## Root Cause Analysis

### Parliament Scraper Issues:
1. **JavaScript Dependency**: The Parliament site (bills.parliament.nz) is heavily JavaScript-based and loads content dynamically. The scraper uses basic HTML parsing but the content loads after initial page load.
2. **Incorrect API/URL Targets**: The scraper attempts multiple URLs but none match the actual working endpoints.
3. **Wrong HTML Selectors**: The HTML structure has changed since the scraper was written, so selectors like `.bill-item`, `.bill-card` no longer match.
4. **Missing API Integration**: The site has JSON APIs that should be used instead of HTML scraping.

### Beehive Scraper Issues:
1. **Incorrect URL Structure**: The scraper targets `/release` and `/speech` but should target `/releases` and `/speeches`.
2. **Wrong HTML Selectors**: Current selectors don't match the actual HTML structure of the listings.
3. **Missing Container Logic**: The scraper looks for containers that don't exist in the current page structure.

### Debug Logging Issues:
1. **Insufficient Visibility**: Both scrapers lack detailed debug output about what URLs they're accessing and what HTML elements they find.
2. **No Element Count Reporting**: They don't report how many potential elements they found before filtering.
3. **No Content Sampling**: They don't show samples of the HTML they're trying to parse.

## Relevant Files
Use these files to fix the bug:

### Parliament Scraper
- `backend/src/keep_track_nz/scrapers/parliament.py` - Main scraper that needs URL and selector fixes, plus API integration for JavaScript content
- `backend/src/keep_track_nz/scrapers/base.py` - Base class that may need enhanced debug methods

### Beehive Scraper
- `backend/src/keep_track_nz/scrapers/beehive.py` - Main scraper that needs URL corrections and HTML selector updates
- `backend/src/keep_track_nz/scrapers/base.py` - Base class for enhanced debug logging

### Documentation Files
- `docs/parliament-scraping-guide.md` - New file documenting how to scrape Parliament site with current structure and APIs
- `docs/beehive-scraping-guide.md` - New file documenting Beehive site structure and correct selectors

## Step by Step Tasks

### Step 1: Enhance Base Debug Capabilities
- Add `_debug_log_request_details()` method to base scraper class to log URL, status code, content type, and response size
- Add `_debug_log_html_sample()` method to log first 500 characters of HTML response
- Add `_debug_log_selector_attempts()` method to log which selectors were tried and how many elements found
- Enhance `_debug_log_scraped_items()` method to show more detail about successful vs failed extractions

### Step 2: Fix Parliament Scraper URLs and API Integration
- Update Parliament scraper to use the correct API endpoints discovered via Playwright inspection
- Add API endpoint: `https://bills.parliament.nz/api/bills` with proper parameters
- Add fallback to HTML scraping of `https://bills.parliament.nz/bills-proposed-laws?Tab=Current`
- Implement JavaScript-aware request handling or API-first approach
- Add comprehensive debug logging for each URL attempt and API response structure

### Step 3: Fix Parliament Scraper HTML Selectors
- Update HTML selectors to match current page structure: `table tbody tr` for bill rows
- Update title extraction to use the link text within each row
- Update URL extraction to get the `href` attribute from links in the table
- Update bill number extraction to use the "Bill no." column content
- Update date extraction to use the "Last activity" column content
- Add debug logging showing exactly which elements are found and their content

### Step 4: Fix Beehive Scraper URLs
- Correct URLs from `/release` to `/releases` and `/speech` to `/speeches`
- Verify URLs match the actual working endpoints found via Playwright inspection
- Add debug logging for each URL being attempted

### Step 5: Fix Beehive Scraper HTML Selectors
- Update selectors to target the correct article containers: `article` elements within the main content area
- Update title extraction to use `heading h2 a` within each article
- Update URL extraction from the heading links
- Update date extraction to use `time` elements with proper parsing
- Update minister/entity extraction to use the `emphasis a` links for minister names
- Add debug logging showing found articles, titles, and extracted data

### Step 6: Create Documentation and Knowledge Storage
- Create comprehensive documentation of the current Parliament site structure including API endpoints, HTML selectors, and JavaScript behavior patterns
- Create comprehensive documentation of the current Beehive site structure including URL patterns, HTML selectors, and content organization
- Include examples of working requests and responses
- Document the debug logging patterns for future maintenance

### Step 7: Enhanced Error Handling and Recovery
- Add retry logic with exponential backoff for failed requests
- Add handling for rate limiting and request throttling
- Add fallback mechanisms when primary scraping methods fail
- Add clear error messages indicating which specific step failed

### Step 8: Add Selenium/Playwright Option for Parliament
- Add optional Playwright integration for Parliament scraper to handle JavaScript-rendered content
- Make it configurable so the scraper can fall back to API-first, then HTML, then JavaScript rendering
- Document when each method should be used

### Step 9: Integration Testing and Validation
- Test both scrapers individually with `--test` flag to verify they can extract data
- Test the full pipeline to ensure scraped data integrates correctly with processors
- Verify that the enhanced debug output provides sufficient information for troubleshooting
- Test with various network conditions and error scenarios

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

- `cd backend && uv run python -m keep_track_nz.scrapers.parliament --test` - Test Parliament scraper individually
- `cd backend && uv run python -m keep_track_nz.scrapers.beehive --test` - Test Beehive scraper individually
- `cd backend && uv run python -m keep_track_nz.main --dry-run --debug --limit 5` - Test full pipeline with enhanced debug output
- `cd backend && uv run python -m keep_track_nz.main --dry-run --stats-file validation_stats.json` - Run with statistics collection to verify data collection
- `cd backend && uv run pytest tests/ -v` - Run all backend tests to ensure no regressions
- `cd backend && uv run pytest tests/test_models.py -v` - Verify model integration still works
- `cd backend && uv run pytest tests/test_processors.py -v` - Verify processors can handle the new data format

## Notes
- Both sites are actively maintained government websites with current data, so the issue is definitely with the scraper code, not the source data
- The Parliament site's heavy JavaScript usage requires special handling - API-first approach is recommended
- The Beehive site has a simple, consistent HTML structure that should be reliable to scrape
- Enhanced debug logging is critical for future maintenance as government websites often change their structure
- Consider adding website change detection to alert when scraper maintenance is needed
- The Playwright exploration confirmed both sites have abundant recent data that should be accessible to the scrapers