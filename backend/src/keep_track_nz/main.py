"""Main orchestrator for the Keep Track NZ data collection system."""

import argparse
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import importlib.util
import warnings

# Import configuration from backend/config.py
def _load_config():
    """Load config from backend/config.py using path-based import."""
    # Navigate from main.py (backend/src/keep_track_nz/) up to backend/config.py
    backend_dir = Path(__file__).parent.parent.parent
    config_path = backend_dir / "config.py"
    
    if config_path.exists():
        spec = importlib.util.spec_from_file_location("config", config_path)
        if spec is not None and spec.loader is not None:
            config_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(config_module)
            return config_module
        else:
            warnings.warn(
                f"Failed to load config module spec from {config_path}. Using default configuration.",
                UserWarning
            )
    else:
        warnings.warn(
            f"Config file not found at {config_path}. Using default configuration. "
            f"Copy config.example.py to config.py and customize as needed.",
            UserWarning
        )
        # Return a class with default values matching config.example.py
        class DefaultConfig:
            REPO_PATH = str(backend_dir.parent)
            OUTPUT_DIR = "src/data"
            GIT_AUTHOR_NAME = "Keep Track NZ Bot"
            GIT_AUTHOR_EMAIL = "bot@keeptrack.nz"
            GIT_BRANCH = "main"
            SCRAPER_LIMITS = {
                "PARLIAMENT": 50,
                "LEGISLATION": 50,
                "GAZETTE": 50,
                "BEEHIVE": 50
            }
            DIGITALNZ_API_KEY = ""
            LOG_LEVEL = "INFO"
            LOG_FILE = "keep_track_nz.log"
            CRON_SCHEDULE = "0 2 * * *"
        return DefaultConfig()

config = _load_config()

from .models import GovernmentAction, ActionCollection, SourceSystem
from .scrapers import (
    parliament,
    legislation,
    gazette,
    beehive
)
from .processors import (
    DataValidator,
    LabelClassifier,
    DeduplicationProcessor
)
from .exporters import TypeScriptExporter
from .git_integration import GitIntegration
from .debug import DebugContext, DebugFormatter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)


class DataCollectionOrchestrator:
    """Main orchestrator for the data collection pipeline."""

    def __init__(
        self,
        output_dir: Path,
        repo_path: Optional[Path] = None,
        dry_run: bool = False,
        limit_per_source: Optional[int] = None,
        debug_mode: bool = False
    ):
        """
        Initialize the orchestrator.

        Args:
            output_dir: Directory for output files
            repo_path: Path to Git repository (if different from output_dir parent)
            dry_run: If True, don't commit changes to Git
            limit_per_source: Limit number of items to scrape per source (for testing)
            debug_mode: If True, enable detailed debug output
        """
        self.output_dir = Path(output_dir)
        self.repo_path = repo_path or self.output_dir.parent
        self.dry_run = dry_run
        self.limit_per_source = limit_per_source
        self.debug_mode = debug_mode

        # Initialize debug context
        self.debug_context = DebugContext(enabled=debug_mode)

        # Initialize components
        self.scrapers = {
            'PARLIAMENT': parliament.ParliamentScraper(debug_context=self.debug_context),
            'LEGISLATION': legislation.LegislationScraper(debug_context=self.debug_context),
            'GAZETTE': gazette.GazetteScraper(debug_context=self.debug_context),
            'BEEHIVE': beehive.BeehiveScraper(debug_context=self.debug_context)
        }

        self.processors = [
            DataValidator(debug_context=self.debug_context, strict_mode=False),
            DeduplicationProcessor(debug_context=self.debug_context),
            LabelClassifier(debug_context=self.debug_context)
        ]

        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.typescript_exporter = TypeScriptExporter(self.output_dir / "actions.ts")

        if not dry_run:
            self.git_integration = GitIntegration(
                repo_path=self.repo_path,
                commit_author_name=config.GIT_AUTHOR_NAME,
                commit_author_email=config.GIT_AUTHOR_EMAIL
            )
        else:
            self.git_integration = None

        # Statistics tracking
        self.run_stats = {
            'start_time': None,
            'end_time': None,
            'total_scraped': 0,
            'total_processed': 0,
            'source_stats': {},
            'processing_stats': {},
            'errors': [],
            'warnings': []
        }

    def run_complete_pipeline(self) -> bool:
        """
        Run the complete data collection and export pipeline.

        Returns:
            True if pipeline completed successfully, False otherwise
        """
        logger.info("Starting complete data collection pipeline")
        self.run_stats['start_time'] = datetime.now()

        try:
            # 1. Scrape data from all sources
            all_raw_data = self._scrape_all_sources()
            if not all_raw_data:
                logger.error("No data scraped from any source")
                return False

            # 2. Convert to GovernmentAction objects
            government_actions = self._convert_to_actions(all_raw_data)

            # 3. Process data (validate, deduplicate, label)
            processed_actions = self._process_data(government_actions)

            # 4. Export data
            export_success = self._export_data(processed_actions)
            if not export_success:
                logger.error("Data export failed")
                return False

            # 5. Commit to Git (if not dry run)
            if not self.dry_run:
                commit_success = self._commit_changes(processed_actions)
                if not commit_success:
                    logger.warning("Git commit failed, but data was exported successfully")

            self._finalize_stats(processed_actions)

            # Final debug summary
            if self.debug_context and self.debug_context.enabled:
                print(DebugFormatter.format_pipeline_debug_summary(
                    self.run_stats['total_scraped'],
                    self.run_stats['total_processed'],
                    self.run_stats['source_stats'],
                    {}  # No deduplication stats
                ))

            logger.info("Pipeline completed successfully")
            return True

        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            self.run_stats['errors'].append(f"Pipeline error: {e}")
            return False

        finally:
            self.run_stats['end_time'] = datetime.now()
            self._log_final_statistics()
            self._cleanup_resources()

    def _scrape_all_sources(self) -> List[Dict[str, Any]]:
        """Scrape data from all configured sources."""
        logger.info("Starting data scraping from all sources")

        if self.debug_context and self.debug_context.enabled:
            print(DebugFormatter.format_section_header("SCRAPING PROCESS"))

        all_data = []

        for source_name, scraper in self.scrapers.items():
            try:
                logger.info(f"Scraping {source_name}")

                if self.debug_context and self.debug_context.enabled:
                    print(f"\n🔍 Scraping {source_name}...")

                source_data = scraper.scrape(limit=self.limit_per_source)

                # Add source system to each item and log debug info
                for item in source_data:
                    item['source_system'] = source_name
                    # Debug logging is handled within the scraper now

                self.run_stats['source_stats'][source_name] = {
                    'scraped': len(source_data),
                    'success': True
                }

                all_data.extend(source_data)
                logger.info(f"Scraped {len(source_data)} items from {source_name}")

            except Exception as e:
                logger.error(f"Scraping failed for {source_name}: {e}")
                self.run_stats['source_stats'][source_name] = {
                    'scraped': 0,
                    'success': False,
                    'error': str(e)
                }
                self.run_stats['errors'].append(f"Scraping error ({source_name}): {e}")

        self.run_stats['total_scraped'] = len(all_data)
        logger.info(f"Total scraped: {len(all_data)} items")
        return all_data

    def _convert_to_actions(self, raw_data: List[Dict[str, Any]]) -> List[GovernmentAction]:
        """Convert raw scraped data to GovernmentAction objects."""
        logger.info("Converting raw data to GovernmentAction objects")
        actions = []

        for item in raw_data:
            try:
                source_system = SourceSystem(item['source_system'])
                scraper = self.scrapers[source_system.value]

                if hasattr(scraper, 'create_government_action'):
                    action = scraper.create_government_action(item)
                    actions.append(action)
                else:
                    logger.warning(f"Scraper {source_system.value} doesn't have create_government_action method")

            except Exception as e:
                logger.warning(f"Failed to convert item to GovernmentAction: {e}")
                self.run_stats['warnings'].append(f"Conversion warning: {e}")

        logger.info(f"Converted {len(actions)} items to GovernmentAction objects")
        return actions

    def _process_data(self, actions: List[GovernmentAction]) -> List[GovernmentAction]:
        """Process data through validation, deduplication, and labeling."""
        logger.info("Processing data through validation, deduplication, and labeling")

        for processor in self.processors:
            processor_name = processor.__class__.__name__
            logger.info(f"Running {processor_name}")

            try:
                input_count = len(actions)

                if processor_name == 'DeduplicationProcessor':
                    # Deduplication processor expects GovernmentAction objects
                    actions = processor.process(actions)
                else:
                    # Other processors expect dictionaries
                    data = [action.to_dict() for action in actions]
                    data = processor.process(data)

                    # Convert back to GovernmentAction objects
                    processed_actions = []
                    for item in data:
                        try:
                            action = GovernmentAction(**item)
                            processed_actions.append(action)
                        except Exception as e:
                            logger.warning(f"Failed to create GovernmentAction from processed data: {e}")

                    actions = processed_actions

                output_count = len(actions)

                self.run_stats['processing_stats'][processor_name] = {
                    'input_count': input_count,
                    'output_count': output_count,
                    'success': True
                }

                logger.info(f"{processor_name}: {input_count} -> {output_count}")

            except Exception as e:
                logger.error(f"Processing failed in {processor_name}: {e}")
                self.run_stats['processing_stats'][processor_name] = {
                    'success': False,
                    'error': str(e)
                }
                self.run_stats['errors'].append(f"Processing error ({processor_name}): {e}")

        self.run_stats['total_processed'] = len(actions)
        logger.info(f"Processing complete: {len(actions)} final actions")
        return actions

    def _export_data(self, actions: List[GovernmentAction]) -> bool:
        """Export processed data to TypeScript format."""
        logger.info("Exporting data to TypeScript format")

        try:
            # Prepare export statistics
            export_stats = {
                'total_count': len(actions),
                'source_counts': {},
                'label_counts': {},
                'date_range': {}
            }

            # Calculate statistics
            for action in actions:
                # Source counts
                source = action.source_system.value
                export_stats['source_counts'][source] = export_stats['source_counts'].get(source, 0) + 1

                # Label counts
                for label in action.labels:
                    export_stats['label_counts'][label] = export_stats['label_counts'].get(label, 0) + 1

            # Date range
            dates = [action.date for action in actions if action.date]
            if dates:
                dates.sort()
                export_stats['date_range'] = {
                    'earliest': dates[0],
                    'latest': dates[-1]
                }

            # Export to TypeScript
            self.typescript_exporter.export(
                actions,
                include_metadata=True,
                format_pretty=True
            )

            # Also export as JSON for potential API use
            json_path = self.output_dir / "data.json"
            self.typescript_exporter.export_json(actions, json_path)

            # Validate export
            validation = self.typescript_exporter.validate_export(actions)
            if not validation['valid']:
                logger.warning(f"Export validation issues: {validation['errors']}")
                self.run_stats['warnings'].extend(validation['errors'])

            logger.info(f"Export complete: {len(actions)} actions exported")
            return True

        except Exception as e:
            logger.error(f"Export failed: {e}")
            self.run_stats['errors'].append(f"Export error: {e}")
            return False

    def _commit_changes(self, actions: List[GovernmentAction]) -> bool:
        """Commit changes to Git repository."""
        if self.dry_run:
            logger.info("Dry run mode: skipping Git commit")
            return True

        logger.info("Committing changes to Git repository")

        try:
            if not self.git_integration:
                logger.error("Git integration not initialized")
                return False

            self.git_integration.initialize_repo()

            # Prepare commit statistics
            commit_stats = {
                'total_count': len(actions),
                'source_counts': {},
                'date_range': {}
            }

            for action in actions:
                source = action.source_system.value
                commit_stats['source_counts'][source] = commit_stats['source_counts'].get(source, 0) + 1

            dates = [action.date for action in actions if action.date]
            if dates:
                dates.sort()
                commit_stats['date_range'] = {
                    'earliest': dates[0],
                    'latest': dates[-1]
                }

            # Files to commit (relative to repo root)
            files_to_commit = [
                self.output_dir.relative_to(self.repo_path) / "actions.ts",
                self.output_dir.relative_to(self.repo_path) / "data.json"
            ]

            success = self.git_integration.commit_data_update(
                files_to_commit,
                stats=commit_stats
            )

            if success:
                logger.info("Git commit successful")
            else:
                logger.error("Git commit failed")

            return success

        except Exception as e:
            logger.error(f"Git commit error: {e}")
            self.run_stats['errors'].append(f"Git error: {e}")
            return False

    def _finalize_stats(self, actions: List[GovernmentAction]) -> None:
        """Finalize run statistics."""
        self.run_stats['total_processed'] = len(actions)

        # Calculate success rates
        total_sources = len(self.scrapers)
        successful_sources = len([s for s in self.run_stats['source_stats'].values() if s.get('success', False)])
        self.run_stats['scraping_success_rate'] = successful_sources / total_sources if total_sources > 0 else 0

        total_processors = len(self.processors)
        successful_processors = len([p for p in self.run_stats['processing_stats'].values() if p.get('success', False)])
        self.run_stats['processing_success_rate'] = successful_processors / total_processors if total_processors > 0 else 0

    def _log_final_statistics(self) -> None:
        """Log final pipeline statistics."""
        stats = self.run_stats
        duration = stats['end_time'] - stats['start_time'] if stats['end_time'] and stats['start_time'] else None

        logger.info("=" * 60)
        logger.info("PIPELINE SUMMARY")
        logger.info("=" * 60)

        if duration:
            logger.info(f"Duration: {duration.total_seconds():.1f} seconds")

        logger.info(f"Total scraped: {stats['total_scraped']}")
        logger.info(f"Total processed: {stats['total_processed']}")

        logger.info("\nSource Statistics:")
        for source, source_stats in stats['source_stats'].items():
            status = "✓" if source_stats.get('success', False) else "✗"
            scraped = source_stats.get('scraped', 0)
            logger.info(f"  {status} {source}: {scraped} items")

        logger.info("\nProcessor Statistics:")
        for processor, proc_stats in stats['processing_stats'].items():
            if proc_stats.get('success', False):
                input_count = proc_stats.get('input_count', 0)
                output_count = proc_stats.get('output_count', 0)
                logger.info(f"  ✓ {processor}: {input_count} -> {output_count}")
            else:
                logger.info(f"  ✗ {processor}: FAILED")

        if stats['errors']:
            logger.info(f"\nErrors ({len(stats['errors'])}):")
            for error in stats['errors'][:5]:  # Show first 5 errors
                logger.info(f"  - {error}")
            if len(stats['errors']) > 5:
                logger.info(f"  ... and {len(stats['errors']) - 5} more")

        if stats['warnings']:
            logger.info(f"\nWarnings ({len(stats['warnings'])}):")
            for warning in stats['warnings'][:3]:  # Show first 3 warnings
                logger.info(f"  - {warning}")
            if len(stats['warnings']) > 3:
                logger.info(f"  ... and {len(stats['warnings']) - 3} more")

        logger.info("=" * 60)

    def _cleanup_resources(self) -> None:
        """Cleanup resources."""
        for scraper in self.scrapers.values():
            try:
                scraper.close()
            except Exception:
                pass

    def get_run_statistics(self) -> Dict[str, Any]:
        """Get detailed run statistics."""
        return self.run_stats.copy()


def create_argument_parser() -> argparse.ArgumentParser:
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Keep Track NZ - Government Action Data Collection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                           # Run full pipeline
  %(prog)s --dry-run                 # Run without Git commit
  %(prog)s --limit 5                 # Limit to 5 items per source (testing)
  %(prog)s --debug --dry-run --limit 5  # Run with debug output (testing)
  %(prog)s --output-dir /tmp/test    # Use custom output directory
        """
    )

    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path(__file__).parent.parent.parent.parent / 'src' / 'data',
        help='Output directory for data files (default: src/data)'
    )

    parser.add_argument(
        '--repo-path',
        type=Path,
        help='Path to Git repository (default: parent of output-dir)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run pipeline without committing to Git'
    )

    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of items to scrape per source (for testing)'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode with detailed output for scraping and deduplication'
    )

    parser.add_argument(
        '--stats-file',
        type=Path,
        help='Save run statistics to JSON file'
    )

    return parser


def main() -> int:
    """Main entry point."""
    parser = create_argument_parser()
    args = parser.parse_args()

    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")

    logger.info("Starting Keep Track NZ Data Collection")
    logger.info(f"Output directory: {args.output_dir}")
    logger.info(f"Dry run mode: {args.dry_run}")
    if args.debug:
        logger.info("Debug mode enabled")

    # Initialize orchestrator
    orchestrator = DataCollectionOrchestrator(
        output_dir=args.output_dir,
        repo_path=args.repo_path,
        dry_run=args.dry_run,
        limit_per_source=args.limit,
        debug_mode=args.debug
    )

    # Run pipeline
    success = orchestrator.run_complete_pipeline()

    # Save statistics if requested
    if args.stats_file:
        try:
            stats = orchestrator.get_run_statistics()
            # Convert datetime objects to strings for JSON serialization
            if stats.get('start_time'):
                stats['start_time'] = stats['start_time'].isoformat()
            if stats.get('end_time'):
                stats['end_time'] = stats['end_time'].isoformat()

            with open(args.stats_file, 'w') as f:
                json.dump(stats, f, indent=2)
            logger.info(f"Statistics saved to {args.stats_file}")
        except Exception as e:
            logger.error(f"Failed to save statistics: {e}")

    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())