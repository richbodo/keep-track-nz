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
    RELEASES_URL = f"{BASE_URL}/release"
    SPEECHES_URL = f"{BASE_URL}/speech"

    def __init__(self, session: requests.Session | None = None, debug_context=None):
        """Initialize Beehive scraper."""
        super().__init__(session, debug_context)

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
        """Scrape press releases from beehive.govt.nz/release."""
        try:
            response = self._make_request(self.RELEASES_URL)
            return self._parse_announcements_page(response, 'Press Release', limit)
        except Exception as e:
            logger.error(f"Failed to scrape releases: {e}")
            return []

    def _scrape_speeches(self, limit: int | None = None) -> List[Dict[str, Any]]:
        """Scrape speeches from beehive.govt.nz/speech."""
        try:
            response = self._make_request(self.SPEECHES_URL)
            return self._parse_announcements_page(response, 'Speech', limit)
        except Exception as e:
            logger.error(f"Failed to scrape speeches: {e}")
            return []

    def _parse_announcements_page(self, response: requests.Response, document_type: str, limit: int | None) -> List[Dict[str, Any]]:
        """Parse announcements listing page."""
        soup = BeautifulSoup(response.text, 'html.parser')
        announcements = []

        # Look for announcement listing elements
        announcement_selectors = [
            '.view-content .views-row',
            '.release-list .release-item',
            '.speech-list .speech-item',
            '.content-list .content-item',
            'article',
            '.node-teaser',
            '.announcement'
        ]

        announcement_elements = []
        for selector in announcement_selectors:
            announcement_elements = soup.select(selector)
            if announcement_elements:
                logger.debug(f"Found {len(announcement_elements)} announcements using selector: {selector}")
                break

        # Fallback: look for any links in the main content
        if not announcement_elements:
            main_content = soup.select_one('.main-content, .content, #content')
            if main_content:
                announcement_elements = main_content.select('a[href*="/release/"], a[href*="/speech/"]')

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
            # Find the main link
            link = element.select_one('a') if element.name != 'a' else element
            if not link:
                return None

            title = link.get_text(strip=True)
            url = link.get('href', '')

            # Ensure URL is absolute
            if url and not url.startswith('http'):
                url = urljoin(self.BASE_URL, url)

            # Extract date
            date_str = ''
            date_selectors = [
                '.date',
                '.published',
                '.timestamp',
                'time',
                '.field-name-post-date',
                '.submitted'
            ]

            for selector in date_selectors:
                date_elem = element.select_one(selector)
                if date_elem:
                    date_str = date_elem.get_text(strip=True)
                    break

            # If no date found, try to extract from nearby text
            if not date_str:
                text = element.get_text()
                date_match = re.search(r'(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})', text)
                if date_match:
                    date_str = date_match.group(1)

            # Extract portfolio/minister from title or URL
            portfolio = self._extract_portfolio_from_title(title)
            primary_entity = self._extract_minister_from_title(title)

            if title and url:
                return {
                    'title': title,
                    'url': url,
                    'date': self._normalize_date(date_str) or datetime.now().strftime('%Y-%m-%d'),
                    'primary_entity': primary_entity,
                    'document_type': document_type,
                    'portfolio': portfolio,
                    'summary': '',  # Will be extracted from detail page
                }

        except Exception as e:
            logger.warning(f"Failed to extract announcement from element: {e}")

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
            # Generate ID
            url_path = urlparse(raw_data['url']).path
            path_parts = [part for part in url_path.split('/') if part]
            url_id = path_parts[-1] if path_parts else 'unknown'

            # Clean URL ID and create action ID
            clean_id = re.sub(r'[^a-zA-Z0-9]', '', url_id)[:10]
            action_id = f"bee-{datetime.now().year}-{clean_id}"

            # Create metadata
            metadata = ActionMetadata(
                document_type=raw_data.get('document_type', 'Press Release'),
                portfolio=raw_data.get('portfolio')
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
                metadata=metadata
            )

        except Exception as e:
            logger.error(f"Failed to create GovernmentAction from Beehive data: {e}")
            raise


def main():
    """Test the Beehive scraper."""
    import sys

    logging.basicConfig(level=logging.INFO)

    scraper = BeehiveScraper()
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