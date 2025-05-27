# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Version extraction engine module.

This module provides functionality to extract version information from project files
using regex patterns and handles various file formats and encoding issues.
"""

import logging
import re
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any

from .exceptions import VersionExtractionError
from .parser import SemanticVersion
from .project_mappings import ProjectMapping
from .version_source import VersionExtractionResult

logger = logging.getLogger(__name__)


class VersionExtractor:
    """
    Extracts version information from project files using regex patterns.

    Handles various file formats, encoding issues, and provides confidence scoring
    for extracted versions based on pattern matching and validation.
    """

    def __init__(self, max_file_size: int = 1024 * 1024):  # 1MB default
        """
        Initialize the version extractor.

        Args:
            max_file_size: Maximum file size to process (security limit)
        """
        self.max_file_size = max_file_size

    def extract_version_from_file(
        self,
        file_path: str,
        mapping: ProjectMapping
    ) -> Optional[VersionExtractionResult]:
        """
        Extract version information from a single file using a project mapping.

        Args:
            file_path: Path to the file to extract version from
            mapping: ProjectMapping containing regex patterns to use

        Returns:
            VersionExtractionResult if version found, None otherwise
        """
        path = Path(file_path)

        if not path.exists():
            logger.debug(f"File does not exist: {file_path}")
            return None

        if not path.is_file():
            logger.debug(f"Path is not a file: {file_path}")
            return None

        # Check file size
        try:
            file_size = path.stat().st_size
            if file_size > self.max_file_size:
                logger.warning(f"File too large ({file_size} bytes), skipping: {file_path}")
                return None
        except OSError as e:
            logger.debug(f"Cannot stat file {file_path}: {e}")
            return None

        # Read file content
        try:
            content = self._read_file_content(path, mapping.file_encoding)
        except Exception as e:
            logger.debug(f"Failed to read file {file_path}: {e}")
            return None

        # Extract version using regex patterns
        for pattern in mapping.regex:
            try:
                result = self._extract_version_with_pattern(
                    content, pattern, file_path, mapping
                )
                if result:
                    logger.debug(f"Extracted version from {file_path}: {result.version}")
                    return result
            except Exception as e:
                logger.debug(f"Pattern {pattern} failed for {file_path}: {e}")
                continue

        logger.debug(f"No version found in {file_path}")
        return None

    def extract_versions_from_files(
        self,
        file_mappings: List[Tuple[str, ProjectMapping]]
    ) -> List[VersionExtractionResult]:
        """
        Extract versions from multiple files.

        Args:
            file_mappings: List of (file_path, mapping) tuples

        Returns:
            List of VersionExtractionResult objects
        """
        results = []

        for file_path, mapping in file_mappings:
            try:
                result = self.extract_version_from_file(file_path, mapping)
                if result:
                    results.append(result)
            except Exception as e:
                logger.debug(f"Failed to extract version from {file_path}: {e}")
                continue

        return results

    def find_best_version(
        self,
        file_mappings: List[Tuple[str, ProjectMapping]]
    ) -> Optional[VersionExtractionResult]:
        """
        Find the best version from multiple files based on priority and confidence.

        Args:
            file_mappings: List of (file_path, mapping) tuples

        Returns:
            Best VersionExtractionResult or None if no versions found
        """
        all_results = self.extract_versions_from_files(file_mappings)

        if not all_results:
            return None

        # Sort by confidence (higher is better)
        all_results.sort(key=lambda r: -r.confidence)

        # Get the mapping for the best result
        best_result = all_results[0]

        # Find the corresponding mapping
        for file_path, mapping in file_mappings:
            if file_path == best_result.source_file:
                # Create a new result with the mapping reference
                return VersionExtractionResult(
                    version=best_result.version,
                    source_file=best_result.source_file,
                    source_pattern=best_result.source_pattern,
                    project_type=best_result.project_type,
                    confidence=best_result.confidence
                )

        return best_result

    def _read_file_content(self, path: Path, encoding: str) -> str:
        """
        Read file content with encoding handling.

        Args:
            path: Path to the file
            encoding: Preferred encoding

        Returns:
            File content as string

        Raises:
            VersionExtractionError: If file cannot be read
        """
        encodings_to_try = [encoding, 'utf-8', 'utf-16', 'latin-1']

        for enc in encodings_to_try:
            try:
                with open(path, 'r', encoding=enc) as f:
                    return f.read()
            except (UnicodeDecodeError, UnicodeError):
                continue
            except Exception as e:
                raise VersionExtractionError(f"Failed to read file {path}: {e}")

        raise VersionExtractionError(f"Could not decode file {path} with any encoding")

    def _extract_version_with_pattern(
        self,
        content: str,
        pattern: str,
        file_path: str,
        mapping: ProjectMapping
    ) -> Optional[VersionExtractionResult]:
        """
        Extract version using a specific regex pattern.

        Args:
            content: File content to search in
            pattern: Regex pattern to use
            file_path: Path to the source file
            mapping: ProjectMapping for context

        Returns:
            VersionExtractionResult if version found, None otherwise
        """
        try:
            # Compile regex with appropriate flags
            flags = re.MULTILINE if mapping.multiline else 0
            if not mapping.case_sensitive:
                flags |= re.IGNORECASE

            regex = re.compile(pattern, flags)

            # Find all matches
            matches = regex.findall(content)

            if not matches:
                return None

            # Take the first match (or most relevant one)
            version_string = matches[0]

            # If the match is a tuple (multiple groups), take the first group
            if isinstance(version_string, tuple):
                version_string = version_string[0]

            # Clean up the version string
            version_string = version_string.strip()

            if not version_string:
                return None

            # Try to parse as semantic version
            try:
                semantic_version = SemanticVersion.parse(version_string)
            except Exception as e:
                logger.debug(f"Failed to parse version '{version_string}' from {file_path}: {e}")
                return None

            # Calculate confidence score
            confidence = self._calculate_confidence(
                version_string, pattern, content, len(matches)
            )

            return VersionExtractionResult(
                version=semantic_version,
                source_file=file_path,
                source_pattern=pattern,
                project_type=mapping.name,
                confidence=confidence
            )

        except re.error as e:
            logger.debug(f"Invalid regex pattern '{pattern}': {e}")
            return None
        except Exception as e:
            logger.debug(f"Error extracting version with pattern '{pattern}': {e}")
            return None

    def _calculate_confidence(
        self,
        version_string: str,
        pattern: str,
        content: str,
        match_count: int
    ) -> float:
        """
        Calculate confidence score for an extracted version.

        Args:
            version_string: The extracted version string
            pattern: The regex pattern used
            content: The full file content
            match_count: Number of matches found

        Returns:
            Confidence score between 0.0 and 1.0
        """
        confidence = 0.5  # Base confidence

        # Higher confidence for semantic version patterns
        if re.match(r'^\d+\.\d+\.\d+', version_string):
            confidence += 0.2

        # Higher confidence for specific patterns
        if 'version' in pattern.lower():
            confidence += 0.1

        # Lower confidence for multiple matches (ambiguous)
        if match_count > 1:
            confidence -= 0.1

        # Higher confidence for patterns that match typical version contexts
        version_contexts = [
            r'"version":', r'version\s*=', r'<version>', r'VERSION\s*=',
            r'__version__', r'version:', r'appVersion:'
        ]

        for context in version_contexts:
            if re.search(context, content, re.IGNORECASE):
                confidence += 0.05
                break

        # Higher confidence for well-formed semantic versions
        if re.match(r'^\d+\.\d+\.\d+(?:-[a-zA-Z0-9.-]+)?(?:\+[a-zA-Z0-9.-]+)?$', version_string):
            confidence += 0.1

        # Clamp confidence to valid range
        return max(0.0, min(1.0, confidence))

    def validate_extracted_version(self, result: VersionExtractionResult) -> bool:
        """
        Validate an extracted version result.

        Args:
            result: The VersionExtractionResult to validate

        Returns:
            True if the result is valid, False otherwise
        """
        try:
            # Check if version is valid
            if not result.version:
                return False

            # Check if source file exists
            if not Path(result.source_file).exists():
                return False

            # Check confidence threshold
            if result.confidence < 0.1:  # Minimum confidence threshold
                return False

            # Try to re-parse the version to ensure it's still valid
            SemanticVersion.parse(str(result.version))

            return True

        except Exception as e:
            logger.debug(f"Validation failed for {result}: {e}")
            return False

    def get_extraction_summary(
        self,
        file_mappings: List[Tuple[str, ProjectMapping]]
    ) -> Dict[str, Any]:
        """
        Get a summary of version extraction results.

        Args:
            file_mappings: List of (file_path, mapping) tuples

        Returns:
            Dictionary with extraction summary
        """
        all_results = self.extract_versions_from_files(file_mappings)

        summary = {
            'total_files_checked': len(file_mappings),
            'versions_found': len(all_results),
            'success_rate': len(all_results) / len(file_mappings) if file_mappings else 0.0,
            'results': []
        }

        results_list: List[Dict[str, Any]] = []
        for result in all_results:
            results_list.append({
                'version': str(result.version),
                'source_file': result.source_file,
                'project_type': result.project_type,
                'confidence': result.confidence,
                'pattern': result.source_pattern
            })

        summary['results'] = results_list

        # Sort results by confidence
        results_list.sort(key=lambda x: x['confidence'], reverse=True)

        return summary

    def extract_version_with_fallback(
        self,
        file_mappings: List[Tuple[str, ProjectMapping]],
        fallback_patterns: Optional[List[str]] = None
    ) -> Optional[VersionExtractionResult]:
        """
        Extract version with fallback patterns if primary extraction fails.

        Args:
            file_mappings: List of (file_path, mapping) tuples
            fallback_patterns: Optional list of fallback regex patterns

        Returns:
            VersionExtractionResult if any version found, None otherwise
        """
        # Try primary extraction first
        result = self.find_best_version(file_mappings)
        if result:
            return result

        # If no fallback patterns provided, use default ones
        if fallback_patterns is None:
            fallback_patterns = [
                r'version["\']?\s*[:=]\s*["\']?([0-9]+\.[0-9]+\.[0-9]+[^"\'\\s]*)',
                r'["\']version["\']\s*:\s*["\']([^"\']+)["\']',
                r'VERSION\s*=\s*["\']([^"\']+)["\']',
                r'__version__\s*=\s*["\']([^"\']+)["\']',
                r'([0-9]+\.[0-9]+\.[0-9]+(?:-[a-zA-Z0-9.-]+)?(?:\+[a-zA-Z0-9.-]+)?)'
            ]

        # Try fallback patterns on all files
        for file_path, mapping in file_mappings:
            try:
                path = Path(file_path)
                if not path.exists():
                    continue

                content = self._read_file_content(path, mapping.file_encoding)

                for pattern in fallback_patterns:
                    try:
                        result = self._extract_version_with_pattern(
                            content, pattern, file_path, mapping
                        )
                        if result:
                            # Mark as fallback result
                            result.confidence *= 0.5  # Reduce confidence for fallback
                            logger.debug(f"Fallback extraction successful: {result.version}")
                            return result
                    except Exception:
                        continue

            except Exception as e:
                logger.debug(f"Fallback extraction failed for {file_path}: {e}")
                continue

        return None
