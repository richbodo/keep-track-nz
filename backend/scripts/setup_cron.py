#!/usr/bin/env python3
"""Setup cron job for Keep Track NZ backend."""

import os
import sys
import subprocess
from pathlib import Path


def get_current_crontab() -> str:
    """Get current crontab content."""
    try:
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout
        else:
            return ""
    except Exception:
        return ""


def add_cron_job(cron_line: str) -> bool:
    """Add cron job to crontab."""
    try:
        # Get current crontab
        current_crontab = get_current_crontab()

        # Check if job already exists
        if "keep-track-nz" in current_crontab:
            print("Keep Track NZ cron job already exists in crontab")
            print("Current entry:")
            for line in current_crontab.split('\n'):
                if "keep-track-nz" in line:
                    print(f"  {line}")
            return True

        # Add new job
        new_crontab = current_crontab.rstrip('\n') + '\n' + cron_line + '\n'

        # Write to crontab
        result = subprocess.run(['crontab', '-'], input=new_crontab, text=True)
        return result.returncode == 0

    except Exception as e:
        print(f"Error setting up cron job: {e}")
        return False


def generate_cron_command() -> str:
    """Generate the cron command."""
    backend_dir = Path(__file__).parent.parent.resolve()
    repo_dir = backend_dir.parent

    # Use uv to run the command
    python_cmd = f"cd {backend_dir} && uv run python -m keep_track_nz.main"

    # Add logging
    log_file = backend_dir / "logs" / "cron.log"
    log_file.parent.mkdir(exist_ok=True)

    cron_cmd = f"{python_cmd} >> {log_file} 2>&1"

    return cron_cmd


def main():
    """Main setup function."""
    print("Keep Track NZ Cron Job Setup")
    print("=" * 40)

    # Generate cron command
    cron_cmd = generate_cron_command()
    print(f"Command: {cron_cmd}")

    # Cron schedule (2 AM daily)
    cron_schedule = "0 2 * * *"

    # Full cron line
    cron_line = f"# Keep Track NZ - Daily data collection\n{cron_schedule} {cron_cmd}"

    print(f"\nCron job to be added:")
    print(cron_line)

    # Ask for confirmation
    response = input("\nDo you want to add this cron job? (y/N): ").strip().lower()

    if response in ['y', 'yes']:
        success = add_cron_job(cron_line)
        if success:
            print("✓ Cron job added successfully!")
            print("\nTo verify the cron job was added, run:")
            print("  crontab -l")
        else:
            print("✗ Failed to add cron job")
            return 1
    else:
        print("Cron job setup cancelled")

        # Show manual instructions
        print("\nTo set up manually:")
        print("1. Run: crontab -e")
        print("2. Add this line:")
        print(f"   {cron_line}")
        print("3. Save and exit")

    print("\nAdditional setup notes:")
    print("- Ensure the server has access to the Git repository")
    print("- Test the cron job manually first:")
    print(f"  {cron_cmd.replace(' >> /dev/null 2>&1', '')}")
    print("- Check logs for any issues:")
    print(f"  tail -f {Path(__file__).parent.parent}/logs/cron.log")

    return 0


if __name__ == "__main__":
    sys.exit(main())