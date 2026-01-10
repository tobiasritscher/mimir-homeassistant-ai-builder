"""Git manager for Mímir configuration version control."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class GitConfig:
    """Git configuration."""

    repo_path: str = "/config"
    author_name: str = "Mimir"
    author_email: str = "mimir@asgard.local"
    enabled: bool = True


class GitManager:
    """Manager for git operations on Home Assistant config directory."""

    def __init__(self, config: GitConfig | None = None) -> None:
        """Initialize the git manager.

        Args:
            config: Git configuration. Uses defaults if not provided.
        """
        self._config = config or GitConfig()
        self._repo_path = Path(self._config.repo_path)
        self._initialized = False

    @property
    def enabled(self) -> bool:
        """Check if git is enabled."""
        return self._config.enabled

    async def _run_git(self, *args: str, timeout: float = 30.0) -> tuple[str, str, int]:
        """Run a git command.

        Args:
            *args: Git command arguments.
            timeout: Timeout in seconds (default 30).

        Returns:
            Tuple of (stdout, stderr, returncode).
        """
        cmd = ["git", "-C", str(self._repo_path), *args]
        logger.debug("Running: %s", " ".join(cmd))

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
            return (
                stdout.decode("utf-8", errors="replace").strip(),
                stderr.decode("utf-8", errors="replace").strip(),
                process.returncode or 0,
            )
        except TimeoutError:
            process.kill()
            await process.wait()
            logger.warning("Git command timed out: %s", " ".join(cmd))
            return ("", "Command timed out", 1)

    async def initialize(self) -> bool:
        """Initialize git repository if needed.

        Returns:
            True if initialization successful.
        """
        if not self._config.enabled:
            logger.info("Git is disabled")
            return False

        if not self._repo_path.exists():
            logger.warning("Repository path does not exist: %s", self._repo_path)
            return False

        # Check if already a git repo
        _stdout, stderr, code = await self._run_git("rev-parse", "--git-dir")

        if code != 0:
            # Initialize new repository
            logger.info("Initializing git repository at %s", self._repo_path)
            _stdout, stderr, code = await self._run_git("init")

            if code != 0:
                logger.error("Failed to initialize git: %s", stderr)
                return False

            # Configure user
            await self._run_git("config", "user.name", self._config.author_name)
            await self._run_git("config", "user.email", self._config.author_email)

            # Create initial commit
            await self._run_git("add", "-A")
            await self._run_git(
                "commit",
                "-m",
                "Initial commit by Mimir",
                "--allow-empty",
            )

        self._initialized = True
        logger.info("Git repository initialized")
        return True

    async def generate_commit_message(self) -> str:
        """Generate a meaningful commit message based on changed files.

        Returns:
            Generated commit message.
        """
        stdout, _stderr, code = await self._run_git("status", "--porcelain")
        if code != 0 or not stdout:
            return "Update configuration"

        lines = [line for line in stdout.split("\n") if line.strip()]
        changes: dict[str, list[str]] = {"added": [], "modified": [], "deleted": []}

        for line in lines:
            status = line[:2].strip()
            filepath = line[3:].strip()
            filename = filepath.split("/")[-1]

            if status in ("A", "??"):
                changes["added"].append(filename)
            elif status == "D":
                changes["deleted"].append(filename)
            else:
                changes["modified"].append(filename)

        # Categorize by file type
        automations = []
        scripts = []
        configs = []
        others = []

        for files in changes.values():
            for f in files:
                f_lower = f.lower()
                if "automation" in f_lower:
                    automations.append(f)
                elif "script" in f_lower:
                    scripts.append(f)
                elif f_lower in (
                    "configuration.yaml",
                    "secrets.yaml",
                    "customize.yaml",
                ):
                    configs.append(f)
                else:
                    others.append(f)

        # Build message
        parts = []
        if automations:
            parts.append(f"automations ({len(automations)})")
        if scripts:
            parts.append(f"scripts ({len(scripts)})")
        if configs:
            parts.append(f"core config ({len(configs)})")
        if others:
            parts.append(f"other files ({len(others)})")

        if not parts:
            return "Update configuration"

        total = len(lines)
        action = "Update"
        if changes["added"] and not changes["modified"] and not changes["deleted"]:
            action = "Add"
        elif changes["deleted"] and not changes["added"] and not changes["modified"]:
            action = "Remove"

        return f"{action} {', '.join(parts)} - {total} file(s) changed"

    async def commit_all(self) -> dict[str, Any]:
        """Commit all changes with an auto-generated message.

        Returns:
            Commit info dict with message used.
        """
        if not self._initialized:
            await self.initialize()

        # Generate message before staging (to see what's changing)
        message = await self.generate_commit_message()

        # Perform the commit
        result = await self.commit(message)
        if result.get("status") == "ok":
            result["message"] = message

        return result

    async def commit(
        self,
        message: str,
        files: list[str] | None = None,
    ) -> dict[str, Any]:
        """Commit changes.

        Args:
            message: Commit message.
            files: Specific files to commit. If None, commits all changes.

        Returns:
            Commit info dict.
        """
        if not self._initialized:
            await self.initialize()

        # Stage files
        if files:
            for f in files:
                await self._run_git("add", f)
        else:
            await self._run_git("add", "-A")

        # Check if there are changes to commit
        stdout, stderr, code = await self._run_git("status", "--porcelain")
        if not stdout:
            logger.debug("No changes to commit")
            return {"status": "no_changes"}

        # Commit
        stdout, stderr, code = await self._run_git(
            "commit",
            "-m",
            message,
            f"--author={self._config.author_name} <{self._config.author_email}>",
        )

        if code != 0:
            logger.error("Commit failed: %s", stderr)
            return {"status": "error", "error": stderr}

        # Get commit info
        commit = await self.get_latest_commit()
        logger.info("Created commit: %s", commit.get("sha", "")[:8])

        return {"status": "ok", "commit": commit}

    async def get_latest_commit(self) -> dict[str, Any]:
        """Get the latest commit info.

        Returns:
            Commit info dict.
        """
        stdout, _stderr, code = await self._run_git(
            "log",
            "-1",
            "--format=%H|%s|%an|%aI",
        )

        if code != 0 or not stdout:
            return {}

        parts = stdout.split("|", 3)
        if len(parts) < 4:
            return {}

        return {
            "sha": parts[0],
            "message": parts[1],
            "author": parts[2],
            "date": parts[3],
        }

    async def get_commits(self, limit: int = 20) -> list[dict[str, Any]]:
        """Get recent commits.

        Args:
            limit: Maximum number of commits to return.

        Returns:
            List of commit info dicts.
        """
        if not self._initialized:
            await self.initialize()

        stdout, _stderr, code = await self._run_git(
            "log",
            f"-{limit}",
            "--format=%H|%s|%an|%aI",
        )

        if code != 0 or not stdout:
            return []

        commits = []
        for line in stdout.split("\n"):
            if not line:
                continue
            parts = line.split("|", 3)
            if len(parts) >= 4:
                commits.append(
                    {
                        "sha": parts[0],
                        "message": parts[1],
                        "author": parts[2],
                        "date": parts[3],
                    }
                )

        return commits

    async def get_diff(self, sha: str) -> str:
        """Get the diff for a specific commit.

        Args:
            sha: Commit SHA.

        Returns:
            Diff string.
        """
        if not self._initialized:
            await self.initialize()

        # First get diff stats to check size
        stat_out, stat_err, stat_code = await self._run_git(
            "show", sha, "--format=", "--stat", timeout=10.0
        )

        if stat_code != 0:
            return f"Error: {stat_err}"

        # Count files changed from stat output
        stat_lines = [line for line in stat_out.split("\n") if line.strip()]

        # If too many files or stat timed out, just return stats
        if len(stat_lines) > 50 or "timed out" in stat_err.lower():
            return f"Large commit - showing stats only:\n\n{stat_out}"

        # Try to get full diff with timeout
        stdout, stderr, code = await self._run_git("show", sha, "--format=", timeout=15.0)

        if code != 0:
            if "timed out" in stderr.lower():
                return f"Diff too large to display. Stats:\n\n{stat_out}"
            return f"Error: {stderr}"

        # If diff is very large, truncate it
        if len(stdout) > 100000:  # 100KB limit
            truncated = stdout[:100000]
            return f"{truncated}\n\n... (truncated, diff too large)"

        return stdout

    async def get_status(self) -> dict[str, Any]:
        """Get repository status.

        Returns:
            Status info dict.
        """
        if not self._initialized:
            await self.initialize()

        stdout, _stderr, _code = await self._run_git("status", "--porcelain")

        changed_files = len([line for line in stdout.split("\n") if line.strip()])

        return {
            "clean": changed_files == 0,
            "changed_files": changed_files,
        }

    async def get_branches(self) -> list[dict[str, Any]]:
        """Get list of branches.

        Returns:
            List of branch info dicts.
        """
        if not self._initialized:
            await self.initialize()

        stdout, _stderr, code = await self._run_git("branch", "-a")

        if code != 0:
            return []

        branches = []
        for line in stdout.split("\n"):
            if not line.strip():
                continue

            current = line.startswith("*")
            name = line.lstrip("* ").strip()

            # Skip remote tracking branches
            if name.startswith("remotes/"):
                continue

            branches.append(
                {
                    "name": name,
                    "current": current,
                }
            )

        return branches

    async def create_branch(self, name: str) -> bool:
        """Create a new branch.

        Args:
            name: Branch name.

        Returns:
            True if successful.
        """
        _stdout, _stderr, code = await self._run_git("checkout", "-b", name)
        return code == 0

    async def checkout(self, branch: str) -> bool:
        """Checkout a branch.

        Args:
            branch: Branch name.

        Returns:
            True if successful.
        """
        _stdout, _stderr, code = await self._run_git("checkout", branch)
        return code == 0

    async def rollback(self, sha: str) -> bool:
        """Rollback to a specific commit.

        This creates a new commit that reverts all changes since the target commit.

        Args:
            sha: Target commit SHA.

        Returns:
            True if successful.
        """
        # Get list of commits to revert
        stdout, stderr, code = await self._run_git(
            "rev-list",
            "--ancestry-path",
            f"{sha}..HEAD",
        )

        if code != 0:
            logger.error("Failed to get commits to revert: %s", stderr)
            return False

        commits_to_revert = [c for c in stdout.split("\n") if c.strip()]

        if not commits_to_revert:
            logger.info("Already at commit %s", sha[:8])
            return True

        # Revert each commit in reverse order (newest first)
        for commit in commits_to_revert:
            stdout, stderr, code = await self._run_git(
                "revert",
                "--no-commit",
                commit,
            )

            if code != 0:
                # If revert fails, abort and reset
                await self._run_git("revert", "--abort")
                logger.error("Revert failed at %s: %s", commit[:8], stderr)
                return False

        # Commit the combined revert
        result = await self.commit(f"Rollback to {sha[:8]}")
        return result.get("status") == "ok"
