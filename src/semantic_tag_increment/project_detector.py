# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Project detection engine module.

This module provides functionality to detect project types by scanning
for project files and matching them against the project mappings database.
"""

import fnmatch
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from .config import get_config_manager
from .exceptions import ProjectDetectionError
from .project_mappings import ProjectMapping, get_database

logger = logging.getLogger(__name__)


class ProjectDetector:
    """
    Detects project types by scanning for project files and matching patterns.

    Uses the project mappings database to identify project types based on
    file patterns and provides methods to search for project files efficiently.
    """

    def __init__(self, path: str = ".", max_depth: int = 3, max_files: int = 1000):
        """
        Initialize the project detector.

        Args:
            path: The directory path to scan for project files
            max_depth: Maximum directory depth to scan (security limit)
            max_files: Maximum number of files to examine (security limit)
        """
        self.path = Path(path).resolve()
        self.max_depth = max_depth
        self.max_files = max_files
        self._validate_path()

        # Load project mappings
        self.database = get_database()
        self.database.load_default_mappings()

        # Load user-defined mappings
        try:
            config_manager = get_config_manager()
            user_mappings = config_manager.load_user_project_mappings()
            for mapping in user_mappings:
                self.database.add_mapping(mapping)
        except Exception as e:
            logger.debug(f"Failed to load user project mappings: {e}")

        # Cache for file existence checks
        self._file_cache: Dict[str, bool] = {}

    def _validate_path(self) -> None:
        """Validate the path for security and existence."""
        if not self.path.exists():
            raise ProjectDetectionError(f"Path does not exist: {self.path}")

        if not self.path.is_dir():
            raise ProjectDetectionError(f"Path is not a directory: {self.path}")

        # Security check: ensure path is not too deep or contains suspicious patterns
        try:
            self.path.resolve(strict=True)
        except (OSError, RuntimeError) as e:
            raise ProjectDetectionError(f"Invalid or inaccessible path: {e}")

    def find_project_files(self) -> List[Tuple[str, ProjectMapping]]:
        """
        Find all project files in the target directory.

        Returns:
            List of tuples containing (file_path, matching_mapping)

        Raises:
            ProjectDetectionError: If scanning fails
        """
        found_files = []
        all_mappings = self.database.get_all_mappings()

        logger.debug(f"Scanning {self.path} for project files using {len(all_mappings)} mappings")

        try:
            # Get all files in the directory (respecting limits)
            all_files = self._get_all_files()

            # Check each mapping against the found files
            for mapping in all_mappings:
                for pattern in mapping.patterns:
                    matching_files = self._find_files_matching_pattern(all_files, pattern)

                    for file_path in matching_files:
                        found_files.append((file_path, mapping))
                        logger.debug(f"Found project file: {file_path} ({mapping.name})")

        except Exception as e:
            raise ProjectDetectionError(f"Failed to scan for project files: {e}")

        # Sort by mapping priority (lower priority number = higher priority)
        found_files.sort(key=lambda x: x[1].priority)

        logger.info(f"Found {len(found_files)} project files")
        return found_files

    def find_first_project_file(self) -> Optional[Tuple[str, ProjectMapping]]:
        """
        Find the first (highest priority) project file.

        Returns:
            Tuple of (file_path, matching_mapping) or None if no files found
        """
        all_mappings = self.database.get_all_mappings()

        logger.debug(f"Searching for first project file in {self.path}")

        try:
            # Get all files once
            all_files = self._get_all_files()

            # Check mappings in priority order
            for mapping in all_mappings:
                for pattern in mapping.patterns:
                    matching_files = self._find_files_matching_pattern(all_files, pattern)

                    if matching_files:
                        first_file = matching_files[0]
                        logger.debug(f"First project file found: {first_file} ({mapping.name})")
                        return (first_file, mapping)

        except Exception as e:
            logger.warning(f"Failed to find first project file: {e}")
            return None

        logger.debug("No project files found")
        return None

    def detect_project_types(self) -> List[Dict[str, Any]]:
        """
        Detect all project types in the target directory.

        Returns:
            List of dictionaries containing project type information
        """
        project_files = self.find_project_files()

        # Group by project type
        project_types: Dict[str, Dict[str, Any]] = {}
        for file_path, mapping in project_files:
            if mapping.name not in project_types:
                project_types[mapping.name] = {
                    'name': mapping.name,
                    'priority': mapping.priority,
                    'description': mapping.description,
                    'files': [],
                    'mapping': mapping
                }
            project_types[mapping.name]['files'].append(file_path)

        # Convert to list and sort by priority
        result = list(project_types.values())
        result.sort(key=lambda x: x['priority'])

        return result

    def _get_all_files(self) -> List[str]:
        """
        Get all files in the directory tree (respecting limits).

        Returns:
            List of file paths relative to the scan directory
        """
        all_files = []
        files_examined = 0

        try:
            for root, dirs, files in os.walk(self.path):
                # Calculate current depth
                current_depth = len(Path(root).relative_to(self.path).parts)

                # Skip if too deep
                if current_depth > self.max_depth:
                    dirs.clear()  # Don't recurse deeper
                    continue

                # Skip hidden directories and common non-project directories
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in {
                    '__pycache__', 'node_modules', 'vendor', 'build', 'dist',
                    'target', '.git', '.svn', '.hg', 'coverage', 'htmlcov'
                }]

                for file in files:
                    # Skip hidden files
                    if file.startswith('.'):
                        continue

                    files_examined += 1
                    if files_examined > self.max_files:
                        logger.warning(f"File limit ({self.max_files}) reached, stopping scan")
                        break

                    file_path = Path(root) / file
                    relative_path = file_path.relative_to(self.path)
                    all_files.append(str(relative_path))

                if files_examined > self.max_files:
                    break

        except Exception as e:
            logger.warning(f"Error during file enumeration: {e}")

        logger.debug(f"Found {len(all_files)} files to examine")
        return all_files

    def _find_files_matching_pattern(self, all_files: List[str], pattern: str) -> List[str]:
        """
        Find files matching a specific pattern.

        Args:
            all_files: List of all files to search in
            pattern: The pattern to match against

        Returns:
            List of file paths matching the pattern
        """
        matching_files = []

        # Handle different pattern types
        if '*' in pattern:
            # Glob pattern
            for file_path in all_files:
                if fnmatch.fnmatch(file_path, pattern) or fnmatch.fnmatch(os.path.basename(file_path), pattern):
                    full_path = self.path / file_path
                    if full_path.exists() and full_path.is_file():
                        matching_files.append(str(file_path))
        else:
            # Exact match
            if pattern in all_files:
                full_path = self.path / pattern
                if full_path.exists() and full_path.is_file():
                    matching_files.append(pattern)
            else:
                # Also check for exact filename matches in subdirectories
                for file_path in all_files:
                    if os.path.basename(file_path) == pattern:
                        full_path = self.path / file_path
                        if full_path.exists() and full_path.is_file():
                            matching_files.append(str(file_path))

        return matching_files

    def get_file_path(self, relative_path: str) -> Path:
        """
        Get the full path for a relative file path.

        Args:
            relative_path: Relative path from the scan directory

        Returns:
            Full Path object
        """
        return self.path / relative_path

    def is_project_directory(self) -> bool:
        """
        Check if the target directory appears to be a project directory.

        Returns:
            True if project files are found, False otherwise
        """
        return bool(self.find_first_project_file())

    def get_project_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the project detection results.

        Returns:
            Dictionary with project summary information
        """
        project_types = self.detect_project_types()

        summary = {
            'path': str(self.path),
            'is_project': bool(project_types),
            'project_types_count': len(project_types),
            'project_types': project_types,
            'primary_type': project_types[0] if project_types else None,
            'scan_limits': {
                'max_depth': self.max_depth,
                'max_files': self.max_files
            }
        }

        return summary

    def get_recommended_files(self, limit: int = 5) -> List[Tuple[str, ProjectMapping]]:
        """
        Get recommended project files for version extraction.

        Args:
            limit: Maximum number of files to return

        Returns:
            List of (file_path, mapping) tuples, ordered by priority
        """
        all_files = self.find_project_files()

        # Take only the highest priority files
        recommended = []
        seen_types = set()

        for file_path, mapping in all_files:
            # Skip if we've already seen this project type
            if mapping.name in seen_types:
                continue

            recommended.append((file_path, mapping))
            seen_types.add(mapping.name)

            if len(recommended) >= limit:
                break

        return recommended

    def clear_cache(self) -> None:
        """Clear the internal file cache."""
        self._file_cache.clear()
