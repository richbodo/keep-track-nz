# Parliament Scraping Guide

This guide documents how to scrape parliamentary bills data from bills.parliament.nz for the Keep Track NZ project.

## Site Overview

**URL**: https://bills.parliament.nz/bills-proposed-laws?lang=en
**Content**: Parliamentary bills (proposed laws) with stages, committees, and activity dates
**Data Volume**: ~96 current bills (as of December 2025)
**JavaScript Dependency**: Heavy - content loads dynamically via JavaScript

## Data Sources and Methods

### 1. RSS Feed (Recommended Primary Method)

**URL**: `https://bills.parliament.nz/rss?set=Bills`
**Pros**:
- No JavaScript rendering required
- Structured XML data
- Real-time updates
- Reliable and fast

**Cons**:
- May have limited historical data
- RSS format requires XML parsing

**Implementation**:
```python
import feedparser
import requests

def scrape_parliament_rss():
    """Scrape Parliament bills via RSS feed"""
    url = "https://bills.parliament.nz/rss?set=Bills"

    try:
        feed = feedparser.parse(url)
        items = []

        for entry in feed.entries:
            item = {
                'title': entry.title,
                'url': entry.link,
                'date': entry.published,
                'summary': entry.summary if hasattr(entry, 'summary') else '',
                'source_system': 'PARLIAMENT'
            }
            items.append(item)

        return items
    except Exception as e:
        print(f"RSS scraping failed: {e}")
        return []
```

### 2. JavaScript-Rendered Table Scraping

**URL**: `https://bills.parliament.nz/bills-proposed-laws?lang=en`
**Method**: Browser automation with Playwright/Selenium

**Table Structure**:
- **Name of bill**: Link to bill details + bill type (Government Bill, Private Bill, etc.)
- **Bill no.**: Official bill number (e.g., "133-2", "159-4")
- **Stage**: Current stage code (1, 2, SC, RA, etc.)
  - 1 = First Reading
  - 2 = Second Reading
  - SC = Select Committee
  - RA = Royal Assent
- **Select Committee**: Committee handling the bill
- **Last activity**: Date of last update

**Implementation with Playwright**:
```python
from playwright.sync_api import sync_playwright

def scrape_parliament_with_browser():
    """Scrape Parliament bills using browser automation"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        # Navigate and wait for content to load
        page.goto("https://bills.parliament.nz/bills-proposed-laws?lang=en")
        page.wait_for_selector("table tbody tr", timeout=10000)

        bills = []
        rows = page.query_selector_all("table tbody tr")

        for row in rows:
            cells = row.query_selector_all("td")
            if len(cells) >= 5:
                title_link = cells[0].query_selector("a")
                bill_type_elem = cells[0].query_selector("generic")

                bill = {
                    'title': title_link.inner_text() if title_link else '',
                    'url': title_link.get_attribute('href') if title_link else '',
                    'bill_number': cells[1].inner_text(),
                    'stage': cells[2].inner_text(),
                    'committee': cells[3].inner_text(),
                    'last_activity': cells[4].inner_text(),
                    'bill_type': bill_type_elem.inner_text() if bill_type_elem else '',
                    'source_system': 'PARLIAMENT'
                }
                bills.append(bill)

        browser.close()
        return bills
```

### 3. API Access (Currently Unavailable)

**Status**: Parliament developer site is DOWN as of December 2025
**Potential URL**: `https://api.parliament.nz/` or similar
**Notes**:
- API would be the most reliable method if available
- Check periodically for developer site restoration
- Contact Parliament IT services for API access information

**Future Implementation** (when available):
```python
def scrape_parliament_api(api_key):
    """Scrape Parliament bills via official API (when available)"""
    headers = {'Authorization': f'Bearer {api_key}'}
    url = "https://api.parliament.nz/bills"  # Hypothetical endpoint

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return None
```

## Data Processing and Validation

### Bill Stage Mapping
```python
STAGE_MAPPING = {
    '1': 'First Reading',
    '2': 'Second Reading',
    'SC': 'Select Committee',
    'COWH': 'Committee of Whole House',
    '3': 'Third Reading',
    'RA': 'Royal Assent'
}

def normalize_stage(stage_code):
    return STAGE_MAPPING.get(stage_code, stage_code)
```

### Data Deduplication Strategy

**Primary Key**: `bill_number` + `stage`
**Reasoning**: Bills can have multiple versions (e.g., "133-1", "133-2") representing different readings

```python
def deduplicate_bills(bills):
    """Remove duplicate bills, keeping the latest version"""
    seen = {}
    for bill in bills:
        base_number = bill['bill_number'].split('-')[0]
        key = f"{base_number}_{bill['stage']}"

        if key not in seen or bill['bill_number'] > seen[key]['bill_number']:
            seen[key] = bill

    return list(seen.values())
```

### Data Validation
```python
def validate_bill_data(bill):
    """Validate bill data structure"""
    required_fields = ['title', 'bill_number', 'stage', 'last_activity']

    for field in required_fields:
        if not bill.get(field):
            return False

    # Validate date format
    try:
        from datetime import datetime
        datetime.strptime(bill['last_activity'], '%d %b %Y')
    except ValueError:
        return False

    return True
```

## Current Scraper Issues and Solutions

### Issue 1: JavaScript Dependency
**Problem**: Parliament site loads content dynamically
**Solution**: Use RSS feed as primary method, browser automation as fallback

### Issue 2: Rate Limiting
**Problem**: Multiple rapid requests may be blocked
**Solution**: Implement exponential backoff and respect robots.txt

```python
import time
import random

def scrape_with_backoff(scrape_func, max_retries=3):
    """Scrape with exponential backoff"""
    for attempt in range(max_retries):
        try:
            return scrape_func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise e

            wait_time = (2 ** attempt) + random.uniform(0, 1)
            time.sleep(wait_time)

    return None
```

### Issue 3: Data Format Inconsistencies
**Problem**: Different bill types may have varying data formats
**Solution**: Robust parsing with fallbacks

```python
def safe_extract_text(element, fallback=''):
    """Safely extract text from DOM element"""
    try:
        return element.inner_text().strip() if element else fallback
    except:
        return fallback
```

## Testing and Debugging

### Manual Testing Commands
```bash
# Test RSS feed availability
curl -s "https://bills.parliament.nz/rss?set=Bills" | head -20

# Test main page accessibility
curl -s "https://bills.parliament.nz/bills-proposed-laws?lang=en" | grep -o "<title>.*</title>"

# Test individual bill page
curl -s "https://bills.parliament.nz/v/6/[bill-id]" | head -10
```

### Debug Logging Implementation
```python
import logging

def setup_parliament_logging():
    """Set up debug logging for Parliament scraper"""
    logger = logging.getLogger('parliament_scraper')
    logger.setLevel(logging.DEBUG)

    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger

# Usage in scraper
logger = setup_parliament_logging()
logger.info(f"🌐 Accessing Parliament URL: {url}")
logger.debug(f"📄 Found {len(bills)} bills in response")
logger.info(f"✅ Successfully scraped {len(valid_bills)} valid bills")
```

## Recommended Implementation Strategy

1. **Primary Method**: RSS feed scraping for real-time data
2. **Fallback Method**: Browser automation for comprehensive data
3. **Future Enhancement**: API integration when Parliament developer services are restored
4. **Monitoring**: Regular checks for RSS feed availability and website structure changes

### Hybrid Approach Implementation
```python
def scrape_parliament_bills():
    """Hybrid approach to Parliament bill scraping"""
    logger = setup_parliament_logging()

    # Try RSS first (fast, reliable)
    logger.info("🔄 Attempting RSS feed scraping...")
    bills = scrape_parliament_rss()

    if bills:
        logger.info(f"✅ RSS scraping successful: {len(bills)} bills")
        return bills

    # Fallback to browser automation
    logger.warning("⚠️  RSS failed, trying browser automation...")
    bills = scrape_parliament_with_browser()

    if bills:
        logger.info(f"✅ Browser scraping successful: {len(bills)} bills")
        return bills

    logger.error("❌ All scraping methods failed")
    return []
```

## Versioning and Change Detection

### Website Structure Monitoring
```python
def check_parliament_structure():
    """Monitor Parliament website for structural changes"""
    expected_selectors = [
        "table tbody tr",  # Bills table
        "table th",        # Table headers
        ".rss-link"        # RSS link
    ]

    with sync_playwright() as p:
        page = p.chromium.launch().new_page()
        page.goto("https://bills.parliament.nz/bills-proposed-laws?lang=en")

        missing_selectors = []
        for selector in expected_selectors:
            if not page.query_selector(selector):
                missing_selectors.append(selector)

        if missing_selectors:
            logger.warning(f"⚠️  Website structure changed. Missing: {missing_selectors}")
            return False

        return True
```

## Performance Considerations

- **RSS Feed**: ~2-3 seconds response time
- **Browser Automation**: ~10-15 seconds for full page load
- **Memory Usage**: Browser automation requires ~100MB additional memory
- **Network**: RSS uses minimal bandwidth, browser automation loads full page assets

## Maintenance Notes

- Monitor Parliament developer site for API restoration
- Check RSS feed format changes quarterly
- Validate bill stage codes against official Parliament documentation
- Update selectors if table structure changes
- Consider adding support for historical bills if needed

## Contact Information

For Parliament API access or technical issues:
- Parliament IT Services: [Contact via parliament.nz]
- Keep Track NZ Issues: [GitHub repository]

## Research Note

The parliament API is down, and has been down for a while.  In addition to that, Parliament kind of blew off a request to expose voting records, which involve some of the most difficult to aggregate data sources you can still call “exposed”, requiring significant manual effort to accumulate 11000+ pdf files that we hope there is no human error in.  So a passion project, voted.nz kind of keeps track of these, but you still have to go back to the original web sources - there is no API.  There IS a guy already building a scraper, though, so I’ll build on his scraper for that data source: github.com/kayakr/parliament.nz.  Request for voting records from parliament.nz from data.nz: https://data.govt.nz/datasetrequest/show/849