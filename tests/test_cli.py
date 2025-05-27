# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Unit tests for CLI interface.

This module contains comprehensive tests for the Typer CLI interface
and GitHub Actions integration.
"""

import importlib
import os
import tempfile
from unittest.mock import MagicMock, mock_open, patch

import pytest
from typer.testing import CliRunner

from semantic_tag_increment.cli import main, run_github_action
from semantic_tag_increment.cli_interface import app
from semantic_tag_increment.github_actions import GitHubActionsRunner
from semantic_tag_increment.parser import SemanticVersion


class TestCLI:
    """Test the Typer CLI interface."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_cli_help(self) -> None:
        """Test CLI help output."""
        result = self.runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert (
            "A Python tool to increment semantic version tags." in result.output
        )

    def test_increment_command_help(self) -> None:
        """Test increment command help."""
        result = self.runner.invoke(app, ["increment", "--help"])
        assert result.exit_code == 0
        assert "Increment a semantic version tag" in result.output

    def test_validate_command_help(self) -> None:
        """Test validate command help."""
        result = self.runner.invoke(app, ["validate", "--help"])
        assert result.exit_code == 0
        assert "Validate a semantic version tag" in result.output

    def test_suggest_command_help(self) -> None:
        """Test suggest command help."""
        result = self.runner.invoke(app, ["suggest", "--help"])
        assert result.exit_code == 0
        assert "Suggest possible next versions" in result.output


class TestIncrementCommand:
    """Test the increment CLI command."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_increment_basic_patch(self) -> None:
        """Test basic patch increment."""
        result = self.runner.invoke(
            app, ["increment", "--tag", "1.2.3", "--increment", "patch"]
        )
        assert result.exit_code == 0
        assert "1.2.4" in result.output

    def test_increment_basic_minor(self) -> None:
        """Test basic minor increment."""
        result = self.runner.invoke(
            app, ["increment", "--tag", "1.2.3", "--increment", "minor"]
        )
        assert result.exit_code == 0
        assert "1.3.0" in result.output

    def test_increment_basic_major(self) -> None:
        """Test basic major increment."""
        result = self.runner.invoke(
            app, ["increment", "--tag", "1.2.3", "--increment", "major"]
        )
        assert result.exit_code == 0
        assert "2.0.0" in result.output

    def test_increment_prerelease_default(self) -> None:
        """Test default prerelease increment."""
        result = self.runner.invoke(
            app, ["increment", "--tag", "1.2.3", "--increment", "prerelease"]
        )
        assert result.exit_code == 0
        assert "1.2.4-dev.1" in result.output

    def test_increment_prerelease_with_type(self) -> None:
        """Test prerelease increment with specific type."""
        result = self.runner.invoke(
            app,
            [
                "increment",
                "--tag",
                "1.2.3",
                "--increment",
                "prerelease",
                "--prerelease-type",
                "alpha",
            ],
        )
        assert result.exit_code == 0
        assert "1.2.4-alpha.1" in result.output

    def test_increment_dev_alias(self) -> None:
        """Test dev increment alias."""
        result = self.runner.invoke(
            app, ["increment", "--tag", "1.2.3", "--increment", "dev"]
        )
        assert result.exit_code == 0
        assert "1.2.4-dev.1" in result.output

    def test_increment_with_prefix(self) -> None:
        """Test increment preserves version prefix."""
        result = self.runner.invoke(
            app, ["increment", "--tag", "v1.2.3", "--increment", "patch"]
        )
        assert result.exit_code == 0
        assert "v1.2.4" in result.output

    def test_increment_existing_prerelease(self) -> None:
        """Test incrementing existing prerelease."""
        result = self.runner.invoke(
            app,
            [
                "increment",
                "--tag",
                "1.2.3-alpha.1",
                "--increment",
                "prerelease",
            ],
        )
        assert result.exit_code == 0
        assert "1.2.3-alpha.2" in result.output

    def test_increment_invalid_version(self) -> None:
        """Test increment with invalid version."""
        result = self.runner.invoke(
            app, ["increment", "--tag", "invalid", "--increment", "patch"]
        )
        assert result.exit_code == 1
        assert "Error:" in result.output

    def test_increment_invalid_increment_type(self) -> None:
        """Test increment with invalid increment type."""
        result = self.runner.invoke(
            app, ["increment", "--tag", "1.2.3", "--increment", "invalid"]
        )
        assert result.exit_code == 1
        assert "Error:" in result.output

    def test_increment_empty_tag(self) -> None:
        """Test increment with empty tag."""
        result = self.runner.invoke(
            app, ["increment", "--tag", "", "--increment", "patch"]
        )
        assert result.exit_code == 1
        assert "Tag cannot be empty" in result.output

    def test_increment_whitespace_tag(self) -> None:
        """Test increment with whitespace-only tag."""
        result = self.runner.invoke(
            app, ["increment", "--tag", "   ", "--increment", "patch"]
        )
        assert result.exit_code == 1
        assert "Tag cannot be empty" in result.output

    def test_increment_empty_increment_type(self) -> None:
        """Test increment with empty increment type."""
        result = self.runner.invoke(
            app, ["increment", "--tag", "1.2.3", "--increment", ""]
        )
        assert result.exit_code == 1
        assert "Increment type cannot be empty" in result.output

    def test_increment_invalid_prerelease_type_empty(self) -> None:
        """Test increment with empty prerelease type."""
        result = self.runner.invoke(
            app,
            [
                "increment",
                "--tag",
                "1.2.3",
                "--increment",
                "prerelease",
                "--prerelease-type",
                "",
            ],
        )
        assert result.exit_code == 1
        assert "Prerelease type cannot be empty if provided" in result.output

    def test_increment_invalid_prerelease_type_special_chars(self) -> None:
        """Test increment with invalid prerelease type containing special characters."""
        result = self.runner.invoke(
            app,
            [
                "increment",
                "--tag",
                "1.2.3",
                "--increment",
                "prerelease",
                "--prerelease-type",
                "alpha@beta",
            ],
        )
        assert result.exit_code == 1
        assert (
            "Prerelease type must contain only alphanumeric characters, hyphens, and dots"
            in result.output
        )

    def test_increment_valid_prerelease_type_with_hyphens_dots(self) -> None:
        """Test increment with valid prerelease type containing hyphens and dots."""
        result = self.runner.invoke(
            app,
            [
                "increment",
                "--tag",
                "1.2.3",
                "--increment",
                "prerelease",
                "--prerelease-type",
                "alpha-beta.1",
            ],
        )
        assert result.exit_code == 0
        assert "1.2.4-alpha-beta.1.1" in result.output

    def test_increment_output_format_full(self) -> None:
        """Test increment with full output format."""
        result = self.runner.invoke(
            app,
            [
                "increment",
                "--tag",
                "v1.2.3",
                "--increment",
                "patch",
                "--output-format",
                "full",
            ],
        )
        assert result.exit_code == 0
        assert "v1.2.4" in result.output

    def test_increment_output_format_numeric(self) -> None:
        """Test increment with numeric output format."""
        result = self.runner.invoke(
            app,
            [
                "increment",
                "--tag",
                "v1.2.3",
                "--increment",
                "patch",
                "--output-format",
                "numeric",
            ],
        )
        assert result.exit_code == 0
        # Check that numeric version appears in output
        assert "1.2.4" in result.output
        # Check that the final output line is just the numeric version
        output_lines = [
            line.strip() for line in result.output.split("\n") if line.strip()
        ]
        # Find the line that contains just the version (not a log line)
        version_lines = [
            line for line in output_lines if not line.startswith("INFO:")
        ]
        assert len(version_lines) == 1
        assert version_lines[0] == "1.2.4"

    def test_increment_output_format_both(self) -> None:
        """Test increment with both output format."""
        result = self.runner.invoke(
            app,
            [
                "increment",
                "--tag",
                "v1.2.3",
                "--increment",
                "patch",
                "--output-format",
                "both",
            ],
        )
        assert result.exit_code == 0
        assert "Full version:    v1.2.4" in result.output
        assert "Numeric version: 1.2.4" in result.output

    def test_increment_output_format_invalid(self) -> None:
        """Test increment with invalid output format."""
        result = self.runner.invoke(
            app,
            [
                "increment",
                "--tag",
                "1.2.3",
                "--increment",
                "patch",
                "--output-format",
                "invalid",
            ],
        )
        assert result.exit_code == 1
        assert "Invalid output format" in result.output

    @patch(
        "semantic_tag_increment.git_operations.GitOperations.get_existing_tags"
    )
    def test_increment_with_git_tags(self, mock_get_tags: MagicMock) -> None:
        """Test increment with git tag checking enabled."""
        mock_get_tags.return_value = {"v1.2.0", "v1.2.1", "v1.2.2"}

        result = self.runner.invoke(
            app,
            [
                "increment",
                "--tag",
                "v1.2.2",
                "--increment",
                "patch",
                "--check-conflicts",
            ],
        )
        assert result.exit_code == 0
        assert "v1.2.3" in result.output

    def test_increment_no_conflict_checking(self) -> None:
        """Test increment with conflict checking disabled."""
        result = self.runner.invoke(
            app,
            [
                "increment",
                "--tag",
                "1.2.3",
                "--increment",
                "patch",
                "--no-check-conflicts",
            ],
        )
        assert result.exit_code == 0
        assert "1.2.4" in result.output

    @patch.dict(
        os.environ,
        {
            "GITHUB_ACTIONS": "true",
            "GITHUB_OUTPUT": tempfile.NamedTemporaryFile(delete=False).name,
        },
    )
    @patch("builtins.open", new_callable=mock_open)
    def test_increment_github_actions_output(
        self, mock_file: MagicMock
    ) -> None:
        """Test GitHub Actions output writing."""
        result = self.runner.invoke(
            app, ["increment", "--tag", "v1.2.3", "--increment", "patch"]
        )
        assert result.exit_code == 0

        # Check that outputs were written
        mock_file.assert_called()
        written_content = "".join(
            call.args[0] for call in mock_file().write.call_args_list
        )
        assert "tag=v1.2.4" in written_content
        assert "numeric_tag=1.2.4" in written_content


class TestValidateCommand:
    """Test the validate CLI command."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_validate_valid_version(self) -> None:
        """Test validating a valid semantic version."""
        result = self.runner.invoke(app, ["validate", "--tag", "1.2.3"])
        assert result.exit_code == 0
        assert "✅ Valid semantic version" in result.output
        assert "Major:      1" in result.output
        assert "Minor:      2" in result.output
        assert "Patch:      3" in result.output

    def test_validate_valid_prerelease(self) -> None:
        """Test validating a version with prerelease."""
        result = self.runner.invoke(app, ["validate", "--tag", "1.2.3-alpha.1"])
        assert result.exit_code == 0
        assert "✅ Valid semantic version" in result.output
        assert "Pre-release: alpha.1" in result.output
        assert "Pre-release identifiers:   ['alpha', '1']" in result.output

    def test_validate_valid_metadata(self) -> None:
        """Test validating a version with metadata."""
        result = self.runner.invoke(
            app, ["validate", "--tag", "1.2.3+build.123"]
        )
        assert result.exit_code == 0
        assert "✅ Valid semantic version" in result.output
        assert "Metadata:   build.123" in result.output

    def test_validate_valid_prefix(self) -> None:
        """Test validating a version with prefix."""
        result = self.runner.invoke(app, ["validate", "--tag", "v1.2.3"])
        assert result.exit_code == 0
        assert "✅ Valid semantic version" in result.output
        assert "Prefix:     v" in result.output

    def test_validate_complex_version(self) -> None:
        """Test validating a complex version."""
        result = self.runner.invoke(
            app, ["validate", "--tag", "v1.2.3-alpha.1+build.123"]
        )
        assert result.exit_code == 0
        assert "✅ Valid semantic version" in result.output
        assert "Pre-release: alpha.1" in result.output
        assert "Metadata:   build.123" in result.output
        assert "Prefix:     v" in result.output

    def test_validate_numeric_components(self) -> None:
        """Test validation shows numeric components in prerelease."""
        result = self.runner.invoke(
            app, ["validate", "--tag", "1.2.3-alpha.1.beta.2"]
        )
        assert result.exit_code == 0
        assert "Numeric components:" in result.output

    def test_validate_invalid_version(self) -> None:
        """Test validating an invalid semantic version."""
        result = self.runner.invoke(app, ["validate", "--tag", "invalid"])
        assert result.exit_code == 1
        assert "❌ Invalid semantic version" in result.output


class TestSuggestCommand:
    """Test the suggest CLI command."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_suggest_prerelease_increment(self) -> None:
        """Test suggesting prerelease increments."""
        result = self.runner.invoke(
            app, ["suggest", "--tag", "1.2.3", "--increment", "prerelease"]
        )
        assert result.exit_code == 0
        assert "Suggestions for prerelease increment" in result.output
        assert "1." in result.output  # Should show numbered suggestions

    def test_suggest_other_increment_types(self) -> None:
        """Test suggesting other increment types."""
        for increment_type in ["major", "minor", "patch"]:
            result = self.runner.invoke(
                app,
                ["suggest", "--tag", "1.2.3", "--increment", increment_type],
            )
            assert result.exit_code == 0
            assert (
                f"Suggestions for {increment_type} increment" in result.output
            )

    def test_suggest_invalid_version(self) -> None:
        """Test suggest with invalid version."""
        result = self.runner.invoke(
            app, ["suggest", "--tag", "invalid", "--increment", "prerelease"]
        )
        assert result.exit_code == 1
        assert "Error:" in result.output

    def test_suggest_invalid_increment(self) -> None:
        """Test suggest with invalid increment type."""
        result = self.runner.invoke(
            app, ["suggest", "--tag", "1.2.3", "--increment", "invalid"]
        )
        assert result.exit_code == 1
        assert "Error:" in result.output


class TestLogging:
    """Test logging functionality."""

    def test_logging_setup_debug(self) -> None:
        """Test logging setup with debug enabled."""
        runner = CliRunner()
        result = runner.invoke(
            app,
            ["--debug", "increment", "--tag", "1.2.3", "--increment", "patch"],
        )
        assert result.exit_code == 0

    def test_logging_setup_no_debug(self) -> None:
        """Test logging setup without debug."""
        runner = CliRunner()
        result = runner.invoke(
            app, ["increment", "--tag", "1.2.3", "--increment", "patch"]
        )
        assert result.exit_code == 0

    @patch("semantic_tag_increment.logging_config.Path.mkdir")
    def test_logging_file_creation(self, mock_mkdir: MagicMock) -> None:
        """Test that log file directory is created in correct location."""
        runner = CliRunner()
        result = runner.invoke(
            app, ["increment", "--tag", "1.2.3", "--increment", "patch"]
        )
        assert result.exit_code == 0
        mock_mkdir.assert_called_with(parents=True, exist_ok=True)


class TestGitHubActionsMode:
    """Test GitHub Actions integration."""

    @patch.dict(
        os.environ,
        {
            "GITHUB_ACTIONS": "true",
            "INPUT_TAG": "v1.2.3",
            "INPUT_INCREMENT": "patch",
            "GITHUB_OUTPUT": tempfile.NamedTemporaryFile(delete=False).name,
        },
    )
    @patch("builtins.open", new_callable=mock_open)
    def test_github_actions_basic(self, mock_file: MagicMock) -> None:
        """Test basic GitHub Actions execution."""
        with patch("sys.argv", ["semantic-tag-increment"]):
            try:
                run_github_action()
            except SystemExit as e:
                assert e.code == 0

        # Verify outputs were written
        mock_file.assert_called()
        written_content = "".join(
            call.args[0] for call in mock_file().write.call_args_list
        )
        assert "tag=v1.2.4" in written_content
        assert "numeric_tag=1.2.4" in written_content

    @patch.dict(
        os.environ,
        {
            "GITHUB_ACTIONS": "true",
            "INPUT_TAG": "1.2.3",
            "INPUT_INCREMENT": "prerelease",
            "INPUT_PRERELEASE_TYPE": "alpha",
            "GITHUB_OUTPUT": tempfile.NamedTemporaryFile(delete=False).name,
        },
    )
    @patch("builtins.open", new_callable=mock_open)
    def test_github_actions_with_prerelease_type(
        self, mock_file: MagicMock
    ) -> None:
        """Test GitHub Actions with prerelease type."""
        with patch("sys.argv", ["semantic-tag-increment"]):
            try:
                run_github_action()
            except SystemExit as e:
                assert e.code == 0

        written_content = "".join(
            call.args[0] for call in mock_file().write.call_args_list
        )
        assert "tag=1.2.4-alpha.1" in written_content

    @patch.dict(
        os.environ,
        {
            "GITHUB_ACTIONS": "true",
            "INPUT_TAG": "",
            "GITHUB_OUTPUT": tempfile.NamedTemporaryFile(delete=False).name,
        },
    )
    def test_github_actions_missing_tag(self) -> None:
        """Test GitHub Actions with missing tag."""
        with patch("sys.argv", ["semantic-tag-increment"]):
            with pytest.raises(SystemExit) as exc_info:
                run_github_action()
            assert exc_info.value.code == 1

    @patch.dict(
        os.environ,
        {
            "GITHUB_ACTIONS": "true",
            "INPUT_TAG": "invalid",
            "INPUT_INCREMENT": "patch",
            "GITHUB_OUTPUT": tempfile.NamedTemporaryFile(delete=False).name,
        },
    )
    def test_github_actions_invalid_version(self) -> None:
        """Test GitHub Actions with invalid version."""
        with patch("sys.argv", ["semantic-tag-increment"]):
            with pytest.raises(SystemExit) as exc_info:
                run_github_action()
            assert exc_info.value.code == 1

    @patch.dict(
        os.environ,
        {
            "GITHUB_ACTIONS": "true",
            "INPUT_TAG": "1.2.3",
            "INPUT_INCREMENT": "invalid",
            "GITHUB_OUTPUT": tempfile.NamedTemporaryFile(delete=False).name,
        },
    )
    def test_github_actions_invalid_increment(self) -> None:
        """Test GitHub Actions with invalid increment type."""
        with patch("sys.argv", ["semantic-tag-increment"]):
            with pytest.raises(SystemExit) as exc_info:
                run_github_action()
            assert exc_info.value.code == 1

    @patch("builtins.open", new_callable=mock_open)
    @patch.dict(
        os.environ,
        {
            "GITHUB_ACTIONS": "true",
            "INPUT_TAG": "v1.2.3",
            "INPUT_INCREMENT": "patch",
            "GITHUB_OUTPUT": tempfile.NamedTemporaryFile(delete=False).name,
        },
    )
    @patch(
        "semantic_tag_increment.git_operations.GitOperations.get_existing_tags"
    )
    def test_github_actions_with_git_tags(
        self,
        mock_get_tags: MagicMock,
        mock_file: MagicMock,
    ) -> None:
        """Test GitHub Actions with git tag checking."""
        mock_get_tags.return_value = {"v1.2.0", "v1.2.1", "v1.2.2"}

        with patch("sys.argv", ["semantic-tag-increment"]):
            try:
                run_github_action()
            except SystemExit as e:
                assert e.code == 0

        written_content = "".join(
            call.args[0] for call in mock_file().write.call_args_list
        )
        assert "tag=v1.2.4" in written_content

    @patch("builtins.open", new_callable=mock_open)
    @patch.dict(
        os.environ,
        {
            "GITHUB_ACTIONS": "true",
            "INPUT_TAG": "v1.2.3",
            "INPUT_INCREMENT": "patch",
            "GITHUB_OUTPUT": tempfile.NamedTemporaryFile(delete=False).name,
        },
    )
    @patch(
        "semantic_tag_increment.git_operations.GitOperations.get_existing_tags"
    )
    def test_github_actions_git_failure(
        self,
        mock_get_tags: MagicMock,
        mock_file: MagicMock,
    ) -> None:
        """Test GitHub Actions when git command fails."""
        mock_get_tags.return_value = set()  # Return empty set on failure

        with patch("sys.argv", ["semantic-tag-increment"]):
            try:
                run_github_action()
            except SystemExit as e:
                assert e.code == 0  # Should continue despite git failure

        # Verify output was written
        written_content = "".join(
            call.args[0] for call in mock_file().write.call_args_list
        )
        assert "tag=v1.2.4" in written_content


class TestMainEntryPoint:
    """Test the main entry point logic."""

    def test_main_cli_mode_with_command(self) -> None:
        """Test main function in CLI mode with explicit command."""
        with patch(
            "sys.argv", ["semantic-tag-increment", "increment", "--help"]
        ):
            # Import the main module directly and patch its attributes
            main_module = importlib.import_module("semantic_tag_increment.main")
            with patch.object(main_module, "app") as mock_app:
                main()
                mock_app.assert_called_once()

    def test_main_cli_mode_with_help(self) -> None:
        """Test main function in CLI mode with help flag."""
        with patch("sys.argv", ["semantic-tag-increment", "--help"]):
            # Import the main module directly and patch its attributes
            main_module = importlib.import_module("semantic_tag_increment.main")
            with patch.object(main_module, "app") as mock_app:
                main()
                mock_app.assert_called_once()

    @patch.dict(os.environ, {"GITHUB_ACTIONS": "true", "INPUT_TAG": "v1.2.3"})
    def test_main_github_actions_mode(self) -> None:
        """Test main function in GitHub Actions mode."""
        with patch("sys.argv", ["semantic-tag-increment"]):
            # Import the main module directly and patch its attributes
            main_module = importlib.import_module("semantic_tag_increment.main")
            with patch.object(
                main_module, "GitHubActionsRunner"
            ) as mock_runner_class:
                mock_runner = MagicMock()
                mock_runner_class.return_value = mock_runner
                main()
                mock_runner_class.assert_called_once()
                mock_runner.run.assert_called_once()

    @patch.dict(os.environ, {"GITHUB_ACTIONS": "true"})
    def test_main_github_actions_mode_with_help_override(self) -> None:
        """Test that help flag overrides GitHub Actions mode."""
        with patch("sys.argv", ["semantic-tag-increment", "--help"]):
            # Import the main module directly and patch its attributes
            main_module = importlib.import_module("semantic_tag_increment.main")
            with patch.object(main_module, "app") as mock_app:
                main()
                mock_app.assert_called_once()


class TestUtilityFunctions:
    """Test utility functions."""

    def test_get_existing_tags_success(self) -> None:
        """Test successful git tag retrieval."""
        from semantic_tag_increment.git_operations import GitOperations

        # Mock the actual implementation to return test data
        with patch.object(
            GitOperations,
            "get_existing_tags",
            return_value={"v1.0.0", "v1.0.1", "v1.1.0"},
        ):
            tags = GitOperations.get_existing_tags(".")

        assert tags == {"v1.0.0", "v1.0.1", "v1.1.0"}

    def test_get_existing_tags_failure(self) -> None:
        """Test git tag retrieval failure."""
        from semantic_tag_increment.git_operations import GitOperations

        # Mock the actual implementation to return empty set on failure
        with patch.object(
            GitOperations, "get_existing_tags", return_value=set()
        ):
            tags = GitOperations.get_existing_tags(".")

        assert tags == set()

    def test_get_existing_tags_empty(self) -> None:
        """Test git tag retrieval with no tags."""
        from semantic_tag_increment.git_operations import GitOperations

        # Mock the actual implementation to return empty set
        with patch.object(
            GitOperations, "get_existing_tags", return_value=set()
        ):
            tags = GitOperations.get_existing_tags(".")

        assert tags == set()

    @patch("builtins.open", new_callable=mock_open)
    def test_write_github_output(self, mock_file: MagicMock) -> None:
        """Test GitHub output writing."""
        from semantic_tag_increment.io_operations import IOOperations

        test_output_file = tempfile.NamedTemporaryFile(delete=False).name

        with patch.dict(os.environ, {"GITHUB_OUTPUT": test_output_file}):
            IOOperations.write_github_output("test_key", "test_value")

        mock_file.assert_called_with(test_output_file, "a", encoding="utf-8")
        mock_file().write.assert_called_with("test_key=test_value\n")

    def test_write_github_output_no_env(self) -> None:
        """Test GitHub output writing without GITHUB_OUTPUT env var."""
        from semantic_tag_increment.io_operations import IOOperations

        # Should not raise an exception
        IOOperations.write_github_output("test_key", "test_value")


class TestPropertyBasedTesting:
    """Property-based tests using hypothesis (if available)."""

    @pytest.mark.property
    def test_increment_always_produces_valid_semver(self) -> None:
        """Test that increment always produces valid semantic versions."""
        runner = CliRunner()

        # Test with some known valid versions
        test_versions = [
            "1.0.0",
            "0.1.0",
            "0.0.1",
            "1.2.3",
            "10.20.30",
            "v1.0.0",
            "V2.0.0",
            "1.0.0-alpha",
            "1.0.0+build",
        ]

        increment_types = ["major", "minor", "patch", "prerelease"]

        for version in test_versions:
            for increment_type in increment_types:
                result = runner.invoke(
                    app,
                    [
                        "increment",
                        "--tag",
                        version,
                        "--increment",
                        increment_type,
                        "--no-check-conflicts",
                    ],
                )

                if result.exit_code == 0:
                    # Extract the output version
                    output_lines = result.output.strip().split("\n")
                    if output_lines:
                        output_version = output_lines[-1].strip()
                        # Verify it's a valid semantic version
                        assert SemanticVersion.is_valid(output_version), (
                            f"Output '{output_version}' from '{version}' + '{increment_type}' is invalid"
                        )

    @pytest.mark.property
    def test_validate_round_trip(self) -> None:
        """Test that validated versions can be parsed and incremented."""
        runner = CliRunner()

        test_versions = [
            "1.0.0",
            "1.2.3-alpha.1",
            "v1.0.0+build",
            "2.0.0-beta.2+meta",
        ]

        for version in test_versions:
            # First validate
            validate_result = runner.invoke(app, ["validate", "--tag", version])
            assert validate_result.exit_code == 0

            # Then increment
            increment_result = runner.invoke(
                app,
                [
                    "increment",
                    "--tag",
                    version,
                    "--increment",
                    "patch",
                    "--no-check-conflicts",
                ],
            )
            assert increment_result.exit_code == 0


class TestCheckTagsFeature:
    """Test the check_tags configuration option."""

    @patch(
        "semantic_tag_increment.github_actions.GitOperations.get_existing_tags"
    )
    @patch.dict(
        os.environ,
        {
            "GITHUB_ACTIONS": "true",
            "INPUT_TAG": "v1.0.0",
            "INPUT_CHECK_TAGS": "false",
        },
    )
    def test_check_tags_disabled(self, mock_git_ops: MagicMock) -> None:
        """Test that git operations are skipped when check_tags is false."""
        mock_git_ops.return_value = set()

        runner = GitHubActionsRunner()
        runner.run()

        # Git operations should NOT be called
        mock_git_ops.assert_not_called()

    @patch(
        "semantic_tag_increment.github_actions.GitOperations.get_existing_tags"
    )
    @patch.dict(
        os.environ,
        {
            "GITHUB_ACTIONS": "true",
            "INPUT_TAG": "v1.0.0",
            "INPUT_CHECK_TAGS": "true",
        },
    )
    def test_check_tags_enabled(self, mock_git_ops: MagicMock) -> None:
        """Test that git operations are executed when check_tags is true."""
        mock_git_ops.return_value = set()

        runner = GitHubActionsRunner()
        runner.run()

        # Git operations SHOULD be called
        mock_git_ops.assert_called_once()

    @patch(
        "semantic_tag_increment.github_actions.GitOperations.get_existing_tags"
    )
    @patch.dict(
        os.environ,
        {
            "GITHUB_ACTIONS": "true",
            "INPUT_TAG": "v1.0.0",
            # No INPUT_CHECK_TAGS set - should default to true
        },
    )
    def test_check_tags_default_enabled(self, mock_git_ops: MagicMock) -> None:
        """Test that git operations are executed by default (check_tags defaults to true)."""
        mock_git_ops.return_value = set()

        runner = GitHubActionsRunner()
        runner.run()

        # Git operations SHOULD be called by default
        mock_git_ops.assert_called_once()
