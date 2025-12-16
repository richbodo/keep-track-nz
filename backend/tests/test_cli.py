"""Tests for CLI interface and argument parsing."""

import pytest
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock
from argparse import ArgumentParser

from keep_track_nz.main import create_argument_parser, main


class TestArgumentParser:
    """Test command line argument parsing."""

    def test_parser_creation(self):
        """Test that argument parser is created correctly."""
        parser = create_argument_parser()
        assert isinstance(parser, ArgumentParser)
        assert 'Keep Track NZ' in parser.description

    def test_default_arguments(self):
        """Test default argument values."""
        parser = create_argument_parser()
        args = parser.parse_args([])

        # Check default values - the actual path calculation is based on main.py location
        # so we check that it's a Path object and ends with src/data
        assert isinstance(args.output_dir, Path)
        assert str(args.output_dir).endswith('/src/data')
        assert args.repo_path is None
        assert args.dry_run is False
        assert args.limit is None
        assert args.verbose is False
        assert args.stats_file is None

    def test_output_dir_argument(self):
        """Test --output-dir argument."""
        parser = create_argument_parser()
        test_dir = '/tmp/test-output'

        args = parser.parse_args(['--output-dir', test_dir])
        assert str(args.output_dir) == test_dir

    def test_repo_path_argument(self):
        """Test --repo-path argument."""
        parser = create_argument_parser()
        test_path = '/tmp/test-repo'

        args = parser.parse_args(['--repo-path', test_path])
        assert str(args.repo_path) == test_path

    def test_dry_run_argument(self):
        """Test --dry-run flag."""
        parser = create_argument_parser()

        # Test dry run enabled
        args = parser.parse_args(['--dry-run'])
        assert args.dry_run is True

        # Test default (dry run disabled)
        args = parser.parse_args([])
        assert args.dry_run is False

    def test_limit_argument(self):
        """Test --limit argument."""
        parser = create_argument_parser()

        args = parser.parse_args(['--limit', '10'])
        assert args.limit == 10

    def test_verbose_argument(self):
        """Test --verbose/-v argument."""
        parser = create_argument_parser()

        # Test long form
        args = parser.parse_args(['--verbose'])
        assert args.verbose is True

        # Test short form
        args = parser.parse_args(['-v'])
        assert args.verbose is True

    def test_stats_file_argument(self):
        """Test --stats-file argument."""
        parser = create_argument_parser()
        test_file = '/tmp/stats.json'

        args = parser.parse_args(['--stats-file', test_file])
        assert str(args.stats_file) == test_file

    def test_combined_arguments(self):
        """Test multiple arguments together."""
        parser = create_argument_parser()

        args = parser.parse_args([
            '--output-dir', '/tmp/output',
            '--repo-path', '/tmp/repo',
            '--dry-run',
            '--limit', '5',
            '--verbose',
            '--stats-file', '/tmp/stats.json'
        ])

        assert str(args.output_dir) == '/tmp/output'
        assert str(args.repo_path) == '/tmp/repo'
        assert args.dry_run is True
        assert args.limit == 5
        assert args.verbose is True
        assert str(args.stats_file) == '/tmp/stats.json'

    def test_help_text(self):
        """Test that help text is generated properly."""
        parser = create_argument_parser()

        # This should not raise an exception
        help_text = parser.format_help()
        assert 'Keep Track NZ' in help_text
        assert '--output-dir' in help_text
        assert '--dry-run' in help_text
        assert '--limit' in help_text


class TestMainFunction:
    """Test the main CLI entry point."""

    @pytest.fixture
    def mock_orchestrator(self):
        """Mock DataCollectionOrchestrator for testing."""
        with patch('keep_track_nz.main.DataCollectionOrchestrator') as mock_class:
            mock_instance = Mock()
            mock_instance.run_complete_pipeline.return_value = True
            mock_instance.get_run_statistics.return_value = {
                'total_actions': 100,
                'sources': ['PARLIAMENT', 'LEGISLATION'],
                'start_time': None,
                'end_time': None
            }
            mock_class.return_value = mock_instance
            yield mock_class, mock_instance

    def test_main_success(self, mock_orchestrator):
        """Test successful main function execution."""
        mock_class, mock_instance = mock_orchestrator

        with patch.object(sys, 'argv', ['script']):
            result = main()

        assert result == 0
        mock_class.assert_called_once()
        mock_instance.run_complete_pipeline.assert_called_once()

    def test_main_failure(self, mock_orchestrator):
        """Test main function when pipeline fails."""
        mock_class, mock_instance = mock_orchestrator
        mock_instance.run_complete_pipeline.return_value = False

        with patch.object(sys, 'argv', ['script']):
            result = main()

        assert result == 1

    def test_main_with_output_dir(self, mock_orchestrator):
        """Test main with custom output directory."""
        mock_class, mock_instance = mock_orchestrator
        test_dir = '/tmp/test-output'

        with patch.object(sys, 'argv', ['script', '--output-dir', test_dir]):
            result = main()

        assert result == 0
        # Check that orchestrator was called with correct output_dir
        mock_class.assert_called_once()
        call_args = mock_class.call_args[1]
        assert str(call_args['output_dir']) == test_dir

    def test_main_with_dry_run(self, mock_orchestrator):
        """Test main with dry run enabled."""
        mock_class, mock_instance = mock_orchestrator

        with patch.object(sys, 'argv', ['script', '--dry-run']):
            result = main()

        assert result == 0
        # Check that orchestrator was called with dry_run=True
        call_args = mock_class.call_args[1]
        assert call_args['dry_run'] is True

    def test_main_with_limit(self, mock_orchestrator):
        """Test main with scraping limit."""
        mock_class, mock_instance = mock_orchestrator

        with patch.object(sys, 'argv', ['script', '--limit', '10']):
            result = main()

        assert result == 0
        # Check that orchestrator was called with correct limit
        call_args = mock_class.call_args[1]
        assert call_args['limit_per_source'] == 10

    def test_main_with_verbose_logging(self, mock_orchestrator):
        """Test main with verbose logging enabled."""
        mock_class, mock_instance = mock_orchestrator

        with patch('logging.getLogger') as mock_logger, \
             patch.object(sys, 'argv', ['script', '--verbose']):

            main()

            # Check that debug logging was enabled
            mock_logger.return_value.setLevel.assert_called_with(10)  # DEBUG level

    def test_main_with_stats_file(self, mock_orchestrator):
        """Test main with statistics file output."""
        mock_class, mock_instance = mock_orchestrator

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            stats_file = f.name

        try:
            with patch.object(sys, 'argv', ['script', '--stats-file', stats_file]):
                result = main()

            assert result == 0

            # Check that statistics were saved
            with open(stats_file, 'r') as f:
                saved_stats = json.load(f)

            assert saved_stats['total_actions'] == 100
            assert 'sources' in saved_stats

        finally:
            Path(stats_file).unlink(missing_ok=True)

    def test_main_with_stats_file_datetime_serialization(self, mock_orchestrator):
        """Test that datetime objects in stats are properly serialized."""
        from datetime import datetime

        mock_class, mock_instance = mock_orchestrator
        # Mock stats with datetime objects
        mock_instance.get_run_statistics.return_value = {
            'total_actions': 50,
            'start_time': datetime(2024, 12, 15, 10, 30),
            'end_time': datetime(2024, 12, 15, 10, 35)
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            stats_file = f.name

        try:
            with patch.object(sys, 'argv', ['script', '--stats-file', stats_file]):
                result = main()

            assert result == 0

            # Check that datetime objects were converted to ISO format strings
            with open(stats_file, 'r') as f:
                saved_stats = json.load(f)

            assert saved_stats['start_time'] == '2024-12-15T10:30:00'
            assert saved_stats['end_time'] == '2024-12-15T10:35:00'

        finally:
            Path(stats_file).unlink(missing_ok=True)

    def test_main_stats_file_error_handling(self, mock_orchestrator):
        """Test error handling when stats file save fails."""
        mock_class, mock_instance = mock_orchestrator

        # Use an invalid file path that will cause an error
        invalid_path = '/invalid/path/stats.json'

        with patch.object(sys, 'argv', ['script', '--stats-file', invalid_path]), \
             patch('keep_track_nz.main.logger') as mock_logger:

            result = main()

            # Should still succeed even if stats save fails
            assert result == 0
            # Should log the error
            mock_logger.error.assert_called()

    def test_main_all_arguments(self, mock_orchestrator):
        """Test main with all possible arguments."""
        mock_class, mock_instance = mock_orchestrator

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / 'output'
            repo_path = Path(temp_dir) / 'repo'
            stats_file = Path(temp_dir) / 'stats.json'

            with patch.object(sys, 'argv', [
                'script',
                '--output-dir', str(output_dir),
                '--repo-path', str(repo_path),
                '--dry-run',
                '--limit', '25',
                '--verbose',
                '--stats-file', str(stats_file)
            ]):
                result = main()

            assert result == 0

            # Check all arguments were passed correctly
            call_args = mock_class.call_args[1]
            assert call_args['output_dir'] == output_dir
            assert call_args['repo_path'] == repo_path
            assert call_args['dry_run'] is True
            assert call_args['limit_per_source'] == 25

            # Check stats file was created
            assert stats_file.exists()


class TestCLIIntegration:
    """Integration tests for CLI functionality."""

    def test_help_command(self):
        """Test --help command exits gracefully."""
        parser = create_argument_parser()

        with pytest.raises(SystemExit) as excinfo:
            parser.parse_args(['--help'])

        # Help should exit with code 0
        assert excinfo.value.code == 0

    def test_invalid_argument(self):
        """Test that invalid arguments are handled."""
        parser = create_argument_parser()

        with pytest.raises(SystemExit) as excinfo:
            parser.parse_args(['--invalid-argument'])

        # Invalid arguments should exit with error code
        assert excinfo.value.code != 0

    def test_invalid_limit_value(self):
        """Test that non-integer limit values are rejected."""
        parser = create_argument_parser()

        with pytest.raises(SystemExit):
            parser.parse_args(['--limit', 'not-a-number'])

    @patch('keep_track_nz.main.DataCollectionOrchestrator')
    def test_orchestrator_initialization_parameters(self, mock_class):
        """Test that DataCollectionOrchestrator is initialized with correct parameters."""
        mock_instance = Mock()
        mock_instance.run_complete_pipeline.return_value = True
        mock_class.return_value = mock_instance

        test_output = Path('/tmp/test-output')
        test_repo = Path('/tmp/test-repo')

        with patch.object(sys, 'argv', [
            'script',
            '--output-dir', str(test_output),
            '--repo-path', str(test_repo),
            '--dry-run',
            '--limit', '15'
        ]):
            main()

        # Verify orchestrator was initialized with correct parameters
        mock_class.assert_called_once_with(
            output_dir=test_output,
            repo_path=test_repo,
            dry_run=True,
            limit_per_source=15,
            debug_mode=False
        )

    def test_repo_path_default_behavior(self):
        """Test that repo_path defaults to None when not specified."""
        parser = create_argument_parser()
        args = parser.parse_args(['--output-dir', '/tmp/test'])

        assert args.repo_path is None
        # The orchestrator should handle None repo_path by deriving it from output_dir

    def test_examples_in_help(self):
        """Test that help text contains usage examples."""
        parser = create_argument_parser()
        help_text = parser.format_help()

        assert 'Examples:' in help_text
        assert '--dry-run' in help_text
        assert '--limit' in help_text
        assert '--output-dir' in help_text


class TestCLIErrorHandling:
    """Test error handling in CLI scenarios."""

    @patch('keep_track_nz.main.DataCollectionOrchestrator')
    def test_orchestrator_exception_handling(self, mock_class):
        """Test behavior when orchestrator raises an exception."""
        mock_class.side_effect = Exception("Orchestrator initialization failed")

        with patch.object(sys, 'argv', ['script']):
            # Should not crash the entire program
            with pytest.raises(Exception):
                main()

    @patch('keep_track_nz.main.DataCollectionOrchestrator')
    def test_pipeline_exception_handling(self, mock_class):
        """Test behavior when pipeline execution fails."""
        mock_instance = Mock()
        mock_instance.run_complete_pipeline.side_effect = Exception("Pipeline failed")
        mock_class.return_value = mock_instance

        with patch.object(sys, 'argv', ['script']):
            with pytest.raises(Exception):
                main()

    @patch('keep_track_nz.main.DataCollectionOrchestrator')
    def test_stats_retrieval_exception(self, mock_class):
        """Test behavior when stats retrieval fails but stats file is requested."""
        mock_instance = Mock()
        mock_instance.run_complete_pipeline.return_value = True
        mock_instance.get_run_statistics.side_effect = Exception("Stats failed")
        mock_class.return_value = mock_instance

        with tempfile.NamedTemporaryFile(suffix='.json') as f:
            with patch.object(sys, 'argv', ['script', '--stats-file', f.name]), \
                 patch('keep_track_nz.main.logger') as mock_logger:

                result = main()

                # Should succeed despite stats error
                assert result == 0
                # Should log the error
                mock_logger.error.assert_called()