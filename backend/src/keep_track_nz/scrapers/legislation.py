"""Legislation scraper for legislation.govt.nz using the official RSS/Atom feed."""

import re
import logging
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional
from datetime import datetime

import requests

from ..models import SourceSystem, ActionMetadata, GovernmentAction
from .base import BaseScraper

logger = logging.getLogger(__name__)

# Atom namespace
ATOM_NS = {'atom': 'http://www.w3.org/2005/Atom'}


class LegislationScraper(BaseScraper):
    """
    Scraper for New Zealand legislation from legislation.govt.nz.
    
    Uses the official Atom feed which provides reliable access to recent
    legislation without anti-bot blocking issues.
    """

    BASE_URL = "https://www.legislation.govt.nz"
    RSS_FEED_URL = f"{BASE_URL}/subscribe/nzpco-rss.xml"

    def __init__(self, session: requests.Session | None = None, debug_context=None):
        """Initialize Legislation scraper."""
        super().__init__(session, debug_context)

    def get_source_system(self) -> str:
        """Get the source system identifier."""
        return SourceSystem.LEGISLATION.value

    def scrape(self, limit: int | None = None) -> List[Dict[str, Any]]:
        """
        Scrape recent legislation acts from the RSS feed.

        Args:
            limit: Optional limit on number of acts to scrape

        Returns:
            List of raw legislation data dictionaries
        """
        logger.info(f"Starting Legislation scraper (RSS feed) with limit: {limit}")

        try:
            # Fetch and parse the RSS feed
            response = self._make_request(self.RSS_FEED_URL)
            acts_data = self._parse_atom_feed(response.text, limit)

            logger.info(f"Successfully scraped {len(acts_data)} acts from Legislation RSS feed")
            return self._debug_log_scraped_items(acts_data)

        except Exception as e:
            logger.error(f"Legislation scraper failed: {e}")
            return []

    def _parse_atom_feed(self, xml_content: str, limit: int | None = None) -> List[Dict[str, Any]]:
        """Parse the Atom feed and extract Acts."""
        acts = []
        
        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as e:
            logger.error(f"Failed to parse RSS feed XML: {e}")
            return []

        # Find all entry elements
        entries = root.findall('atom:entry', ATOM_NS)
        logger.debug(f"Found {len(entries)} entries in RSS feed")

        for entry in entries:
            if limit and len(acts) >= limit:
                break

            act_data = self._parse_entry(entry)
            if act_data:
                acts.append(act_data)

        return acts

    def _parse_entry(self, entry: ET.Element) -> Optional[Dict[str, Any]]:
        """Parse a single Atom entry and extract act data if it's an Act."""
        try:
            # Get the content element which contains metadata
            content_elem = entry.find('atom:content', ATOM_NS)
            if content_elem is None or content_elem.text is None:
                return None

            content = content_elem.text

            # Only process entries that are Acts (not Bills, Regulations, etc.)
            if 'Information type: Acts' not in content:
                return None

            # Extract title
            title_elem = entry.find('atom:title', ATOM_NS)
            title = title_elem.text if title_elem is not None and title_elem.text else ''

            # Extract URL
            link_elem = entry.find('atom:link', ATOM_NS)
            url = link_elem.get('href', '') if link_elem is not None else ''

            # Extract publication date
            published_elem = entry.find('atom:published', ATOM_NS)
            published = published_elem.text if published_elem is not None and published_elem.text else ''

            # Parse the content for metadata
            metadata = self._parse_content_metadata(content)

            # Extract year, number, and version from content or URL
            year = metadata.get('year', self._extract_year_from_url(url))
            number = metadata.get('number', self._extract_number_from_url(url))
            version = metadata.get('version', self._extract_version_from_url(url))

            # Generate act number string
            act_number = f"{year} No {number}" if year and number else ''

            # Extract primary entity based on title keywords
            primary_entity = self._extract_primary_entity(title)

            # Normalize date to YYYY-MM-DD format
            date_str = self._normalize_date(published) or datetime.now().strftime('%Y-%m-%d')

            return {
                'title': title.strip(),
                'url': url,
                'act_number': act_number,
                'year': year,
                'number': number,
                'primary_entity': primary_entity,
                'date': date_str,
                'published': published,
                'current_as_at': metadata.get('current_as_at'),
                'version': version,  # Use the extracted version from URL or metadata
                'last_scraped': datetime.now().isoformat(),
            }

        except Exception as e:
            logger.warning(f"Failed to parse entry: {e}")
            return None

    def _parse_content_metadata(self, content: str) -> Dict[str, str]:
        """Parse the structured metadata from the entry content."""
        metadata = {}

        # Parse key-value pairs from the HTML content
        # Format: "Key: Value<br />"
        patterns = {
            'year': r'Year:\s*(\d{4})',
            'number': r'No:\s*(\d+)',
            'version': r'Version:\s*([^<]+)',
            'current_as_at': r'Current as at date:\s*([^<]+)',
            'status': r'Status:\s*([^<]+)',
            'legislation_type': r'Legislation type:\s*([^<]+)',
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, content)
            if match:
                metadata[key] = match.group(1).strip()

        return metadata

    def _extract_year_from_url(self, url: str) -> str:
        """Extract year from URL path like /act/public/2024/0012/..."""
        match = re.search(r'/act/public/(\d{4})/', url)
        if match:
            return match.group(1)
        return str(datetime.now().year)

    def _extract_number_from_url(self, url: str) -> str:
        """Extract act number from URL path like /act/public/2024/0012/..."""
        match = re.search(r'/act/public/\d{4}/(\d+)/', url)
        if match:
            return str(int(match.group(1)))  # Remove leading zeros
        return ''

    def _extract_version_from_url(self, url: str) -> str:
        """Extract version from URL path like /202.0/contents.html or /199.0/latest/..."""
        # Look for version pattern like /202.0/ in URL
        match = re.search(r'/(\d+)\.0/', url)
        if match:
            return match.group(1)

        # Look for other version patterns
        match = re.search(r'/version/(\d+)', url)
        if match:
            return match.group(1)

        # Default to version 1 if no version found
        return "1"

    def _extract_primary_entity(self, title: str) -> str:
        """Extract primary entity from act title based on policy area."""
        # Ministry/portfolio keyword mappings
        ministry_mappings = {
            'taxation': 'Hon Nicola Willis',
            'tax': 'Hon Nicola Willis',
            'budget': 'Hon Nicola Willis',
            'appropriation': 'Hon Nicola Willis',
            'education': 'Hon Erica Stanford',
            'health': 'Hon Dr Shane Reti',
            'housing': 'Hon Chris Bishop',
            'building': 'Hon Chris Bishop',
            'transport': 'Hon Simeon Brown',
            'road': 'Hon Simeon Brown',
            'justice': 'Hon Paul Goldsmith',
            'crime': 'Hon Mark Mitchell',
            'police': 'Hon Mark Mitchell',
            'environment': 'Hon Penny Simmonds',
            'immigration': 'Hon Erica Stanford',
            'defence': 'Hon Judith Collins',
            'treaty': 'Hon David Seymour',
        }

        lower_title = title.lower()
        for keyword, minister in ministry_mappings.items():
            if keyword in lower_title:
                return minister

        return 'Parliament'

    def _normalize_date(self, date_str: str) -> Optional[str]:
        """Normalize ISO 8601 date to YYYY-MM-DD format."""
        if not date_str:
            return None

        try:
            # Handle ISO 8601 format like "2025-12-15T18:40:28+13:00"
            # Try parsing with timezone
            if 'T' in date_str:
                # Remove timezone for simple parsing
                date_part = date_str.split('T')[0]
                datetime.strptime(date_part, '%Y-%m-%d')
                return date_part

            # Try other common formats
            formats = [
                '%Y-%m-%d',
                '%d/%m/%Y',
                '%d-%m-%Y',
                '%d %B %Y',
                '%d %b %Y',
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

    def _normalize_commencement_date(self, date_str: str) -> Optional[str]:
        """Normalize commencement date (often in dd/mm/yyyy format) to YYYY-MM-DD."""
        if not date_str:
            return None

        try:
            # Common formats for commencement dates
            formats = [
                '%d/%m/%Y',  # Most common: 27/11/2025
                '%d-%m-%Y',
                '%Y-%m-%d',
                '%d %B %Y',
                '%d %b %Y',
            ]

            for fmt in formats:
                try:
                    date_obj = datetime.strptime(date_str.strip(), fmt)
                    return date_obj.strftime('%Y-%m-%d')
                except ValueError:
                    continue

        except Exception as e:
            logger.warning(f"Failed to normalize commencement date '{date_str}': {e}")

        return None

    def _clean_version(self, version_str: str) -> str:
        """Clean version string to extract numeric version."""
        if not version_str:
            return "1"

        # Try to extract numeric version from various formats
        # "as at 27 November 2025" -> "1"
        # "as enacted" -> "1"
        # "202.0" -> "202"
        # "version 5" -> "5"

        # Look for numeric patterns
        numeric_match = re.search(r'(\d+)\.?\d*', version_str)
        if numeric_match:
            return numeric_match.group(1)

        # Default to version 1
        return "1"

    def create_government_action(self, raw_data: Dict[str, Any]) -> GovernmentAction:
        """Convert raw Legislation data to GovernmentAction."""
        try:
            # Generate version-aware ID
            year = raw_data.get('year', str(datetime.now().year))
            number = raw_data.get('number', '000')
            raw_version = raw_data.get('version', '1')
            version = self._clean_version(raw_version)

            # Generate base ID
            base_id = f"leg-{year}-{str(number).zfill(3)}"

            # Generate full ID with version
            action_id = f"{base_id}-v{version}"

            # Use the scraped date
            date_str = raw_data.get('date') or datetime.now().strftime('%Y-%m-%d')

            # Normalize commencement date to YYYY-MM-DD format
            commencement_date = raw_data.get('current_as_at')
            if commencement_date:
                commencement_date = self._normalize_commencement_date(commencement_date)

            # Create metadata with version information
            metadata = ActionMetadata(
                act_number=raw_data.get('act_number'),
                commencement_date=commencement_date,
                version=version
            )

            # Create the action
            return GovernmentAction(
                id=action_id,
                title=raw_data['title'],
                date=date_str,
                source_system=SourceSystem.LEGISLATION,
                url=raw_data['url'],
                primary_entity=raw_data.get('primary_entity', 'Parliament'),
                summary=f"Version {version} of {raw_data['title']}",  # Better summary than just version
                labels=[],  # Will be filled by label processor
                metadata=metadata,
                version=version,
                base_id=base_id
            )

        except Exception as e:
            logger.error(f"Failed to create GovernmentAction from Legislation data: {e}")
            raise


def main():
    """Test the Legislation scraper."""
    import sys

    logging.basicConfig(level=logging.INFO)

    scraper = LegislationScraper()
    try:
        if '--test' in sys.argv:
            acts = scraper.scrape(limit=5)
            print(f"Scraped {len(acts)} acts")
            for act in acts:
                print(f"- {act.get('title', 'No title')}")
                print(f"  Act Number: {act.get('act_number', 'Unknown')}")
                print(f"  URL: {act.get('url', 'No URL')}")
                print(f"  Date: {act.get('date', 'Unknown')}")
                print(f"  Primary Entity: {act.get('primary_entity', 'Unknown')}")
                print()
    finally:
        scraper.close()


if __name__ == '__main__':
    main()
