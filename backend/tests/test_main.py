"""Tests for main orchestrator."""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from keep_track_nz.main import DataCollectionOrchestrator, main
from keep_track_nz.models import GovernmentAction, SourceSystem, ActionMetadata


class TestDataCollectionOrchestrator:
    """Test the main orchestrator."""

    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary output directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def sample_raw_data(self):
        """Sample raw data from scrapers."""
        return [
            {
                'title': 'Test Parliament Bill',
                'url': 'https://parliament.nz/test',
                'source_system': 'PARLIAMENT',
                'date': '2024-12-15',
                'primary_entity': 'Hon Test Minister',
                'summary': 'A test bill',
                'bill_number': '123456'
            },
            {
                'title': 'Test Legislation Act',
                'url': 'https://legislation.govt.nz/test',
                'source_system': 'LEGISLATION',
                'date': '2024-12-15',
                'primary_entity': 'Parliament',
                'summary': 'A test act',
                'act_number': '2024 No 1'
            }
        ]

    def test_orchestrator_initialization(self, temp_output_dir):
        """Test orchestrator initialization."""
        orchestrator = DataCollectionOrchestrator(
            output_dir=temp_output_dir,
            dry_run=True,
            limit_per_source=5
        )

        assert orchestrator.output_dir == temp_output_dir
        assert orchestrator.dry_run is True
        assert orchestrator.limit_per_source == 5
        assert len(orchestrator.scrapers) == 4  # All 4 scrapers
        assert len(orchestrator.processors) == 3  # Validator, Deduplicator, Classifier

    @patch('keep_track_nz.main.parliament.ParliamentScraper')
    @patch('keep_track_nz.main.legislation.LegislationScraper')
    @patch('keep_track_nz.main.gazette.GazetteScraper')
    @patch('keep_track_nz.main.beehive.BeehiveScraper')
    def test_scrape_all_sources_success(
        self,
        mock_beehive,
        mock_gazette,
        mock_legislation,
        mock_parliament,
        temp_output_dir,
        sample_raw_data
    ):
        """Test successful scraping from all sources."""
        # Mock scrapers to return sample data
        mock_parliament_instance = Mock()
        mock_parliament_instance.scrape.return_value = [sample_raw_data[0]]
        mock_parliament.return_value = mock_parliament_instance

        mock_legislation_instance = Mock()
        mock_legislation_instance.scrape.return_value = [sample_raw_data[1]]
        mock_legislation.return_value = mock_legislation_instance

        mock_gazette_instance = Mock()
        mock_gazette_instance.scrape.return_value = []
        mock_gazette.return_value = mock_gazette_instance

        mock_beehive_instance = Mock()
        mock_beehive_instance.scrape.return_value = []
        mock_beehive.return_value = mock_beehive_instance

        orchestrator = DataCollectionOrchestrator(temp_output_dir, dry_run=True)
        raw_data = orchestrator._scrape_all_sources()

        assert len(raw_data) == 2
        assert raw_data[0]['title'] == 'Test Parliament Bill'
        assert raw_data[1]['title'] == 'Test Legislation Act'

        # Check stats
        assert orchestrator.run_stats['total_scraped'] == 2
        assert orchestrator.run_stats['source_stats']['PARLIAMENT']['scraped'] == 1
        assert orchestrator.run_stats['source_stats']['LEGISLATION']['scraped'] == 1

    @patch('keep_track_nz.main.parliament.ParliamentScraper')
    def test_scrape_with_error(self, mock_parliament, temp_output_dir):
        """Test scraping with one source failing."""
        # Mock scraper to raise exception
        mock_parliament_instance = Mock()
        mock_parliament_instance.scrape.side_effect = Exception("Scraping failed")
        mock_parliament.return_value = mock_parliament_instance

        orchestrator = DataCollectionOrchestrator(temp_output_dir, dry_run=True)
        raw_data = orchestrator._scrape_all_sources()

        # Should continue even with one source failing
        assert isinstance(raw_data, list)
        assert orchestrator.run_stats['source_stats']['PARLIAMENT']['success'] is False
        assert 'Scraping failed' in str(orchestrator.run_stats['source_stats']['PARLIAMENT']['error'])

    def test_convert_to_actions(self, temp_output_dir, sample_raw_data):
        """Test converting raw data to GovernmentAction objects."""
        orchestrator = DataCollectionOrchestrator(temp_output_dir, dry_run=True)

        # Mock the create_government_action method on scrapers
        for scraper in orchestrator.scrapers.values():
            scraper.create_government_action = Mock()

        # Mock return values
        orchestrator.scrapers['PARLIAMENT'].create_government_action.return_value = GovernmentAction(
            id='parl-2024-001',
            title='Test Parliament Bill',
            date='2024-12-15',
            source_system=SourceSystem.PARLIAMENT,
            url='https://parliament.nz/test',
            primary_entity='Hon Test Minister',
            summary='A test bill'
        )

        orchestrator.scrapers['LEGISLATION'].create_government_action.return_value = GovernmentAction(
            id='leg-2024-001',
            title='Test Legislation Act',
            date='2024-12-15',
            source_system=SourceSystem.LEGISLATION,
            url='https://legislation.govt.nz/test',
            primary_entity='Parliament',
            summary='A test act'
        )

        actions = orchestrator._convert_to_actions(sample_raw_data)

        assert len(actions) == 2
        assert isinstance(actions[0], GovernmentAction)
        assert isinstance(actions[1], GovernmentAction)

    @patch('keep_track_nz.processors.DataValidator.process')
    @patch('keep_track_nz.processors.Deduplicator.process')
    @patch('keep_track_nz.processors.LabelClassifier.process')
    def test_process_data(
        self,
        mock_classifier,
        mock_deduplicator,
        mock_validator,
        temp_output_dir
    ):
        """Test data processing pipeline."""
        # Mock processors
        mock_validator.return_value = [{'id': 'test', 'title': 'Test'}]
        mock_deduplicator.return_value = [{'id': 'test', 'title': 'Test'}]
        mock_classifier.return_value = [{'id': 'test', 'title': 'Test', 'labels': ['Housing']}]

        orchestrator = DataCollectionOrchestrator(temp_output_dir, dry_run=True)

        sample_action = GovernmentAction(
            id='test-2024-001',
            title='Test Action',
            date='2024-12-15',
            source_system=SourceSystem.PARLIAMENT,
            url='https://example.com/test',
            primary_entity='Test Entity',
            summary='Test summary'
        )

        processed = orchestrator._process_data([sample_action])

        # Should call all processors in order
        assert mock_validator.called
        assert mock_deduplicator.called
        assert mock_classifier.called

        # Check processing stats
        assert 'DataValidator' in orchestrator.run_stats['processing_stats']
        assert 'Deduplicator' in orchestrator.run_stats['processing_stats']
        assert 'LabelClassifier' in orchestrator.run_stats['processing_stats']

    @patch('keep_track_nz.exporters.TypeScriptExporter.export')
    @patch('keep_track_nz.exporters.TypeScriptExporter.export_json')
    @patch('keep_track_nz.exporters.TypeScriptExporter.validate_export')
    def test_export_data(
        self,
        mock_validate,
        mock_export_json,
        mock_export,
        temp_output_dir
    ):
        """Test data export."""
        mock_validate.return_value = {'valid': True, 'errors': []}

        orchestrator = DataCollectionOrchestrator(temp_output_dir, dry_run=True)

        sample_action = GovernmentAction(
            id='test-2024-001',
            title='Test Action',
            date='2024-12-15',
            source_system=SourceSystem.PARLIAMENT,
            url='https://example.com/test',
            primary_entity='Test Entity',
            summary='Test summary'
        )

        success = orchestrator._export_data([sample_action])

        assert success is True
        assert mock_export.called
        assert mock_export_json.called

    @patch('keep_track_nz.git_integration.GitIntegration.initialize_repo')
    @patch('keep_track_nz.git_integration.GitIntegration.commit_data_update')
    def test_commit_changes(
        self,
        mock_commit,
        mock_init,
        temp_output_dir
    ):
        """Test Git commit functionality."""
        mock_commit.return_value = True

        orchestrator = DataCollectionOrchestrator(temp_output_dir, dry_run=False)

        sample_action = GovernmentAction(
            id='test-2024-001',
            title='Test Action',
            date='2024-12-15',
            source_system=SourceSystem.PARLIAMENT,
            url='https://example.com/test',
            primary_entity='Test Entity',
            summary='Test summary'
        )

        success = orchestrator._commit_changes([sample_action])

        assert success is True
        assert mock_init.called
        assert mock_commit.called

    def test_dry_run_skips_commit(self, temp_output_dir):
        """Test that dry run skips Git commit."""
        orchestrator = DataCollectionOrchestrator(temp_output_dir, dry_run=True)

        sample_action = GovernmentAction(
            id='test-2024-001',
            title='Test Action',
            date='2024-12-15',
            source_system=SourceSystem.PARLIAMENT,
            url='https://example.com/test',
            primary_entity='Test Entity',
            summary='Test summary'
        )

        success = orchestrator._commit_changes([sample_action])

        # Should return True but not actually commit
        assert success is True

    @patch('keep_track_nz.main.DataCollectionOrchestrator._scrape_all_sources')
    @patch('keep_track_nz.main.DataCollectionOrchestrator._convert_to_actions')
    @patch('keep_track_nz.main.DataCollectionOrchestrator._process_data')
    @patch('keep_track_nz.main.DataCollectionOrchestrator._export_data')
    @patch('keep_track_nz.main.DataCollectionOrchestrator._commit_changes')
    def test_complete_pipeline_success(
        self,
        mock_commit,
        mock_export,
        mock_process,
        mock_convert,
        mock_scrape,
        temp_output_dir
    ):
        """Test successful complete pipeline execution."""
        # Mock all pipeline steps
        mock_scrape.return_value = [{'title': 'Test'}]
        mock_convert.return_value = [Mock()]
        mock_process.return_value = [Mock()]
        mock_export.return_value = True
        mock_commit.return_value = True

        orchestrator = DataCollectionOrchestrator(temp_output_dir, dry_run=True)
        success = orchestrator.run_complete_pipeline()

        assert success is True
        assert mock_scrape.called
        assert mock_convert.called
        assert mock_process.called
        assert mock_export.called

    @patch('keep_track_nz.main.DataCollectionOrchestrator._scrape_all_sources')
    def test_pipeline_failure_no_data(self, mock_scrape, temp_output_dir):
        """Test pipeline failure when no data is scraped."""
        mock_scrape.return_value = []  # No data scraped

        orchestrator = DataCollectionOrchestrator(temp_output_dir, dry_run=True)
        success = orchestrator.run_complete_pipeline()

        assert success is False

    def test_statistics_tracking(self, temp_output_dir):
        """Test that statistics are properly tracked."""
        orchestrator = DataCollectionOrchestrator(temp_output_dir, dry_run=True)

        # Check initial stats
        assert orchestrator.run_stats['start_time'] is None
        assert orchestrator.run_stats['total_scraped'] == 0
        assert len(orchestrator.run_stats['errors']) == 0

        # Get stats
        stats = orchestrator.get_run_statistics()
        assert isinstance(stats, dict)
        assert 'start_time' in stats
        assert 'source_stats' in stats


class TestMainFunction:
    """Test the main CLI function."""

    @patch('keep_track_nz.main.DataCollectionOrchestrator')
    @patch('sys.argv', ['main.py', '--dry-run', '--limit', '5'])
    def test_main_with_arguments(self, mock_orchestrator_class):
        """Test main function with command line arguments."""
        mock_orchestrator = Mock()
        mock_orchestrator.run_complete_pipeline.return_value = True
        mock_orchestrator.get_run_statistics.return_value = {}
        mock_orchestrator_class.return_value = mock_orchestrator

        result = main()

        assert result == 0
        assert mock_orchestrator_class.called
        assert mock_orchestrator.run_complete_pipeline.called

    @patch('keep_track_nz.main.DataCollectionOrchestrator')
    @patch('sys.argv', ['main.py'])
    def test_main_default_arguments(self, mock_orchestrator_class):
        """Test main function with default arguments."""
        mock_orchestrator = Mock()
        mock_orchestrator.run_complete_pipeline.return_value = True
        mock_orchestrator.get_run_statistics.return_value = {}
        mock_orchestrator_class.return_value = mock_orchestrator

        result = main()

        assert result == 0

    @patch('keep_track_nz.main.DataCollectionOrchestrator')
    @patch('sys.argv', ['main.py'])
    def test_main_pipeline_failure(self, mock_orchestrator_class):
        """Test main function when pipeline fails."""
        mock_orchestrator = Mock()
        mock_orchestrator.run_complete_pipeline.return_value = False
        mock_orchestrator.get_run_statistics.return_value = {}
        mock_orchestrator_class.return_value = mock_orchestrator

        result = main()

        assert result == 1

    @patch('keep_track_nz.main.DataCollectionOrchestrator')
    @patch('sys.argv', ['main.py', '--stats-file', '/tmp/test_stats.json'])
    def test_main_with_stats_file(self, mock_orchestrator_class, tmp_path):
        """Test main function with stats file output."""
        stats_file = tmp_path / "test_stats.json"

        mock_orchestrator = Mock()
        mock_orchestrator.run_complete_pipeline.return_value = True
        mock_orchestrator.get_run_statistics.return_value = {
            'total_scraped': 10,
            'total_processed': 8,
            'errors': []
        }
        mock_orchestrator_class.return_value = mock_orchestrator

        # Patch sys.argv to use our temp file
        with patch('sys.argv', ['main.py', '--stats-file', str(stats_file)]):
            result = main()

        assert result == 0
        assert stats_file.exists()

        # Check stats file content
        with open(stats_file) as f:
            stats_data = json.load(f)

        assert stats_data['total_scraped'] == 10
        assert stats_data['total_processed'] == 8

    @patch('sys.argv', ['main.py', '--help'])
    def test_main_help(self):
        """Test main function with help argument."""
        with pytest.raises(SystemExit) as exc_info:
            main()

        # Help should exit with code 0
        assert exc_info.value.code == 0