# Beehive Scraping Guide

This guide documents how to scrape government announcements from beehive.govt.nz for the Keep Track NZ project.

## Site Overview

**URL**: https://www.beehive.govt.nz/
**Content**: Government press releases, speeches, and ministerial announcements
**Data Volume**: ~100+ current items per feed
**JavaScript Dependency**: Minimal - mostly server-rendered content

## Data Sources and Methods

### 1. RSS Feeds (Recommended Primary Method)

Beehive.govt.nz provides excellent RSS feed support with multiple granular options:

#### Site-Wide Feeds
- **All Site Updates**: `https://www.beehive.govt.nz/rss.xml`
- **All Releases**: `https://www.beehive.govt.nz/releases/feed`
- **All Speeches**: `https://www.beehive.govt.nz/speeches/feed`
- **All Features**: `https://www.beehive.govt.nz/features/feed`

#### Minister-Specific Feeds
Each minister has their own dedicated RSS feed:
- **Prime Minister**: `/taxonomy/term/6794/feed`
- **Finance Minister**: `/taxonomy/term/6795/feed`
- **[Other ministers]**: `/taxonomy/term/{id}/feed`

#### Portfolio-Specific Feeds
Each government portfolio has its own RSS feed:
- **Health**: `/taxonomy/term/6724/feed`
- **Housing**: `/taxonomy/term/6720/feed`
- **Education**: `/taxonomy/term/6729/feed`
- **[All portfolios]**: `/taxonomy/term/{id}/feed`

**Implementation**:
```python
import feedparser
import requests
from datetime import datetime

def scrape_beehive_rss(feed_type='releases'):
    """Scrape Beehive announcements via RSS feed"""
    feed_urls = {
        'all': 'https://www.beehive.govt.nz/rss.xml',
        'releases': 'https://www.beehive.govt.nz/releases/feed',
        'speeches': 'https://www.beehive.govt.nz/speeches/feed',
        'features': 'https://www.beehive.govt.nz/features/feed'
    }

    url = feed_urls.get(feed_type, feed_urls['releases'])

    try:
        feed = feedparser.parse(url)
        items = []

        for entry in feed.entries:
            item = {
                'title': entry.title,
                'url': entry.link,
                'date': entry.published,
                'summary': entry.summary if hasattr(entry, 'summary') else '',
                'source_system': 'BEEHIVE',
                'document_type': feed_type.title(),
                'primary_entity': extract_minister_from_content(entry),
                'portfolio': extract_portfolio_from_content(entry)
            }
            items.append(item)

        return items
    except Exception as e:
        print(f"RSS scraping failed for {feed_type}: {e}")
        return []

def extract_minister_from_content(entry):
    """Extract minister name from RSS entry content"""
    # Ministers typically appear in entry.summary or entry.content
    content = getattr(entry, 'summary', '') + ' ' + getattr(entry, 'content', '')

    # Look for minister patterns like "Minister John Smith says"
    import re
    minister_pattern = r'(?:Minister|Hon\.?\s+)([A-Z][a-z]+ (?:[A-Z][a-z]+ )*[A-Z][a-z]+)'
    match = re.search(minister_pattern, content)

    return match.group(1) if match else 'Unknown'

def extract_portfolio_from_content(entry):
    """Extract portfolio from RSS entry content"""
    # Portfolio information might be in categories or content
    if hasattr(entry, 'tags'):
        for tag in entry.tags:
            if tag.term in KNOWN_PORTFOLIOS:
                return tag.term

    return 'General'
```

### 2. HTML Scraping (Fallback Method)

**URLs**:
- Releases: `https://www.beehive.govt.nz/releases`
- Speeches: `https://www.beehive.govt.nz/speeches`

**HTML Structure** (confirmed via Playwright):
```html
<article>
  <div>
    <div>
      <emphasis>Release</emphasis>  <!-- Document type -->
      <time>18 December 2025</time>  <!-- Publication date -->
    </div>
    <heading level="2">
      <a href="/release/title-slug">Title of Announcement</a>
    </heading>
    <paragraph>Summary text of the announcement...</paragraph>
    <emphasis>
      <a href="/minister/minister-name">Hon Minister Name</a>  <!-- Minister -->
    </emphasis>
    <a href="/portfolio/portfolio-name">Portfolio Name</a>  <!-- Portfolio -->
  </div>
</article>
```

**Implementation**:
```python
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import random

def scrape_beehive_html(page_type='releases', max_pages=3):
    """Scrape Beehive announcements via HTML parsing"""
    base_url = f"https://www.beehive.govt.nz/{page_type}"
    all_items = []

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive'
    }

    for page in range(1, max_pages + 1):
        url = f"{base_url}?page={page}" if page > 1 else base_url

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            articles = soup.find_all('article')

            for article in articles:
                item = parse_beehive_article(article, page_type)
                if item:
                    all_items.append(item)

            # Respectful crawling - wait between requests
            time.sleep(random.uniform(1, 3))

        except Exception as e:
            print(f"Error scraping {url}: {e}")
            continue

    return all_items

def parse_beehive_article(article, page_type):
    """Parse individual Beehive article"""
    try:
        # Extract title and URL
        heading = article.find('h2') or article.find(['h1', 'h3'])
        if not heading:
            return None

        title_link = heading.find('a')
        if not title_link:
            return None

        title = title_link.get_text(strip=True)
        relative_url = title_link.get('href')
        url = f"https://www.beehive.govt.nz{relative_url}"

        # Extract date
        time_elem = article.find('time')
        date_str = time_elem.get_text(strip=True) if time_elem else ''

        # Extract summary
        summary_elem = article.find('p')
        summary = summary_elem.get_text(strip=True) if summary_elem else ''

        # Extract minister
        minister_links = article.find_all('a', href=lambda x: x and '/minister/' in x)
        minister = minister_links[0].get_text(strip=True) if minister_links else 'Unknown'

        # Extract portfolio
        portfolio_links = article.find_all('a', href=lambda x: x and '/portfolio/' in x)
        portfolio = portfolio_links[0].get_text(strip=True) if portfolio_links else 'General'

        # Extract document type
        doc_type_elem = article.find('emphasis')
        document_type = doc_type_elem.get_text(strip=True) if doc_type_elem else page_type.title()

        return {
            'title': title,
            'url': url,
            'date': normalize_beehive_date(date_str),
            'summary': summary,
            'primary_entity': clean_minister_name(minister),
            'portfolio': clean_portfolio_name(portfolio),
            'document_type': document_type,
            'source_system': 'BEEHIVE'
        }

    except Exception as e:
        print(f"Error parsing article: {e}")
        return None

def normalize_beehive_date(date_str):
    """Normalize Beehive date format to ISO format"""
    try:
        # Beehive uses format like "18 December 2025"
        dt = datetime.strptime(date_str, '%d %B %Y')
        return dt.strftime('%Y-%m-%d')
    except ValueError:
        try:
            # Try alternative format
            dt = datetime.strptime(date_str, '%d %b %Y')
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            return date_str  # Return as-is if parsing fails

def clean_minister_name(minister):
    """Clean and normalize minister names"""
    # Remove honorifics and clean up
    minister = minister.replace('Hon ', '').replace('Rt Hon ', '')
    minister = minister.replace(' KC', '').replace(' QC', '')
    return minister.strip()

def clean_portfolio_name(portfolio):
    """Clean and normalize portfolio names"""
    # Remove government coalition identifiers
    portfolio = portfolio.split('/')[-1]  # Take last part after slashes
    return portfolio.strip()
```

### 3. Comprehensive Multi-Feed Scraping

**Implementation for collecting from all relevant feeds**:
```python
def scrape_all_beehive_feeds():
    """Scrape from all relevant Beehive RSS feeds"""
    all_items = []

    # Primary content feeds
    content_feeds = ['releases', 'speeches']
    for feed_type in content_feeds:
        items = scrape_beehive_rss(feed_type)
        all_items.extend(items)

    # Merge and deduplicate
    return deduplicate_beehive_items(all_items)

def scrape_priority_minister_feeds():
    """Scrape feeds for key ministers"""
    priority_ministers = {
        'prime_minister': 6794,
        'finance': 6795,
        'health': 6797,
        'education': 6799,
        'housing': 6820
    }

    all_items = []
    for minister, term_id in priority_ministers.items():
        url = f"https://www.beehive.govt.nz/taxonomy/term/{term_id}/feed"
        feed = feedparser.parse(url)

        for entry in feed.entries:
            item = {
                'title': entry.title,
                'url': entry.link,
                'date': entry.published,
                'summary': entry.summary if hasattr(entry, 'summary') else '',
                'source_system': 'BEEHIVE',
                'primary_entity': minister,
                'feed_source': f'minister_{minister}'
            }
            all_items.append(item)

    return deduplicate_beehive_items(all_items)
```

## Data Processing and Validation

### Data Deduplication Strategy

**Primary Key**: `url` (Beehive URLs are unique and stable)
**Secondary Key**: `title` + `date` (for cross-feed deduplication)

```python
def deduplicate_beehive_items(items):
    """Remove duplicate Beehive items"""
    seen_urls = set()
    seen_title_date = set()
    unique_items = []

    for item in items:
        url = item.get('url', '')
        title_date = f"{item.get('title', '')}_{item.get('date', '')}"

        # Skip if we've seen this URL before
        if url in seen_urls:
            continue

        # Skip if we've seen this title+date combination
        if title_date in seen_title_date:
            continue

        seen_urls.add(url)
        seen_title_date.add(title_date)
        unique_items.append(item)

    return unique_items

def enhance_beehive_items(items):
    """Enhance items with additional metadata"""
    for item in items:
        # Standardize document type
        item['document_type'] = standardize_document_type(item.get('document_type', ''))

        # Extract portfolio from URL if not present
        if not item.get('portfolio'):
            item['portfolio'] = extract_portfolio_from_url(item.get('url', ''))

        # Generate ID
        item['id'] = generate_beehive_id(item)

    return items

def standardize_document_type(doc_type):
    """Standardize document type names"""
    type_mapping = {
        'release': 'Press Release',
        'speech': 'Speech',
        'feature': 'Feature Article'
    }
    return type_mapping.get(doc_type.lower(), doc_type)

def generate_beehive_id(item):
    """Generate unique ID for Beehive item"""
    import hashlib
    url = item.get('url', '')
    if url:
        # Extract slug from URL
        slug = url.split('/')[-1]
        return f"beehive_{slug}"
    else:
        # Fallback to hash of title+date
        content = f"{item.get('title', '')}_{item.get('date', '')}"
        return f"beehive_{hashlib.md5(content.encode()).hexdigest()[:12]}"
```

### Data Validation
```python
def validate_beehive_item(item):
    """Validate Beehive item data structure"""
    required_fields = ['title', 'url', 'date']

    # Check required fields
    for field in required_fields:
        if not item.get(field):
            print(f"Missing required field: {field}")
            return False

    # Validate URL format
    url = item.get('url', '')
    if not url.startswith('https://www.beehive.govt.nz/'):
        print(f"Invalid URL format: {url}")
        return False

    # Validate date format
    try:
        datetime.strptime(item['date'], '%Y-%m-%d')
    except ValueError:
        try:
            # Try RSS date format
            datetime.strptime(item['date'], '%a, %d %b %Y %H:%M:%S %z')
        except ValueError:
            print(f"Invalid date format: {item['date']}")
            return False

    return True
```

## Error Handling and Resilience

### Anti-Bot Protection Handling
```python
def handle_beehive_blocking():
    """Handle potential bot protection measures"""
    session = requests.Session()

    # Enhanced headers to appear more like a real browser
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    })

    return session

def scrape_with_retry_and_backoff(scrape_func, max_retries=3):
    """Scrape with exponential backoff and retry logic"""
    for attempt in range(max_retries):
        try:
            return scrape_func()
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                print(f"❌ All {max_retries} attempts failed: {e}")
                return []

            wait_time = (2 ** attempt) + random.uniform(0, 2)
            print(f"⚠️  Attempt {attempt + 1} failed, retrying in {wait_time:.1f}s")
            time.sleep(wait_time)

    return []
```

### Browser Automation Fallback (for persistent blocking)
```python
from playwright.sync_api import sync_playwright

def scrape_beehive_with_browser():
    """Use browser automation to bypass bot protection"""
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )

        context = browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        )

        page = context.new_page()

        try:
            page.goto("https://www.beehive.govt.nz/releases")
            page.wait_for_selector("article", timeout=10000)

            articles = page.query_selector_all("article")
            items = []

            for article in articles:
                item = parse_article_with_playwright(article)
                if item:
                    items.append(item)

            return items

        except Exception as e:
            print(f"Browser automation failed: {e}")
            return []

        finally:
            browser.close()

def parse_article_with_playwright(article):
    """Parse article using Playwright selectors"""
    try:
        title_elem = article.query_selector("h2 a, h1 a, h3 a")
        title = title_elem.inner_text() if title_elem else ''
        url = title_elem.get_attribute('href') if title_elem else ''

        time_elem = article.query_selector("time")
        date_str = time_elem.inner_text() if time_elem else ''

        summary_elem = article.query_selector("p")
        summary = summary_elem.inner_text() if summary_elem else ''

        return {
            'title': title,
            'url': f"https://www.beehive.govt.nz{url}" if url else '',
            'date': normalize_beehive_date(date_str),
            'summary': summary,
            'source_system': 'BEEHIVE'
        }

    except Exception as e:
        print(f"Error parsing article with Playwright: {e}")
        return None
```

## Performance and Monitoring

### Performance Metrics
- **RSS Feeds**: ~2-3 seconds per feed
- **HTML Scraping**: ~5-8 seconds per page
- **Browser Automation**: ~15-20 seconds setup + ~3 seconds per page

### Monitoring and Alerts
```python
def monitor_beehive_health():
    """Monitor Beehive scraper health"""
    health_checks = {
        'rss_all': 'https://www.beehive.govt.nz/rss.xml',
        'rss_releases': 'https://www.beehive.govt.nz/releases/feed',
        'html_releases': 'https://www.beehive.govt.nz/releases'
    }

    results = {}
    for name, url in health_checks.items():
        try:
            response = requests.get(url, timeout=10)
            results[name] = {
                'status': 'healthy' if response.status_code == 200 else 'unhealthy',
                'status_code': response.status_code,
                'response_time': response.elapsed.total_seconds()
            }
        except Exception as e:
            results[name] = {
                'status': 'error',
                'error': str(e)
            }

    return results
```

## Recommended Implementation Strategy

### Primary Approach: RSS-First with HTML Fallback
```python
def scrape_beehive_comprehensive():
    """Comprehensive Beehive scraping strategy"""
    logger = setup_beehive_logging()
    all_items = []

    # Step 1: Try RSS feeds (primary method)
    logger.info("🔄 Starting RSS feed scraping...")
    try:
        rss_items = scrape_beehive_rss('releases')
        rss_items.extend(scrape_beehive_rss('speeches'))

        if rss_items:
            logger.info(f"✅ RSS scraping successful: {len(rss_items)} items")
            all_items.extend(rss_items)
        else:
            raise Exception("No RSS items found")

    except Exception as e:
        logger.warning(f"⚠️  RSS scraping failed: {e}")

        # Step 2: Fallback to HTML scraping
        logger.info("🔄 Trying HTML scraping fallback...")
        try:
            html_items = scrape_beehive_html('releases', max_pages=2)
            html_items.extend(scrape_beehive_html('speeches', max_pages=2))

            if html_items:
                logger.info(f"✅ HTML scraping successful: {len(html_items)} items")
                all_items.extend(html_items)
            else:
                raise Exception("No HTML items found")

        except Exception as e2:
            logger.error(f"❌ HTML scraping also failed: {e2}")

            # Step 3: Last resort - browser automation
            logger.info("🔄 Trying browser automation...")
            browser_items = scrape_beehive_with_browser()

            if browser_items:
                logger.info(f"✅ Browser scraping successful: {len(browser_items)} items")
                all_items.extend(browser_items)
            else:
                logger.error("❌ All scraping methods failed")

    # Process and validate results
    if all_items:
        all_items = deduplicate_beehive_items(all_items)
        all_items = enhance_beehive_items(all_items)
        valid_items = [item for item in all_items if validate_beehive_item(item)]

        logger.info(f"🎉 Final result: {len(valid_items)} valid items")
        return valid_items

    return []
```

## Testing and Validation

### Manual Testing Commands
```bash
# Test RSS feeds
curl -s "https://www.beehive.govt.nz/rss.xml" | head -20
curl -s "https://www.beehive.govt.nz/releases/feed" | head -20

# Test HTML pages
curl -s "https://www.beehive.govt.nz/releases" | grep -o "<title>.*</title>"

# Test specific minister feed
curl -s "https://www.beehive.govt.nz/taxonomy/term/6794/feed" | head -10
```

### Integration Testing
```python
def test_beehive_integration():
    """Integration test for Beehive scraper"""
    items = scrape_beehive_comprehensive()

    assert len(items) > 0, "Should return some items"
    assert all(item.get('title') for item in items), "All items should have titles"
    assert all(item.get('url') for item in items), "All items should have URLs"
    assert all(item.get('source_system') == 'BEEHIVE' for item in items), "All items should be from BEEHIVE"

    print(f"✅ Integration test passed: {len(items)} items retrieved")
```

## Maintenance and Updates

### Regular Maintenance Tasks
1. **Monthly**: Check RSS feed availability and structure
2. **Quarterly**: Validate HTML selectors against website changes
3. **As needed**: Update minister and portfolio taxonomy IDs
4. **Monitor**: Watch for new portfolio additions or government reshuffles

### Known Issues and Solutions
1. **Incapsula Protection**: Use RSS feeds primarily, browser automation as fallback
2. **Rate Limiting**: Implement respectful delays between requests
3. **Content Changes**: RSS feeds are more stable than HTML structure
4. **Duplicate Content**: URLs are reliable deduplication keys

This comprehensive approach ensures reliable data collection from Beehive.govt.nz while respecting their infrastructure and providing multiple fallback mechanisms.