# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Version source abstraction module.

This module provides abstractions for different sources of version information,
whether from explicit string input or extracted from project files.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from .parser import SemanticVersion

logger = logging.getLogger(__name__)


@dataclass
class VersionExtractionResult:
    """
    Result of version extraction from a project file.

    Contains the extracted version along with metadata about the source.
    """
    version: SemanticVersion
    source_file: str
    source_pattern: str
    project_type: str
    confidence: float = 1.0  # Confidence score (0.0-1.0)

    def __str__(self) -> str:
        return f"Version {self.version} from {self.source_file} ({self.project_type})"


class VersionSource(ABC):
    """
    Abstract base class for version sources.

    Defines the interface for obtaining version information from different sources.
    """

    @abstractmethod
    def get_version(self) -> SemanticVersion:
        """
        Get the semantic version from this source.

        Returns:
            SemanticVersion object

        Raises:
            Exception: If version cannot be obtained from this source
        """
        pass

    @abstractmethod
    def get_source_description(self) -> str:
        """
        Get a human-readable description of this version source.

        Returns:
            Description string
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if this version source is available/valid.

        Returns:
            True if the source is available, False otherwise
        """
        pass


class StringVersionSource(VersionSource):
    """
    Version source that uses an explicit string input.

    This is the traditional mode where the user provides the version string directly.
    """

    def __init__(self, version_string: str):
        """
        Initialize with a version string.

        Args:
            version_string: The version string to parse
        """
        self.version_string = version_string
        self._parsed_version: Optional[SemanticVersion] = None

    def get_version(self) -> SemanticVersion:
        """Get the semantic version from the string input."""
        if self._parsed_version is None:
            self._parsed_version = SemanticVersion.parse(self.version_string)
            logger.debug(f"Parsed version from string: {self._parsed_version}")
        return self._parsed_version

    def get_source_description(self) -> str:
        """Get description of this version source."""
        return f"Explicit string input: '{self.version_string}'"

    def is_available(self) -> bool:
        """Check if the string version source is available."""
        if not self.version_string or not self.version_string.strip():
            return False

        try:
            # Try to parse the version to check validity
            SemanticVersion.parse(self.version_string)
            return True
        except Exception:
            return False


class ExtractedVersionSource(VersionSource):
    """
    Version source that extracts version from project files.

    This source uses the project detection system to find and extract
    version information from various project file types.
    """

    def __init__(self, extraction_result: VersionExtractionResult):
        """
        Initialize with an extraction result.

        Args:
            extraction_result: The result of version extraction
        """
        self.extraction_result = extraction_result

    def get_version(self) -> SemanticVersion:
        """Get the semantic version from the extraction result."""
        logger.debug(f"Using extracted version: {self.extraction_result}")
        return self.extraction_result.version

    def get_source_description(self) -> str:
        """Get description of this version source."""
        return (
            f"Extracted from {self.extraction_result.source_file} "
            f"({self.extraction_result.project_type})"
        )

    def is_available(self) -> bool:
        """Check if the extracted version source is available."""
        return (
            self.extraction_result is not None and
            self.extraction_result.version is not None
        )

    def get_extraction_details(self) -> VersionExtractionResult:
        """Get the detailed extraction result."""
        return self.extraction_result


class CompositeVersionSource(VersionSource):
    """
    Version source that can fall back between multiple sources.

    Useful for auto mode where we might have both explicit input and
    extracted versions available.
    """

    def __init__(self, primary_source: VersionSource, fallback_source: Optional[VersionSource] = None):
        """
        Initialize with primary and optional fallback sources.

        Args:
            primary_source: The primary version source to use
            fallback_source: Optional fallback source if primary fails
        """
        self.primary_source = primary_source
        self.fallback_source = fallback_source
        self._active_source: Optional[VersionSource] = None

    def get_version(self) -> SemanticVersion:
        """Get version from the available source."""
        if self._active_source is None:
            self._determine_active_source()

        if self._active_source is None:
            raise RuntimeError("No available version source")

        return self._active_source.get_version()

    def get_source_description(self) -> str:
        """Get description of the active version source."""
        if self._active_source is None:
            self._determine_active_source()

        if self._active_source is None:
            return "No available version source"

        return self._active_source.get_source_description()

    def is_available(self) -> bool:
        """Check if any version source is available."""
        return (
            self.primary_source.is_available() or
            (self.fallback_source is not None and self.fallback_source.is_available())
        )

    def _determine_active_source(self) -> None:
        """Determine which source to use based on availability."""
        if self.primary_source.is_available():
            self._active_source = self.primary_source
            logger.debug(f"Using primary version source: {self.primary_source.get_source_description()}")
        elif self.fallback_source is not None and self.fallback_source.is_available():
            self._active_source = self.fallback_source
            logger.debug(f"Using fallback version source: {self.fallback_source.get_source_description()}")
            logger.warning("Primary version source not available, using fallback")
        else:
            logger.error("No available version sources")

    def get_active_source(self) -> Optional[VersionSource]:
        """Get the currently active version source."""
        if self._active_source is None:
            self._determine_active_source()
        return self._active_source


class VersionSourceFactory:
    """
    Factory for creating appropriate version sources based on mode and inputs.
    """

    @staticmethod
    def create_string_source(version_string: str) -> StringVersionSource:
        """
        Create a string version source.

        Args:
            version_string: The version string

        Returns:
            StringVersionSource instance
        """
        return StringVersionSource(version_string)

    @staticmethod
    def create_extracted_source(extraction_result: VersionExtractionResult) -> ExtractedVersionSource:
        """
        Create an extracted version source.

        Args:
            extraction_result: The extraction result

        Returns:
            ExtractedVersionSource instance
        """
        return ExtractedVersionSource(extraction_result)

    @staticmethod
    def create_composite_source(
        primary_source: VersionSource,
        fallback_source: Optional[VersionSource] = None
    ) -> CompositeVersionSource:
        """
        Create a composite version source.

        Args:
            primary_source: The primary version source
            fallback_source: Optional fallback source

        Returns:
            CompositeVersionSource instance
        """
        return CompositeVersionSource(primary_source, fallback_source)

    @staticmethod
    def create_auto_source(
        version_string: Optional[str] = None,
        extraction_result: Optional[VersionExtractionResult] = None
    ) -> VersionSource:
        """
        Create an appropriate version source for auto mode.

        Args:
            version_string: Optional explicit version string
            extraction_result: Optional extraction result

        Returns:
            Appropriate VersionSource instance

        Raises:
            ValueError: If no valid source can be created
        """
        string_source = None
        extracted_source = None

        if version_string and version_string.strip():
            string_source = VersionSourceFactory.create_string_source(version_string)

        if extraction_result:
            extracted_source = VersionSourceFactory.create_extracted_source(extraction_result)

        # In auto mode, explicit string takes precedence over extracted
        if string_source and string_source.is_available():
            if extracted_source and extracted_source.is_available():
                logger.info("Auto mode: Using explicit string input, extracted version available as fallback")
                return VersionSourceFactory.create_composite_source(string_source, extracted_source)
            else:
                return string_source
        elif extracted_source and extracted_source.is_available():
            return extracted_source
        else:
            raise ValueError("No valid version source available for auto mode")
