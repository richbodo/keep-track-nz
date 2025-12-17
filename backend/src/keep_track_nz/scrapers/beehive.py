"""Beehive scraper for beehive.govt.nz government announcements."""

import re
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from ..models import SourceSystem, ActionMetadata, GovernmentAction
from .base import BaseScraper

logger = logging.getLogger(__name__)


class BeehiveScraper(BaseScraper):
    """Scraper for New Zealand Government announcements from beehive.govt.nz."""

    BASE_URL = "https://www.beehive.govt.nz"
    RELEASES_URL = f"{BASE_URL}/releases"
    SPEECHES_URL = f"{BASE_URL}/speeches"

    def __init__(self, session: requests.Session | None = None, debug_context=None):
        """Initialize Beehive scraper."""
        super().__init__(session, debug_context)

        # Add additional headers to bypass bot detection
        self.session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
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
        Scrape recent government announcements.

        Args:
            limit: Optional limit on number of announcements to scrape

        Returns:
            List of raw announcement data dictionaries
        """
        logger.info(f"Starting Beehive scraper with limit: {limit}")

        try:
            announcements = []

            # Scrape press releases
            releases = self._scrape_releases(limit // 2 if limit else None)
            announcements.extend(releases)

            # Scrape speeches
            speeches = self._scrape_speeches(limit // 2 if limit else None)
            announcements.extend(speeches)

            # Sort by date and limit
            announcements.sort(key=lambda x: x.get('date', ''), reverse=True)
            if limit:
                announcements = announcements[:limit]

            # Enrich with detailed information
            enriched_announcements = []
            for announcement in announcements:
                try:
                    detailed_announcement = self._scrape_announcement_details(announcement)
                    if detailed_announcement:
                        enriched_announcements.append(detailed_announcement)
                except Exception as e:
                    logger.warning(f"Failed to get details for {announcement.get('url', 'unknown')}: {e}")
                    enriched_announcements.append(announcement)

            logger.info(f"Successfully scraped {len(enriched_announcements)} announcements from Beehive")
            return self._debug_log_scraped_items(enriched_announcements)

        except Exception as e:
            logger.error(f"Beehive scraper failed: {e}")
            return []

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
        """Make HTTP request with retry logic for bot protection."""
        import time

        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    # Add delay between retries to avoid rate limiting
                    time.sleep(2 ** attempt)  # Exponential backoff

                self._debug_log_request_details(f"{url} (attempt {attempt + 1})")
                response = self.session.get(url, timeout=30)
                response.raise_for_status()

                # Check if we got the bot protection page
                if len(response.text) < 500 and 'incapsula' in response.text.lower():
                    self._debug_log_parsing_attempt(f"Bot protection detected", False, f"Attempt {attempt + 1}")
                    if attempt < max_retries - 1:
                        continue

                self._debug_log_response_details(response)
                return response

            except requests.exceptions.RequestException as e:
                self._debug_log_parsing_attempt(f"Request failed", False, f"Attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    logger.error(f"Request failed for {url} after {max_retries} attempts: {e}")
                    raise

        return response

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

    def _extract_portfolio_from_title(self, title: str) -> str:
        """Extract government portfolio from announcement title."""
        portfolio_keywords = {
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

        title_lower = title.lower()
        for keyword, portfolio in portfolio_keywords.items():
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