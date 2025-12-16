#!/usr/bin/env python3
"""Setup script for Keep Track NZ backend."""

import os
import sys
import subprocess
from pathlib import Path


def run_command(cmd: str, description: str) -> bool:
    """Run a command and return success status."""
    print(f"Running: {description}")
    print(f"Command: {cmd}")

    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    if result.returncode == 0:
        print("✓ Success")
        if result.stdout:
            print(f"Output: {result.stdout}")
    else:
        print("✗ Failed")
        if result.stderr:
            print(f"Error: {result.stderr}")
        return False

    print("-" * 50)
    return True


def main():
    """Main setup function."""
    print("Keep Track NZ Backend Setup")
    print("=" * 40)

    # Get the backend directory
    backend_dir = Path(__file__).parent.parent
    print(f"Backend directory: {backend_dir}")

    # Change to backend directory
    os.chdir(backend_dir)

    # Install dependencies
    if not run_command("uv sync", "Installing Python dependencies"):
        return 1

    # Install development dependencies
    if not run_command("uv sync --extra dev", "Installing development dependencies"):
        return 1

    # Run basic tests to verify setup
    if not run_command("uv run python -c \"from keep_track_nz.models import GovernmentAction; print('✓ Models import successful')\"",
                      "Testing model imports"):
        return 1

    # Test scrapers
    if not run_command("uv run python -m keep_track_nz.scrapers.parliament --test",
                      "Testing Parliament scraper"):
        print("Warning: Parliament scraper test failed")

    # Create example configuration
    config_file = backend_dir / "config.example.py"
    config_content = '''"""
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
'''

    try:
        with open(config_file, 'w') as f:
            f.write(config_content)
        print(f"✓ Created example configuration: {config_file}")
    except Exception as e:
        print(f"✗ Failed to create configuration: {e}")

    print("\nSetup complete!")
    print("\nNext steps:")
    print("1. Copy config.example.py to config.py and customize")
    print("2. Set up cron job: python scripts/setup_cron.py")
    print("3. Test the pipeline: uv run python -m keep_track_nz.main --dry-run --limit 3")

    return 0


if __name__ == "__main__":
    sys.exit(main())