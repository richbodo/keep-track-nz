"""Tests for data models."""

import pytest
from datetime import datetime
from pydantic import ValidationError

from keep_track_nz.models import (
    SourceSystem,
    StageHistory,
    ActionMetadata,
    GovernmentAction,
    ActionCollection,
    PREDEFINED_LABELS
)


class TestSourceSystem:
    """Test SourceSystem enum."""

    def test_source_system_values(self):
        """Test that all expected source systems exist."""
        assert SourceSystem.PARLIAMENT == "PARLIAMENT"
        assert SourceSystem.LEGISLATION == "LEGISLATION"
        assert SourceSystem.GAZETTE == "GAZETTE"
        assert SourceSystem.BEEHIVE == "BEEHIVE"

    def test_source_system_string_conversion(self):
        """Test string conversion of source systems."""
        assert str(SourceSystem.PARLIAMENT) == "SourceSystem.PARLIAMENT"


class TestStageHistory:
    """Test StageHistory model."""

    def test_valid_stage_history(self):
        """Test creating valid stage history."""
        stage = StageHistory(stage="First Reading", date="2024-12-15")
        assert stage.stage == "First Reading"
        assert stage.date == "2024-12-15"

    def test_invalid_date_format(self):
        """Test that invalid date format raises error."""
        with pytest.raises(ValidationError):
            StageHistory(stage="First Reading", date="15/12/2024")

    def test_empty_stage(self):
        """Test that empty stage raises error."""
        with pytest.raises(ValidationError):
            StageHistory(stage="", date="2024-12-15")


class TestActionMetadata:
    """Test ActionMetadata model."""

    def test_parliament_metadata(self):
        """Test Parliament-specific metadata."""
        metadata = ActionMetadata(
            bill_number="123456",
            parliament_number=54,
            stage_history=[
                StageHistory(stage="First Reading", date="2024-01-01"),
                StageHistory(stage="Second Reading", date="2024-02-01")
            ]
        )
        assert metadata.bill_number == "123456"
        assert metadata.parliament_number == 54
        assert len(metadata.stage_history) == 2

    def test_legislation_metadata(self):
        """Test Legislation-specific metadata."""
        metadata = ActionMetadata(
            act_number="2024 No 12",
            commencement_date="2024-12-15"
        )
        assert metadata.act_number == "2024 No 12"
        assert metadata.commencement_date == "2024-12-15"

    def test_gazette_metadata(self):
        """Test Gazette-specific metadata."""
        metadata = ActionMetadata(
            notice_number="2024-go1234",
            notice_type="General",
            portfolio="Justice"
        )
        assert metadata.notice_number == "2024-go1234"
        assert metadata.notice_type == "General"
        assert metadata.portfolio == "Justice"

    def test_invalid_commencement_date(self):
        """Test that invalid commencement date raises error."""
        with pytest.raises(ValidationError):
            ActionMetadata(commencement_date="invalid-date")

    def test_empty_metadata(self):
        """Test empty metadata is valid."""
        metadata = ActionMetadata()
        assert metadata.bill_number is None
        assert metadata.act_number is None


class TestGovernmentAction:
    """Test GovernmentAction model."""

    def test_valid_government_action(self):
        """Test creating valid government action."""
        action = GovernmentAction(
            id="parl-2024-001",
            title="Test Bill",
            date="2024-12-15",
            source_system=SourceSystem.PARLIAMENT,
            url="https://example.com/bill",
            primary_entity="Hon Test Minister",
            summary="A test bill for testing",
            labels=["Housing", "Infrastructure"],
            metadata=ActionMetadata(bill_number="123456")
        )

        assert action.id == "parl-2024-001"
        assert action.title == "Test Bill"
        assert action.date == "2024-12-15"
        assert action.source_system == SourceSystem.PARLIAMENT
        assert action.url == "https://example.com/bill"
        assert action.primary_entity == "Hon Test Minister"
        assert action.summary == "A test bill for testing"
        assert action.labels == ["Housing", "Infrastructure"]
        assert action.metadata.bill_number == "123456"

    def test_invalid_date_format(self):
        """Test that invalid date format raises error."""
        with pytest.raises(ValidationError):
            GovernmentAction(
                id="parl-2024-001",
                title="Test Bill",
                date="15/12/2024",  # Invalid format
                source_system=SourceSystem.PARLIAMENT,
                url="https://example.com/bill",
                primary_entity="Hon Test Minister",
                summary="A test bill"
            )

    def test_invalid_url(self):
        """Test that invalid URL raises error."""
        with pytest.raises(ValidationError):
            GovernmentAction(
                id="parl-2024-001",
                title="Test Bill",
                date="2024-12-15",
                source_system=SourceSystem.PARLIAMENT,
                url="not-a-valid-url",  # Invalid URL
                primary_entity="Hon Test Minister",
                summary="A test bill"
            )

    def test_invalid_id_format(self):
        """Test that invalid ID format raises error."""
        with pytest.raises(ValidationError):
            GovernmentAction(
                id="invalid-id",  # Invalid format
                title="Test Bill",
                date="2024-12-15",
                source_system=SourceSystem.PARLIAMENT,
                url="https://example.com/bill",
                primary_entity="Hon Test Minister",
                summary="A test bill"
            )

    def test_to_dict(self):
        """Test converting action to dictionary."""
        action = GovernmentAction(
            id="parl-2024-001",
            title="Test Bill",
            date="2024-12-15",
            source_system=SourceSystem.PARLIAMENT,
            url="https://example.com/bill",
            primary_entity="Hon Test Minister",
            summary="A test bill",
            labels=["Housing"]
        )

        action_dict = action.to_dict()
        assert isinstance(action_dict, dict)
        assert action_dict["id"] == "parl-2024-001"
        assert action_dict["source_system"] == "PARLIAMENT"


class TestActionCollection:
    """Test ActionCollection model."""

    def test_empty_collection(self):
        """Test creating empty collection."""
        collection = ActionCollection()
        assert len(collection.actions) == 0
        assert collection.total_count == 0
        assert collection.source_counts == {}

    def test_add_action(self):
        """Test adding action to collection."""
        collection = ActionCollection()
        action = GovernmentAction(
            id="parl-2024-001",
            title="Test Bill",
            date="2024-12-15",
            source_system=SourceSystem.PARLIAMENT,
            url="https://example.com/bill",
            primary_entity="Hon Test Minister",
            summary="A test bill"
        )

        collection.add_action(action)
        assert len(collection.actions) == 1
        assert collection.total_count == 1
        assert collection.source_counts["PARLIAMENT"] == 1

    def test_multiple_actions(self):
        """Test collection with multiple actions."""
        collection = ActionCollection()

        # Add Parliament action
        parl_action = GovernmentAction(
            id="parl-2024-001",
            title="Parliament Bill",
            date="2024-12-15",
            source_system=SourceSystem.PARLIAMENT,
            url="https://example.com/bill",
            primary_entity="Hon Test Minister",
            summary="A parliament bill"
        )

        # Add Legislation action
        leg_action = GovernmentAction(
            id="leg-2024-001",
            title="Test Act",
            date="2024-12-15",
            source_system=SourceSystem.LEGISLATION,
            url="https://example.com/act",
            primary_entity="Parliament",
            summary="A test act"
        )

        collection.add_action(parl_action)
        collection.add_action(leg_action)

        assert collection.total_count == 2
        assert collection.source_counts["PARLIAMENT"] == 1
        assert collection.source_counts["LEGISLATION"] == 1

    def test_typescript_export(self):
        """Test TypeScript export format."""
        collection = ActionCollection()
        action = GovernmentAction(
            id="parl-2024-001",
            title="Test Bill",
            date="2024-12-15",
            source_system=SourceSystem.PARLIAMENT,
            url="https://example.com/bill",
            primary_entity="Hon Test Minister",
            summary="A test bill",
            labels=["Housing"]
        )

        collection.add_action(action)
        export_data = collection.to_typescript_export()

        assert "labels" in export_data
        assert "actions" in export_data
        assert export_data["labels"] == PREDEFINED_LABELS
        assert len(export_data["actions"]) == 1
        assert export_data["actions"][0]["id"] == "parl-2024-001"


class TestPredefinedLabels:
    """Test predefined labels."""

    def test_predefined_labels_exist(self):
        """Test that predefined labels are available."""
        assert isinstance(PREDEFINED_LABELS, list)
        assert len(PREDEFINED_LABELS) > 0

    def test_expected_labels(self):
        """Test that expected labels are present."""
        expected_labels = [
            'Housing', 'Health', 'Education', 'Infrastructure',
            'Environment', 'Economy', 'Justice', 'Immigration',
            'Defence', 'Transport', 'Social Welfare', 'Tax',
            'Local Government', 'Treaty of Waitangi', 'Agriculture'
        ]

        for label in expected_labels:
            assert label in PREDEFINED_LABELS