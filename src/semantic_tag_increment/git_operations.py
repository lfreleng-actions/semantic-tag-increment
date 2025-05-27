# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Git operations module.

This module handles all Git-related operations, including retrieving existing tags
and other repository interactions using GitPython for native Git operations.
"""

import logging
import os
from typing import Set, Optional

from .exceptions import ErrorReporter, GitOperationError, SecurityError

# Import GitPython (required dependency)
import git
from git.exc import GitCommandError, InvalidGitRepositoryError

logger = logging.getLogger(__name__)

# Constants
NO_CONFLICT_CHECK_MSG = "Proceeding without conflict checking"


class GitOperations:
    """Handles Git repository operations."""

    # Default fetch timeout in seconds
    DEFAULT_FETCH_TIMEOUT = 120

    # Class-level cache for tag operations
    _tag_cache: dict[str, set[str]] = {}
    _cache_enabled: bool = True

    @staticmethod
    def _validate_path(path: str) -> str:
        """
        Validate and sanitize path to prevent path traversal.

        Args:
            path: The path to validate

        Returns:
            Absolute path if valid

        Raises:
            ValueError: If path is invalid or doesn't exist
        """
        if not path or not isinstance(path, str):
            ErrorReporter.log_and_raise_security_error(
                "Path must be a non-empty string",
                "path_type_validation",
                str(path)
            )

        # Resolve to absolute path and check if it exists
        abs_path = os.path.abspath(path)
        if not os.path.exists(abs_path):
            ErrorReporter.log_and_raise_security_error(
                f"Path does not exist: {path}",
                "path_existence_validation",
                path
            )
        if not os.path.isdir(abs_path):
            ErrorReporter.log_and_raise_security_error(
                f"Path is not a directory: {path}",
                "path_directory_validation",
                path
            )
        return abs_path

    @staticmethod
    def get_existing_tags(path_prefix: str = ".", fetch_remote: bool = True, use_cache: bool = True, timeout: Optional[int] = None) -> Set[str]:
        """
        Get existing git tags from the repository.

        Args:
            path_prefix: Directory path containing the git repository
            fetch_remote: Whether to fetch tags from remote repository
            use_cache: Whether to use cached results if available
            timeout: Timeout in seconds for remote fetch operations (defaults to DEFAULT_FETCH_TIMEOUT)

        Returns:
            Set of existing git tags, or empty set if unable to retrieve
        """
        try:
            # Validate path for security
            validated_path = GitOperations._validate_path(path_prefix)
        except SecurityError as e:
            logger.warning(f"Invalid path provided: {e}")
            logger.info(NO_CONFLICT_CHECK_MSG)
            return set()

        # Check cache first if enabled
        cache_key = f"{validated_path}:{fetch_remote}:{timeout}"
        if use_cache and GitOperations._cache_enabled and cache_key in GitOperations._tag_cache:
            logger.debug(f"Using cached tags for {validated_path}")
            return GitOperations._tag_cache[cache_key]

        tags = GitOperations._get_tags_with_gitpython(validated_path, fetch_remote, timeout)

        # Cache the results if enabled
        if use_cache and GitOperations._cache_enabled:
            GitOperations._tag_cache[cache_key] = tags
            logger.debug(f"Cached {len(tags)} tags for {validated_path}")

        return tags

    @staticmethod
    def _get_tags_with_gitpython(path_prefix: str, fetch_remote: bool = True, timeout: Optional[int] = None) -> Set[str]:
        """Get tags using GitPython library."""
        try:
            # Try to open the repository
            repo = git.Repo(path_prefix, search_parent_directories=True)

            # Conditionally fetch tags from remote
            if fetch_remote and repo.remotes:
                try:
                    fetch_timeout = timeout if timeout is not None else GitOperations.DEFAULT_FETCH_TIMEOUT
                    repo.remotes.origin.fetch(tags=True, timeout=fetch_timeout)
                    logger.debug("Fetched latest tags from remote")
                except Exception as e:
                    logger.debug(f"Could not fetch tags from remote: {e}")

            # Get all tags
            tags = set()
            for tag_ref in repo.tags:
                tags.add(tag_ref.name)

            logger.debug(f"Found {len(tags)} existing git tags using GitPython")
            return tags

        except InvalidGitRepositoryError:
            logger.warning(f"Not a git repository: {path_prefix}")
            logger.info(NO_CONFLICT_CHECK_MSG)
            return set()
        except GitCommandError as e:
            logger.warning(f"Git command failed: {e}")
            logger.info(NO_CONFLICT_CHECK_MSG)
            return set()
        except Exception as e:
            # Convert unexpected errors to GitOperationError for better tracking
            git_error = GitOperationError(
                f"Failed to retrieve git tags with GitPython: {str(e)}",
                details={
                    "original_error_type": type(e).__name__,
                    "path": path_prefix,
                    "operation": "get_tags_with_gitpython"
                }
            )
            logger.warning(f"Git operation failed: {git_error}")
            logger.info(NO_CONFLICT_CHECK_MSG)
            return set()

    @staticmethod
    def is_git_repository(path_prefix: str = ".") -> bool:
        """
        Check if the specified directory is a Git repository.

        Args:
            path_prefix: Directory path to check

        Returns:
            True if in a Git repository, False otherwise
        """
        try:
            # Validate path for security
            validated_path = GitOperations._validate_path(path_prefix)
        except SecurityError:
            return False

        return GitOperations._is_git_repo_with_gitpython(validated_path)

    @staticmethod
    def _is_git_repo_with_gitpython(path_prefix: str) -> bool:
        """Check if directory is a Git repository using GitPython."""
        try:
            git.Repo(path_prefix, search_parent_directories=True)
            return True
        except (InvalidGitRepositoryError, Exception):
            return False

    @staticmethod
    def clear_cache() -> None:
        """Clear the tag cache."""
        GitOperations._tag_cache.clear()
        logger.debug("Git tag cache cleared")

    @staticmethod
    def disable_cache() -> None:
        """Disable tag caching."""
        GitOperations._cache_enabled = False
        GitOperations.clear_cache()
        logger.debug("Git tag caching disabled")

    @staticmethod
    def enable_cache() -> None:
        """Enable tag caching."""
        GitOperations._cache_enabled = True
        logger.debug("Git tag caching enabled")
