# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Unit tests for I/O operations module.

This module tests file I/O operations and error handling.
"""

import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from semantic_tag_increment.io_operations import IOOperations


class TestIOOperations:
    """Test I/O operations and error handling."""

    def test_write_github_output_success(self) -> None:
        """Test successful GitHub output writing."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp_file:
            tmp_file_path = tmp_file.name

        try:
            with patch.dict(os.environ, {"GITHUB_OUTPUT": tmp_file_path}):
                IOOperations.write_github_output("test_key", "test_value")

            # Verify the output was written correctly
            with open(tmp_file_path, encoding="utf-8") as f:
                content = f.read()
            assert "test_key=test_value\n" in content
        finally:
            os.unlink(tmp_file_path)

    def test_write_github_output_no_env_var(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test GitHub output writing when GITHUB_OUTPUT is not set."""
        # Set the logging level to capture debug messages
        caplog.set_level("DEBUG", logger="semantic_tag_increment.io_operations")

        with patch.dict(os.environ, {}, clear=True):
            IOOperations.write_github_output("test_key", "test_value")

        # Verify debug message was logged
        assert "GITHUB_OUTPUT environment variable not set" in caplog.text

    def test_write_github_output_file_error(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test GitHub output writing when file operation fails."""
        # Set the logging level to capture error messages
        caplog.set_level("ERROR", logger="semantic_tag_increment.io_operations")

        # Use a non-existent directory to trigger OSError
        invalid_path = "/nonexistent/directory/output.txt"

        with patch.dict(os.environ, {"GITHUB_OUTPUT": invalid_path}):
            IOOperations.write_github_output("test_key", "test_value")

        # Verify error was logged and exception was handled
        assert "Failed to write GitHub output" in caplog.text

    def test_write_github_output_permission_denied(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test GitHub output writing when file permissions are denied."""
        # Set the logging level to capture error messages
        caplog.set_level("ERROR", logger="semantic_tag_increment.io_operations")

        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file_path = tmp_file.name

        try:
            # Remove write permissions
            os.chmod(tmp_file_path, 0o444)

            with patch.dict(os.environ, {"GITHUB_OUTPUT": tmp_file_path}):
                IOOperations.write_github_output("test_key", "test_value")

            # Verify error was logged
            assert "Failed to write GitHub output" in caplog.text
        finally:
            # Restore permissions and cleanup
            os.chmod(tmp_file_path, 0o644)
            os.unlink(tmp_file_path)

    @patch("builtins.open", side_effect=OSError("Disk full"))
    def test_write_github_output_disk_full(
        self, mock_open: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test GitHub output writing when disk is full."""
        # Set the logging level to capture error messages
        caplog.set_level("ERROR", logger="semantic_tag_increment.io_operations")

        with patch.dict(os.environ, {"GITHUB_OUTPUT": "/tmp/output.txt"}):
            IOOperations.write_github_output("test_key", "test_value")

        # Verify error was logged and exception was handled
        assert "Failed to write GitHub output" in caplog.text
        assert "Disk full" in caplog.text

    def test_write_outputs_to_github(self) -> None:
        """Test writing both tag outputs to GitHub."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp_file:
            tmp_file_path = tmp_file.name

        try:
            with patch.dict(os.environ, {"GITHUB_OUTPUT": tmp_file_path}):
                IOOperations.write_outputs_to_github("v1.2.3", "1.2.3")

            # Verify both outputs were written
            with open(tmp_file_path, encoding="utf-8") as f:
                content = f.read()
            assert "tag=v1.2.3\n" in content
            assert "numeric_tag=1.2.3\n" in content
        finally:
            os.unlink(tmp_file_path)

    def test_get_env_var_exists(self) -> None:
        """Test getting an existing environment variable."""
        with patch.dict(os.environ, {"TEST_VAR": "test_value"}):
            result = IOOperations.get_env_var("TEST_VAR")
            assert result == "test_value"

    def test_get_env_var_not_exists(self) -> None:
        """Test getting a non-existent environment variable."""
        with patch.dict(os.environ, {}, clear=True):
            result = IOOperations.get_env_var("NONEXISTENT_VAR")
            assert result is None

    def test_get_env_var_with_default(self) -> None:
        """Test getting a non-existent environment variable with default."""
        with patch.dict(os.environ, {}, clear=True):
            result = IOOperations.get_env_var(
                "NONEXISTENT_VAR", "default_value"
            )
            assert result == "default_value"

    def test_get_env_var_empty_string(self) -> None:
        """Test getting an environment variable that is an empty string."""
        with patch.dict(os.environ, {"EMPTY_VAR": ""}):
            result = IOOperations.get_env_var("EMPTY_VAR", "default_value")
            assert result == "default_value"

    def test_get_env_var_whitespace_only(self) -> None:
        """Test getting an environment variable that contains only whitespace."""
        with patch.dict(os.environ, {"WHITESPACE_VAR": "   "}):
            result = IOOperations.get_env_var("WHITESPACE_VAR", "default_value")
            assert result == "default_value"

    def test_is_github_actions_true(self) -> None:
        """Test GitHub Actions detection when in GitHub Actions."""
        with patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}):
            assert IOOperations.is_github_actions() is True

    def test_is_github_actions_false(self) -> None:
        """Test GitHub Actions detection when not in GitHub Actions."""
        with patch.dict(os.environ, {}, clear=True):
            assert IOOperations.is_github_actions() is False

    def test_is_github_actions_false_value(self) -> None:
        """Test GitHub Actions detection with false value."""
        with patch.dict(os.environ, {"GITHUB_ACTIONS": "false"}):
            assert IOOperations.is_github_actions() is False
