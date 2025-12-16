"""
Example configuration for Keep Track NZ backend.
Copy this to config.py and customize as needed.
"""

# Repository settings
REPO_PATH = "/path/to/keep-track-nz"
OUTPUT_DIR = "src/data"

# Git settings
GIT_AUTHOR_NAME = "Keep Track NZ Bot"
GIT_AUTHOR_EMAIL = "bot@keeptrack.nz"
GIT_BRANCH = "main"

# Scraper settings
SCRAPER_LIMITS = {
    "PARLIAMENT": 50,
    "LEGISLATION": 50,
    "GAZETTE": 50,
    "BEEHIVE": 50
}

# API Keys (optional)
DIGITALNZ_API_KEY = ""  # For Gazette scraping

# Logging
LOG_LEVEL = "INFO"
LOG_FILE = "keep_track_nz.log"

# Scheduling
CRON_SCHEDULE = "0 2 * * *"  # 2 AM daily
