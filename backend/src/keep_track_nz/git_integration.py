"""Git integration for automated commits of data updates."""

import logging
import os
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

import git
from git import Repo, GitCommandError

logger = logging.getLogger(__name__)


class GitIntegration:
    """Handle Git operations for committing updated data."""

    def __init__(
        self,
        repo_path: Path | str,
        branch: str = "main",
        commit_author_name: str = "Keep Track NZ Bot",
        commit_author_email: str = "bot@keeptrack.nz"
    ):
        """
        Initialize Git integration.

        Args:
            repo_path: Path to the Git repository
            branch: Branch to commit to (default: "main")
            commit_author_name: Name for commit author
            commit_author_email: Email for commit author
        """
        self.repo_path = Path(repo_path)
        self.branch = branch
        self.commit_author_name = commit_author_name
        self.commit_author_email = commit_author_email
        self.repo: Optional[Repo] = None

    def initialize_repo(self) -> None:
        """Initialize or open the Git repository."""
        try:
            if self.repo_path.exists() and (self.repo_path / ".git").exists():
                self.repo = Repo(self.repo_path)
                logger.info(f"Opened existing repository at {self.repo_path}")
            else:
                # Repository doesn't exist, this is an error for our use case
                raise ValueError(f"Repository not found at {self.repo_path}")

            # Ensure we're on the correct branch
            self._ensure_branch()

        except Exception as e:
            logger.error(f"Failed to initialize repository: {e}")
            raise

    def _ensure_branch(self) -> None:
        """Ensure we're on the correct branch."""
        if not self.repo:
            raise ValueError("Repository not initialized")

        try:
            # Check if branch exists
            if self.branch in [branch.name for branch in self.repo.branches]:
                # Switch to branch if not already on it
                if self.repo.active_branch.name != self.branch:
                    self.repo.git.checkout(self.branch)
                    logger.info(f"Switched to branch {self.branch}")
            else:
                logger.warning(f"Branch {self.branch} does not exist, staying on current branch")

        except Exception as e:
            logger.warning(f"Failed to switch to branch {self.branch}: {e}")

    def commit_data_update(
        self,
        files_to_commit: List[Path | str],
        commit_message: Optional[str] = None,
        stats: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Commit data updates to the repository.

        Args:
            files_to_commit: List of file paths to commit
            commit_message: Custom commit message (optional)
            stats: Statistics about the update (optional)

        Returns:
            True if commit was successful, False otherwise
        """
        if not self.repo:
            logger.error("Repository not initialized")
            return False

        try:
            # Check if there are any changes to commit
            if not self._has_changes(files_to_commit):
                logger.info("No changes detected, skipping commit")
                return True

            # Stage the files
            staged_files = []
            for file_path in files_to_commit:
                abs_path = self.repo_path / file_path if not Path(file_path).is_absolute() else Path(file_path)
                rel_path = abs_path.relative_to(self.repo_path)

                if abs_path.exists():
                    self.repo.index.add([str(rel_path)])
                    staged_files.append(str(rel_path))
                    logger.debug(f"Staged file: {rel_path}")
                else:
                    logger.warning(f"File does not exist, skipping: {abs_path}")

            if not staged_files:
                logger.warning("No files were staged for commit")
                return False

            # Generate commit message
            if not commit_message:
                commit_message = self._generate_commit_message(staged_files, stats)

            # Create the commit
            commit = self.repo.index.commit(
                message=commit_message,
                author=git.Actor(self.commit_author_name, self.commit_author_email),
                committer=git.Actor(self.commit_author_name, self.commit_author_email)
            )

            logger.info(f"Successfully committed changes: {commit.hexsha[:8]}")
            logger.info(f"Commit message: {commit_message}")
            return True

        except Exception as e:
            logger.error(f"Failed to commit changes: {e}")
            return False

    def _has_changes(self, files_to_check: List[Path | str]) -> bool:
        """Check if there are any changes in the specified files."""
        if not self.repo:
            return False

        try:
            # Check if repository has any changes at all
            if self.repo.is_dirty(untracked_files=True):
                # Check specifically for our files
                for file_path in files_to_check:
                    abs_path = self.repo_path / file_path if not Path(file_path).is_absolute() else Path(file_path)
                    rel_path = abs_path.relative_to(self.repo_path)

                    # Check if file is modified or untracked
                    if str(rel_path) in self.repo.untracked_files:
                        return True

                    # Check if file is in the diff
                    try:
                        diff = self.repo.git.diff('HEAD', str(rel_path))
                        if diff:
                            return True
                    except GitCommandError:
                        # File might be new or repository might be empty
                        return True

            return False

        except Exception as e:
            logger.warning(f"Error checking for changes: {e}")
            return True  # Assume changes exist if we can't check

    def _generate_commit_message(self, files: List[str], stats: Optional[Dict[str, Any]]) -> str:
        """Generate a descriptive commit message."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')

        # Base message
        message_parts = [f"Update government data ({timestamp})"]

        # Add statistics if available
        if stats:
            total_actions = stats.get('total_count', 0)
            if total_actions > 0:
                message_parts.append(f"\n\n- Total actions: {total_actions}")

            source_counts = stats.get('source_counts', {})
            if source_counts:
                message_parts.append("- Sources:")
                for source, count in sorted(source_counts.items()):
                    message_parts.append(f"  - {source}: {count}")

            date_range = stats.get('date_range', {})
            if date_range.get('earliest') and date_range.get('latest'):
                message_parts.append(f"- Date range: {date_range['earliest']} to {date_range['latest']}")

        # Add file information
        message_parts.append(f"\n\nFiles updated:")
        for file_path in sorted(files):
            message_parts.append(f"- {file_path}")

        # Add generation info
        message_parts.append(f"\n🤖 Generated with Keep Track NZ Backend")
        message_parts.append(f"\nCo-Authored-By: {self.commit_author_name} <{self.commit_author_email}>")

        return "".join(message_parts)

    def get_last_update_time(self, file_path: Path | str) -> Optional[datetime]:
        """Get the timestamp of the last commit that modified a file."""
        if not self.repo:
            return None

        try:
            abs_path = self.repo_path / file_path if not Path(file_path).is_absolute() else Path(file_path)
            rel_path = abs_path.relative_to(self.repo_path)

            # Get the last commit that modified this file
            commits = list(self.repo.iter_commits(paths=str(rel_path), max_count=1))
            if commits:
                return datetime.fromtimestamp(commits[0].committed_date)

            return None

        except Exception as e:
            logger.warning(f"Failed to get last update time for {file_path}: {e}")
            return None

    def check_repository_status(self) -> Dict[str, Any]:
        """Check the status of the repository."""
        status = {
            'initialized': False,
            'clean': False,
            'current_branch': '',
            'remote_connected': False,
            'last_commit': None,
            'untracked_files': [],
            'modified_files': [],
            'staged_files': []
        }

        try:
            if not self.repo:
                return status

            status['initialized'] = True
            status['clean'] = not self.repo.is_dirty(untracked_files=True)
            status['current_branch'] = self.repo.active_branch.name
            status['untracked_files'] = list(self.repo.untracked_files)

            # Get modified and staged files
            status['modified_files'] = [item.a_path for item in self.repo.index.diff(None)]
            status['staged_files'] = [item.a_path for item in self.repo.index.diff('HEAD')]

            # Check remote connection
            try:
                remotes = list(self.repo.remotes)
                status['remote_connected'] = len(remotes) > 0
            except Exception:
                status['remote_connected'] = False

            # Get last commit info
            try:
                last_commit = next(self.repo.iter_commits(max_count=1))
                status['last_commit'] = {
                    'hash': last_commit.hexsha[:8],
                    'message': last_commit.message.strip(),
                    'author': str(last_commit.author),
                    'date': datetime.fromtimestamp(last_commit.committed_date).isoformat()
                }
            except Exception:
                status['last_commit'] = None

        except Exception as e:
            logger.error(f"Failed to check repository status: {e}")

        return status

    def validate_repository(self) -> Dict[str, Any]:
        """Validate the repository is ready for automated commits."""
        validation = {
            'valid': True,
            'errors': [],
            'warnings': []
        }

        try:
            # Check if repository exists
            if not self.repo_path.exists():
                validation['errors'].append(f"Repository path does not exist: {self.repo_path}")
                validation['valid'] = False
                return validation

            # Check if it's a Git repository
            if not (self.repo_path / ".git").exists():
                validation['errors'].append(f"Not a Git repository: {self.repo_path}")
                validation['valid'] = False
                return validation

            # Initialize if not already done
            if not self.repo:
                self.initialize_repo()

            # Check repository status
            status = self.check_repository_status()

            # Validate branch
            if status['current_branch'] != self.branch:
                validation['warnings'].append(f"Not on target branch {self.branch}, currently on {status['current_branch']}")

            # Check for pending changes
            if not status['clean']:
                validation['warnings'].append("Repository has uncommitted changes")

            # Check remote connection
            if not status['remote_connected']:
                validation['warnings'].append("No remote repository configured")

        except Exception as e:
            validation['errors'].append(f"Repository validation failed: {e}")
            validation['valid'] = False

        return validation

    def dry_run(self, files_to_commit: List[Path | str], stats: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Perform a dry run to show what would be committed.

        Args:
            files_to_commit: List of file paths that would be committed
            stats: Statistics that would be included in commit message

        Returns:
            Dictionary with dry run results
        """
        result = {
            'would_commit': False,
            'files_to_stage': [],
            'commit_message': '',
            'changes_detected': False,
            'errors': []
        }

        try:
            if not self.repo:
                self.initialize_repo()

            # Check which files exist and have changes
            for file_path in files_to_commit:
                abs_path = self.repo_path / file_path if not Path(file_path).is_absolute() else Path(file_path)

                if abs_path.exists():
                    rel_path = abs_path.relative_to(self.repo_path)
                    result['files_to_stage'].append(str(rel_path))
                else:
                    result['errors'].append(f"File does not exist: {abs_path}")

            # Check if there are changes
            result['changes_detected'] = self._has_changes(files_to_commit)

            # Generate commit message
            if result['files_to_stage']:
                result['commit_message'] = self._generate_commit_message(result['files_to_stage'], stats)

            result['would_commit'] = result['changes_detected'] and len(result['files_to_stage']) > 0

        except Exception as e:
            result['errors'].append(f"Dry run failed: {e}")

        return result


def main():
    """Test Git integration."""
    import sys
    import tempfile

    logging.basicConfig(level=logging.INFO)

    if '--test' in sys.argv:
        # Create a temporary Git repository for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_repo = Path(temp_dir)

            # Initialize a test repository
            repo = Repo.init(temp_repo)
            test_file = temp_repo / "test.txt"
            test_file.write_text("Initial content")
            repo.index.add(["test.txt"])
            repo.index.commit("Initial commit")

            # Test GitIntegration
            git_integration = GitIntegration(temp_repo)
            git_integration.initialize_repo()

            # Test repository status
            status = git_integration.check_repository_status()
            print(f"Repository status: {status}")

            # Test validation
            validation = git_integration.validate_repository()
            print(f"Repository validation: {validation}")

            # Test dry run
            test_file.write_text("Updated content")
            dry_run = git_integration.dry_run(["test.txt"], {"total_count": 10})
            print(f"Dry run result: {dry_run}")

            # Test actual commit
            if dry_run['would_commit']:
                success = git_integration.commit_data_update(["test.txt"])
                print(f"Commit successful: {success}")


if __name__ == '__main__':
    main()