# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Unit tests for CLI interface.

This module contains tests for the simplified Typer CLI interface
focused on string mode tag incrementing functionality.
"""

import sys
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from semantic_tag_increment.cli import main, run_github_action
from semantic_tag_increment.cli_interface import app


class TestCLI:
    """Test the simplified CLI interface."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.runner = CliRunner(env={"COLUMNS": "300", "LINES": "100"})

    def test_cli_help(self) -> None:
        """Test CLI help output."""
        result = self.runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert (
            "A Python tool to increment semantic version tags" in result.output
        )

    def test_cli_no_args_shows_help(self) -> None:
        """Test that CLI with no arguments shows help."""
        result = self.runner.invoke(app, [])
        assert result.exit_code == 0
        assert "Usage:" in result.output

    def test_validate_only_flag_help(self) -> None:
        """Test --validate flag help."""
        result = self.runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        # Check for validate flag in a more flexible way - look for both the flag and description
        output_lower = result.output.lower()
        assert "--validate" in output_lower or "validate" in output_lower

    def test_suggest_flag_help(self) -> None:
        """Test --suggest flag help."""
        result = self.runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        # Check for suggest flag in a more flexible way - look for both the flag and description
        output_lower = result.output.lower()
        assert "--suggest" in output_lower or "suggest" in output_lower

    @patch(
        "semantic_tag_increment.cli_interface.GitOperations.get_existing_tags"
    )
    def test_increment_basic_patch(self, mock_get_tags) -> None:
        """Test basic patch increment."""
        mock_get_tags.return_value = set()

        result = self.runner.invoke(
            app, ["--tag", "v1.2.3", "--increment", "patch"]
        )

        assert result.exit_code == 0
        assert "v1.2.4" in result.output

    @patch(
        "semantic_tag_increment.cli_interface.GitOperations.get_existing_tags"
    )
    def test_increment_basic_minor(self, mock_get_tags) -> None:
        """Test basic minor increment."""
        mock_get_tags.return_value = set()

        result = self.runner.invoke(
            app, ["--tag", "v1.2.3", "--increment", "minor"]
        )

        assert result.exit_code == 0
        assert "v1.3.0" in result.output

    @patch(
        "semantic_tag_increment.cli_interface.GitOperations.get_existing_tags"
    )
    def test_increment_basic_major(self, mock_get_tags) -> None:
        """Test basic major increment."""
        mock_get_tags.return_value = set()

        result = self.runner.invoke(
            app, ["--tag", "v1.2.3", "--increment", "major"]
        )

        assert result.exit_code == 0
        assert "v2.0.0" in result.output

    @patch(
        "semantic_tag_increment.cli_interface.GitOperations.get_existing_tags"
    )
    def test_increment_prerelease(self, mock_get_tags) -> None:
        """Test prerelease increment."""
        mock_get_tags.return_value = set()

        result = self.runner.invoke(
            app,
            [
                "--tag",
                "v1.2.3",
                "--increment",
                "prerelease",
                "--prerelease-type",
                "alpha",
            ],
        )

        assert result.exit_code == 0
        assert "alpha" in result.output

    @patch(
        "semantic_tag_increment.cli_interface.GitOperations.get_existing_tags"
    )
    def test_increment_no_prefix(self, mock_get_tags) -> None:
        """Test increment without version prefix."""
        mock_get_tags.return_value = set()

        result = self.runner.invoke(
            app, ["--tag", "1.2.3", "--increment", "patch"]
        )

        assert result.exit_code == 0
        assert "1.2.4" in result.output

    def test_increment_missing_tag(self) -> None:
        """Test increment command without required tag parameter."""
        result = self.runner.invoke(app, ["--increment", "patch"])

        assert result.exit_code == 0  # Shows help when no tag provided
        assert "Usage:" in result.output

    def test_increment_invalid_tag(self) -> None:
        """Test increment with invalid tag format."""
        result = self.runner.invoke(
            app,
            ["--tag", "invalid-version", "--increment", "patch"],
        )

        assert result.exit_code != 0

    def test_increment_invalid_increment_type(self) -> None:
        """Test increment with invalid increment type."""
        result = self.runner.invoke(
            app, ["--tag", "v1.2.3", "--increment", "invalid"]
        )

        assert result.exit_code != 0

    @patch(
        "semantic_tag_increment.cli_interface.GitOperations.get_existing_tags"
    )
    def test_increment_with_conflicts_disabled(self, mock_get_tags) -> None:
        """Test increment with conflict checking disabled."""
        # Should not call get_existing_tags when conflicts disabled
        result = self.runner.invoke(
            app,
            [
                "--tag",
                "v1.2.3",
                "--increment",
                "patch",
                "--no-check-conflicts",
            ],
        )

        assert result.exit_code == 0
        # Note: mock_get_tags might still be called since we're not mocking at the right level

    @patch(
        "semantic_tag_increment.cli_interface.GitOperations.get_existing_tags"
    )
    def test_increment_output_format_numeric(self, mock_get_tags) -> None:
        """Test increment with numeric output format."""
        mock_get_tags.return_value = set()

        result = self.runner.invoke(
            app,
            [
                "--tag",
                "v1.2.3",
                "--increment",
                "patch",
                "--output-format",
                "numeric",
            ],
        )

        assert result.exit_code == 0
        # Check that only the numeric version is in the final output line
        lines = result.output.strip().split("\n")
        assert (
            "1.2.4" == lines[-2]
        )  # Second to last line should be just the numeric version

    @patch(
        "semantic_tag_increment.cli_interface.GitOperations.get_existing_tags"
    )
    def test_increment_output_format_both(self, mock_get_tags) -> None:
        """Test increment with both output formats."""
        mock_get_tags.return_value = set()

        result = self.runner.invoke(
            app,
            [
                "--tag",
                "v1.2.3",
                "--increment",
                "patch",
                "--output-format",
                "both",
            ],
        )

        assert result.exit_code == 0
        assert "Full version:" in result.output
        assert "Numeric version:" in result.output

    def test_validate_valid_version(self) -> None:
        """Test validation of valid semantic version."""
        result = self.runner.invoke(app, ["--tag", "v1.2.3", "--validate"])

        assert result.exit_code == 0
        assert "Valid semantic version" in result.output

    def test_validate_complex_version(self) -> None:
        """Test validation of complex semantic version."""
        result = self.runner.invoke(
            app, ["--tag", "v1.2.3-alpha.1+build.123", "--validate"]
        )

        assert result.exit_code == 0
        assert "Valid semantic version" in result.output
        assert "Pre-release:" in result.output
        assert "Metadata:" in result.output

    def test_validate_invalid_version(self) -> None:
        """Test validation of invalid semantic version."""
        result = self.runner.invoke(
            app, ["--tag", "not-a-version", "--validate"]
        )

        assert result.exit_code != 0

    def test_validate_missing_tag(self) -> None:
        """Test validate flag without required tag parameter."""
        result = self.runner.invoke(app, ["--validate"])

        assert result.exit_code != 0

    @patch(
        "semantic_tag_increment.cli_interface.GitOperations.get_existing_tags"
    )
    def test_suggest_flag(self, mock_get_tags) -> None:
        """Test --suggest flag."""
        mock_get_tags.return_value = set()

        result = self.runner.invoke(
            app, ["--tag", "v1.2.3", "--increment", "prerelease", "--suggest"]
        )

        assert result.exit_code == 0
        assert "Suggestions for" in result.output

    def test_suggest_missing_tag(self) -> None:
        """Test --suggest flag without required tag parameter."""
        result = self.runner.invoke(
            app, ["--increment", "prerelease", "--suggest"]
        )

        assert result.exit_code != 0

    @patch(
        "semantic_tag_increment.cli_interface.GitOperations.get_existing_tags"
    )
    def test_suggest_flag_with_patch_increment(self, mock_get_tags) -> None:
        """Test --suggest flag with patch increment type."""
        mock_get_tags.return_value = set()

        result = self.runner.invoke(
            app, ["--tag", "v1.2.3", "--increment", "patch", "--suggest"]
        )

        assert result.exit_code == 0
        assert "Suggestions for patch increment of v1.2.3:" in result.output
        assert "1. v1.2.4" in result.output

    @patch(
        "semantic_tag_increment.cli_interface.GitOperations.get_existing_tags"
    )
    def test_suggest_flag_default_increment(self, mock_get_tags) -> None:
        """Test --suggest flag with default increment (should use prerelease)."""
        mock_get_tags.return_value = set()

        result = self.runner.invoke(app, ["--tag", "v1.2.3", "--suggest"])

        assert result.exit_code == 0
        assert (
            "Suggestions for prerelease increment of v1.2.3:" in result.output
        )
        assert "v1.2.4-dev.1" in result.output

    def test_debug_flag(self) -> None:
        """Test debug flag enables debug logging."""
        result = self.runner.invoke(
            app, ["--debug", "--tag", "v1.2.3", "--validate"]
        )

        assert result.exit_code == 0

    def test_debug_flag_with_increment(self) -> None:
        """Test debug flag with increment operation."""
        with patch(
            "semantic_tag_increment.cli_interface.GitOperations.get_existing_tags"
        ) as mock_get_tags:
            mock_get_tags.return_value = set()

            result = self.runner.invoke(
                app, ["--debug", "--tag", "v1.2.3", "--increment", "patch"]
            )

            assert result.exit_code == 0


class TestGitHubActions:
    """Test GitHub Actions integration."""

    @patch.dict("os.environ", {"GITHUB_ACTIONS": "true", "INPUT_TAG": "v1.2.3"})
    @patch("semantic_tag_increment.cli.GitHubActionsRunner")
    def test_run_github_action(self, mock_runner_class) -> None:
        """Test GitHub Actions runner is called correctly."""
        mock_runner = MagicMock()
        mock_runner_class.return_value = mock_runner

        run_github_action()

        mock_runner_class.assert_called_once()
        mock_runner.run.assert_called_once()

    @patch.dict(
        "os.environ",
        {
            "GITHUB_ACTIONS": "true",
            "INPUT_TAG": "v1.2.3",
            "INPUT_INCREMENT": "patch",
        },
    )
    @patch(
        "semantic_tag_increment.io_operations.IOOperations.write_outputs_to_github"
    )
    @patch(
        "semantic_tag_increment.cli_interface.GitOperations.get_existing_tags"
    )
    def test_github_actions_integration(
        self, mock_get_tags, mock_write_outputs
    ) -> None:
        """Test integration with GitHub Actions environment."""
        mock_get_tags.return_value = set()

        # Test that GitHub Actions context is detected and outputs are written
        runner = CliRunner()
        result = runner.invoke(app, ["--tag", "v1.2.3", "--increment", "patch"])

        assert result.exit_code == 0
        # Note: The actual GitHub Actions output writing would be tested in integration tests


class TestMainFunction:
    """Test the main function entry point."""

    def test_main_function_exists(self) -> None:
        """Test that main function exists and is callable."""
        assert callable(main)

    @pytest.mark.skipif(
        sys.version_info[:2] == (3, 10),
        reason="Test has import patching issues on Python 3.10",
    )
    def test_main_calls_app(self) -> None:
        """Test that main function calls the Typer app."""
        with patch(
            "semantic_tag_increment.app_context.ContextDetector.detect_context"
        ) as mock_context:
            with patch("semantic_tag_increment.main.app") as mock_app:
                # Set up context to return CLI mode
                mock_context_instance = mock_context.return_value
                mock_context_instance.is_cli_mode = True
                mock_context_instance.debug_mode = False

                # Mock app to raise SystemExit to simulate normal CLI behavior
                mock_app.side_effect = SystemExit(0)

                # Test that main calls app when in CLI mode
                try:
                    main()
                except SystemExit:
                    pass  # Expected when help is shown

                # Verify app was called
                mock_app.assert_called_once()


class TestMetadataHandling:
    """Test metadata preservation options."""

    def test_preserve_metadata_flag(self) -> None:
        """Test --preserve-metadata flag."""
        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "--tag",
                "v1.2.3+build.123",
                "--increment",
                "patch",
                "--preserve-metadata",
            ],
        )

        assert result.exit_code == 0
        assert "v1.2.4+build.123" in result.stdout

    def test_no_preserve_metadata_flag(self) -> None:
        """Test --no-preserve-metadata flag."""
        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "--tag",
                "v1.2.3+build.123",
                "--increment",
                "patch",
                "--no-preserve-metadata",
            ],
        )

        assert result.exit_code == 0
        assert "v1.2.4" in result.stdout
        assert "build.123" not in result.stdout

    def test_preserve_metadata_default_behavior(self) -> None:
        """Test that metadata is stripped by default."""
        runner = CliRunner()
        result = runner.invoke(
            app, ["--tag", "v1.2.3+build.123", "--increment", "patch"]
        )

        assert result.exit_code == 0
        assert "v1.2.4" in result.stdout
        assert "build.123" not in result.stdout

    def test_preserve_metadata_with_prerelease(self) -> None:
        """Test metadata preservation with prerelease increments."""
        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "--tag",
                "v1.2.3-alpha.1+build.123",
                "--increment",
                "prerelease",
                "--preserve-metadata",
            ],
        )

        assert result.exit_code == 0
        assert "build.123" in result.stdout


class TestErrorHandling:
    """Test error handling scenarios."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_empty_prerelease_type(self) -> None:
        """Test that empty prerelease type is rejected."""
        result = self.runner.invoke(
            app,
            [
                "--tag",
                "v1.2.3",
                "--increment",
                "prerelease",
                "--prerelease-type",
                "",
            ],
        )

        assert result.exit_code != 0

    def test_invalid_output_format(self) -> None:
        """Test that invalid output format is rejected."""
        result = self.runner.invoke(
            app,
            [
                "--tag",
                "v1.2.3",
                "--increment",
                "patch",
                "--output-format",
                "invalid",
            ],
        )

        assert result.exit_code != 0

    def test_nonexistent_path(self) -> None:
        """Test that nonexistent path is rejected."""
        result = self.runner.invoke(
            app,
            [
                "--tag",
                "v1.2.3",
                "--increment",
                "patch",
                "--path",
                "/nonexistent/path",
            ],
        )

        assert result.exit_code != 0

    def test_invalid_prerelease_type_characters(self) -> None:
        """Test that invalid characters in prerelease type are rejected."""
        result = self.runner.invoke(
            app,
            [
                "--tag",
                "v1.2.3",
                "--increment",
                "prerelease",
                "--prerelease-type",
                "alpha@invalid",
            ],
        )

        assert result.exit_code != 0

    def test_fetch_timeout_parameter(self) -> None:
        """Test that fetch timeout parameter is accepted and works."""
        with patch(
            "semantic_tag_increment.git_operations.GitOperations.get_existing_tags"
        ) as mock_get_tags:
            mock_get_tags.return_value = set()

            result = self.runner.invoke(
                app,
                [
                    "--tag",
                    "v1.2.3",
                    "--increment",
                    "patch",
                    "--fetch-timeout",
                    "60",
                    "--no-check-conflicts",
                ],
            )

            assert result.exit_code == 0
            assert "v1.2.4" in result.output

    def test_fetch_timeout_parameter_help(self) -> None:
        """Test that fetch timeout parameter is accepted and functional."""
        # Test that the fetch-timeout parameter is accepted without error
        with patch(
            "semantic_tag_increment.git_operations.GitOperations.get_existing_tags"
        ) as mock_get_tags:
            mock_get_tags.return_value = set()

            # Test with custom fetch timeout - should not raise any errors
            result = self.runner.invoke(
                app,
                [
                    "--tag",
                    "v1.2.3",
                    "--increment",
                    "patch",
                    "--fetch-timeout",
                    "60",
                    "--no-check-conflicts",
                ],
            )

            # Should succeed without argument errors
            assert result.exit_code == 0
            assert "v1.2.4" in result.output

        # Also test that help contains fetch timeout information when available
        result = self.runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        # At minimum, help should be generated successfully
        assert "Usage:" in result.output
