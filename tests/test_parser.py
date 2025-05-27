# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Unit tests for semantic version parser.

This module contains comprehensive tests for the SemanticVersion parser,
including all the complex patterns from the RegEx101 examples.
"""

import pytest

from semantic_tag_increment.parser import SemanticVersion


class TestSemanticVersionParser:
    """Test the SemanticVersion parser with various valid and invalid inputs."""

    # Valid semantic versions from RegEx101 examples
    VALID_VERSIONS = [
        "0.0.4",
        "1.2.3",
        "10.20.30",
        "1.1.2-prerelease+meta",
        "1.1.2+meta",
        "1.1.2+meta-valid",
        "1.0.0-alpha",
        "1.0.0-beta",
        "1.0.0-alpha.beta",
        "1.0.0-alpha.beta.1",
        "1.0.0-alpha.1",
        "1.0.0-alpha0.valid",
        "1.0.0-alpha.0valid",
        "1.0.0-alpha-a.b-c-somethinglong+build.1-aef.1-its-okay",
        "1.0.0-rc.1+build.1",
        "2.0.0-rc.1+build.123",
        "1.2.3-beta",
        "10.2.3-DEV-SNAPSHOT",
        "1.2.3-SNAPSHOT-123",
        "1.0.0",
        "2.0.0",
        "1.1.7",
        "2.0.0+build.1848",
        "2.0.1-alpha.1227",
        "1.0.0-alpha+beta",
        "1.2.3----RC-SNAPSHOT.12.9.1--.12+788",
        "1.2.3----R-S.12.9.1--.12+meta",
        "1.2.3----RC-SNAPSHOT.12.9.1--.12",
        "1.0.0+0.build.1-rc.10000aaa-kk-0.1",
        "99999999999999999999999.999999999999999999.99999999999999999",
        "1.0.0-0A.is.legal",
        # With v prefix
        "v1.2.3",
        "V1.0.0-alpha",
        "v2.0.0+build.123",
    ]

    # Invalid semantic versions
    INVALID_VERSIONS = [
        "",
        "1",
        "1.2",
        "1.2.3-",
        "1.2.3+",
        "01.2.3",
        "1.02.3",
        "1.2.03",
        "1.2.3-+",
        "1.2.3-alpha_beta",
        "1.2.3-alpha..beta",
        "+invalid",
        "-invalid",
        "alpha",
        "1.2.3.DEV",
        "1.2-SNAPSHOT-123",
    ]

    @pytest.mark.parametrize("version_string", VALID_VERSIONS)
    def test_parse_valid_versions(self, version_string: str) -> None:
        """Test parsing of all valid semantic version patterns."""
        version = SemanticVersion.parse(version_string)
        assert isinstance(version, SemanticVersion)
        assert version.major >= 0
        assert version.minor >= 0
        assert version.patch >= 0

    @pytest.mark.parametrize("version_string", INVALID_VERSIONS)
    def test_parse_invalid_versions(self, version_string: str) -> None:
        """Test that invalid versions raise ValueError."""
        with pytest.raises(ValueError):
            SemanticVersion.parse(version_string)

    def test_parse_none_or_empty(self) -> None:
        """Test parsing None or empty strings."""
        with pytest.raises(ValueError):
            SemanticVersion.parse("")

        with pytest.raises(ValueError):
            SemanticVersion.parse(None)  # type: ignore

    def test_basic_version_parsing(self) -> None:
        """Test parsing basic version components."""
        version = SemanticVersion.parse("1.2.3")
        assert version.major == 1
        assert version.minor == 2
        assert version.patch == 3
        assert version.prerelease is None
        assert version.metadata is None
        assert version.prefix == ""

    def test_version_with_prefix(self) -> None:
        """Test parsing versions with v/V prefix."""
        version_v = SemanticVersion.parse("v1.2.3")
        assert version_v.major == 1
        assert version_v.minor == 2
        assert version_v.patch == 3
        assert version_v.prefix == "v"

        version_V = SemanticVersion.parse("V1.2.3")
        assert version_V.major == 1
        assert version_V.minor == 2
        assert version_V.patch == 3
        assert version_V.prefix == "V"

    def test_version_with_prerelease(self) -> None:
        """Test parsing versions with pre-release identifiers."""
        version = SemanticVersion.parse("1.2.3-alpha.1")
        assert version.major == 1
        assert version.minor == 2
        assert version.patch == 3
        assert version.prerelease == "alpha.1"
        assert version.metadata is None

    def test_version_with_metadata(self) -> None:
        """Test parsing versions with build metadata."""
        version = SemanticVersion.parse("1.2.3+build.123")
        assert version.major == 1
        assert version.minor == 2
        assert version.patch == 3
        assert version.prerelease is None
        assert version.metadata == "build.123"

    def test_version_with_prerelease_and_metadata(self) -> None:
        """Test parsing versions with both pre-release and metadata."""
        version = SemanticVersion.parse("1.2.3-alpha.1+build.123")
        assert version.major == 1
        assert version.minor == 2
        assert version.patch == 3
        assert version.prerelease == "alpha.1"
        assert version.metadata == "build.123"

    def test_complex_prerelease_patterns(self) -> None:
        """Test parsing complex pre-release patterns."""
        # Complex pattern from RegEx101
        version = SemanticVersion.parse("1.2.3----RC-SNAPSHOT.12.9.1--.12+788")
        assert version.major == 1
        assert version.minor == 2
        assert version.patch == 3
        assert version.prerelease == "---RC-SNAPSHOT.12.9.1--.12"
        assert version.metadata == "788"

    def test_large_numbers(self) -> None:
        """Test parsing versions with very large numbers."""
        version_str = (
            "99999999999999999999999.999999999999999999.99999999999999999"
        )
        version = SemanticVersion.parse(version_str)
        assert version.major == 99999999999999999999999
        assert version.minor == 999999999999999999
        assert version.patch == 99999999999999999

    def test_is_valid_method(self) -> None:
        """Test the is_valid class method."""
        assert SemanticVersion.is_valid("1.2.3")
        assert SemanticVersion.is_valid("v1.2.3-alpha+build")
        assert not SemanticVersion.is_valid("invalid")
        assert not SemanticVersion.is_valid("1.2")


class TestSemanticVersionMethods:
    """Test methods and properties of SemanticVersion objects."""

    def test_string_representation(self) -> None:
        """Test string representation methods."""
        version = SemanticVersion.parse("v1.2.3-alpha+build")

        # Full string with prefix
        assert str(version) == "v1.2.3-alpha+build"
        assert version.to_string(include_prefix=True) == "v1.2.3-alpha+build"

        # Numeric version without prefix
        assert version.numeric_version() == "1.2.3-alpha+build"
        assert version.to_string(include_prefix=False) == "1.2.3-alpha+build"

    def test_string_without_prefix(self) -> None:
        """Test string representation for version without prefix."""
        version = SemanticVersion.parse("1.2.3-alpha+build")
        assert str(version) == "1.2.3-alpha+build"
        assert version.to_string(include_prefix=True) == "1.2.3-alpha+build"
        assert version.numeric_version() == "1.2.3-alpha+build"

    def test_is_prerelease(self) -> None:
        """Test prerelease detection."""
        assert SemanticVersion.parse("1.2.3-alpha").is_prerelease()
        assert not SemanticVersion.parse("1.2.3").is_prerelease()
        assert SemanticVersion.parse("1.2.3-alpha+build").is_prerelease()

    def test_has_metadata(self) -> None:
        """Test metadata detection."""
        assert SemanticVersion.parse("1.2.3+build").has_metadata()
        assert not SemanticVersion.parse("1.2.3").has_metadata()
        assert SemanticVersion.parse("1.2.3-alpha+build").has_metadata()

    def test_core_version(self) -> None:
        """Test core version extraction."""
        version = SemanticVersion.parse("v1.2.3-alpha+build")
        assert version.core_version() == (1, 2, 3)

    def test_get_prerelease_identifiers(self) -> None:
        """Test extraction of prerelease identifiers."""
        version = SemanticVersion.parse("1.2.3-alpha.1.beta")
        identifiers = version.get_prerelease_identifiers()
        assert identifiers == ["alpha", "1", "beta"]

        version_no_prerelease = SemanticVersion.parse("1.2.3")
        assert version_no_prerelease.get_prerelease_identifiers() == []

    def test_find_numeric_prerelease_components(self) -> None:
        """Test finding numeric components in prerelease identifiers."""
        # Pure numeric identifier
        version = SemanticVersion.parse("1.2.3-alpha.1.beta.2")
        numeric_components = version.find_numeric_prerelease_components()
        assert len(numeric_components) == 2
        assert (1, "1", 1) in numeric_components
        assert (3, "2", 2) in numeric_components

        # Alphanumeric with trailing numbers
        version = SemanticVersion.parse("1.2.3-alpha1.beta2")
        numeric_components = version.find_numeric_prerelease_components()
        assert len(numeric_components) == 2
        assert (0, "alpha1", 1) in numeric_components
        assert (1, "beta2", 2) in numeric_components

        # Complex pattern
        version = SemanticVersion.parse("1.2.3-RC-SNAPSHOT.12.dev1")
        numeric_components = version.find_numeric_prerelease_components()
        assert len(numeric_components) == 2
        assert (1, "12", 12) in numeric_components
        assert (2, "dev1", 1) in numeric_components

        # No numeric components
        version = SemanticVersion.parse("1.2.3-alpha.beta")
        numeric_components = version.find_numeric_prerelease_components()
        assert len(numeric_components) == 0


class TestSemanticVersionComparison:
    """Test version comparison and precedence rules."""

    def test_basic_version_comparison(self) -> None:
        """Test basic version comparison."""
        v1 = SemanticVersion.parse("1.0.0")
        v2 = SemanticVersion.parse("2.0.0")
        v3 = SemanticVersion.parse("1.1.0")
        v4 = SemanticVersion.parse("1.0.1")

        assert v1 < v2
        assert v1 < v3
        assert v1 < v4
        assert v3 > v4
        assert v2 > v3

    def test_prerelease_precedence(self) -> None:
        """Test that prereleases have lower precedence than normal versions."""
        normal = SemanticVersion.parse("1.0.0")
        prerelease = SemanticVersion.parse("1.0.0-alpha")

        assert prerelease < normal
        assert normal > prerelease

    def test_prerelease_comparison(self) -> None:
        """Test comparison between different prereleases."""
        alpha = SemanticVersion.parse("1.0.0-alpha")
        alpha1 = SemanticVersion.parse("1.0.0-alpha.1")
        alpha2 = SemanticVersion.parse("1.0.0-alpha.2")
        beta = SemanticVersion.parse("1.0.0-beta")

        assert alpha < alpha1
        assert alpha1 < alpha2
        assert alpha < beta
        assert alpha2 < beta

    def test_equality_ignores_metadata(self) -> None:
        """Test that metadata is ignored in equality comparison."""
        v1 = SemanticVersion.parse("1.0.0+build1")
        v2 = SemanticVersion.parse("1.0.0+build2")
        v3 = SemanticVersion.parse("1.0.0")

        assert v1 == v2
        assert v1 == v3
        assert v2 == v3

    def test_prefix_ignored_in_comparison(self) -> None:
        """Test that prefixes are ignored in comparison."""
        v1 = SemanticVersion.parse("v1.2.3")
        v2 = SemanticVersion.parse("1.2.3")
        v3 = SemanticVersion.parse("V1.2.3")

        assert v1 == v2
        assert v1 == v3
        assert v2 == v3

    def test_comparison_operators(self) -> None:
        """Test all comparison operators."""
        v1 = SemanticVersion.parse("1.0.0")
        v2 = SemanticVersion.parse("1.0.1")
        v3 = SemanticVersion.parse("1.0.0")

        # Less than
        assert v1 < v2
        assert not v2 < v1

        # Less than or equal
        assert v1 <= v2
        assert v1 <= v3
        assert not v2 <= v1

        # Greater than
        assert v2 > v1
        assert not v1 > v2

        # Greater than or equal
        assert v2 >= v1
        assert v1 >= v3
        assert not v1 >= v2

        # Equality
        assert v1 == v3
        assert not v1 == v2

    def test_complex_prerelease_comparison(self) -> None:
        """Test comparison of complex prerelease patterns."""
        versions = [
            SemanticVersion.parse("1.0.0-alpha"),
            SemanticVersion.parse("1.0.0-alpha.1"),
            SemanticVersion.parse("1.0.0-alpha.beta"),
            SemanticVersion.parse("1.0.0-beta"),
            SemanticVersion.parse("1.0.0-beta.2"),
            SemanticVersion.parse("1.0.0-beta.11"),
            SemanticVersion.parse("1.0.0-rc.1"),
            SemanticVersion.parse("1.0.0"),
        ]

        # Check that they are in ascending order
        for i in range(len(versions) - 1):
            assert versions[i] < versions[i + 1], (
                f"{versions[i]} should be < {versions[i + 1]}"
            )

    def test_numeric_vs_alphanumeric_identifiers(self) -> None:
        """Test precedence rules for numeric vs alphanumeric identifiers."""
        # Numeric identifiers have lower precedence than alphanumeric
        numeric = SemanticVersion.parse("1.0.0-1")
        alphanumeric = SemanticVersion.parse("1.0.0-alpha")

        assert numeric < alphanumeric

        # But numeric comparison works correctly within numeric identifiers
        numeric1 = SemanticVersion.parse("1.0.0-1")
        numeric2 = SemanticVersion.parse("1.0.0-2")
        numeric10 = SemanticVersion.parse("1.0.0-10")

        assert numeric1 < numeric2
        assert numeric2 < numeric10  # Should be numeric comparison, not lexical
