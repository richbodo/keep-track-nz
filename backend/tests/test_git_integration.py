"""Tests for Git integration."""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

import git

from keep_track_nz.git_integration import GitIntegration


class TestGitIntegration:
    """Test Git integration functionality."""

    @pytest.fixture
    def temp_repo(self):
        """Create a temporary Git repository for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        repo = git.Repo.init(temp_dir)

        # Create an initial commit
        test_file = temp_dir / "README.md"
        test_file.write_text("# Test Repository")
        repo.index.add(["README.md"])
        repo.index.commit("Initial commit")

        try:
            yield temp_dir, repo
        finally:
            shutil.rmtree(temp_dir)

    def test_initialize_existing_repo(self, temp_repo):
        """Test initializing with existing repository."""
        temp_dir, _ = temp_repo

        git_integration = GitIntegration(temp_dir)
        git_integration.initialize_repo()

        assert git_integration.repo is not None
        assert git_integration.repo.working_dir == str(temp_dir)

    def test_initialize_nonexistent_repo(self):
        """Test initializing with non-existent repository."""
        git_integration = GitIntegration("/path/that/does/not/exist")

        with pytest.raises(ValueError, match="Repository not found"):
            git_integration.initialize_repo()

    def test_commit_data_update_success(self, temp_repo):
        """Test successful data update commit."""
        temp_dir, repo = temp_repo

        git_integration = GitIntegration(temp_dir)
        git_integration.initialize_repo()

        # Create a file to commit
        data_file = temp_dir / "data.json"
        data_file.write_text('{"test": "data"}')

        # Commit the file
        success = git_integration.commit_data_update(
            files_to_commit=["data.json"],
            commit_message="Test data update"
        )

        assert success is True

        # Verify commit was created
        commits = list(repo.iter_commits(max_count=2))
        assert len(commits) == 2  # Initial + new commit
        assert commits[0].message.strip() == "Test data update"

    def test_commit_with_no_changes(self, temp_repo):
        """Test commit when there are no changes."""
        temp_dir, _ = temp_repo

        git_integration = GitIntegration(temp_dir)
        git_integration.initialize_repo()

        # Try to commit with no changes
        success = git_integration.commit_data_update(
            files_to_commit=["nonexistent.txt"]
        )

        # Should return True but not create a commit
        assert success is True

    def test_commit_with_stats(self, temp_repo):
        """Test commit with statistics."""
        temp_dir, repo = temp_repo

        git_integration = GitIntegration(temp_dir)
        git_integration.initialize_repo()

        # Create a file to commit
        data_file = temp_dir / "data.json"
        data_file.write_text('{"actions": []}')

        stats = {
            'total_count': 42,
            'source_counts': {'PARLIAMENT': 20, 'LEGISLATION': 22},
            'date_range': {'earliest': '2024-01-01', 'latest': '2024-12-15'}
        }

        success = git_integration.commit_data_update(
            files_to_commit=["data.json"],
            stats=stats
        )

        assert success is True

        # Check commit message includes stats
        latest_commit = next(repo.iter_commits(max_count=1))
        commit_message = latest_commit.message

        assert "Total actions: 42" in commit_message
        assert "PARLIAMENT: 20" in commit_message
        assert "LEGISLATION: 22" in commit_message
        assert "2024-01-01 to 2024-12-15" in commit_message

    def test_commit_message_generation(self, temp_repo):
        """Test automatic commit message generation."""
        temp_dir, _ = temp_repo

        git_integration = GitIntegration(temp_dir)
        git_integration.initialize_repo()

        # Create multiple files
        data_file = temp_dir / "data.json"
        data_file.write_text('{}')
        ts_file = temp_dir / "data.ts"
        ts_file.write_text('export const data = {};')

        success = git_integration.commit_data_update(
            files_to_commit=["data.json", "data.ts"]
        )

        assert success is True

        # Check generated commit message
        latest_commit = next(git_integration.repo.iter_commits(max_count=1))
        commit_message = latest_commit.message

        assert "Update government data" in commit_message
        assert "data.json" in commit_message
        assert "data.ts" in commit_message
        assert "Keep Track NZ Backend" in commit_message

    def test_check_repository_status(self, temp_repo):
        """Test repository status checking."""
        temp_dir, repo = temp_repo

        git_integration = GitIntegration(temp_dir)
        git_integration.initialize_repo()

        status = git_integration.check_repository_status()

        assert status['initialized'] is True
        assert status['clean'] is True
        assert status['current_branch'] in ['main', 'master']  # Could be either
        assert status['last_commit'] is not None
        assert status['last_commit']['message'] == "Initial commit"

    def test_check_status_with_changes(self, temp_repo):
        """Test status with uncommitted changes."""
        temp_dir, _ = temp_repo

        git_integration = GitIntegration(temp_dir)
        git_integration.initialize_repo()

        # Create an uncommitted file
        new_file = temp_dir / "new_file.txt"
        new_file.write_text("New content")

        status = git_integration.check_repository_status()

        assert status['clean'] is False
        assert "new_file.txt" in status['untracked_files']

    def test_get_last_update_time(self, temp_repo):
        """Test getting last update time for a file."""
        temp_dir, repo = temp_repo

        git_integration = GitIntegration(temp_dir)
        git_integration.initialize_repo()

        # Get last update time for README.md
        last_update = git_integration.get_last_update_time("README.md")

        assert last_update is not None
        # Should be recent (within last minute)
        from datetime import datetime, timedelta
        assert (datetime.now() - last_update) < timedelta(minutes=1)

    def test_get_last_update_time_nonexistent(self, temp_repo):
        """Test getting last update time for non-existent file."""
        temp_dir, _ = temp_repo

        git_integration = GitIntegration(temp_dir)
        git_integration.initialize_repo()

        last_update = git_integration.get_last_update_time("nonexistent.txt")
        assert last_update is None

    def test_validate_repository_success(self, temp_repo):
        """Test successful repository validation."""
        temp_dir, _ = temp_repo

        git_integration = GitIntegration(temp_dir)
        validation = git_integration.validate_repository()

        assert validation['valid'] is True
        assert len(validation['errors']) == 0

    def test_validate_repository_not_git(self):
        """Test validation of non-Git directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            git_integration = GitIntegration(temp_dir)
            validation = git_integration.validate_repository()

            assert validation['valid'] is False
            assert len(validation['errors']) > 0
            assert any("Not a Git repository" in error for error in validation['errors'])

    def test_validate_repository_nonexistent(self):
        """Test validation of non-existent directory."""
        git_integration = GitIntegration("/path/that/does/not/exist")
        validation = git_integration.validate_repository()

        assert validation['valid'] is False
        assert len(validation['errors']) > 0
        assert any("does not exist" in error for error in validation['errors'])

    def test_dry_run_with_changes(self, temp_repo):
        """Test dry run with file changes."""
        temp_dir, _ = temp_repo

        git_integration = GitIntegration(temp_dir)
        git_integration.initialize_repo()

        # Create a file that would be committed
        data_file = temp_dir / "data.json"
        data_file.write_text('{"test": true}')

        stats = {'total_count': 10}

        result = git_integration.dry_run(["data.json"], stats)

        assert result['would_commit'] is True
        assert result['changes_detected'] is True
        assert "data.json" in result['files_to_stage']
        assert "Test data update" not in result['commit_message']  # Should be generated message
        assert len(result['errors']) == 0

    def test_dry_run_no_changes(self, temp_repo):
        """Test dry run with no changes."""
        temp_dir, _ = temp_repo

        git_integration = GitIntegration(temp_dir)
        git_integration.initialize_repo()

        result = git_integration.dry_run(["nonexistent.txt"])

        assert result['would_commit'] is False
        assert result['changes_detected'] is False
        assert len(result['files_to_stage']) == 0

    def test_custom_author_info(self, temp_repo):
        """Test custom commit author information."""
        temp_dir, repo = temp_repo

        custom_name = "Custom Bot"
        custom_email = "custom@example.com"

        git_integration = GitIntegration(
            temp_dir,
            commit_author_name=custom_name,
            commit_author_email=custom_email
        )
        git_integration.initialize_repo()

        # Create and commit a file
        data_file = temp_dir / "test.txt"
        data_file.write_text("Test content")

        success = git_integration.commit_data_update(["test.txt"])
        assert success is True

        # Check author information
        latest_commit = next(repo.iter_commits(max_count=1))
        assert latest_commit.author.name == custom_name
        assert latest_commit.author.email == custom_email

    def test_branch_handling(self, temp_repo):
        """Test branch handling."""
        temp_dir, repo = temp_repo

        # Create a new branch
        test_branch = repo.create_head('test-branch')

        git_integration = GitIntegration(temp_dir, branch='test-branch')
        git_integration.initialize_repo()

        # Should be on test-branch
        assert git_integration.repo.active_branch.name == 'test-branch'

    def test_has_changes_detection(self, temp_repo):
        """Test change detection logic."""
        temp_dir, _ = temp_repo

        git_integration = GitIntegration(temp_dir)
        git_integration.initialize_repo()

        # No changes initially
        assert git_integration._has_changes(["README.md"]) is False

        # Create a new file
        new_file = temp_dir / "new.txt"
        new_file.write_text("New content")

        # Should detect changes
        assert git_integration._has_changes(["new.txt"]) is True

        # Modify existing file
        readme = temp_dir / "README.md"
        readme.write_text("Modified README")

        # Should detect changes
        assert git_integration._has_changes(["README.md"]) is True