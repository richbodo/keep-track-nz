# Keep Track NZ Backend

A Python-based data collection system that automatically scrapes, processes, and exports New Zealand government action data.

## Overview

This backend system runs as a scheduled cron job to:

1. **Scrape** government actions from four official NZ sources:
   - Parliament bills (bills.parliament.nz)
   - Legislation acts (legislation.govt.nz)
   - Gazette notices (gazette.govt.nz)
   - Government announcements (beehive.govt.nz)

2. **Process** the data through:
   - Validation and normalization
   - Automatic label classification

3. **Export** the processed data as:
   - TypeScript files for frontend consumption
   - JSON files for potential API use

4. **Commit** updated data to the Git repository automatically

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- Git repository access for Keep Track NZ

### Installation

1. **Clone and setup the backend:**
   ```bash
   cd backend
   uv sync
   ```

2. **Install development dependencies:**
   ```bash
   uv sync --extra dev
   ```

3. **Run setup script:**
   ```bash
   python scripts/setup.py
   ```

4. **Configure the system:**
   ```bash
   cp config.example.py config.py
   # Edit config.py with your settings
   ```

### Basic Usage

**Test the pipeline (dry run):**
```bash
uv run python -m keep_track_nz.main --dry-run --limit 5
```

**Run the full pipeline:**
```bash
uv run python -m keep_track_nz.main
```

**Set up cron job:**
```bash
python scripts/setup_cron.py
```

## Architecture

### Core Components

```
keep_track_nz/
├── models/          # Data models and schema validation
├── scrapers/        # Source-specific data scrapers
├── processors/      # Data validation, labeling
├── exporters/       # TypeScript and JSON export
├── git_integration.py  # Automated Git operations
└── main.py         # Main orchestrator
```

### Data Flow

```
[Government Sources] → [Scrapers] → [Processors] → [Exporters] → [Git Commit]
       ↓                   ↓            ↓            ↓             ↓
   4 Official APIs    Raw Data     Validated    TypeScript    Repository
                                   Labeled      & JSON        Updated
                                               Files
```

## Configuration

### Basic Configuration

Copy `config.example.py` to `config.py` and customize:

```python
# Repository settings
REPO_PATH = "/path/to/keep-track-nz"
OUTPUT_DIR = "src/data"

# Git settings
GIT_AUTHOR_NAME = "Keep Track NZ Bot"
GIT_AUTHOR_EMAIL = "bot@keeptrack.nz"

# Scraper limits (for testing)
SCRAPER_LIMITS = {
    "PARLIAMENT": 50,
    "LEGISLATION": 50,
    "GAZETTE": 50,
    "BEEHIVE": 50
}

# API Keys (optional)
DIGITALNZ_API_KEY = ""  # For enhanced Gazette scraping
```

### Environment Variables

Optional environment variables:

- `DIGITALNZ_API_KEY`: API key for DigitalNZ Gazette access
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `KEEP_TRACK_CONFIG`: Path to custom config file

## Data Sources

### 1. Parliament Bills (bills.parliament.nz)
- **What**: Current and recent parliamentary bills
- **Method**: Web scraping with fallback to HTML parsing
- **Data**: Bill titles, stages, sponsors, summaries
- **Output**: Parliament actions with stage history

### 2. Legislation Acts (legislation.govt.nz)
- **What**: Recently passed Acts of Parliament
- **Method**: Web scraping of legislation browse pages
- **Data**: Act titles, numbers, commencement dates
- **Output**: Legislation actions with act metadata

### 3. Gazette Notices (gazette.govt.nz)
- **What**: Official government notices and appointments
- **Method**: DigitalNZ API + web scraping fallback
- **Data**: Notice types, appointments, regulatory changes
- **Output**: Gazette actions with notice metadata

### 4. Government Announcements (beehive.govt.nz)
- **What**: Press releases and ministerial speeches
- **Method**: Web scraping of press release listings
- **Data**: Announcements, portfolios, ministers
- **Output**: Beehive actions with document metadata

## Data Processing

### Validation Pipeline

1. **Schema Validation**: Ensures all data meets TypeScript interface requirements
2. **Data Cleaning**: Normalizes dates, URLs, and text formatting
3. **Field Generation**: Creates missing IDs and infers primary entities

### Label Classification

Automatic assignment of policy area labels based on:

- **Keyword Matching**: Title and summary content analysis
- **Portfolio Inference**: Minister and department information
- **Business Rules**: Source-specific classification logic

**Available Labels**: Housing, Health, Education, Infrastructure, Environment, Economy, Justice, Immigration, Defence, Transport, Social Welfare, Tax, Local Government, Treaty of Waitangi, Agriculture

## Development

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=keep_track_nz --cov-report=html

# Run specific test file
uv run pytest tests/test_models.py -v
```

### Code Quality

```bash
# Linting
uv run ruff check .

# Type checking
uv run mypy keep_track_nz

# Formatting
uv run black .
```

### Testing Individual Components

```bash
# Test scrapers
uv run python -m keep_track_nz.scrapers.parliament --test
uv run python -m keep_track_nz.scrapers.legislation --test
uv run python -m keep_track_nz.scrapers.gazette --test
uv run python -m keep_track_nz.scrapers.beehive --test

# Test processors
uv run python -m keep_track_nz.processors.labeler --test
uv run python -m keep_track_nz.processors.validator --test

# Test exporters
uv run python -m keep_track_nz.exporters.typescript --test

# Test Git integration
uv run python -m keep_track_nz.git_integration --test
```

## Troubleshooting

### Common Issues

**No data scraped:**
- Check network connectivity to government websites
- Verify website structure hasn't changed
- Check rate limiting or IP blocking

**Git commit failures:**
- Verify repository access and permissions
- Check Git configuration and branch settings
- Ensure working directory is clean

**Processing errors:**
- Check data validation errors in logs
- Verify schema compatibility

**Export failures:**
- Check file system permissions
- Verify output directory exists
- Check TypeScript syntax generation

### Current Scraper Status and Limitations

As of December 2025, each scraper has specific characteristics and limitations:

#### ✅ Working Scrapers

**Legislation Scraper (legislation.govt.nz)**
- Status: ✅ Fully functional
- Returns: ~145 recent Acts of Parliament
- Notes: Reliable HTML structure, consistent data format

**Gazette Scraper (gazette.govt.nz)**
- Status: ✅ Fully functional
- Returns: ~100 official government notices
- Notes: Uses DigitalNZ API with HTML fallback

#### ⚠️ Limited Functionality Scrapers

**Parliament Scraper (bills.parliament.nz)**
- Status: ⚠️ Requires JavaScript rendering
- Returns: 0 items (currently non-functional)
- Issue: Website is heavily JavaScript-based and loads content dynamically
- URLs Fixed: Updated to use `/bills-proposed-laws?lang=en`
- Selectors Fixed: Updated to parse table structure (`table tbody tr`)
- **Potential Solutions:**
  - Implement Playwright/Selenium for JavaScript rendering
  - Investigate if Parliament provides a JSON API endpoint
  - Use headless browser automation for data extraction

**Beehive Scraper (beehive.govt.nz)**
- Status: ⚠️ Blocked by bot protection
- Returns: 0 items (currently blocked)
- Issue: Incapsula bot detection service blocks requests
- URLs Fixed: Corrected to use `/releases` and `/speeches`
- Selectors Fixed: Updated to parse article structure
- **Current Mitigations:** Enhanced headers, retry logic, exponential backoff
- **Potential Solutions:**
  - Implement Playwright/Selenium to bypass bot protection
  - Use rotating user agents and proxy services
  - Investigate if Beehive provides RSS feeds or API access

#### Debug Capabilities

All scrapers now include comprehensive debug logging:
- Request/response details with status codes and content types
- HTML sample viewing (first 500 characters)
- Selector attempt tracking with success/failure indicators
- Parsing status reporting with clear error messages
- Visual indicators (✅❌🌐📄🔍) for better readability

**Test individual scrapers with debug output:**
```bash
# Test with debug information
cd backend
uv run python -m keep_track_nz.scrapers.parliament --test --debug
uv run python -m keep_track_nz.scrapers.beehive --test --debug
uv run python -m keep_track_nz.scrapers.legislation --test --debug
uv run python -m keep_track_nz.scrapers.gazette --test --debug
```

#### Recommended Next Steps

1. **High Priority:** Implement JavaScript rendering support for Parliament scraper
2. **High Priority:** Add bot protection bypass for Beehive scraper
3. **Medium Priority:** Investigate API alternatives for both problematic scrapers
4. **Low Priority:** Add website change detection to alert when scraper maintenance is needed

### Debug Mode

Run with verbose logging:
```bash
uv run python -m keep_track_nz.main --verbose --dry-run
```

Save debug statistics:
```bash
uv run python -m keep_track_nz.main --stats-file debug_stats.json
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see the main repository for details.

## Support

For issues and questions:
- Create an issue in the GitHub repository
- Check the troubleshooting section above
- Review the logs for error details
