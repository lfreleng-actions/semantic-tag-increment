# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Version Incrementer.

This module provides intelligent version incrementing logic for semantic versions,
including smart pre-release handling and various increment strategies.
"""

import logging
import re
from enum import Enum

from .parser import SemanticVersion

logger = logging.getLogger(__name__)


class IncrementType(Enum):
    """Supported version increment types."""

    MAJOR = "major"
    MINOR = "minor"
    PATCH = "patch"
    PRERELEASE = "prerelease"
    DEV = "dev"  # Alias for prerelease for backwards compatibility


class VersionIncrementer:
    """
    Handles intelligent incrementing of semantic versions.

    Supports major, minor, patch, and intelligent pre-release incrementing
    with preservation of metadata and smart handling of complex pre-release
    patterns.
    """

    # Safety limits to prevent infinite loops and excessive search attempts
    MAX_PATCH_ATTEMPTS = 100  # For searching available patch versions
    MAX_PRERELEASE_ATTEMPTS = 1000  # For searching available prerelease versions

    def __init__(self, existing_tags: set[str] | None = None, preserve_metadata: bool = False):
        """
        Initialize the version incrementer.

        Args:
            existing_tags: Set of existing version tags to avoid conflicts
            preserve_metadata: Whether to preserve build metadata during increments
        """
        self.existing_tags = existing_tags or set()
        self.preserve_metadata = preserve_metadata
        # Cache normalized tags for performance optimization
        self._normalized_tags_cache: set[str] | None = None

    def increment(
        self,
        version: SemanticVersion,
        increment_type: IncrementType,
        prerelease_type: str | None = None,
    ) -> SemanticVersion:
        """
        Increment a semantic version based on the specified increment type.

        Args:
            version: The version to increment
            increment_type: The type of increment to perform
            prerelease_type: Optional prerelease identifier for new prereleases

        Returns:
            New incremented SemanticVersion
        """
        if increment_type == IncrementType.MAJOR:
            return self._increment_major(version)
        elif increment_type == IncrementType.MINOR:
            return self._increment_minor(version)
        elif increment_type == IncrementType.PATCH:
            return self._increment_patch(version, prerelease_type or "dev")
        elif increment_type in (IncrementType.PRERELEASE, IncrementType.DEV):
            return self._increment_prerelease(version, prerelease_type)
        else:
            raise ValueError(f"Unsupported increment type: {increment_type}")

    def _increment_major(self, version: SemanticVersion) -> SemanticVersion:
        """Increment the major version and reset minor and patch."""
        candidate = SemanticVersion(
            major=version.major + 1,
            minor=0,
            patch=0,
            prerelease=None,
            metadata=version.metadata if self.preserve_metadata else None,
            prefix=version.prefix,
        )

        # Check for conflicts with existing tags
        if self._version_exists(candidate):
            # If a conflict exists, try incrementing the patch version
            for patch in range(1, self.MAX_PATCH_ATTEMPTS):
                next_candidate = SemanticVersion(
                    major=candidate.major,
                    minor=candidate.minor,
                    patch=patch,
                    prerelease=None,
                    metadata=version.metadata if self.preserve_metadata else None,
                    prefix=version.prefix,
                )
                if not self._version_exists(next_candidate):
                    return next_candidate

            # If no available version found, try prerelease versions
            return self._find_next_available_prerelease_for_conflict(
                candidate, "dev"
            )

        return candidate

    def _increment_minor(self, version: SemanticVersion) -> SemanticVersion:
        """Increment the minor version and reset patch."""
        candidate = SemanticVersion(
            major=version.major,
            minor=version.minor + 1,
            patch=0,
            prerelease=None,
            metadata=version.metadata if self.preserve_metadata else None,
            prefix=version.prefix,
        )

        # Check for conflicts with existing tags
        if self._version_exists(candidate):
            # If a conflict exists, try incrementing the patch version
            for patch in range(1, self.MAX_PATCH_ATTEMPTS):
                next_candidate = SemanticVersion(
                    major=candidate.major,
                    minor=candidate.minor,
                    patch=patch,
                    prerelease=None,
                    metadata=version.metadata if self.preserve_metadata else None,
                    prefix=version.prefix,
                )
                if not self._version_exists(next_candidate):
                    return next_candidate

            # If no available version found, try prerelease versions
            return self._find_next_available_prerelease_for_conflict(
                candidate, "dev"
            )

        return candidate

    def _increment_patch(
        self, version: SemanticVersion, prerelease_type: str = "dev"
    ) -> SemanticVersion:
        """Increment the patch version and reset prerelease."""
        candidate = self._create_patch_candidate(version)

        if not self._version_exists(candidate):
            return candidate

        return self._resolve_patch_conflict(version, prerelease_type)

    def _create_patch_candidate(self, version: SemanticVersion) -> SemanticVersion:
        """Create a candidate patch version."""
        return SemanticVersion(
            major=version.major,
            minor=version.minor,
            patch=version.patch + 1,
            prerelease=None,
            metadata=version.metadata if self.preserve_metadata else None,
            prefix=version.prefix,
        )

    def _resolve_patch_conflict(
        self, version: SemanticVersion, prerelease_type: str
    ) -> SemanticVersion:
        """Resolve conflicts when incrementing patch version."""
        # Try finding next available patch number
        next_patch = self._find_next_available_patch(version)
        if next_patch:
            return next_patch

        # Fall back to prerelease version
        return self._create_conflict_prerelease(version, prerelease_type)

    def _find_next_available_patch(
        self, version: SemanticVersion
    ) -> SemanticVersion | None:
        """Find the next available patch version using optimized search."""
        # Get existing patch versions for this major.minor
        existing_patches = self._get_existing_patches(version.major, version.minor)

        # Find first gap in sequence starting from patch + 1
        patch = version.patch + 1
        max_patch = version.patch + self.MAX_PATCH_ATTEMPTS

        while patch <= max_patch:
            if patch not in existing_patches:
                candidate = SemanticVersion(
                    major=version.major,
                    minor=version.minor,
                    patch=patch,
                    prerelease=None,
                    metadata=version.metadata if self.preserve_metadata else None,
                    prefix=version.prefix,
                )
                # Double-check with full version string matching
                if not self._version_exists(candidate):
                    return candidate
            patch += 1

        return None

    def _create_conflict_prerelease(
        self, version: SemanticVersion, prerelease_type: str
    ) -> SemanticVersion:
        """Create a prerelease version to resolve conflicts."""
        base_version = SemanticVersion(
            major=version.major,
            minor=version.minor,
            patch=version.patch + 1,
            prerelease=None,
            metadata=version.metadata if self.preserve_metadata else None,
            prefix=version.prefix,
        )

        prerelease_candidate = SemanticVersion(
            major=base_version.major,
            minor=base_version.minor,
            patch=base_version.patch,
            prerelease=f"{prerelease_type}.1",
            metadata=base_version.metadata if self.preserve_metadata else None,
            prefix=base_version.prefix,
        )

        if not self._version_exists(prerelease_candidate):
            return prerelease_candidate

        return self._find_next_available_prerelease_for_conflict(
            base_version, prerelease_type
        )

    def _find_next_available_prerelease_for_conflict(
        self, base_version: SemanticVersion, prerelease_type: str
    ) -> SemanticVersion:
        """
        Find the next available prerelease version when a regular version has conflicts.

        Args:
            base_version: The base version to use
            prerelease_type: The prerelease identifier type (dev, alpha, beta, etc.)

        Returns:
            The next available prerelease version
        """
        # Try different prerelease numbers using the shared helper
        available_version = self._find_available_prerelease_version(
            major=base_version.major,
            minor=base_version.minor,
            patch=base_version.patch,
            prerelease_type=prerelease_type,
            metadata=base_version.metadata,
            prefix=base_version.prefix,
        )

        if available_version:
            return available_version

        # If still no available version, increment patch and try again
        fallback = SemanticVersion(
            major=base_version.major,
            minor=base_version.minor,
            patch=base_version.patch + 1,
            prerelease=f"{prerelease_type}.1",
            metadata=base_version.metadata,
            prefix=base_version.prefix,
        )

        if not self._version_exists(fallback):
            return fallback

        # Last resort - use find_next_available_version
        return self._find_next_available_version(fallback)

    def _increment_prerelease(
        self, version: SemanticVersion, prerelease_type: str | None = None
    ) -> SemanticVersion:
        """
        Intelligently increment the pre-release version.

        For existing pre-releases, finds and increments numeric components.
        For non-pre-releases, creates a new pre-release version.
        """
        if not version.is_prerelease():
            # Not a prerelease - create first prerelease
            return self._create_first_prerelease(version, prerelease_type)

        # Check if we're changing prerelease types (e.g., alpha → beta → rc)
        if prerelease_type:
            identifiers = version.get_prerelease_identifiers()
            current_type = identifiers[0].lower() if identifiers else ""
            # If we're switching from one prerelease type to another
            if current_type and current_type != prerelease_type.lower():
                return SemanticVersion(
                    major=version.major,
                    minor=version.minor,
                    patch=version.patch,
                    prerelease=f"{prerelease_type}.1",
                    metadata=version.metadata if self.preserve_metadata else None,
                    prefix=version.prefix,
                )
        # Existing prerelease - increment it
        return self._increment_existing_prerelease(version)

    def _create_first_prerelease(
        self, version: SemanticVersion, prerelease_type: str | None = None
    ) -> SemanticVersion:
        """
        Create the first pre-release version for a given base version.

        If the patch version can be incremented and a prerelease created,
        that's preferred. Otherwise, increment patch and add prerelease.
        """
        # Handle transitions between prerelease types (alpha → beta → rc)
        # We only need to handle the case when we're creating a prerelease
        # from a non-prerelease version. The case for switching between
        # prerelease types is now handled in _increment_prerelease
        prerelease_id = prerelease_type or "dev"
        # Determine first available prerelease by checking for conflicts
        # Start with patch + 1 as default
        patch = version.patch + 1

        # Try incremented patch with different prerelease numbers using the shared helper
        for p in range(patch, patch + 5):
            available_version = self._find_available_prerelease_version(
                major=version.major,
                minor=version.minor,
                patch=p,
                prerelease_type=prerelease_id,
                metadata=version.metadata,
                prefix=version.prefix,
                max_attempts=min(self.MAX_PRERELEASE_ATTEMPTS, self.MAX_PATCH_ATTEMPTS),
            )
            if available_version:
                return available_version

        # If we couldn't find an available version, create a fallback
        return SemanticVersion(
            major=version.major,
            minor=version.minor,
            patch=version.patch,
            prerelease=f"{prerelease_type}.1",
            metadata=version.metadata if self.preserve_metadata else None,
            prefix=version.prefix,
        )

    def _increment_existing_prerelease(
        self, version: SemanticVersion
    ) -> SemanticVersion:
        """
        Increment an existing pre-release version.

        Uses smart logic to find and increment numeric components.
        """
        numeric_components = version.find_numeric_prerelease_components()

        if not numeric_components:
            # No numeric components found - add .1 to the end
            new_prerelease = f"{version.prerelease}.1"
        else:
            # Increment the rightmost numeric component
            identifiers = version.get_prerelease_identifiers()
            last_numeric = numeric_components[-1]
            index, original_id, numeric_value = last_numeric

            # Create new identifier with incremented number
            if original_id.isdigit():
                # Pure numeric identifier
                new_id = str(numeric_value + 1)
            else:
                # Alphanumeric identifier with trailing number
                new_id = re.sub(r"\d+$", str(numeric_value + 1), original_id)

            # Replace the identifier at the found index
            new_identifiers = identifiers.copy()
            new_identifiers[index] = new_id
            new_prerelease = ".".join(new_identifiers)

        candidate = SemanticVersion(
            major=version.major,
            minor=version.minor,
            patch=version.patch,
            prerelease=new_prerelease,
            metadata=version.metadata if self.preserve_metadata else None,
            prefix=version.prefix,
        )

        # If candidate exists, aggressively skip to next patch and search for next available prerelease
        # If candidate exists, always skip to next patch and search for next available prerelease
        if self._version_exists(candidate):
            prerelease_base = (
                new_prerelease.split(".")[0]
                if "." in new_prerelease
                else new_prerelease
            )
            patch = version.patch + 1

            available_version = self._find_available_prerelease_version(
                major=version.major,
                minor=version.minor,
                patch=patch,
                prerelease_type=prerelease_base,
                metadata=version.metadata,
                prefix=version.prefix,
            )

            if available_version:
                return available_version

            raise RuntimeError("Could not find available prerelease version")
        return candidate

    def _find_next_available_prerelease(
        self,
        major: int,
        minor: int,
        patch: int,
        prerelease_base: str,
        metadata: str | None,
        prefix: str,
    ) -> SemanticVersion:
        """Find the next available prerelease version by incrementing numbers."""
        available_version = self._find_available_prerelease_version(
            major=major,
            minor=minor,
            patch=patch,
            prerelease_type=prerelease_base,
            metadata=metadata,
            prefix=prefix,
        )

        if available_version:
            return available_version

        raise RuntimeError("Could not find available prerelease version")

    def _find_next_available_version(
        self, base_version: SemanticVersion
    ) -> SemanticVersion:
        """
        Find the next available version by incrementing prerelease numbers.
        """
        if not base_version.is_prerelease():
            raise ValueError("Base version must be a prerelease")

        numeric_components = base_version.find_numeric_prerelease_components()
        if not numeric_components:
            # Add a numeric component
            new_prerelease = f"{base_version.prerelease}.1"
            return SemanticVersion(
                major=base_version.major,
                minor=base_version.minor,
                patch=base_version.patch,
                prerelease=new_prerelease,
                metadata=base_version.metadata if self.preserve_metadata else None,
                prefix=base_version.prefix,
            )

        # Increment the rightmost numeric component and try versions
        identifiers = base_version.get_prerelease_identifiers()
        last_numeric = numeric_components[-1]
        index, original_id, numeric_value = last_numeric

        counter = numeric_value + 1
        while True:
            new_identifiers = identifiers.copy()

            if original_id.isdigit():
                new_identifiers[index] = str(counter)
            else:
                new_identifiers[index] = re.sub(
                    r"\d+$", str(counter), original_id
                )

            candidate = SemanticVersion(
                major=base_version.major,
                minor=base_version.minor,
                patch=base_version.patch,
                prerelease=".".join(new_identifiers),
                metadata=base_version.metadata,
                prefix=base_version.prefix,
            )

            if not self._version_exists(candidate):
                return candidate

            counter += 1

            # Safety break
            if counter > self.MAX_PRERELEASE_ATTEMPTS:
                raise RuntimeError("Could not find available version")

    def _version_exists(self, version: SemanticVersion) -> bool:
        """Check if a version already exists in the known tags."""
        if not self.existing_tags:
            return False

        # Build normalized tags cache if not already built
        if self._normalized_tags_cache is None:
            self._normalized_tags_cache = {
                self._normalize_version_string(tag) for tag in self.existing_tags
            }

        # Check against cached normalized tags for better performance
        normalized_version = self._normalize_version_string(
            version.to_string(include_prefix=False)
        )

        return normalized_version in self._normalized_tags_cache

    def _normalize_version_string(self, version_str: str) -> str:
        """
        Normalize a version string for consistent comparison.

        Optimized for performance with minimal string operations.
        """
        # Fast path for common cases
        if not version_str:
            return ""

        # Remove leading 'v' or 'V' prefix efficiently
        start_idx = 1 if version_str and (version_str[0] == 'v' or version_str[0] == 'V') else 0

        # Find build metadata separator if present
        plus_idx = version_str.find('+', start_idx)

        # Extract the normalized version without metadata
        if plus_idx != -1:
            return version_str[start_idx:plus_idx].lower()
        else:
            return version_str[start_idx:].lower()

    @classmethod
    def determine_increment_type(cls, increment_str: str) -> IncrementType:
        """
        Determine the increment type from a string.

        Args:
            increment_str: String representation of increment type

        Returns:
            IncrementType enum value

        Raises:
            ValueError: If increment type is not recognized
        """
        increment_str = increment_str.lower().strip()

        for increment_type in IncrementType:
            if increment_type.value == increment_str:
                return increment_type

        # Handle aliases
        aliases = {
            "dev": IncrementType.DEV,
            "pre": IncrementType.PRERELEASE,
            "prerel": IncrementType.PRERELEASE,
        }

        if increment_str in aliases:
            return aliases[increment_str]

        raise ValueError(
            f"Invalid increment type: {increment_str}. "
            f"Valid types: {[t.value for t in IncrementType]}"
        )

    def suggest_next_version(
        self, current_version: SemanticVersion, increment_type: IncrementType
    ) -> list[SemanticVersion]:
        """
        Suggest multiple possible next versions.

        Useful for interactive scenarios or when multiple strategies are valid.

        Args:
            current_version: The current version
            increment_type: The type of increment desired

        Returns:
            List of suggested next versions in order of preference
        """
        suggestions = []

        if increment_type == IncrementType.PRERELEASE:
            # If current version is already a prerelease, suggest the next logical prerelease type
            if current_version.is_prerelease():
                identifiers = current_version.get_prerelease_identifiers()
                current_type = identifiers[0].lower() if identifiers else "dev"

                # Standard prerelease progression: dev → alpha → beta → rc → release
                next_type = None
                if "alpha" in current_type or "dev" in current_type:
                    next_type = "beta"
                elif "beta" in current_type:
                    next_type = "rc"

                if next_type:
                    try:
                        # Maintain same patch version when changing prerelease type
                        suggestion = SemanticVersion(
                            major=current_version.major,
                            minor=current_version.minor,
                            patch=current_version.patch,
                            prerelease=f"{next_type}.1",
                            metadata=current_version.metadata,
                            prefix=current_version.prefix,
                        )
                        suggestions.append(suggestion)
                    except Exception as e:
                        logger.debug(
                            f"Failed to create suggestion with prerelease type {next_type}: {e}"
                        )

            # Offer multiple prerelease strategies
            for prerelease_type in ["dev", "alpha", "beta", "rc"]:
                try:
                    suggestion = self._create_first_prerelease(
                        current_version, prerelease_type
                    )
                    if suggestion not in suggestions:
                        suggestions.append(suggestion)
                except Exception as e:
                    logger.debug(
                        f"Failed to create suggestion with prerelease type {prerelease_type}: {e}"
                    )
                    continue
        else:
            # For other increment types, just return the single increment
            suggestions.append(self.increment(current_version, increment_type))

        return suggestions

    def update_existing_tags(self, new_tags: set[str]) -> None:
        """
        Update the set of existing tags and invalidate the cache.

        Args:
            new_tags: New set of existing version tags
        """
        self.existing_tags = new_tags
        # Invalidate cache to force rebuild on next access
        self._normalized_tags_cache = None

    def _find_available_prerelease_version(
        self,
        major: int,
        minor: int,
        patch: int,
        prerelease_type: str,
        start_counter: int = 1,
        max_attempts: int | None = None,
        metadata: str | None = None,
        prefix: str = "",
    ) -> SemanticVersion | None:
        """
        Find the next available prerelease version with the given parameters.

        Args:
            major: Major version component
            minor: Minor version component
            patch: Patch version component
            prerelease_type: The prerelease identifier (dev, alpha, beta, etc.)
            start_counter: Starting counter value for prerelease numbers
            max_attempts: Maximum number of attempts (defaults to MAX_PRERELEASE_ATTEMPTS)
            metadata: Version metadata
            prefix: Version prefix

        Returns:
            Available SemanticVersion or None if no version found within max_attempts
        """
        max_attempts = max_attempts or self.MAX_PRERELEASE_ATTEMPTS

        for counter in range(start_counter, start_counter + max_attempts):
            candidate = SemanticVersion(
                major=major,
                minor=minor,
                patch=patch,
                prerelease=f"{prerelease_type}.{counter}",
                metadata=metadata,
                prefix=prefix,
            )
            if not self._version_exists(candidate):
                return candidate

        return None

    def _get_existing_patches(self, major: int, minor: int) -> set[int]:
        """
        Get existing patch numbers for a given major.minor version.

        Returns:
            Set of existing patch numbers
        """
        patches = set()
        prefix_pattern = f"{major}.{minor}."

        for tag in self.existing_tags:
            normalized = self._normalize_version_string(tag)
            if normalized.startswith(prefix_pattern):
                try:
                    # Extract patch number (before any prerelease or metadata)
                    remainder = normalized[len(prefix_pattern):]
                    patch_str = remainder.split('-')[0].split('+')[0]
                    if patch_str.isdigit():
                        patches.add(int(patch_str))
                except (ValueError, IndexError):
                    continue

        return patches

    def _get_existing_prerelease_numbers(
        self, major: int, minor: int, patch: int, prerelease_type: str
    ) -> set[int]:
        """
        Get existing prerelease numbers for a given version and prerelease type.

        Returns:
            Set of existing prerelease numbers
        """
        numbers = set()
        version_prefix = f"{major}.{minor}.{patch}-{prerelease_type}."

        for tag in self.existing_tags:
            normalized = self._normalize_version_string(tag)
            if normalized.startswith(version_prefix):
                try:
                    # Extract the number after the prerelease type
                    remainder = normalized[len(version_prefix):]
                    # Get everything before any additional dots, plus, or end of string
                    num_str = remainder.split('.')[0].split('+')[0]
                    if num_str.isdigit():
                        numbers.add(int(num_str))
                except (ValueError, IndexError):
                    continue

        return numbers
