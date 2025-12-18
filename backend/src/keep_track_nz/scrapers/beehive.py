"""Beehive scraper for beehive.govt.nz government announcements."""

import re
import logging
import time
import random
import hashlib
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse

import requests
import feedparser
from bs4 import BeautifulSoup

from ..models import SourceSystem, ActionMetadata, GovernmentAction
from .base import BaseScraper

logger = logging.getLogger(__name__)


class BeehiveScraper(BaseScraper):
    """Scraper for New Zealand Government announcements from beehive.govt.nz."""

    BASE_URL = "https://www.beehive.govt.nz"
    RELEASES_URL = f"{BASE_URL}/releases"
    SPEECHES_URL = f"{BASE_URL}/speeches"

    # RSS Feed URLs
    RSS_FEEDS = {
        'all': f"{BASE_URL}/rss.xml",
        'releases': f"{BASE_URL}/releases/feed",
        'speeches': f"{BASE_URL}/speeches/feed",
        'features': f"{BASE_URL}/features/feed"
    }

    # Priority minister feeds
    PRIORITY_MINISTERS = {
        'prime_minister': 6794,
        'finance': 6795,
        'health': 6797,
        'education': 6799,
        'housing': 6820
    }

    # Known portfolios for classification
    PORTFOLIO_KEYWORDS = {
        'prime minister': 'Prime Minister',
        'deputy prime minister': 'Deputy Prime Minister',
        'finance': 'Finance',
        'treasury': 'Finance',
        'health': 'Health',
        'education': 'Education',
        'housing': 'Housing',
        'transport': 'Transport',
        'justice': 'Justice',
        'defence': 'Defence',
        'foreign affairs': 'Foreign Affairs',
        'trade': 'Trade',
        'environment': 'Environment',
        'climate': 'Climate Change',
        'energy': 'Energy',
        'agriculture': 'Agriculture',
        'fisheries': 'Fisheries',
        'forestry': 'Forestry',
        'immigration': 'Immigration',
        'customs': 'Customs',
        'internal affairs': 'Internal Affairs',
        'social development': 'Social Development',
        'women': 'Women',
        'māori development': 'Māori Development',
        'pacific peoples': 'Pacific Peoples',
        'seniors': 'Seniors',
        'disability issues': 'Disability Issues',
        'workplace relations': 'Workplace Relations',
        'commerce': 'Commerce and Consumer Affairs',
        'sport': 'Sport and Recreation',
        'arts': 'Arts, Culture and Heritage',
        'conservation': 'Conservation',
        'emergency management': 'Emergency Management',
    }

    def __init__(self, session: requests.Session | None = None, debug_context=None):
        """Initialize Beehive scraper."""
        super().__init__(session, debug_context)

        # Enhanced headers to appear more like a real browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })

    def get_source_system(self) -> str:
        """Get the source system identifier."""
        return SourceSystem.BEEHIVE.value

    def scrape(self, limit: int | None = None) -> List[Dict[str, Any]]:
        """
        Comprehensive Beehive scraping with RSS-first strategy and fallbacks.

        Args:
            limit: Optional limit on number of announcements to scrape

        Returns:
            List of raw announcement data dictionaries
        """
        logger.info(f"🔄 Starting comprehensive Beehive scraper with limit: {limit}")
        all_items = []

        try:
            # Step 1: Try RSS feeds (primary method)
            logger.info("🔄 Starting RSS feed scraping...")
            rss_items = self._scrape_beehive_rss_comprehensive(limit)

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
                html_items = self._scrape_html_comprehensive(limit)

                if html_items:
                    logger.info(f"✅ HTML scraping successful: {len(html_items)} items")
                    all_items.extend(html_items)
                else:
                    raise Exception("No HTML items found")

            except Exception as e2:
                logger.error(f"❌ HTML scraping also failed: {e2}")

        # Process and validate results
        if all_items:
            # Deduplicate and enhance
            all_items = self._deduplicate_beehive_items(all_items)
            all_items = self._enhance_beehive_items(all_items)

            # Validate items
            valid_items = []
            for item in all_items:
                if self._validate_beehive_item(item):
                    valid_items.append(item)
                else:
                    logger.warning(f"Invalid item filtered out: {item.get('title', 'No title')[:50]}")

            # Apply limit if specified
            if limit and len(valid_items) > limit:
                valid_items = valid_items[:limit]

            logger.info(f"🎉 Final result: {len(valid_items)} valid items")
            return self._debug_log_scraped_items(valid_items)

        logger.warning("❌ All scraping methods failed")
        return []

    def _scrape_beehive_rss_comprehensive(self, limit: int | None = None) -> List[Dict[str, Any]]:
        """Scrape from all relevant Beehive RSS feeds."""
        all_items = []

        # Primary content feeds
        content_feeds = ['releases', 'speeches']
        for feed_type in content_feeds:
            try:
                items = self._scrape_beehive_rss(feed_type, limit)
                all_items.extend(items)
                logger.info(f"✅ {feed_type} RSS feed: {len(items)} items")
            except Exception as e:
                logger.warning(f"⚠️  {feed_type} RSS feed failed: {e}")

        # Try priority minister feeds if we need more content
        if not all_items or (limit and len(all_items) < limit):
            minister_items = self._scrape_priority_minister_feeds()
            all_items.extend(minister_items)

        return all_items

    def _scrape_beehive_rss(self, feed_type: str = 'releases', limit: int | None = None) -> List[Dict[str, Any]]:
        """Scrape Beehive announcements via RSS feed."""
        url = self.RSS_FEEDS.get(feed_type, self.RSS_FEEDS['releases'])

        try:
            self._debug_log_request_details(f"RSS: {url}")

            # Use requests session to get RSS feed with proper headers
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            # Parse RSS feed
            feed = feedparser.parse(response.content)

            if not feed.entries:
                logger.warning(f"No entries found in RSS feed: {url}")
                return []

            items = []
            for entry in feed.entries:
                if limit and len(items) >= limit:
                    break

                item = self._parse_rss_entry(entry, feed_type)
                if item:
                    items.append(item)

            logger.info(f"RSS feed {feed_type}: parsed {len(items)} items")
            return items

        except Exception as e:
            logger.error(f"RSS scraping failed for {feed_type}: {e}")
            return []

    def _parse_rss_entry(self, entry, feed_type: str) -> Optional[Dict[str, Any]]:
        """Parse individual RSS entry."""
        try:
            # Extract basic information
            title = getattr(entry, 'title', '')
            url = getattr(entry, 'link', '')
            date_str = getattr(entry, 'published', '')
            summary = getattr(entry, 'summary', '')

            if not title or not url:
                return None

            # Extract minister from content
            primary_entity = self._extract_minister_from_rss_content(entry)

            # Extract portfolio from content or tags
            portfolio = self._extract_portfolio_from_rss_content(entry)

            # Normalize date
            normalized_date = self._normalize_rss_date(date_str)

            return {
                'title': title,
                'url': url,
                'date': normalized_date or datetime.now().strftime('%Y-%m-%d'),
                'summary': summary,
                'source_system': 'BEEHIVE',
                'document_type': feed_type.title().rstrip('s') if feed_type.endswith('s') else feed_type.title(),
                'primary_entity': primary_entity,
                'portfolio': portfolio,
                'last_scraped': datetime.now().isoformat(),
            }

        except Exception as e:
            logger.warning(f"Failed to parse RSS entry: {e}")
            return None

    def _extract_minister_from_rss_content(self, entry) -> str:
        """Extract minister name from RSS entry content."""
        # Get content from summary and content fields
        content_parts = []
        if hasattr(entry, 'summary'):
            content_parts.append(entry.summary)
        if hasattr(entry, 'content'):
            for content_item in entry.content:
                content_parts.append(content_item.value)

        content = ' '.join(content_parts)

        # Look for minister patterns
        minister_patterns = [
            r'(?:Minister|Hon\.?\s+)([A-Z][a-z]+ (?:[A-Z][a-z]+ )*[A-Z][a-z]+)',
            r'(?:Rt\.?\s+Hon\.?\s+)([A-Z][a-z]+ (?:[A-Z][a-z]+ )*[A-Z][a-z]+)',
        ]

        for pattern in minister_patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(0)  # Return full match including title

        # Check entry title for minister info
        return self._extract_minister_from_title(getattr(entry, 'title', ''))

    def _extract_portfolio_from_rss_content(self, entry) -> str:
        """Extract portfolio from RSS entry content."""
        # Check tags first
        if hasattr(entry, 'tags'):
            for tag in entry.tags:
                term = tag.term.lower()
                for keyword, portfolio in self.PORTFOLIO_KEYWORDS.items():
                    if keyword in term:
                        return portfolio

        # Check title and content
        title = getattr(entry, 'title', '').lower()
        return self._extract_portfolio_from_title(title) or 'General'

    def _normalize_rss_date(self, date_str: str) -> Optional[str]:
        """Normalize RSS date format to ISO format."""
        if not date_str:
            return None

        try:
            # RSS dates typically in RFC 2822 format
            from email.utils import parsedate_to_datetime
            dt = parsedate_to_datetime(date_str)
            return dt.strftime('%Y-%m-%d')
        except (ValueError, TypeError):
            # Fallback to standard normalization
            return self._normalize_date(date_str)

    def _scrape_priority_minister_feeds(self) -> List[Dict[str, Any]]:
        """Scrape feeds for key ministers."""
        all_items = []

        for minister, term_id in self.PRIORITY_MINISTERS.items():
            url = f"{self.BASE_URL}/taxonomy/term/{term_id}/feed"

            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()

                feed = feedparser.parse(response.content)

                for entry in feed.entries:
                    item = {
                        'title': getattr(entry, 'title', ''),
                        'url': getattr(entry, 'link', ''),
                        'date': self._normalize_rss_date(getattr(entry, 'published', '')),
                        'summary': getattr(entry, 'summary', ''),
                        'source_system': 'BEEHIVE',
                        'primary_entity': minister.replace('_', ' ').title(),
                        'feed_source': f'minister_{minister}',
                        'document_type': 'Press Release'
                    }

                    if item['title'] and item['url']:
                        all_items.append(item)

                logger.info(f"Minister {minister} feed: {len([i for i in all_items if i.get('feed_source') == f'minister_{minister}'])} items")

            except Exception as e:
                logger.warning(f"Minister {minister} feed failed: {e}")

        return all_items

    def _scrape_html_comprehensive(self, limit: int | None = None) -> List[Dict[str, Any]]:
        """Enhanced HTML scraping with retry and fallback logic."""
        all_items = []

        # Try releases first
        try:
            releases = self._scrape_html_with_retry('releases', max_pages=2)
            all_items.extend(releases)
        except Exception as e:
            logger.warning(f"HTML releases scraping failed: {e}")

        # Try speeches
        try:
            speeches = self._scrape_html_with_retry('speeches', max_pages=2)
            all_items.extend(speeches)
        except Exception as e:
            logger.warning(f"HTML speeches scraping failed: {e}")

        # Apply limit
        if limit and len(all_items) > limit:
            all_items = all_items[:limit]

        return all_items

    def _scrape_html_with_retry(self, page_type: str = 'releases', max_pages: int = 3) -> List[Dict[str, Any]]:
        """Scrape Beehive announcements via HTML parsing with retry logic."""
        base_url = f"{self.BASE_URL}/{page_type}"
        all_items = []

        for page in range(1, max_pages + 1):
            url = f"{base_url}?page={page}" if page > 1 else base_url

            try:
                response = self._make_request_with_retry(url)
                items = self._parse_announcements_page(response, page_type.title().rstrip('s'), None)
                all_items.extend(items)

                # Respectful crawling - wait between requests
                if page < max_pages:
                    time.sleep(random.uniform(1, 3))

            except Exception as e:
                logger.error(f"Error scraping {url}: {e}")
                continue

        return all_items

    def _scrape_releases(self, limit: int | None = None) -> List[Dict[str, Any]]:
        """Scrape press releases from beehive.govt.nz/releases."""
        try:
            response = self._make_request_with_retry(self.RELEASES_URL)
            return self._parse_announcements_page(response, 'Press Release', limit)
        except Exception as e:
            logger.error(f"Failed to scrape releases: {e}")
            return []

    def _scrape_speeches(self, limit: int | None = None) -> List[Dict[str, Any]]:
        """Scrape speeches from beehive.govt.nz/speeches."""
        try:
            response = self._make_request_with_retry(self.SPEECHES_URL)
            return self._parse_announcements_page(response, 'Speech', limit)
        except Exception as e:
            logger.error(f"Failed to scrape speeches: {e}")
            return []

    def _make_request_with_retry(self, url: str, max_retries: int = 3) -> requests.Response:
        """Enhanced HTTP request with retry logic, exponential backoff, and bot protection handling."""
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    # Exponential backoff with random jitter
                    wait_time = (2 ** attempt) + random.uniform(0, 2)
                    logger.info(f"⚠️  Attempt {attempt + 1} failed, retrying in {wait_time:.1f}s")
                    time.sleep(wait_time)

                self._debug_log_request_details(f"{url} (attempt {attempt + 1})")

                # Make request with timeout
                response = self.session.get(url, timeout=30)
                response.raise_for_status()

                # Enhanced bot protection detection
                response_text_lower = response.text.lower()
                if (len(response.text) < 500 and
                    any(keyword in response_text_lower for keyword in ['incapsula', 'cloudflare', 'blocked', 'access denied'])):

                    self._debug_log_parsing_attempt(f"Bot protection detected", False, f"Attempt {attempt + 1}")
                    if attempt < max_retries - 1:
                        continue
                    else:
                        raise requests.exceptions.RequestException("Bot protection blocking access")

                # Check for valid content
                if len(response.text) < 100:
                    raise requests.exceptions.RequestException("Response too short, possible error page")

                self._debug_log_response_details(response)
                return response

            except requests.exceptions.RequestException as e:
                self._debug_log_parsing_attempt(f"Request failed", False, f"Attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    logger.error(f"❌ All {max_retries} attempts failed for {url}: {e}")
                    raise

        return response

    def _monitor_beehive_health(self) -> Dict[str, Any]:
        """Monitor Beehive scraper health by checking key endpoints."""
        health_checks = {
            'rss_all': self.RSS_FEEDS['all'],
            'rss_releases': self.RSS_FEEDS['releases'],
            'html_releases': self.RELEASES_URL
        }

        results = {}
        for name, url in health_checks.items():
            try:
                start_time = time.time()
                response = self.session.get(url, timeout=10)
                response_time = time.time() - start_time

                results[name] = {
                    'status': 'healthy' if response.status_code == 200 else 'unhealthy',
                    'status_code': response.status_code,
                    'response_time': response_time,
                    'content_length': len(response.text)
                }
            except Exception as e:
                results[name] = {
                    'status': 'error',
                    'error': str(e)
                }

        return results

    def _parse_announcements_page(self, response: requests.Response, document_type: str, limit: int | None) -> List[Dict[str, Any]]:
        """Parse announcements listing page."""
        soup = BeautifulSoup(response.text, 'html.parser')
        announcements = []

        # Look for announcement listing elements (updated for current Beehive structure)
        announcement_selectors = [
            'article',  # Primary selector for current Beehive structure
            '.view-content .views-row',
            '.release-list .release-item',
            '.speech-list .speech-item',
            '.content-list .content-item',
            '.node-teaser',
            '.announcement',
            '.teaser',  # Common Drupal teaser class
            '.node'     # Generic Drupal node
        ]

        announcement_elements = []
        successful_selector = None
        for selector in announcement_selectors:
            announcement_elements = soup.select(selector)
            if announcement_elements:
                successful_selector = selector
                self._debug_log_parsing_attempt(f"Beehive selector {selector}", True, f"Found {len(announcement_elements)} elements")
                break

        self._debug_log_selector_attempts(announcement_selectors, len(announcement_elements), successful_selector)

        # Fallback: look for any links in the main content
        if not announcement_elements:
            self._debug_log_parsing_attempt("Beehive fallback link search", False, "Trying link fallback")
            main_content = soup.select_one('.main-content, .content, #content, .region-content, main')
            if main_content:
                announcement_elements = main_content.select('a[href*="/release"], a[href*="/speech"]')
                if announcement_elements:
                    self._debug_log_parsing_attempt("Beehive link fallback", True, f"Found {len(announcement_elements)} links")

        if not announcement_elements:
            self._debug_log_parsing_attempt("Beehive announcement extraction", False, "No announcement elements found")
            return []

        self._debug_log_parsing_attempt("Beehive announcement extraction", True, f"Processing {len(announcement_elements)} elements")

        for element in announcement_elements:
            if limit and len(announcements) >= limit:
                break

            announcement_data = self._extract_announcement_from_element(element, document_type)
            if announcement_data:
                announcements.append(announcement_data)

        return announcements

    def _extract_announcement_from_element(self, element, document_type: str) -> Optional[Dict[str, Any]]:
        """Extract announcement data from HTML element."""
        try:
            # Find the main link - prioritize heading links
            link = None
            title = ''

            # Look for links in headings first (more reliable)
            heading_selectors = ['h1 a', 'h2 a', 'h3 a', '.title a', '.heading a']
            for selector in heading_selectors:
                heading_link = element.select_one(selector)
                if heading_link:
                    link = heading_link
                    title = heading_link.get_text(strip=True)
                    break

            # Fallback to any link if no heading link found
            if not link:
                link = element.select_one('a') if element.name != 'a' else element
                if link:
                    title = link.get_text(strip=True)

            if not link or not title:
                self._debug_log_parsing_attempt("Beehive element extraction", False, "No link or title found")
                return None

            url = link.get('href', '')

            # Ensure URL is absolute
            if url and not url.startswith('http'):
                url = urljoin(self.BASE_URL, url)

            # Extract date with enhanced selectors for current Beehive structure
            date_str = ''
            date_selectors = [
                'time',  # Most reliable - HTML5 time elements
                '.date',
                '.published',
                '.timestamp',
                '.field-name-post-date',
                '.submitted',
                '.datetime',
                '.publish-date',
                '.date-display-single'
            ]

            for selector in date_selectors:
                date_elem = element.select_one(selector)
                if date_elem:
                    # Try datetime attribute first
                    if date_elem.has_attr('datetime'):
                        date_str = date_elem.get('datetime')
                    else:
                        date_str = date_elem.get_text(strip=True)
                    if date_str:
                        self._debug_log_parsing_attempt(f"Date extraction via {selector}", True, date_str[:20])
                        break

            # If no date found, try to extract from nearby text
            if not date_str:
                text = element.get_text()
                # Look for various date patterns
                date_patterns = [
                    r'(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})',  # DD/MM/YYYY or DD-MM-YYYY
                    r'(\d{4}[\/\-]\d{1,2}[\/\-]\d{1,2})',  # YYYY/MM/DD or YYYY-MM-DD
                    r'(\d{1,2}\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})',  # DD Month YYYY
                ]
                for pattern in date_patterns:
                    date_match = re.search(pattern, text, re.IGNORECASE)
                    if date_match:
                        date_str = date_match.group(1)
                        self._debug_log_parsing_attempt("Date extraction via regex", True, date_str)
                        break

            # Extract portfolio/minister from title or element
            portfolio = self._extract_portfolio_from_title(title)
            primary_entity = self._extract_minister_from_title(title)

            # Look for minister information in element text or attributes
            if not primary_entity or primary_entity == 'Government':
                minister_selectors = ['.minister', '.author', '.byline', '.attribution']
                for selector in minister_selectors:
                    minister_elem = element.select_one(selector)
                    if minister_elem:
                        minister_text = minister_elem.get_text(strip=True)
                        if minister_text and len(minister_text) > 3:
                            primary_entity = minister_text
                            break

            if title and url:
                announcement = {
                    'title': title,
                    'url': url,
                    'date': self._normalize_date(date_str) or datetime.now().strftime('%Y-%m-%d'),
                    'primary_entity': primary_entity or 'Government',
                    'document_type': document_type,
                    'portfolio': portfolio,
                    'summary': '',  # Will be extracted from detail page
                }

                self._debug_log_parsing_attempt("Beehive announcement", True, f"'{title[:50]}...'")
                return announcement

        except Exception as e:
            logger.warning(f"Failed to extract announcement from element: {e}")
            self._debug_log_parsing_attempt("Beehive element extraction", False, str(e))

        return None

    def _deduplicate_beehive_items(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate Beehive items using URL and title+date as keys."""
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

        logger.info(f"Deduplication: {len(items)} → {len(unique_items)} items")
        return unique_items

    def _enhance_beehive_items(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhance items with additional metadata and standardization."""
        for item in items:
            # Standardize document type
            item['document_type'] = self._standardize_document_type(item.get('document_type', ''))

            # Extract portfolio from URL if not present
            if not item.get('portfolio'):
                item['portfolio'] = self._extract_portfolio_from_url(item.get('url', ''))

            # Generate ID
            item['id'] = self._generate_beehive_id(item)

            # Ensure source system is set
            item['source_system'] = 'BEEHIVE'

        return items

    def _standardize_document_type(self, doc_type: str) -> str:
        """Standardize document type names."""
        type_mapping = {
            'release': 'Press Release',
            'speech': 'Speech',
            'feature': 'Feature Article',
            'announcement': 'Press Release'
        }
        return type_mapping.get(doc_type.lower(), doc_type)

    def _extract_portfolio_from_url(self, url: str) -> str:
        """Extract portfolio from URL path if possible."""
        if not url:
            return 'General'

        # Check URL for portfolio indicators
        url_lower = url.lower()
        for keyword, portfolio in self.PORTFOLIO_KEYWORDS.items():
            if keyword.replace(' ', '-') in url_lower or keyword.replace(' ', '_') in url_lower:
                return portfolio

        return 'General'

    def _generate_beehive_id(self, item: Dict[str, Any]) -> str:
        """Generate unique ID for Beehive item."""
        url = item.get('url', '')
        if url:
            # Extract slug from URL
            parsed_url = urlparse(url)
            path_parts = [part for part in parsed_url.path.split('/') if part]
            if path_parts:
                slug = path_parts[-1]
                # Clean slug for ID usage
                clean_slug = re.sub(r'[^a-zA-Z0-9]', '', slug)[:15]
                return f"beehive_{clean_slug}"

        # Fallback to hash of title+date
        content = f"{item.get('title', '')}_{item.get('date', '')}"
        return f"beehive_{hashlib.md5(content.encode()).hexdigest()[:12]}"

    def _validate_beehive_item(self, item: Dict[str, Any]) -> bool:
        """Validate Beehive item data structure."""
        required_fields = ['title', 'url', 'date']

        # Check required fields
        for field in required_fields:
            if not item.get(field):
                logger.debug(f"Missing required field: {field} in item: {item.get('title', 'No title')[:30]}")
                return False

        # Validate URL format
        url = item.get('url', '')
        if not url.startswith('https://www.beehive.govt.nz/'):
            logger.debug(f"Invalid URL format: {url}")
            return False

        # Validate date format
        date_str = item.get('date', '')
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            try:
                # Try RSS date format
                from email.utils import parsedate_to_datetime
                parsedate_to_datetime(date_str)
            except (ValueError, TypeError):
                logger.debug(f"Invalid date format: {date_str}")
                return False

        # Validate title length
        title = item.get('title', '')
        if len(title) < 10 or len(title) > 500:
            logger.debug(f"Invalid title length: {len(title)} chars")
            return False

        return True

    def _extract_portfolio_from_title(self, title: str) -> str:
        """Extract government portfolio from announcement title."""
        title_lower = title.lower()
        for keyword, portfolio in self.PORTFOLIO_KEYWORDS.items():
            if keyword in title_lower:
                return portfolio

        return ''

    def _extract_minister_from_title(self, title: str) -> str:
        """Extract minister name from announcement title."""
        # Look for "Hon [Name]" pattern
        hon_match = re.search(r'Hon\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', title)
        if hon_match:
            return f"Hon {hon_match.group(1)}"

        # Look for "Rt Hon [Name]" pattern (for PM)
        rt_hon_match = re.search(r'Rt\.?\s+Hon\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', title)
        if rt_hon_match:
            return f"Rt Hon {rt_hon_match.group(1)}"

        # Common minister names (current government)
        minister_names = {
            'luxon': 'Rt Hon Christopher Luxon',
            'peters': 'Rt Hon Winston Peters',
            'seymour': 'Hon David Seymour',
            'bishop': 'Hon Chris Bishop',
            'willis': 'Hon Nicola Willis',
            'mitchell': 'Hon Mark Mitchell',
            'brown': 'Hon Simeon Brown',
            'stanford': 'Hon Erica Stanford',
            'reti': 'Hon Dr Shane Reti',
            'jones': 'Hon Shane Jones',
            'doocey': 'Hon Matt Doocey',
            'van velden': 'Hon Brooke van Velden',
            'costley': 'Hon Andrew Costley',
        }

        title_lower = title.lower()
        for name_key, full_name in minister_names.items():
            if name_key in title_lower:
                return full_name

        return 'Government'

    def _scrape_announcement_details(self, announcement_data: Dict[str, Any]) -> Dict[str, Any]:
        """Scrape detailed information for a specific announcement."""
        if not announcement_data.get('url'):
            return announcement_data

        try:
            response = self._make_request(announcement_data['url'])
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract summary/content
            summary = self._extract_announcement_summary(soup)

            # Extract more accurate date from detail page
            detail_date = self._extract_date_from_detail(soup)
            if detail_date:
                announcement_data['date'] = detail_date

            # Extract more accurate minister/entity information
            detail_entity = self._extract_entity_from_detail(soup)
            if detail_entity:
                announcement_data['primary_entity'] = detail_entity

            # Update announcement data
            announcement_data.update({
                'summary': summary,
                'last_scraped': datetime.now().isoformat(),
            })

            return announcement_data

        except Exception as e:
            logger.warning(f"Failed to scrape announcement details from {announcement_data['url']}: {e}")
            return announcement_data

    def _extract_announcement_summary(self, soup: BeautifulSoup) -> str:
        """Extract announcement summary from detail page."""
        summary_selectors = [
            '.field-name-body .field-item',
            '.content .field-item',
            '.node-content p:first-of-type',
            '.announcement-content p:first-of-type',
            'meta[name="description"]',
            '.summary',
            '.lead'
        ]

        for selector in summary_selectors:
            if selector.startswith('meta'):
                elem = soup.select_one(selector)
                if elem:
                    return elem.get('content', '')
            else:
                elem = soup.select_one(selector)
                if elem:
                    text = elem.get_text(strip=True)
                    # Take first paragraph or first 300 characters
                    if len(text) > 50:
                        sentences = text.split('. ')
                        if len(sentences) > 1:
                            return '. '.join(sentences[:2]) + '.'
                        else:
                            return text[:300] + '...' if len(text) > 300 else text

        return ''

    def _extract_date_from_detail(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract more accurate date from detail page."""
        date_selectors = [
            '.field-name-post-date .field-item',
            '.date-display-single',
            '.submitted time',
            '.published',
            'time[datetime]'
        ]

        for selector in date_selectors:
            elem = soup.select_one(selector)
            if elem:
                if elem.has_attr('datetime'):
                    date_str = elem['datetime']
                else:
                    date_str = elem.get_text(strip=True)

                normalized_date = self._normalize_date(date_str)
                if normalized_date:
                    return normalized_date

        return None

    def _extract_entity_from_detail(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract primary entity from detail page."""
        entity_selectors = [
            '.field-name-field-minister .field-item',
            '.field-name-field-portfolio .field-item',
            '.minister-name',
            '.portfolio-name',
            '.author'
        ]

        for selector in entity_selectors:
            elem = soup.select_one(selector)
            if elem:
                text = elem.get_text(strip=True)
                if text and len(text) > 3:  # Ensure meaningful content
                    return text

        return None

    def _normalize_date(self, date_str: str) -> Optional[str]:
        """Normalize date string to YYYY-MM-DD format."""
        if not date_str:
            return None

        try:
            # Clean the date string
            clean_date = re.sub(r'[^\w\s,/:T-]', '', date_str.strip())

            # Try different date formats
            formats = [
                '%Y-%m-%d',
                '%d/%m/%Y',
                '%d-%m-%Y',
                '%d %B %Y',
                '%d %b %Y',
                '%B %d, %Y',
                '%b %d, %Y',
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%dT%H:%M:%SZ',
                '%d %B %Y - %H:%M',
                '%A, %d %B %Y',
                '%A %d %B %Y',
            ]

            for fmt in formats:
                try:
                    date_obj = datetime.strptime(clean_date, fmt)
                    return date_obj.strftime('%Y-%m-%d')
                except ValueError:
                    continue

        except Exception as e:
            logger.warning(f"Failed to normalize date '{date_str}': {e}")

        return None

    def create_government_action(self, raw_data: Dict[str, Any]) -> GovernmentAction:
        """Convert raw Beehive data to GovernmentAction."""
        try:
            # Generate version-aware ID
            url_path = urlparse(raw_data['url']).path
            path_parts = [part for part in url_path.split('/') if part]
            url_id = path_parts[-1] if path_parts else 'unknown'

            # Clean URL ID and create base ID
            clean_id = re.sub(r'[^a-zA-Z0-9]', '', url_id)[:10]
            base_id = f"bee-{datetime.now().year}-{clean_id}"

            # Beehive releases typically don't have versions, default to v1
            version = raw_data.get('version', '1')

            # Generate full ID with version
            action_id = f"{base_id}-v{version}"

            # Create metadata with version information
            metadata = ActionMetadata(
                document_type=raw_data.get('document_type', 'Press Release'),
                portfolio=raw_data.get('portfolio'),
                version=version
            )

            # Create the action
            return GovernmentAction(
                id=action_id,
                title=raw_data['title'],
                date=raw_data.get('date', datetime.now().strftime('%Y-%m-%d')),
                source_system=SourceSystem.BEEHIVE,
                url=raw_data['url'],
                primary_entity=raw_data.get('primary_entity', 'Government'),
                summary=raw_data.get('summary', ''),
                labels=[],  # Will be filled by label processor
                metadata=metadata,
                version=version,
                base_id=base_id
            )

        except Exception as e:
            logger.error(f"Failed to create GovernmentAction from Beehive data: {e}")
            raise


def main():
    """Test the Beehive scraper."""
    import sys
    from ..debug import DebugContext

    logging.basicConfig(level=logging.DEBUG if '--debug' in sys.argv else logging.INFO)

    # Enable debug context for testing
    debug_context = DebugContext(enabled=True)
    scraper = BeehiveScraper(debug_context=debug_context)

    try:
        if '--test' in sys.argv:
            announcements = scraper.scrape(limit=5)
            print(f"Scraped {len(announcements)} announcements")
            for announcement in announcements:
                print(f"- {announcement.get('title', 'No title')}")
                print(f"  Type: {announcement.get('document_type', 'Unknown')}")
                print(f"  URL: {announcement.get('url', 'No URL')}")
                print(f"  Primary Entity: {announcement.get('primary_entity', 'Unknown')}")
                print()
    finally:
        scraper.close()


if __name__ == '__main__':
    main()