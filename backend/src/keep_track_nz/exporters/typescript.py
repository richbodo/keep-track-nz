"""TypeScript data exporter for frontend compatibility."""

import json
import logging
from typing import List, Any, Dict
from pathlib import Path
from datetime import datetime

from ..models import GovernmentAction, ActionCollection, PREDEFINED_LABELS
from .base import BaseExporter

logger = logging.getLogger(__name__)


class TypeScriptExporter(BaseExporter):
    """Export government actions to TypeScript-compatible format."""

    def __init__(self, output_path: Path, backup_enabled: bool = True):
        """
        Initialize TypeScript exporter.

        Args:
            output_path: Path to the output TypeScript file
            backup_enabled: Whether to create backups of existing files
        """
        super().__init__(output_path)
        self.backup_enabled = backup_enabled

    def export(self, data: List[GovernmentAction], **kwargs) -> None:
        """
        Export government actions to TypeScript format.

        Args:
            data: List of validated GovernmentAction objects
            **kwargs: Additional export options
                - include_metadata: Include export metadata (default: True)
                - format_pretty: Pretty-print the output (default: True)
        """
        include_metadata = kwargs.get('include_metadata', True)
        format_pretty = kwargs.get('format_pretty', True)

        logger.info(f"Exporting {len(data)} actions to TypeScript format")

        try:
            # Create backup if enabled and file exists
            if self.backup_enabled and self.output_path.exists():
                self._create_backup()

            # Ensure output directory exists
            self._ensure_output_directory()

            # Convert actions to export format
            export_data = self._prepare_export_data(data, include_metadata)

            # Generate TypeScript content
            ts_content = self._generate_typescript_content(export_data, format_pretty)

            # Write to file
            with open(self.output_path, 'w', encoding='utf-8') as f:
                f.write(ts_content)

            logger.info(f"Successfully exported data to {self.output_path}")

        except Exception as e:
            logger.error(f"Failed to export to TypeScript: {e}")
            raise

    def _create_backup(self) -> None:
        """Create backup of existing file."""
        if not self.output_path.exists():
            return

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = self.output_path.with_suffix(f'.backup_{timestamp}{self.output_path.suffix}')

        try:
            backup_path.write_text(self.output_path.read_text(encoding='utf-8'), encoding='utf-8')
            logger.info(f"Created backup: {backup_path}")
        except Exception as e:
            logger.warning(f"Failed to create backup: {e}")

    def _prepare_export_data(self, data: List[GovernmentAction], include_metadata: bool) -> Dict[str, Any]:
        """Prepare data for export in TypeScript format."""
        # Convert actions to dictionaries
        actions_data = []
        for action in data:
            action_dict = action.to_dict()

            # Ensure consistent field order and format
            formatted_action = {
                'id': action_dict['id'],
                'title': action_dict['title'],
                'date': action_dict['date'],
                'source_system': action_dict['source_system'].value if hasattr(action_dict['source_system'], 'value') else action_dict['source_system'],
                'url': action_dict['url'],
                'primary_entity': action_dict['primary_entity'],
                'summary': action_dict['summary'],
                'labels': sorted(action_dict.get('labels', [])),
                'metadata': action_dict.get('metadata', {}),
            }

            # Clean empty metadata
            if not formatted_action['metadata']:
                formatted_action['metadata'] = {}

            actions_data.append(formatted_action)

        # Sort actions by date (newest first), then by title
        actions_data.sort(key=lambda x: (x['date'], x['title']), reverse=True)

        export_data = {
            'labels': PREDEFINED_LABELS,
            'actions': actions_data
        }

        # Add metadata if requested
        if include_metadata:
            export_data['_metadata'] = {
                'last_updated': datetime.now().isoformat(),
                'total_count': len(actions_data),
                'source_counts': self._calculate_source_counts(actions_data),
                'label_counts': self._calculate_label_counts(actions_data),
                'date_range': self._calculate_date_range(actions_data),
                'generated_by': 'keep-track-nz-backend',
                'version': '1.0'
            }

        return export_data

    def _calculate_source_counts(self, actions_data: List[Dict[str, Any]]) -> Dict[str, int]:
        """Calculate count of actions by source system."""
        counts = {}
        for action in actions_data:
            source = action.get('source_system', 'UNKNOWN')
            counts[source] = counts.get(source, 0) + 1
        return counts

    def _calculate_label_counts(self, actions_data: List[Dict[str, Any]]) -> Dict[str, int]:
        """Calculate count of actions by label."""
        counts = {label: 0 for label in PREDEFINED_LABELS}

        for action in actions_data:
            for label in action.get('labels', []):
                if label in counts:
                    counts[label] += 1

        # Remove labels with zero count for cleaner output
        return {label: count for label, count in counts.items() if count > 0}

    def _calculate_date_range(self, actions_data: List[Dict[str, Any]]) -> Dict[str, str]:
        """Calculate date range of actions."""
        if not actions_data:
            return {'earliest': '', 'latest': ''}

        dates = [action.get('date', '') for action in actions_data if action.get('date')]
        if not dates:
            return {'earliest': '', 'latest': ''}

        dates.sort()
        return {
            'earliest': dates[0],
            'latest': dates[-1]
        }

    def _generate_typescript_content(self, export_data: Dict[str, Any], format_pretty: bool) -> str:
        """Generate TypeScript file content."""
        # Generate the main content
        if format_pretty:
            json_content = json.dumps(export_data, indent=2, ensure_ascii=False)
        else:
            json_content = json.dumps(export_data, ensure_ascii=False)

        # Parse the JSON to extract parts for TypeScript formatting
        actions_json = json.dumps(export_data['actions'], indent=2 if format_pretty else None, ensure_ascii=False)
        labels_json = json.dumps(export_data['labels'], indent=2 if format_pretty else None, ensure_ascii=False)

        # Generate TypeScript content with proper types
        ts_content = self._generate_typescript_header()
        ts_content += self._generate_typescript_types()
        ts_content += f"\nexport const labels = {labels_json};\n\n"
        ts_content += f"export const actions: GovernmentAction[] = {actions_json};\n"

        # Add metadata as comment if present
        if '_metadata' in export_data:
            metadata = export_data['_metadata']
            ts_content += f"\n/* Export metadata:\n"
            ts_content += f" * Last updated: {metadata.get('last_updated', 'Unknown')}\n"
            ts_content += f" * Total actions: {metadata.get('total_count', 0)}\n"
            ts_content += f" * Source counts: {metadata.get('source_counts', {})}\n"
            ts_content += f" * Date range: {metadata.get('date_range', {})}\n"
            ts_content += f" * Generated by: {metadata.get('generated_by', 'Unknown')}\n"
            ts_content += f" */\n"

        return ts_content

    def _generate_typescript_header(self) -> str:
        """Generate TypeScript file header."""
        return f'''/**
 * Government Actions Data
 *
 * This file contains New Zealand government actions scraped from official sources:
 * - Parliament (bills.parliament.nz)
 * - Legislation (legislation.govt.nz)
 * - Gazette (gazette.govt.nz)
 * - Beehive (beehive.govt.nz)
 *
 * Generated automatically by the Keep Track NZ backend system.
 * Last updated: {datetime.now().isoformat()}
 *
 * DO NOT EDIT MANUALLY - This file is automatically generated by the backend.
 * See backend/README.md for details on the data collection pipeline.
 */

'''

    def _generate_typescript_types(self) -> str:
        """Generate TypeScript type definitions."""
        return '''export type SourceSystem = 'PARLIAMENT' | 'LEGISLATION' | 'GAZETTE' | 'BEEHIVE';

export interface StageHistory {
  stage: string;
  date: string;
}

export interface ActionMetadata {
  bill_number?: string;
  parliament_number?: number;
  stage_history?: StageHistory[];
  act_number?: string;
  commencement_date?: string;
  notice_number?: string;
  notice_type?: string;
  document_type?: string;
  portfolio?: string;
}

export interface GovernmentAction {
  id: string;
  title: string;
  date: string;
  source_system: SourceSystem;
  url: string;
  primary_entity: string;
  summary: string;
  labels: string[];
  metadata: ActionMetadata;
}
'''

    def export_json(self, data: List[GovernmentAction], json_path: Path) -> None:
        """Export data as pure JSON (for API use)."""
        try:
            export_data = self._prepare_export_data(data, include_metadata=True)

            # Remove TypeScript-specific metadata
            if '_metadata' in export_data:
                export_data['metadata'] = export_data.pop('_metadata')

            json_path.parent.mkdir(parents=True, exist_ok=True)

            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Exported JSON data to {json_path}")

        except Exception as e:
            logger.error(f"Failed to export JSON: {e}")
            raise

    def validate_export(self, data: List[GovernmentAction]) -> Dict[str, Any]:
        """Validate export data for consistency."""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'stats': {}
        }

        try:
            # Check for required fields
            for i, action in enumerate(data):
                if not action.id:
                    validation_result['errors'].append(f"Action {i}: Missing ID")
                if not action.title:
                    validation_result['errors'].append(f"Action {i}: Missing title")
                if not action.url:
                    validation_result['errors'].append(f"Action {i}: Missing URL")

            # Check for duplicates
            seen_ids = set()
            seen_urls = set()
            for i, action in enumerate(data):
                if action.id in seen_ids:
                    validation_result['errors'].append(f"Action {i}: Duplicate ID {action.id}")
                seen_ids.add(action.id)

                if action.url in seen_urls:
                    validation_result['warnings'].append(f"Action {i}: Duplicate URL {action.url}")
                seen_urls.add(action.url)

            # Statistics
            validation_result['stats'] = {
                'total_actions': len(data),
                'unique_ids': len(seen_ids),
                'unique_urls': len(seen_urls),
                'source_distribution': self._calculate_source_counts([action.to_dict() for action in data])
            }

            validation_result['valid'] = len(validation_result['errors']) == 0

        except Exception as e:
            validation_result['valid'] = False
            validation_result['errors'].append(f"Validation error: {e}")

        return validation_result


def main():
    """Test the TypeScript exporter."""
    import sys
    from ..models import GovernmentAction, SourceSystem, ActionMetadata

    logging.basicConfig(level=logging.INFO)

    # Create test data
    test_actions = [
        GovernmentAction(
            id='test-001',
            title='Test Bill',
            date='2024-12-15',
            source_system=SourceSystem.PARLIAMENT,
            url='https://example.com/test1',
            primary_entity='Hon Test Minister',
            summary='A test bill for demonstration',
            labels=['Housing', 'Infrastructure'],
            metadata=ActionMetadata(bill_number='123456')
        )
    ]

    output_path = Path('/tmp/test_export.ts')
    exporter = TypeScriptExporter(output_path)

    if '--test' in sys.argv:
        try:
            exporter.export(test_actions)
            print(f"Test export successful: {output_path}")

            # Validate export
            validation = exporter.validate_export(test_actions)
            print(f"Export validation: {'PASSED' if validation['valid'] else 'FAILED'}")
            if validation['errors']:
                print(f"Errors: {validation['errors']}")
            if validation['warnings']:
                print(f"Warnings: {validation['warnings']}")

            # Show content
            if output_path.exists():
                print("\nExported content:")
                print(output_path.read_text()[:500] + "...")

        except Exception as e:
            print(f"Test export failed: {e}")


if __name__ == '__main__':
    main()