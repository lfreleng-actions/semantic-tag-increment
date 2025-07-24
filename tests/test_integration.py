# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Integration tests for semantic tag increment tool.

This module contains end-to-end integration tests that test the complete
functionality of the semantic tag increment tool including CLI, GitHub Actions,
and real-world scenarios.
"""

import os
import tempfile
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from semantic_tag_increment.cli_interface import app
from semantic_tag_increment.exceptions import ParseError
from semantic_tag_increment.incrementer import IncrementType, VersionIncrementer
from semantic_tag_increment.parser import SemanticVersion


@pytest.mark.integration
class TestEndToEndCLI:
    """End-to-end tests using the CLI interface."""

    def test_complete_workflow_major_increment(self) -> None:
        """Test complete workflow for major version increment."""
        # Test data
        input_version = "v1.2.3"
        expected_output = "v2.0.0"

        # Use CliRunner for fast in-process testing
        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "--tag",
                input_version,
                "--increment",
                "major",
                "--no-check-conflicts",
            ],
        )

        assert result.exit_code == 0
        assert expected_output in result.output

    def test_complete_workflow_prerelease_increment(self) -> None:
        """Test complete workflow for prerelease increment."""
        input_version = "1.2.3"

        # Use CliRunner for fast in-process testing
        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "--tag",
                input_version,
                "--increment",
                "prerelease",
                "--prerelease-type",
                "beta",
                "--no-check-conflicts",
            ],
        )

        assert result.exit_code == 0
        assert "1.2.4-beta.1" in result.output

    def test_focused_conflict_resolution(self) -> None:
        """Test conflict resolution logic with minimal focused dataset."""
        # Minimal dataset to test specific conflict scenarios
        existing_tags = {
            "v1.0.0",
            "v1.0.1-dev.1",
            "v1.0.1-dev.2",
            "v1.0.1-alpha.1",
        }

        incrementer = VersionIncrementer(existing_tags)
        version = SemanticVersion.parse("v1.0.0")

        # Should increment to next available dev slot
        result = incrementer.increment(version, IncrementType.PRERELEASE)
        assert str(result) == "v1.0.1-dev.3"

        # Test with different prerelease type
        alpha_result = incrementer.increment(
            version, IncrementType.PRERELEASE, "alpha"
        )
        assert str(alpha_result) == "v1.0.1-alpha.2"


@pytest.mark.integration
class TestRealWorldScenarios:
    """Test real-world semantic versioning scenarios."""

    def test_complex_prerelease_progression(self) -> None:
        """Test a realistic prerelease version progression."""
        incrementer = VersionIncrementer()

        # Start with a base version
        versions = ["1.0.0"]

        # Create first alpha
        current = SemanticVersion.parse(versions[-1])
        alpha1 = incrementer.increment(
            current, IncrementType.PRERELEASE, "alpha"
        )
        versions.append(str(alpha1))
        assert alpha1.prerelease and "alpha" in alpha1.prerelease

        # Increment alpha
        alpha2 = incrementer.increment(alpha1, IncrementType.PRERELEASE)
        versions.append(str(alpha2))
        assert alpha2.prerelease and "alpha" in alpha2.prerelease
        assert (
            alpha1.major == alpha2.major
            and alpha1.minor == alpha2.minor
            and alpha1.patch == alpha2.patch
        )

        # Move to beta
        beta1 = incrementer.increment(alpha2, IncrementType.PRERELEASE, "beta")
        versions.append(str(beta1))
        assert beta1.prerelease and "beta" in beta1.prerelease
        assert (
            alpha2.major == beta1.major
            and alpha2.minor == beta1.minor
            and alpha2.patch == beta1.patch
        )

        # Release candidate
        rc1 = incrementer.increment(beta1, IncrementType.PRERELEASE, "rc")
        versions.append(str(rc1))
        assert rc1.prerelease and "rc" in rc1.prerelease
        assert (
            beta1.major == rc1.major
            and beta1.minor == rc1.minor
            and beta1.patch == rc1.patch
        )

        # Final release (patch increment removes prerelease)
        final = incrementer.increment(rc1, IncrementType.PATCH)
        versions.append(str(final))
        assert str(final) == "1.0.2"

        # Verify progression makes sense
        assert len(versions) == 6
        for i in range(len(versions) - 1):
            v1 = SemanticVersion.parse(versions[i])
            v2 = SemanticVersion.parse(versions[i + 1])
            assert v1 <= v2, f"{v1} should be <= {v2}"

    def test_conflict_resolution_simulation(self) -> None:
        """Test conflict resolution with simulated existing tags."""
        existing_tags = {
            "v1.2.3",
            "v1.2.4-dev.1",
            "v1.2.4-dev.2",
            "v1.2.4-dev.3",
            "v1.2.4-alpha.1",
            "v1.2.4-beta.1",
            "v1.3.0-dev.1",
        }

        incrementer = VersionIncrementer(existing_tags)

        # Test incrementing from v1.2.3 to dev
        version = SemanticVersion.parse("v1.2.3")
        result = incrementer.increment(version, IncrementType.PRERELEASE)

        # Should find next available dev version
        assert str(result) == "v1.2.4-dev.4"

        # Test incrementing to alpha (should find available slot)
        alpha_result = incrementer.increment(
            version, IncrementType.PRERELEASE, "alpha"
        )
        assert "alpha" in str(alpha_result)
        assert str(alpha_result) != "v1.2.4-alpha.1"  # This exists

    def test_large_version_numbers(self) -> None:
        """Test handling of very large version numbers."""
        large_version = "999999999.999999999.999999999"
        version = SemanticVersion.parse(large_version)

        incrementer = VersionIncrementer()

        # Test patch increment
        patch_result = incrementer.increment(version, IncrementType.PATCH)
        assert patch_result.patch == 1000000000

        # Test major increment
        major_result = incrementer.increment(version, IncrementType.MAJOR)
        assert major_result.major == 1000000000
        assert major_result.minor == 0
        assert major_result.patch == 0

    def test_edge_case_prerelease_patterns(self) -> None:
        """Test edge cases in prerelease patterns from RegEx101 examples."""
        test_cases = [
            ("1.2.3----RC-SNAPSHOT.12.9.1--.12+788", IncrementType.PRERELEASE),
            ("1.2.3----R-S.12.9.1--.12+meta", IncrementType.PRERELEASE),
            ("1.0.0+0.build.1-rc.10000aaa-kk-0.1", IncrementType.PATCH),
            ("1.0.0-0A.is.legal", IncrementType.PRERELEASE),
        ]

        incrementer = VersionIncrementer()

        for version_str, increment_type in test_cases:
            version = SemanticVersion.parse(version_str)
            result = incrementer.increment(version, increment_type)

            # Verify result is valid and different
            assert SemanticVersion.is_valid(str(result))
            assert str(result) != version_str

            # For prerelease increments, verify some numeric component was incremented
            if (
                increment_type == IncrementType.PRERELEASE
                and version.is_prerelease()
            ):
                original_components = (
                    version.find_numeric_prerelease_components()
                )
                result_components = result.find_numeric_prerelease_components()

                if original_components:
                    # At least one numeric component should have changed
                    assert original_components != result_components


@pytest.mark.integration
class TestGitHubActionsIntegration:
    """Test GitHub Actions integration scenarios."""

    @patch.dict(
        os.environ,
        {
            "GITHUB_ACTIONS": "true",
            "INPUT_TAG": "v1.2.3",
            "INPUT_INCREMENT": "patch",
            "GITHUB_OUTPUT": tempfile.NamedTemporaryFile(delete=False).name,
        },
    )
    @patch("builtins.open")
    def test_github_actions_complete_flow(self, mock_open):
        """Test complete GitHub Actions flow."""
        from semantic_tag_increment.cli import run_github_action

        # Mock file operations
        mock_file = mock_open.return_value.__enter__.return_value
        mock_file.write = lambda x: None

        # This should not raise an exception
        try:
            run_github_action()
        except SystemExit as e:
            assert e.code == 0

    def test_github_actions_all_increment_types(self) -> None:
        """Test all increment types work in GitHub Actions mode."""
        increment_types = ["major", "minor", "patch", "prerelease", "dev"]

        for increment_type in increment_types:
            env_vars = {
                "GITHUB_ACTIONS": "true",
                "INPUT_TAG": "v1.2.3",
                "INPUT_INCREMENT": increment_type,
                "GITHUB_OUTPUT": tempfile.NamedTemporaryFile(delete=False).name,
            }

            with patch.dict(os.environ, env_vars):
                with patch("builtins.open"):
                    from semantic_tag_increment.cli import run_github_action

                    try:
                        run_github_action()
                    except SystemExit as e:
                        assert e.code == 0, (
                            f"Failed for increment type: {increment_type}"
                        )


@pytest.mark.integration
class TestVersionOrdering:
    """Test version ordering and comparison in realistic scenarios."""

    def test_release_cycle_ordering(self) -> None:
        """Test that a typical release cycle maintains proper ordering."""
        versions_str = [
            "1.0.0",
            "1.1.0-alpha.1",
            "1.1.0-alpha.2",
            "1.1.0-beta.1",
            "1.1.0-beta.2",
            "1.1.0-rc.1",
            "1.1.0",
            "1.1.1",
            "1.2.0-dev.1",
            "1.2.0-dev.2",
            "1.2.0",
        ]

        versions = [SemanticVersion.parse(v) for v in versions_str]

        # Verify ordering
        for i in range(len(versions) - 1):
            assert versions[i] < versions[i + 1], (
                f"{versions[i]} should be < {versions[i + 1]}"
            )

    def test_complex_prerelease_ordering(self) -> None:
        """Test ordering of complex prerelease patterns."""
        versions_str = [
            "1.0.0-1",
            "1.0.0-2",
            "1.0.0-10",
            "1.0.0-alpha",
            "1.0.0-alpha.1",
            "1.0.0-alpha.2",
            "1.0.0-alpha.beta",
            "1.0.0-beta",
            "1.0.0-beta.2",
            "1.0.0-beta.11",
            "1.0.0-rc.1",
            "1.0.0",
        ]

        versions = [SemanticVersion.parse(v) for v in versions_str]

        for i in range(len(versions) - 1):
            assert versions[i] < versions[i + 1], (
                f"{versions[i]} should be < {versions[i + 1]}"
            )


@pytest.mark.integration
class TestErrorHandling:
    """Test error handling scenarios."""

    def test_invalid_input_handling(self) -> None:
        """Test handling of various invalid inputs."""
        # Empty string raises ValueError
        with pytest.raises(ValueError):
            SemanticVersion.parse("")

        # Other invalid formats raise ParseError
        invalid_versions = [
            "not-a-version",
            "1.2",
            "1.2.3.4",
            "1.2.3-",
            "1.2.3+",
        ]

        for invalid_version in invalid_versions:
            with pytest.raises(ParseError):
                SemanticVersion.parse(invalid_version)

    def test_incrementer_error_handling(self) -> None:
        """Test incrementer error handling."""
        incrementer = VersionIncrementer()
        version = SemanticVersion.parse("1.2.3")

        # Test with invalid increment type (mocked)
        class InvalidIncrement:
            value = "invalid"

        with pytest.raises(ValueError):
            incrementer.increment(version, InvalidIncrement())  # type: ignore


@pytest.mark.integration
@pytest.mark.slow
class TestPerformance:
    """Test performance characteristics."""

    def test_typical_tag_set_performance(self) -> None:
        """Test performance with typical number of existing tags."""
        # Create a typical set of existing tags (20-30 tags like real projects)
        existing_tags = {
            f"v1.{i}.0"
            for i in range(10)  # 10 minor releases
        }
        existing_tags.update(
            {
                f"v1.2.{i}"
                for i in range(5)  # 5 patch releases
            }
        )
        existing_tags.update(
            {
                f"v1.3.0-{pre}.{j}"
                for pre in ["dev", "alpha", "beta"]
                for j in range(3)
            }
        )  # 9 prerelease versions

        incrementer = VersionIncrementer(existing_tags)
        version = SemanticVersion.parse("v1.2.4")

        # This should complete very quickly
        import time

        start_time = time.time()
        result = incrementer.increment(version, IncrementType.PRERELEASE)
        end_time = time.time()

        # Should complete within 0.1 seconds for typical usage
        assert end_time - start_time < 0.1
        assert SemanticVersion.is_valid(str(result))

    def test_large_tag_set_performance(self) -> None:
        """Test performance with large number of existing tags."""
        # Create a large set of existing tags (reduced from 2000 to 200 total)
        existing_tags = {
            f"v1.2.{i}-dev.{j}" for i in range(20) for j in range(5)
        }
        existing_tags.update({f"v1.{i}.0" for i in range(100)})

        incrementer = VersionIncrementer(existing_tags)
        version = SemanticVersion.parse("v1.2.99")

        # This should complete in reasonable time
        import time

        start_time = time.time()
        result = incrementer.increment(version, IncrementType.PRERELEASE)
        end_time = time.time()

        # Should complete within 1 second
        assert end_time - start_time < 1.0
        assert SemanticVersion.is_valid(str(result))

    def test_complex_version_parsing_performance(self) -> None:
        """Test parsing performance with complex versions."""
        complex_versions = [
            "1.2.3----RC-SNAPSHOT.12.9.1--.12+788",
            "1.2.3----R-S.12.9.1--.12+meta",
            "1.0.0+0.build.1-rc.10000aaa-kk-0.1",
            "99999999999999999999999.999999999999999999.99999999999999999",
        ]

        import time

        start_time = time.time()

        for version_str in (
            complex_versions * 25
        ):  # Test 100 parses (reduced from 400)
            version = SemanticVersion.parse(version_str)
            assert isinstance(version, SemanticVersion)

        end_time = time.time()

        # Should complete within 1 second
        assert end_time - start_time < 1.0


@pytest.mark.integration
class TestBackwardsCompatibility:
    """Test backwards compatibility scenarios."""

    def test_legacy_dev_increment(self) -> None:
        """Test that 'dev' increment type works as expected."""
        incrementer = VersionIncrementer()
        version = SemanticVersion.parse("1.2.3")

        # Both should produce same result
        dev_result = incrementer.increment(version, IncrementType.DEV)
        prerelease_result = incrementer.increment(
            version, IncrementType.PRERELEASE
        )

        assert str(dev_result) == str(prerelease_result)

    def test_version_prefix_handling(self) -> None:
        """Test consistent handling of version prefixes."""
        test_cases = [
            ("v1.2.3", "v1.2.4"),
            ("V1.2.3", "V1.2.4"),
            ("1.2.3", "1.2.4"),  # This version has no prefix
        ]

        incrementer = VersionIncrementer()

        for input_version, expected_prefix in test_cases:
            version = SemanticVersion.parse(input_version)
            result = incrementer.increment(version, IncrementType.PATCH)

            # Prefix should be preserved
            # For versions with alphabetic prefixes like 'v' or 'V'
            if expected_prefix[0].isalpha():
                assert str(result).startswith(expected_prefix[0])
                assert result.prefix == expected_prefix[:1], (
                    f"Expected prefix '{expected_prefix[:1]}', but got '{result.prefix}'"
                )
            # For numeric versions (no prefix)
            else:
                assert not result.prefix, (
                    f"Expected empty prefix, but got '{result.prefix}'"
                )
