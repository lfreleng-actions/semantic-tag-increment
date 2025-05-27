# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Unit tests for version incrementer.

This module contains comprehensive tests for the VersionIncrementer,
including all increment types and complex pre-release handling.
"""

import pytest

from semantic_tag_increment.incrementer import IncrementType, VersionIncrementer
from semantic_tag_increment.parser import SemanticVersion


class TestIncrementType:
    """Test IncrementType enum and related functionality."""

    def test_increment_type_values(self) -> None:
        """Test that all increment types have correct values."""
        assert IncrementType.MAJOR.value == "major"
        assert IncrementType.MINOR.value == "minor"
        assert IncrementType.PATCH.value == "patch"
        assert IncrementType.PRERELEASE.value == "prerelease"
        assert IncrementType.DEV.value == "dev"

    def test_determine_increment_type(self) -> None:
        """Test determination of increment type from string."""
        assert (
            VersionIncrementer.determine_increment_type("major")
            == IncrementType.MAJOR
        )
        assert (
            VersionIncrementer.determine_increment_type("minor")
            == IncrementType.MINOR
        )
        assert (
            VersionIncrementer.determine_increment_type("patch")
            == IncrementType.PATCH
        )
        assert (
            VersionIncrementer.determine_increment_type("prerelease")
            == IncrementType.PRERELEASE
        )
        assert (
            VersionIncrementer.determine_increment_type("dev")
            == IncrementType.DEV
        )

    def test_determine_increment_type_case_insensitive(self) -> None:
        """Test case insensitive increment type determination."""
        assert (
            VersionIncrementer.determine_increment_type("MAJOR")
            == IncrementType.MAJOR
        )
        assert (
            VersionIncrementer.determine_increment_type("Minor")
            == IncrementType.MINOR
        )
        assert (
            VersionIncrementer.determine_increment_type("  patch  ")
            == IncrementType.PATCH
        )

    def test_determine_increment_type_aliases(self) -> None:
        """Test increment type aliases."""
        assert (
            VersionIncrementer.determine_increment_type("dev")
            == IncrementType.DEV
        )
        assert (
            VersionIncrementer.determine_increment_type("pre")
            == IncrementType.PRERELEASE
        )
        assert (
            VersionIncrementer.determine_increment_type("prerel")
            == IncrementType.PRERELEASE
        )

    def test_determine_increment_type_invalid(self) -> None:
        """Test invalid increment types raise ValueError."""
        with pytest.raises(ValueError, match="Invalid increment type"):
            VersionIncrementer.determine_increment_type("invalid")

        with pytest.raises(ValueError):
            VersionIncrementer.determine_increment_type("")


class TestVersionIncrementer:
    """Test the VersionIncrementer class."""

    def test_init_without_existing_tags(self) -> None:
        """Test initialization without existing tags."""
        incrementer = VersionIncrementer()
        assert incrementer.existing_tags == set()

    def test_init_with_existing_tags(self) -> None:
        """Test initialization with existing tags."""
        tags = {"v1.0.0", "v1.0.1", "v1.1.0"}
        incrementer = VersionIncrementer(tags)
        assert incrementer.existing_tags == tags


class TestMajorIncrement:
    """Test major version incrementing."""

    def test_increment_major_basic(self) -> None:
        """Test basic major increment."""
        incrementer = VersionIncrementer()
        version = SemanticVersion.parse("1.2.3")
        result = incrementer.increment(version, IncrementType.MAJOR)

        assert result.major == 2
        assert result.minor == 0
        assert result.patch == 0
        assert result.prerelease is None
        assert result.metadata == version.metadata
        assert result.prefix == version.prefix

    def test_increment_major_with_prerelease(self) -> None:
        """Test major increment removes prerelease."""
        incrementer = VersionIncrementer()
        version = SemanticVersion.parse("1.2.3-alpha.1")
        result = incrementer.increment(version, IncrementType.MAJOR)

        assert result.major == 2
        assert result.minor == 0
        assert result.patch == 0
        assert result.prerelease is None

    def test_increment_major_preserves_metadata_and_prefix(self) -> None:
        """Test major increment preserves metadata and prefix when requested."""
        incrementer = VersionIncrementer(preserve_metadata=True)
        version = SemanticVersion.parse("v1.2.3-alpha+build")
        result = incrementer.increment(version, IncrementType.MAJOR)

        assert result.major == 2
        assert result.minor == 0
        assert result.patch == 0
        assert result.prerelease is None
        assert result.metadata == "build"
        assert result.prefix == "v"


class TestMinorIncrement:
    """Test minor version incrementing."""

    def test_increment_minor_basic(self) -> None:
        """Test basic minor increment."""
        incrementer = VersionIncrementer()
        version = SemanticVersion.parse("1.2.3")
        result = incrementer.increment(version, IncrementType.MINOR)

        assert result.major == 1
        assert result.minor == 3
        assert result.patch == 0
        assert result.prerelease is None

    def test_increment_minor_with_prerelease(self) -> None:
        """Test minor increment removes prerelease."""
        incrementer = VersionIncrementer()
        version = SemanticVersion.parse("1.2.3-alpha.1")
        result = incrementer.increment(version, IncrementType.MINOR)

        assert result.major == 1
        assert result.minor == 3
        assert result.patch == 0
        assert result.prerelease is None


class TestPatchIncrement:
    """Test patch version incrementing."""

    def test_increment_patch_basic(self) -> None:
        """Test basic patch increment."""
        incrementer = VersionIncrementer()
        version = SemanticVersion.parse("1.2.3")
        result = incrementer.increment(version, IncrementType.PATCH)

        assert result.major == 1
        assert result.minor == 2
        assert result.patch == 4
        assert result.prerelease is None

    def test_increment_patch_with_prerelease(self) -> None:
        """Test patch increment removes prerelease."""
        incrementer = VersionIncrementer()
        version = SemanticVersion.parse("1.2.3-alpha.1")
        result = incrementer.increment(version, IncrementType.PATCH)

        assert result.major == 1
        assert result.minor == 2
        assert result.patch == 4
        assert result.prerelease is None


class TestPrereleaseIncrement:
    """Test prerelease version incrementing."""

    def test_increment_prerelease_from_normal_version(self) -> None:
        """Test creating first prerelease from normal version."""
        incrementer = VersionIncrementer()
        version = SemanticVersion.parse("1.2.3")
        result = incrementer.increment(version, IncrementType.PRERELEASE)

        assert result.major == 1
        assert result.minor == 2
        assert result.patch == 4  # Patch should be incremented
        assert result.prerelease == "dev.1"

    def test_increment_prerelease_from_normal_version_with_type(self) -> None:
        """Test creating first prerelease with specific type."""
        incrementer = VersionIncrementer()
        version = SemanticVersion.parse("1.2.3")
        result = incrementer.increment(
            version, IncrementType.PRERELEASE, "alpha"
        )

        assert result.major == 1
        assert result.minor == 2
        assert result.patch == 4
        assert result.prerelease == "alpha.1"

    def test_increment_existing_prerelease_with_number(self) -> None:
        """Test incrementing existing prerelease with numeric component."""
        incrementer = VersionIncrementer()
        version = SemanticVersion.parse("1.2.3-alpha.1")
        result = incrementer.increment(version, IncrementType.PRERELEASE)

        assert result.major == 1
        assert result.minor == 2
        assert result.patch == 3
        assert result.prerelease == "alpha.2"

    def test_increment_existing_prerelease_trailing_number(self) -> None:
        """Test incrementing prerelease with trailing number in identifier."""
        incrementer = VersionIncrementer()
        version = SemanticVersion.parse("1.2.3-beta1")
        result = incrementer.increment(version, IncrementType.PRERELEASE)

        assert result.major == 1
        assert result.minor == 2
        assert result.patch == 3
        assert result.prerelease == "beta2"

    def test_increment_existing_prerelease_no_numbers(self) -> None:
        """Test incrementing prerelease without numeric components."""
        incrementer = VersionIncrementer()
        version = SemanticVersion.parse("1.2.3-alpha")
        result = incrementer.increment(version, IncrementType.PRERELEASE)

        assert result.major == 1
        assert result.minor == 2
        assert result.patch == 3
        assert result.prerelease == "alpha.1"

    def test_increment_complex_prerelease(self) -> None:
        """Test incrementing complex prerelease patterns."""
        incrementer = VersionIncrementer()
        version = SemanticVersion.parse("1.2.3-RC-SNAPSHOT.12.dev1")
        result = incrementer.increment(version, IncrementType.PRERELEASE)

        assert result.major == 1
        assert result.minor == 2
        assert result.patch == 3
        # Should increment the rightmost numeric component
        assert result.prerelease == "RC-SNAPSHOT.12.dev2"

    def test_increment_multiple_numeric_components(self) -> None:
        """Test incrementing prerelease with multiple numeric components."""
        incrementer = VersionIncrementer()
        version = SemanticVersion.parse("1.2.3-alpha.1.beta.2")
        result = incrementer.increment(version, IncrementType.PRERELEASE)

        assert result.major == 1
        assert result.minor == 2
        assert result.patch == 3
        # Should increment the rightmost numeric component (2 -> 3)
        assert result.prerelease == "alpha.1.beta.3"

    def test_dev_alias(self) -> None:
        """Test that DEV increment type works as alias for PRERELEASE."""
        incrementer = VersionIncrementer()
        version = SemanticVersion.parse("1.2.3")
        result = incrementer.increment(version, IncrementType.DEV)

        assert result.major == 1
        assert result.minor == 2
        assert result.patch == 4
        assert result.prerelease == "dev.1"


class TestConflictDetection:
    """Test conflict detection with existing tags."""

    def test_no_conflicts_empty_tags(self) -> None:
        """Test behavior when no existing tags are provided."""
        incrementer = VersionIncrementer()
        version = SemanticVersion.parse("1.2.3")
        result = incrementer.increment(version, IncrementType.PATCH)

        assert result.to_string() == "1.2.4"

    def test_no_conflicts_available_version(self) -> None:
        """Test behavior when incremented version doesn't conflict."""
        existing_tags = {"v1.2.0", "v1.2.1", "v1.2.2"}
        incrementer = VersionIncrementer(existing_tags)
        version = SemanticVersion.parse("v1.2.2")
        result = incrementer.increment(version, IncrementType.PATCH)

        assert result.to_string() == "v1.2.3"

    def test_conflict_resolution_prerelease(self) -> None:
        """Test conflict resolution for prerelease versions."""
        existing_tags = {"v1.2.4-dev.1", "v1.2.4-dev.2"}
        incrementer = VersionIncrementer(existing_tags)
        version = SemanticVersion.parse("v1.2.3")
        result = incrementer.increment(version, IncrementType.PRERELEASE)

        # Should find next available version
        assert result.to_string() == "v1.2.4-dev.3"

    def test_conflict_resolution_patch(self) -> None:
        """Test conflict resolution for patch versions."""
        existing_tags = {"v1.2.1", "v1.2.2"}
        incrementer = VersionIncrementer(existing_tags)
        version = SemanticVersion.parse("v1.2.0")
        result = incrementer.increment(version, IncrementType.PATCH)

        # Should skip to next available patch version
        assert result.to_string() == "v1.2.3"

    def test_conflict_resolution_minor(self) -> None:
        """Test conflict resolution for minor versions."""
        existing_tags = {"v1.3.0"}
        incrementer = VersionIncrementer(existing_tags)
        version = SemanticVersion.parse("v1.2.0")
        result = incrementer.increment(version, IncrementType.MINOR)

        # Should find next available version by incrementing patch
        assert result.to_string() == "v1.3.1"

    def test_conflict_resolution_major(self) -> None:
        """Test conflict resolution for major versions."""
        existing_tags = {"v2.0.0"}
        incrementer = VersionIncrementer(existing_tags)
        version = SemanticVersion.parse("v1.2.0")
        result = incrementer.increment(version, IncrementType.MAJOR)

        # Should find next available version by incrementing patch
        assert result.to_string() == "v2.0.1"

    def test_conflict_resolution_multiple_conflicts(self) -> None:
        """Test resolution when multiple versions conflict."""
        existing_tags = {
            "v1.2.4-dev.1",
            "v1.2.4-dev.2",
            "v1.2.4-dev.3",
            "v1.2.4-dev.4",
            "v1.2.4-dev.5",
        }
        incrementer = VersionIncrementer(existing_tags)
        version = SemanticVersion.parse("v1.2.3")
        result = incrementer.increment(version, IncrementType.PRERELEASE)

        assert result.to_string() == "v1.2.4-dev.6"

    def test_version_exists_checking(self) -> None:
        """Test internal version existence checking."""
        existing_tags = {"v1.2.3", "1.2.4", "V1.2.5"}
        incrementer = VersionIncrementer(existing_tags)

        # Should detect existence regardless of prefix differences
        v1 = SemanticVersion.parse("v1.2.3")
        v2 = SemanticVersion.parse("1.2.4")
        v3 = SemanticVersion.parse("v1.2.5")
        v4 = SemanticVersion.parse("1.2.6")

        assert incrementer._version_exists(v1)
        assert incrementer._version_exists(v2)
        assert incrementer._version_exists(v3)
        assert not incrementer._version_exists(v4)

    def test_fallback_to_prerelease_when_all_patches_exist(self) -> None:
        """Test fallback to prerelease when all patch versions are taken."""
        # Create a scenario where all reasonable patch versions are taken
        incrementer = VersionIncrementer(set())
        existing_tags = {
            f"v1.2.{i}" for i in range(1, incrementer.MAX_PATCH_ATTEMPTS)
        }
        incrementer.existing_tags = existing_tags
        version = SemanticVersion.parse("v1.2.0")
        result = incrementer.increment(version, IncrementType.PATCH)

        # Should find the next available patch version (v1.2.100)
        assert result.patch == incrementer.MAX_PATCH_ATTEMPTS
        assert not result.is_prerelease()


class TestNextAvailableVersion:
    """Test finding next available versions."""

    def test_find_next_available_prerelease_simple(self) -> None:
        """Test finding next available prerelease version."""
        existing_tags = {"v1.2.3-dev.1"}
        incrementer = VersionIncrementer(existing_tags)

        result = incrementer._find_next_available_prerelease(
            1, 2, 3, "dev", None, "v"
        )

        assert result.to_string() == "v1.2.3-dev.2"

    def test_find_next_available_version_complex(self) -> None:
        """Test finding next available version for complex prerelease."""
        existing_tags = {"v1.2.3-alpha.1", "v1.2.3-alpha.2"}
        incrementer = VersionIncrementer(existing_tags)

        base_version = SemanticVersion.parse("v1.2.3-alpha.1")
        result = incrementer._find_next_available_version(base_version)

        assert result.to_string() == "v1.2.3-alpha.3"

    def test_safety_break_prerelease(self) -> None:
        """Test safety break in prerelease version finding."""
        # Create a scenario where 1000+ versions would conflict
        existing_tags = {f"v1.2.3-dev.{i}" for i in range(1, 1002)}
        incrementer = VersionIncrementer(existing_tags)

        with pytest.raises(
            RuntimeError, match="Could not find available prerelease version"
        ):
            incrementer._find_next_available_prerelease(
                1, 2, 3, "dev", None, "v"
            )

    def test_safety_break_version(self) -> None:
        """Test safety break in version finding."""
        existing_tags = {f"v1.2.3-alpha.{i}" for i in range(1, 1002)}
        incrementer = VersionIncrementer(existing_tags)

        base_version = SemanticVersion.parse("v1.2.3-alpha.1")
        with pytest.raises(
            RuntimeError, match="Could not find available version"
        ):
            incrementer._find_next_available_version(base_version)


class TestVersionSuggestions:
    """Test version suggestion functionality."""

    def test_suggest_next_version_prerelease(self) -> None:
        """Test suggestions for prerelease increment."""
        incrementer = VersionIncrementer()
        version = SemanticVersion.parse("1.2.3")
        suggestions = incrementer.suggest_next_version(
            version, IncrementType.PRERELEASE
        )

        assert len(suggestions) > 0
        # Should include different prerelease types
        suggestion_strings = [s.to_string() for s in suggestions]
        assert any("dev" in s for s in suggestion_strings)

    def test_suggest_next_version_other_types(self) -> None:
        """Test suggestions for non-prerelease increments."""
        incrementer = VersionIncrementer()
        version = SemanticVersion.parse("1.2.3")

        for increment_type in [
            IncrementType.MAJOR,
            IncrementType.MINOR,
            IncrementType.PATCH,
        ]:
            suggestions = incrementer.suggest_next_version(
                version, increment_type
            )
            assert len(suggestions) == 1  # Should return single suggestion

    def test_suggest_next_version_unique(self) -> None:
        """Test that suggestions are unique."""
        incrementer = VersionIncrementer()
        version = SemanticVersion.parse("1.2.3")
        suggestions = incrementer.suggest_next_version(
            version, IncrementType.PRERELEASE
        )

        # Convert to strings for comparison
        suggestion_strings = [s.to_string() for s in suggestions]
        assert len(suggestion_strings) == len(set(suggestion_strings))


class TestErrorHandling:
    """Test error handling in version incrementer."""

    def test_unsupported_increment_type(self) -> None:
        """Test behavior with unsupported increment type."""
        incrementer = VersionIncrementer()
        version = SemanticVersion.parse("1.2.3")

        # Create a mock increment type that doesn't exist
        class FakeIncrementType:
            value = "fake"

        with pytest.raises(ValueError, match="Unsupported increment type"):
            incrementer.increment(version, FakeIncrementType())  # type: ignore

    def test_find_next_available_version_non_prerelease(self) -> None:
        """Test error when trying to find next available for non-prerelease."""
        incrementer = VersionIncrementer()
        version = SemanticVersion.parse("1.2.3")  # Not a prerelease

        with pytest.raises(
            ValueError, match="Base version must be a prerelease"
        ):
            incrementer._find_next_available_version(version)


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_zero_version_increment(self) -> None:
        """Test incrementing from 0.0.0."""
        incrementer = VersionIncrementer()
        version = SemanticVersion.parse("0.0.0")

        # Test all increment types
        major_result = incrementer.increment(version, IncrementType.MAJOR)
        assert major_result.to_string() == "1.0.0"

        minor_result = incrementer.increment(version, IncrementType.MINOR)
        assert minor_result.to_string() == "0.1.0"

        patch_result = incrementer.increment(version, IncrementType.PATCH)
        assert patch_result.to_string() == "0.0.1"

    def test_large_version_numbers(self) -> None:
        """Test incrementing very large version numbers."""
        incrementer = VersionIncrementer()
        version = SemanticVersion.parse("999999999.999999999.999999999")

        result = incrementer.increment(version, IncrementType.PATCH)
        assert result.major == 999999999
        assert result.minor == 999999999
        assert result.patch == 1000000000

    def test_preserve_metadata_all_increments(self) -> None:
        """Test that metadata is preserved across all increment types when explicitly requested."""
        incrementer = VersionIncrementer(preserve_metadata=True)
        version = SemanticVersion.parse("v1.2.3-alpha+build.123")

        for increment_type in [
            IncrementType.MAJOR,
            IncrementType.MINOR,
            IncrementType.PATCH,
            IncrementType.PRERELEASE,
        ]:
            result = incrementer.increment(version, increment_type)
            assert result.metadata == "build.123"
            assert result.prefix == "v"

    def test_strip_metadata_by_default(self) -> None:
        """Test that metadata is stripped by default across all increment types."""
        incrementer = VersionIncrementer(preserve_metadata=False)
        version = SemanticVersion.parse("v1.2.3-alpha+build.123")

        for increment_type in [
            IncrementType.MAJOR,
            IncrementType.MINOR,
            IncrementType.PATCH,
            IncrementType.PRERELEASE,
        ]:
            result = incrementer.increment(version, increment_type)
            assert result.metadata is None
            assert result.prefix == "v"

    def test_empty_prerelease_components(self) -> None:
        """Test handling of unusual prerelease patterns."""
        incrementer = VersionIncrementer()

        # Test version with dashes in prerelease
        version = SemanticVersion.parse("1.2.3----RC-SNAPSHOT.12.9.1--.12")
        result = incrementer.increment(version, IncrementType.PRERELEASE)

        # Should increment the rightmost numeric component (12)
        assert result.prerelease is not None and "13" in result.prerelease

    def test_mixed_case_prerelease_identifiers(self) -> None:
        """Test handling of mixed case prerelease identifiers."""
        incrementer = VersionIncrementer()
        version = SemanticVersion.parse("1.2.3-Alpha.Beta.1")
        result = incrementer.increment(version, IncrementType.PRERELEASE)

        assert result.prerelease == "Alpha.Beta.2"
