# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Semantic Version Parser.

This module provides comprehensive parsing and validation of semantic version
strings according to the Semantic Versioning specification (https://semver.org/)
with support for complex pre-release and metadata patterns.
"""

import re
from dataclasses import dataclass

from .exceptions import ErrorReporter

# Security constants
MAX_VERSION_LENGTH = 1000  # Reasonable limit to prevent ReDoS attacks


@dataclass(frozen=True)
class SemanticVersion:
    """
    Represents a semantic version with major, minor, patch, pre-release, and
    metadata components.

    Supports all valid semantic version patterns including complex pre-release
    identifiers and build metadata.
    """

    major: int
    minor: int
    patch: int
    prerelease: str | None = None
    metadata: str | None = None
    prefix: str = ""  # Store any v/V prefix for output formatting

    # Optimized semantic version regex pattern for better performance
    # Compiled once at class definition for efficiency
    # Based on semver.org specification with performance optimizations
    SEMVER_PATTERN = re.compile(
        r"^(?P<prefix>[vV])?"
        r"(?P<major>0|[1-9]\d*)"
        r"\.(?P<minor>0|[1-9]\d*)"
        r"\.(?P<patch>0|[1-9]\d*)"
        r"(?:-(?P<prerelease>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?"
        r"(?:\+(?P<metadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$",
        re.ASCII  # Use ASCII flag to optimize regex performance for typical version strings.
                  # This flag restricts the regex to ASCII-only characters, which improves performance
                  # but makes it unsuitable for version strings containing Unicode characters. Ensure
                  # that this limitation aligns with your use case before using this flag.
    )

    @classmethod
    def parse(cls, version_string: str) -> "SemanticVersion":
        """
        Parse a semantic version string into a SemanticVersion object.

        Args:
            version_string: The version string to parse

        Returns:
            SemanticVersion object

        Raises:
            ValueError: If the version string is not a valid semantic version
        """
        if not version_string or not isinstance(version_string, str):
            raise ValueError("Version string cannot be empty or None")

        # Security check: prevent ReDoS attacks with overly long input
        if len(version_string) > MAX_VERSION_LENGTH:
            ErrorReporter.log_and_raise_security_error(
                f"Version string too long (max {MAX_VERSION_LENGTH} characters): "
                f"got {len(version_string)} characters",
                "input_length_validation",
                version_string[:100] + "..." if len(version_string) > 100 else version_string
            )

        stripped_version = version_string.strip()

        # Additional security check after stripping
        if len(stripped_version) > MAX_VERSION_LENGTH:
            ErrorReporter.log_and_raise_security_error(
                f"Version string too long after stripping (max {MAX_VERSION_LENGTH} characters): "
                f"got {len(stripped_version)} characters",
                "stripped_length_validation",
                stripped_version[:100] + "..." if len(stripped_version) > 100 else stripped_version
            )

        match = cls.SEMVER_PATTERN.match(stripped_version)
        if not match:
            ErrorReporter.log_and_raise_parse_error(
                f"Invalid semantic version format: {version_string}",
                version_string
            )
            # This return statement will never be reached due to the exception above
            # but is needed to satisfy type checker
            return cls(0, 0, 0)

        groups = match.groupdict()

        try:
            return cls(
                major=int(groups["major"]),
                minor=int(groups["minor"]),
                patch=int(groups["patch"]),
                prerelease=groups["prerelease"],
                metadata=groups["metadata"],
                prefix=groups["prefix"] or "",
            )
        except (ValueError, TypeError) as e:
            ErrorReporter.log_and_raise_parse_error(
                f"Invalid semantic version components: {e}",
                version_string
            )
            # This return statement will never be reached due to the exception above
            # but is needed to satisfy type checker
            return cls(0, 0, 0)

    @classmethod
    def is_valid(cls, version_string: str) -> bool:
        """
        Check if a version string is a valid semantic version.

        Args:
            version_string: The version string to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            # Basic safety checks before attempting parse
            if not version_string or not isinstance(version_string, str):
                return False

            if len(version_string) > MAX_VERSION_LENGTH:
                return False

            cls.parse(version_string)
            return True
        except (ValueError, TypeError):
            return False

    def __str__(self) -> str:
        """Return the complete version string with prefix."""
        return self.to_string(include_prefix=True)

    def to_string(self, include_prefix: bool = True) -> str:
        """
        Convert the semantic version to a string representation.

        Args:
            include_prefix: Whether to include the v/V prefix if present

        Returns:
            String representation of the version
        """
        version = f"{self.major}.{self.minor}.{self.patch}"

        if self.prerelease:
            version += f"-{self.prerelease}"

        if self.metadata:
            version += f"+{self.metadata}"

        if include_prefix and self.prefix:
            version = f"{self.prefix}{version}"

        return version

    def numeric_version(self) -> str:
        """Return version without any prefix (for numeric comparisons)."""
        return self.to_string(include_prefix=False)

    def is_prerelease(self) -> bool:
        """Check if this is a pre-release version."""
        return self.prerelease is not None

    def has_metadata(self) -> bool:
        """Check if this version has build metadata."""
        return self.metadata is not None

    def core_version(self) -> tuple[int, int, int]:
        """Return the core version tuple (major, minor, patch)."""
        return (self.major, self.minor, self.patch)

    def compare_precedence(self, other: "SemanticVersion") -> int:
        """
        Compare version precedence according to semver rules.

        Args:
            other: Another SemanticVersion to compare against

        Returns:
            -1 if self < other, 0 if equal, 1 if self > other
        """
        # Compare core version first
        self_core = self.core_version()
        other_core = other.core_version()

        if self_core < other_core:
            return -1
        elif self_core > other_core:
            return 1

        # Core versions are equal, check pre-release
        if not self.is_prerelease() and not other.is_prerelease():
            return 0
        elif not self.is_prerelease() and other.is_prerelease():
            return 1  # Normal version has higher precedence than pre-release
        elif self.is_prerelease() and not other.is_prerelease():
            return -1  # Pre-release has lower precedence than normal

        # Both are pre-releases, compare identifiers
        return self._compare_prerelease_identifiers(
            self.prerelease, other.prerelease
        )

    def _compare_prerelease_identifiers(
        self, pre1: str | None, pre2: str | None
    ) -> int:
        """
        Compare pre-release version identifiers.

        According to semver: identifiers are compared numerically if both are
        numeric, otherwise lexically in ASCII sort order.
        """
        if pre1 is None and pre2 is None:
            return 0
        if pre1 is None:
            return -1
        if pre2 is None:
            return 1

        ids1 = pre1.split(".")
        ids2 = pre2.split(".")

        # Compare each identifier pair
        for i in range(max(len(ids1), len(ids2))):
            id1 = ids1[i] if i < len(ids1) else None
            id2 = ids2[i] if i < len(ids2) else None

            if id1 is None:
                return -1  # Fewer identifiers = lower precedence
            if id2 is None:
                return 1  # More identifiers = higher precedence

            # Check if both are numeric
            id1_numeric = id1.isdigit()
            id2_numeric = id2.isdigit()

            if id1_numeric and id2_numeric:
                # Both numeric - compare as integers
                result = int(id1) - int(id2)
                if result != 0:
                    return -1 if result < 0 else 1
            elif id1_numeric and not id2_numeric:
                return -1  # Numeric identifiers have lower precedence
            elif not id1_numeric and id2_numeric:
                return 1  # Alphanumeric identifiers have higher precedence
            else:
                # Both alphanumeric - lexical comparison
                if id1 < id2:
                    return -1
                elif id1 > id2:
                    return 1

        return 0

    def __eq__(self, other: object) -> bool:
        """Check equality based on version precedence (ignoring metadata)."""
        if not isinstance(other, SemanticVersion):
            return NotImplemented
        return self.compare_precedence(other) == 0

    def __lt__(self, other: "SemanticVersion") -> bool:
        """Check if this version is less than another."""
        return self.compare_precedence(other) < 0

    def __le__(self, other: "SemanticVersion") -> bool:
        """Check if this version is less than or equal to another."""
        return self.compare_precedence(other) <= 0

    def __gt__(self, other: "SemanticVersion") -> bool:
        """Check if this version is greater than another."""
        return self.compare_precedence(other) > 0

    def __ge__(self, other: "SemanticVersion") -> bool:
        """Check if this version is greater than or equal to another."""
        return self.compare_precedence(other) >= 0

    def get_prerelease_identifiers(self) -> list[str]:
        """
        Get the list of pre-release identifiers.

        Returns:
            List of pre-release identifiers, empty if no pre-release
        """
        if not self.prerelease:
            return []
        return self.prerelease.split(".")

    def find_numeric_prerelease_components(self) -> list[tuple[int, str, int]]:
        """
        Find numeric components in pre-release identifiers for incrementing.

        Returns:
            List of tuples: (index, identifier, numeric_value)
            where index is the position in the pre-release identifier list
        """
        numeric_components = []
        identifiers = self.get_prerelease_identifiers()

        for i, identifier in enumerate(identifiers):
            # Look for purely numeric identifiers
            if identifier.isdigit():
                numeric_components.append((i, identifier, int(identifier)))
            else:
                # Look for trailing numbers in alphanumeric identifiers
                match = re.search(r"(\d+)$", identifier)
                if match:
                    numeric_value = int(match.group(1))
                    numeric_components.append((i, identifier, numeric_value))

        return numeric_components
