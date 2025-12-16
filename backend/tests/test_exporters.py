"""Tests for data exporters."""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from keep_track_nz.models import GovernmentAction, SourceSystem, ActionMetadata
from keep_track_nz.exporters import TypeScriptExporter


class TestTypeScriptExporter:
    """Test TypeScript exporter."""

    @pytest.fixture
    def sample_action(self):
        """Create a sample GovernmentAction for testing."""
        return GovernmentAction(
            id='test-2024-001',
            title='Test Action',
            date='2024-12-15',
            source_system=SourceSystem.PARLIAMENT,
            url='https://example.com/test',
            primary_entity='Hon Test Minister',
            summary='A test action for testing purposes',
            labels=['Housing', 'Infrastructure'],
            metadata=ActionMetadata(bill_number='123456')
        )

    @pytest.fixture
    def temp_output_path(self):
        """Create a temporary output path for testing."""
        with tempfile.NamedTemporaryFile(suffix='.ts', delete=False) as f:
            temp_path = Path(f.name)
        try:
            yield temp_path
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_export_single_action(self, sample_action, temp_output_path):
        """Test exporting a single action."""
        exporter = TypeScriptExporter(temp_output_path, backup_enabled=False)
        exporter.export([sample_action])

        # Check that file was created
        assert temp_output_path.exists()

        # Check file content
        content = temp_output_path.read_text()
        assert 'export const labels =' in content
        assert 'export const actions: GovernmentAction[] =' in content
        assert 'test-2024-001' in content
        assert 'Test Action' in content

    def test_export_multiple_actions(self, temp_output_path):
        """Test exporting multiple actions."""
        actions = [
            GovernmentAction(
                id='parl-2024-001',
                title='Parliament Action',
                date='2024-12-15',
                source_system=SourceSystem.PARLIAMENT,
                url='https://example.com/parl',
                primary_entity='Hon Parliament Minister',
                summary='A parliament action',
                labels=['Education']
            ),
            GovernmentAction(
                id='leg-2024-001',
                title='Legislation Action',
                date='2024-12-14',
                source_system=SourceSystem.LEGISLATION,
                url='https://example.com/leg',
                primary_entity='Parliament',
                summary='A legislation action',
                labels=['Health', 'Justice']
            )
        ]

        exporter = TypeScriptExporter(temp_output_path, backup_enabled=False)
        exporter.export(actions)

        content = temp_output_path.read_text()
        assert 'parl-2024-001' in content
        assert 'leg-2024-001' in content
        assert 'Parliament Action' in content
        assert 'Legislation Action' in content

    def test_export_with_metadata(self, sample_action, temp_output_path):
        """Test export includes metadata in comments."""
        exporter = TypeScriptExporter(temp_output_path, backup_enabled=False)
        exporter.export([sample_action], include_metadata=True)

        content = temp_output_path.read_text()
        assert '/* Export metadata:' in content
        assert 'Last updated:' in content
        assert 'Total actions: 1' in content

    def test_export_without_metadata(self, sample_action, temp_output_path):
        """Test export without metadata."""
        exporter = TypeScriptExporter(temp_output_path, backup_enabled=False)
        exporter.export([sample_action], include_metadata=False)

        content = temp_output_path.read_text()
        assert '/* Export metadata:' not in content

    def test_typescript_types_generation(self, sample_action, temp_output_path):
        """Test that TypeScript types are correctly generated."""
        exporter = TypeScriptExporter(temp_output_path, backup_enabled=False)
        exporter.export([sample_action])

        content = temp_output_path.read_text()
        assert 'export type SourceSystem =' in content
        assert 'export interface StageHistory' in content
        assert 'export interface ActionMetadata' in content
        assert 'export interface GovernmentAction' in content

    def test_json_export(self, sample_action):
        """Test JSON export functionality."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            json_path = Path(f.name)

        try:
            exporter = TypeScriptExporter(Path('/tmp/dummy.ts'))
            exporter.export_json([sample_action], json_path)

            assert json_path.exists()

            # Load and verify JSON content
            with open(json_path) as f:
                data = json.load(f)

            assert 'labels' in data
            assert 'actions' in data
            assert 'metadata' in data
            assert len(data['actions']) == 1
            assert data['actions'][0]['id'] == 'test-2024-001'

        finally:
            if json_path.exists():
                json_path.unlink()

    def test_backup_creation(self, sample_action):
        """Test backup creation when file already exists."""
        with tempfile.NamedTemporaryFile(suffix='.ts', delete=False) as f:
            temp_path = Path(f.name)

        try:
            # Write initial content
            temp_path.write_text('Initial content')

            # Export with backup enabled
            exporter = TypeScriptExporter(temp_path, backup_enabled=True)
            exporter.export([sample_action])

            # Check that backup was created
            backup_files = list(temp_path.parent.glob(f"{temp_path.stem}.backup_*{temp_path.suffix}"))
            assert len(backup_files) > 0

            # Check that original file was overwritten
            content = temp_path.read_text()
            assert 'Initial content' not in content
            assert 'test-2024-001' in content

            # Clean up backup files
            for backup_file in backup_files:
                backup_file.unlink()

        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_data_sorting(self, temp_output_path):
        """Test that actions are sorted by date (newest first)."""
        actions = [
            GovernmentAction(
                id='test-2024-001',
                title='Older Action',
                date='2024-12-01',
                source_system=SourceSystem.PARLIAMENT,
                url='https://example.com/older',
                primary_entity='Minister',
                summary='Older action'
            ),
            GovernmentAction(
                id='test-2024-002',
                title='Newer Action',
                date='2024-12-15',
                source_system=SourceSystem.PARLIAMENT,
                url='https://example.com/newer',
                primary_entity='Minister',
                summary='Newer action'
            )
        ]

        exporter = TypeScriptExporter(temp_output_path, backup_enabled=False)
        exporter.export(actions)

        content = temp_output_path.read_text()

        # Check that newer action appears before older action
        newer_pos = content.find('test-2024-002')
        older_pos = content.find('test-2024-001')
        assert newer_pos < older_pos

    def test_validation(self, sample_action):
        """Test export validation."""
        exporter = TypeScriptExporter(Path('/tmp/dummy.ts'))
        validation = exporter.validate_export([sample_action])

        assert validation['valid'] is True
        assert len(validation['errors']) == 0
        assert validation['stats']['total_actions'] == 1
        assert validation['stats']['unique_ids'] == 1

    def test_validation_with_duplicates(self):
        """Test validation with duplicate IDs."""
        actions = [
            GovernmentAction(
                id='dup-2024-001',
                title='Action 1',
                date='2024-12-15',
                source_system=SourceSystem.PARLIAMENT,
                url='https://example.com/1',
                primary_entity='Minister',
                summary='Action 1'
            ),
            GovernmentAction(
                id='dup-2024-001',  # Duplicate ID
                title='Action 2',
                date='2024-12-15',
                source_system=SourceSystem.LEGISLATION,
                url='https://example.com/2',
                primary_entity='Minister',
                summary='Action 2'
            )
        ]

        exporter = TypeScriptExporter(Path('/tmp/dummy.ts'))
        validation = exporter.validate_export(actions)

        assert validation['valid'] is False
        assert len(validation['errors']) > 0
        assert any('Duplicate ID' in error for error in validation['errors'])

    def test_source_counts_calculation(self, temp_output_path):
        """Test calculation of source counts in metadata."""
        actions = [
            GovernmentAction(
                id='parl-2024-001',
                title='Parliament Action',
                date='2024-12-15',
                source_system=SourceSystem.PARLIAMENT,
                url='https://example.com/parl',
                primary_entity='Minister',
                summary='Parliament action'
            ),
            GovernmentAction(
                id='leg-2024-001',
                title='Legislation Action',
                date='2024-12-15',
                source_system=SourceSystem.LEGISLATION,
                url='https://example.com/leg',
                primary_entity='Minister',
                summary='Legislation action'
            ),
            GovernmentAction(
                id='parl-2024-002',
                title='Another Parliament Action',
                date='2024-12-15',
                source_system=SourceSystem.PARLIAMENT,
                url='https://example.com/parl2',
                primary_entity='Minister',
                summary='Another parliament action'
            )
        ]

        exporter = TypeScriptExporter(temp_output_path, backup_enabled=False)
        exporter.export(actions, include_metadata=True)

        content = temp_output_path.read_text()

        # Should show PARLIAMENT: 2, LEGISLATION: 1
        assert 'PARLIAMENT\': 2' in content or 'PARLIAMENT": 2' in content
        assert 'LEGISLATION\': 1' in content or 'LEGISLATION": 1' in content

    def test_label_counts_calculation(self, temp_output_path):
        """Test calculation of label counts in metadata."""
        actions = [
            GovernmentAction(
                id='act-2024-001',
                title='Housing Action',
                date='2024-12-15',
                source_system=SourceSystem.PARLIAMENT,
                url='https://example.com/1',
                primary_entity='Minister',
                summary='Housing action',
                labels=['Housing', 'Infrastructure']
            ),
            GovernmentAction(
                id='act-2024-002',
                title='Education Action',
                date='2024-12-15',
                source_system=SourceSystem.LEGISLATION,
                url='https://example.com/2',
                primary_entity='Minister',
                summary='Education action',
                labels=['Education', 'Infrastructure']
            )
        ]

        exporter = TypeScriptExporter(temp_output_path, backup_enabled=False)
        exporter.export(actions, include_metadata=True)

        content = temp_output_path.read_text()

        # Should show Infrastructure: 2, Housing: 1, Education: 1
        assert 'Infrastructure' in content
        assert 'Housing' in content
        assert 'Education' in content

    def test_empty_actions_list(self, temp_output_path):
        """Test exporting empty actions list."""
        exporter = TypeScriptExporter(temp_output_path, backup_enabled=False)
        exporter.export([])

        content = temp_output_path.read_text()
        assert 'export const actions: GovernmentAction[] = []' in content

    def test_pretty_formatting(self, sample_action, temp_output_path):
        """Test pretty formatting option."""
        exporter = TypeScriptExporter(temp_output_path, backup_enabled=False)
        exporter.export([sample_action], format_pretty=True)

        content = temp_output_path.read_text()

        # Should have indentation and newlines for readability
        lines = content.split('\n')
        assert len(lines) > 10  # Should be multi-line

        # Check for proper indentation
        action_lines = [line for line in lines if 'test-2024-001' in line]
        assert len(action_lines) > 0