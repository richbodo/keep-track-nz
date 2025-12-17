"""Parliament bills scraper for bills.parliament.nz."""

import re
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from ..models import SourceSystem, StageHistory, ActionMetadata, GovernmentAction
from .base import BaseScraper

logger = logging.getLogger(__name__)


class ParliamentScraper(BaseScraper):
    """Scraper for New Zealand Parliament bills."""

    BASE_URL = "https://bills.parliament.nz"
    BILLS_API_URL = f"{BASE_URL}/api/bills"
    BILLS_SEARCH_URL = f"{BASE_URL}/bills-proposed-laws"
    CURRENT_BILLS_URL = f"{BASE_URL}/bills-proposed-laws?lang=en"

    def __init__(self, session: requests.Session | None = None, debug_context=None):
        """Initialize Parliament scraper."""
        super().__init__(session, debug_context)

    def get_source_system(self) -> str:
        """Get the source system identifier."""
        return SourceSystem.PARLIAMENT.value

    def scrape(self, limit: int | None = None) -> List[Dict[str, Any]]:
        """
        Scrape recent parliament bills.

        Args:
            limit: Optional limit on number of bills to scrape

        Returns:
            List of raw bill data dictionaries
        """
        logger.info(f"Starting Parliament scraper with limit: {limit}")

        try:
            # First try to get bills from the search page
            bills_data = self._scrape_bills_list(limit)

            # Enrich each bill with detailed information
            enriched_bills = []
            for bill_data in bills_data:
                try:
                    detailed_bill = self._scrape_bill_details(bill_data)
                    if detailed_bill:
                        enriched_bills.append(detailed_bill)
                except Exception as e:
                    logger.warning(f"Failed to get details for bill {bill_data.get('url', 'unknown')}: {e}")
                    # Still include the basic bill data
                    enriched_bills.append(bill_data)

            logger.info(f"Successfully scraped {len(enriched_bills)} bills from Parliament")
            return self._debug_log_scraped_items(enriched_bills)

        except Exception as e:
            logger.error(f"Parliament scraper failed: {e}")
            return []

    def _scrape_bills_list(self, limit: int | None = None) -> List[Dict[str, Any]]:
        """Scrape the bills list page to get recent bills."""
        try:
            # Try API first, then fallback to HTML scraping
            self._debug_log_parsing_attempt("Parliament API access", False, "Attempting API first")

            # Try the API endpoint with proper parameters
            api_urls = [
                f"{self.BILLS_API_URL}?limit={limit or 50}",
                f"{self.BILLS_API_URL}",
            ]

            for url in api_urls:
                try:
                    response = self._make_request(url)
                    if response.status_code == 200 and 'json' in response.headers.get('content-type', '').lower():
                        bills = self._parse_bills_response(response, limit)
                        if bills:
                            self._debug_log_parsing_attempt("Parliament API", True, f"Found {len(bills)} bills via API")
                            return bills
                except Exception as e:
                    self._debug_log_parsing_attempt(f"API URL {url}", False, str(e))
                    continue

            self._debug_log_parsing_attempt("Parliament API", False, "API failed, trying HTML")

            # If API fails, try HTML scraping with correct URLs
            html_urls = [
                self.CURRENT_BILLS_URL,
                f"{self.BILLS_SEARCH_URL}?lang=en",
                self.BILLS_SEARCH_URL,
            ]

            for url in html_urls:
                try:
                    response = self._make_request(url)
                    if response.status_code == 200:
                        bills = self._parse_bills_response(response, limit)
                        if bills:
                            self._debug_log_parsing_attempt(f"HTML scraping from {url}", True, f"Found {len(bills)} bills")
                            return bills
                except Exception as e:
                    self._debug_log_parsing_attempt(f"HTML URL {url}", False, str(e))
                    continue

            self._debug_log_parsing_attempt("Parliament scraping", False, "All methods failed")
            return []

        except Exception as e:
            logger.error(f"Failed to scrape bills list: {e}")
            return []

    def _parse_bills_response(self, response: requests.Response, limit: int | None) -> List[Dict[str, Any]]:
        """Parse response from bills endpoint."""
        content_type = response.headers.get('content-type', '').lower()

        if 'json' in content_type:
            return self._parse_bills_json(response.json(), limit)
        else:
            return self._parse_bills_html_response(response, limit)

    def _parse_bills_json(self, data: Dict[str, Any], limit: int | None) -> List[Dict[str, Any]]:
        """Parse JSON response from Parliament API."""
        bills = []

        # Handle different possible JSON structures
        bill_items = data.get('items', data.get('bills', data.get('results', [])))

        for item in bill_items:
            if limit and len(bills) >= limit:
                break

            bill_data = self._extract_bill_from_json(item)
            if bill_data:
                bills.append(bill_data)

        return bills

    def _extract_bill_from_json(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract bill data from JSON item."""
        try:
            # Extract basic bill information
            bill_number = item.get('billNumber', item.get('bill_number'))
            title = item.get('title', item.get('name', ''))
            url = item.get('url', item.get('link'))

            # Ensure URL is absolute
            if url and not url.startswith('http'):
                url = urljoin(self.BASE_URL, url)

            # Extract sponsor/primary entity
            sponsor = item.get('sponsor', item.get('sponsoringMember', ''))
            if isinstance(sponsor, dict):
                sponsor = sponsor.get('displayName', sponsor.get('name', ''))

            # Extract dates
            introduction_date = item.get('introductionDate', item.get('dateIntroduced'))
            last_updated = item.get('lastModified', item.get('lastUpdated'))

            return {
                'bill_number': bill_number,
                'title': title,
                'url': url,
                'primary_entity': sponsor,
                'introduction_date': introduction_date,
                'last_updated': last_updated,
                'parliament_number': 54,  # Current parliament
            }

        except Exception as e:
            logger.warning(f"Failed to extract bill from JSON: {e}")
            return None

    def _scrape_bills_html(self, limit: int | None) -> List[Dict[str, Any]]:
        """Fallback: scrape bills from HTML pages."""
        try:
            response = self._make_request(f"{self.BILLS_SEARCH_URL}?Tab=Current")
            return self._parse_bills_html_response(response, limit)
        except Exception as e:
            logger.error(f"Failed to scrape bills HTML: {e}")
            return []

    def _parse_bills_html_response(self, response: requests.Response, limit: int | None) -> List[Dict[str, Any]]:
        """Parse HTML response to extract bill information."""
        soup = BeautifulSoup(response.text, 'html.parser')
        bills = []

        # Look for bill table rows (current Parliament website structure)
        bill_selectors = [
            'table tbody tr',  # Primary selector for Parliament table
            '.bill-item',
            '.bill-card',
            '.search-result',
            '[data-bill-id]',
            'article',
            '.legislation-item',
            '.datatable tbody tr',  # Alternative table structure
            'tbody tr'  # Generic table rows as fallback
        ]

        bill_elements = []
        successful_selector = None
        for selector in bill_selectors:
            bill_elements = soup.select(selector)
            if bill_elements:
                successful_selector = selector
                break

        self._debug_log_selector_attempts(bill_selectors, len(bill_elements), successful_selector)

        if not bill_elements:
            self._debug_log_parsing_attempt("HTML bill extraction", False, "No bill elements found with any selector")
            return []

        self._debug_log_parsing_attempt("HTML bill extraction", True, f"Found {len(bill_elements)} potential bill elements")

        for element in bill_elements:
            if limit and len(bills) >= limit:
                break

            bill_data = self._extract_bill_from_html(element)
            if bill_data:
                bills.append(bill_data)

        return bills

    def _extract_bill_from_html(self, element) -> Optional[Dict[str, Any]]:
        """Extract bill data from HTML element (assumes table row structure)."""
        try:
            # For table rows, extract data from columns
            cells = element.select('td')
            if len(cells) >= 2:  # At least title and one other column
                # Extract title and URL from first column (usually contains the link)
                title_cell = cells[0]
                link_elem = title_cell.select_one('a')

                if link_elem:
                    title = link_elem.get_text(strip=True)
                    url = link_elem.get('href', '')

                    # Ensure URL is absolute
                    if url and not url.startswith('http'):
                        url = urljoin(self.BASE_URL, url)

                    # Extract bill number from URL or title
                    bill_number = self._extract_bill_number(title, url)

                    # Extract sponsor from second or third column (varies by table structure)
                    sponsor = ''
                    for i in range(1, min(len(cells), 4)):  # Check columns 2-4 for sponsor
                        cell_text = cells[i].get_text(strip=True)
                        if cell_text and len(cell_text) > 2 and not cell_text.isdigit():
                            # Skip numeric values (likely bill numbers) and very short text
                            if not re.match(r'^\d{4}-\d{2}-\d{2}$', cell_text):  # Skip dates
                                sponsor = cell_text
                                break

                    # Extract date from last activity column (usually last column)
                    date_str = ''
                    if len(cells) > 2:
                        date_cell = cells[-1]  # Last column usually has date
                        date_text = date_cell.get_text(strip=True)
                        if re.search(r'\d{4}', date_text):  # Contains a year
                            date_str = date_text

                    if title and url:
                        bill_data = {
                            'bill_number': bill_number,
                            'title': title,
                            'url': url,
                            'primary_entity': sponsor or 'Unknown',
                            'parliament_number': 54,
                        }

                        if date_str:
                            normalized_date = self._normalize_date(date_str)
                            if normalized_date:
                                bill_data['last_activity_date'] = normalized_date

                        self._debug_log_parsing_attempt(f"Bill extraction", True, f"'{title[:50]}...'")
                        return bill_data

            # Fallback: try original extraction method for non-table structures
            title_selectors = ['h2', 'h3', '.title', '.bill-title', 'a']
            title = ''
            url = ''

            for selector in title_selectors:
                title_elem = element.select_one(selector)
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    if title_elem.name == 'a':
                        url = title_elem.get('href', '')
                    break

            if not url:
                link_elem = element.select_one('a')
                if link_elem:
                    url = link_elem.get('href', '')

            if url and not url.startswith('http'):
                url = urljoin(self.BASE_URL, url)

            if title and url:
                bill_number = self._extract_bill_number(title, url)
                return {
                    'bill_number': bill_number,
                    'title': title,
                    'url': url,
                    'primary_entity': 'Unknown',
                    'parliament_number': 54,
                }

        except Exception as e:
            logger.warning(f"Failed to extract bill from HTML element: {e}")

        return None

    def _extract_bill_number(self, title: str, url: str) -> str:
        """Extract bill number from title or URL."""
        # Try to extract from URL first
        url_match = re.search(r'BILL(\d+)', url)
        if url_match:
            return url_match.group(1)

        # Try to extract from title
        title_match = re.search(r'Bill\s+(\d+)', title, re.IGNORECASE)
        if title_match:
            return title_match.group(1)

        # Generate from URL if available
        if url:
            parsed = urlparse(url)
            path_parts = [part for part in parsed.path.split('/') if part]
            if path_parts:
                return path_parts[-1]

        return ''

    def _scrape_bill_details(self, bill_data: Dict[str, Any]) -> Dict[str, Any]:
        """Scrape detailed information for a specific bill."""
        if not bill_data.get('url'):
            return bill_data

        try:
            response = self._make_request(bill_data['url'])
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract summary
            summary = self._extract_summary(soup)

            # Extract stage history
            stage_history = self._extract_stage_history(soup)

            # Update bill data with detailed information
            bill_data.update({
                'summary': summary,
                'stage_history': stage_history,
                'last_scraped': datetime.now().isoformat(),
            })

            return bill_data

        except Exception as e:
            logger.warning(f"Failed to scrape bill details from {bill_data['url']}: {e}")
            return bill_data

    def _extract_summary(self, soup: BeautifulSoup) -> str:
        """Extract bill summary from detail page."""
        summary_selectors = [
            '.summary',
            '.description',
            '.bill-summary',
            '.explanatory-note',
            'meta[name="description"]',
            '.content p'
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
                    if len(text) > 50:  # Ensure it's a meaningful summary
                        return text

        return ''

    def _extract_stage_history(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract parliamentary stage history."""
        stages = []

        # Look for stage history table or timeline
        stage_selectors = [
            '.stage-history tr',
            '.timeline .stage',
            '.progress .step',
            '.stages li'
        ]

        for selector in stage_selectors:
            stage_elements = soup.select(selector)
            if stage_elements:
                for elem in stage_elements:
                    stage_info = self._extract_stage_info(elem)
                    if stage_info:
                        stages.append(stage_info)
                break

        return stages

    def _extract_stage_info(self, element) -> Optional[Dict[str, str]]:
        """Extract stage information from a stage element."""
        try:
            # Extract stage name
            stage_name = ''
            date_str = ''

            # Try different patterns for stage and date extraction
            text = element.get_text(strip=True)

            # Pattern 1: "Stage Name - Date"
            if ' - ' in text:
                parts = text.split(' - ', 1)
                if len(parts) == 2:
                    stage_name, date_str = parts

            # Pattern 2: Look for separate elements
            if not stage_name:
                stage_elem = element.select_one('.stage-name, .stage, th, td:first-child')
                if stage_elem:
                    stage_name = stage_elem.get_text(strip=True)

            if not date_str:
                date_elem = element.select_one('.date, .stage-date, td:last-child')
                if date_elem:
                    date_str = date_elem.get_text(strip=True)

            # Normalize date format
            if stage_name and date_str:
                normalized_date = self._normalize_date(date_str)
                if normalized_date:
                    return {
                        'stage': stage_name,
                        'date': normalized_date
                    }

        except Exception as e:
            logger.warning(f"Failed to extract stage info: {e}")

        return None

    def _normalize_date(self, date_str: str) -> Optional[str]:
        """Normalize date string to YYYY-MM-DD format."""
        try:
            # Try different date formats
            formats = [
                '%Y-%m-%d',
                '%d/%m/%Y',
                '%d-%m-%Y',
                '%d %B %Y',
                '%d %b %Y',
                '%B %d, %Y',
            ]

            for fmt in formats:
                try:
                    date_obj = datetime.strptime(date_str.strip(), fmt)
                    return date_obj.strftime('%Y-%m-%d')
                except ValueError:
                    continue

        except Exception as e:
            logger.warning(f"Failed to normalize date '{date_str}': {e}")

        return None

    def create_government_action(self, raw_data: Dict[str, Any]) -> GovernmentAction:
        """Convert raw Parliament data to GovernmentAction."""
        try:
            # Generate version-aware ID
            bill_number = raw_data.get('bill_number', '000')
            # Clean bill number to only contain digits
            clean_bill_number = re.sub(r'[^0-9]', '', str(bill_number))[:6]
            if not clean_bill_number:
                clean_bill_number = '000'

            # Parliament bills typically don't have URL versions, default to v1
            version = raw_data.get('version', '1')

            # Generate base ID
            base_id = f"parl-{datetime.now().year}-{clean_bill_number.zfill(3)}"

            # Generate full ID with version
            action_id = f"{base_id}-v{version}"

            # Extract date (use introduction date or current date)
            date_str = raw_data.get('introduction_date') or datetime.now().strftime('%Y-%m-%d')
            if date_str:
                normalized_date = self._normalize_date(date_str) or datetime.now().strftime('%Y-%m-%d')
            else:
                normalized_date = datetime.now().strftime('%Y-%m-%d')

            # Build stage history
            stage_history = []
            if raw_data.get('stage_history'):
                stage_history = [
                    StageHistory(stage=s['stage'], date=s['date'])
                    for s in raw_data['stage_history']
                    if s.get('stage') and s.get('date')
                ]

            # Create metadata with version information
            metadata = ActionMetadata(
                bill_number=raw_data.get('bill_number'),
                parliament_number=raw_data.get('parliament_number', 54),
                stage_history=stage_history,
                version=version
            )

            # Create the action
            return GovernmentAction(
                id=action_id,
                title=raw_data['title'],
                date=normalized_date,
                source_system=SourceSystem.PARLIAMENT,
                url=raw_data['url'],
                primary_entity=raw_data.get('primary_entity', 'Unknown'),
                summary=raw_data.get('summary', ''),
                labels=[],  # Will be filled by label processor
                metadata=metadata,
                version=version,
                base_id=base_id
            )

        except Exception as e:
            logger.error(f"Failed to create GovernmentAction from Parliament data: {e}")
            raise


def main():
    """Test the Parliament scraper."""
    import sys

    logging.basicConfig(level=logging.INFO)

    scraper = ParliamentScraper()
    try:
        if '--test' in sys.argv:
            bills = scraper.scrape(limit=5)
            print(f"Scraped {len(bills)} bills")
            for bill in bills:
                print(f"- {bill.get('title', 'No title')}")
                print(f"  URL: {bill.get('url', 'No URL')}")
                print(f"  Primary Entity: {bill.get('primary_entity', 'Unknown')}")
                print()
    finally:
        scraper.close()


if __name__ == '__main__':
    main()