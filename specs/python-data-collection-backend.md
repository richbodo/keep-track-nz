# Feature: Python Data Collection Backend for Keep Track NZ

## Feature Description
A standalone Python backend system that runs as a nightly cron job to automatically collect, validate, deduplicate, and format New Zealand government action data from official sources. The system will scrape data from four canonical NZ government websites (Parliament bills, Legislation, Gazette, and Beehive), process it according to the existing data schema, and commit the updated dataset to the GitHub repository to maintain a flat-file database for the static site.

## User Story
As a citizen of New Zealand
I want to see the most current government actions from all official sources
So that I can stay informed about legislative, parliamentary, and administrative activities without manually checking multiple government websites

## Problem Statement
The current Keep Track NZ website uses static fixture data that requires manual updates. Citizens need access to real-time government action data from multiple official sources (Parliament bills, passed legislation, gazette notices, and government announcements), but there's no automated system to collect, validate, deduplicate, and format this data for consumption by the static site.

## Solution Statement
Create a Python-based data collection system that runs as a scheduled cron job to automatically scrape the four official NZ government data sources, validate and deduplicate the collected actions, format them according to the existing TypeScript schema, and commit the updated data files to the GitHub repository. This solution maintains the static site architecture while ensuring data freshness through automated collection.

## Relevant Files
Use these files to implement the feature:

- `src/data/fixtureData.ts` - Contains the current data schema and sample data structure that the Python backend must replicate
- `src/components/ActionCard.tsx` - Shows how government actions are displayed, informing data requirements
- `src/pages/Index.tsx` - Demonstrates how data filtering and labeling works, ensuring compatibility
- `README.md` - Documents the current deployment process that the backend must integrate with

### New Files
- `backend/` - New Python project root directory
- `backend/pyproject.toml` - Python project configuration with dependencies
- `backend/src/keep_track_nz/` - Main Python package
- `backend/src/keep_track_nz/models/` - Data models and schema validation
- `backend/src/keep_track_nz/scrapers/` - Individual scrapers for each data source
- `backend/src/keep_track_nz/processors/` - Data processing, deduplication, and formatting
- `backend/src/keep_track_nz/exporters/` - Export data to frontend format
- `backend/src/keep_track_nz/main.py` - Main entry point for cron job
- `backend/tests/` - Comprehensive test suite
- `backend/scripts/` - Utility scripts for setup and manual runs
- `backend/README.md` - Backend-specific documentation

## Implementation Plan
### Phase 1: Foundation
Set up the Python project structure with proper dependency management, create data models that mirror the TypeScript schema, establish the basic project architecture with modular scrapers, processors, and exporters.

### Phase 2: Core Implementation
Develop individual scrapers for each of the four NZ government data sources (Parliament, Legislation, Gazette, Beehive), implement data validation and deduplication logic, and create the main orchestrator that coordinates the collection process.

### Phase 3: Integration
Build the export system to generate frontend-compatible data files, implement Git integration for automated commits, add comprehensive error handling and logging, and create the cron job configuration with proper scheduling.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Project Setup and Architecture
- Create Python project structure with `uv` package manager
- Initialize `pyproject.toml` with necessary dependencies (requests, beautifulsoup4, pydantic, gitpython, schedule)
- Set up basic package structure with proper imports
- Create base classes for scrapers, processors, and exporters

### Step 2: Data Schema Implementation
- Analyze current TypeScript interfaces and create equivalent Pydantic models
- Implement `GovernmentAction` model with proper validation
- Create `SourceSystem` enum and `ActionMetadata` models
- Add schema validation and type safety throughout the system

### Step 3: Parliament Bills Scraper
- Research Parliament Open Data API at data.parliament.nz
- Implement scraper for current and recent bills
- Parse bill metadata including stage history and bill numbers
- Create unit tests for Parliament scraper functionality

### Step 4: Legislation Scraper
- Research legislation.govt.nz API or web scraping approach
- Implement scraper for recently passed Acts
- Parse act numbers, commencement dates, and metadata
- Create unit tests for Legislation scraper functionality

### Step 5: Gazette Scraper
- Research DigitalNZ API for Gazette notices access
- Implement scraper for official gazette notices
- Parse notice types, numbers, and portfolio information
- Create unit tests for Gazette scraper functionality

### Step 6: Beehive Scraper
- Research beehive.govt.nz for press releases and speeches
- Implement scraper for government announcements
- Parse document types and portfolio assignments
- Create unit tests for Beehive scraper functionality

### Step 7: Data Processing Pipeline
- Implement deduplication logic using title similarity and URL matching
- Create label classification system using keyword matching
- Add data validation to ensure schema compliance
- Create unit tests for processing pipeline

### Step 8: Export System
- Implement TypeScript data file generation
- Create JSON export functionality for potential future API use
- Add backup and versioning for data files
- Create unit tests for export functionality

### Step 9: Git Integration
- Implement automated Git commits with meaningful messages
- Add proper error handling for Git operations
- Create configuration for commit author and repository settings
- Test Git integration with dummy commits

### Step 10: Main Orchestrator and Scheduling
- Create main entry point that coordinates all scrapers
- Implement proper logging and error reporting
- Add configuration management for different environments
- Create cron job configuration and documentation

### Step 11: Comprehensive Testing
- Create integration tests that test the full pipeline
- Add tests for error conditions and edge cases
- Implement data quality validation tests
- Create performance tests for large datasets

### Step 12: Documentation and Deployment
- Create comprehensive README with setup instructions
- Document the data sources and scraping approach
- Add troubleshooting guide and maintenance procedures
- Create deployment scripts for cron job setup

### Step 13: Validation
- Run the complete pipeline manually to verify functionality
- Test with current data to ensure compatibility with frontend
- Validate all unit and integration tests pass
- Verify Git integration works correctly with the repository

## Testing Strategy
### Unit Tests
- Test each individual scraper with mock data responses
- Test data models for proper validation and serialization
- Test deduplication logic with known duplicate scenarios
- Test export functionality with sample datasets
- Test Git operations with temporary repositories

### Integration Tests
- Test complete pipeline from scraping to Git commit
- Test error handling when data sources are unavailable
- Test data quality validation across multiple scraper runs
- Test schema compatibility between Python backend and TypeScript frontend

### Edge Cases
- Handle network timeouts and connection errors gracefully
- Manage cases where government websites change structure
- Handle duplicate data across different sources
- Manage Git conflicts and repository access issues
- Handle invalid or malformed data from scrapers

## Acceptance Criteria
- [ ] Python backend successfully scrapes data from all four NZ government sources
- [ ] Data deduplication prevents duplicate government actions in the dataset
- [ ] Generated data files are compatible with existing TypeScript frontend
- [ ] System runs successfully as a scheduled cron job
- [ ] All scraped data passes schema validation
- [ ] Git integration automatically commits updated data files
- [ ] Comprehensive logging allows for debugging and monitoring
- [ ] Test suite achieves >90% code coverage
- [ ] System handles network errors and data source changes gracefully
- [ ] Documentation allows for easy setup and maintenance

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `cd backend && uv run python -m pytest` - Run all backend tests to validate functionality
- `cd backend && uv run python -m keep_track_nz.main --dry-run` - Test the full pipeline without Git commits
- `cd backend && uv run python -m keep_track_nz.scrapers.parliament --test` - Test Parliament scraper individually
- `cd backend && uv run python -m keep_track_nz.scrapers.legislation --test` - Test Legislation scraper individually
- `cd backend && uv run python -m keep_track_nz.scrapers.gazette --test` - Test Gazette scraper individually
- `cd backend && uv run python -m keep_track_nz.scrapers.beehive --test` - Test Beehive scraper individually
- `cd backend && uv run python -c "from keep_track_nz.models import GovernmentAction; print('Schema validation works')"` - Validate data models
- `npm run build` - Ensure frontend still builds correctly with new data structure
- `npm run lint` - Ensure no linting errors in existing frontend code

## Notes
- The system uses `uv` for Python dependency management for faster installations and better dependency resolution
- Each scraper is designed as a modular component that can be run independently for testing and debugging
- The Git integration includes proper error handling to prevent data loss during commit failures
- Data sources may require different scraping approaches (APIs vs web scraping) based on availability
- The system maintains backward compatibility with the existing TypeScript frontend data structure
- Consider implementing rate limiting for web scraping to be respectful to government servers
- Future consideration: Add webhook notifications for successful/failed runs
- The flat-file database approach is intentionally simple but may need evolution as data volume grows
- All government data sources referenced are official and publicly available for reuse