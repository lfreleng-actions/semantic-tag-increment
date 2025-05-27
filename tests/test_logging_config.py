# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Unit tests for logging configuration module.

This module tests logging setup and error handling.
"""

import logging
import tempfile
from pathlib import Path
from unittest.mock import patch

from semantic_tag_increment.logging_config import LoggingConfig


class TestLoggingConfig:
    """Test logging configuration and error handling."""

    def setup_method(self) -> None:
        """Reset logging configuration before each test."""
        # Clear all handlers from the root logger
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        root_logger.setLevel(logging.WARNING)

    def teardown_method(self) -> None:
        """Clean up logging configuration after each test."""
        # Reset logging to default state
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        root_logger.setLevel(logging.WARNING)

    def test_setup_logging_success(self) -> None:
        """Test successful logging setup."""
        with tempfile.TemporaryDirectory() as temp_dir:
            fake_home = Path(temp_dir)

            with patch(
                "semantic_tag_increment.logging_config.Path.home",
                return_value=fake_home,
            ):
                LoggingConfig.setup_logging(debug=True, suppress_console=False)

            # Verify root logger configuration
            root_logger = logging.getLogger()
            assert root_logger.level == logging.DEBUG
            assert len(root_logger.handlers) >= 1  # Should have file handler

            # Verify log file was created
            log_file = (
                fake_home
                / ".config"
                / "semantic-tag-increment"
                / "semantic-tag-increment.log"
            )
            assert log_file.exists()

    def test_setup_logging_file_creation_fails(self) -> None:
        """Test logging setup when file creation fails."""
        with patch(
            "semantic_tag_increment.logging_config.Path.mkdir"
        ) as mock_mkdir:
            mock_mkdir.side_effect = OSError("Permission denied")

            # Should not raise an exception
            LoggingConfig.setup_logging(debug=True, suppress_console=False)

            # Verify root logger is still configured (even without file handler)
            root_logger = logging.getLogger()
            assert root_logger.level == logging.DEBUG

    def test_setup_logging_file_handler_fails(self) -> None:
        """Test logging setup when FileHandler creation fails."""
        with tempfile.TemporaryDirectory() as temp_dir:
            fake_home = Path(temp_dir)

            with patch(
                "semantic_tag_increment.logging_config.Path.home",
                return_value=fake_home,
            ):
                with patch(
                    "logging.FileHandler",
                    side_effect=OSError("Cannot create file"),
                ):
                    # Should not raise an exception
                    LoggingConfig.setup_logging(
                        debug=True, suppress_console=False
                    )

                    # Verify root logger is still configured
                    root_logger = logging.getLogger()
                    assert root_logger.level == logging.DEBUG

    def test_setup_logging_suppress_console(self) -> None:
        """Test logging setup with console suppression."""
        with tempfile.TemporaryDirectory() as temp_dir:
            fake_home = Path(temp_dir)

            with patch(
                "semantic_tag_increment.logging_config.Path.home",
                return_value=fake_home,
            ):
                LoggingConfig.setup_logging(debug=False, suppress_console=True)

            # Verify root logger configuration
            root_logger = logging.getLogger()
            assert root_logger.level == logging.DEBUG

            # Should only have file handler (no console handler)
            handler_types = [
                type(handler).__name__ for handler in root_logger.handlers
            ]
            assert "FileHandler" in handler_types
            assert "StreamHandler" not in handler_types

    def test_setup_logging_debug_mode(self) -> None:
        """Test logging setup in debug mode."""
        with tempfile.TemporaryDirectory() as temp_dir:
            fake_home = Path(temp_dir)

            with patch(
                "semantic_tag_increment.logging_config.Path.home",
                return_value=fake_home,
            ):
                LoggingConfig.setup_logging(debug=True, suppress_console=False)

            # Verify root logger configuration
            root_logger = logging.getLogger()
            assert root_logger.level == logging.DEBUG

            # Should have both file and console handlers in debug mode
            handler_types = [
                type(handler).__name__ for handler in root_logger.handlers
            ]
            assert "FileHandler" in handler_types
            assert "StreamHandler" in handler_types

    def test_setup_logging_normal_mode(self) -> None:
        """Test logging setup in normal mode."""
        with tempfile.TemporaryDirectory() as temp_dir:
            fake_home = Path(temp_dir)

            with patch(
                "semantic_tag_increment.logging_config.Path.home",
                return_value=fake_home,
            ):
                LoggingConfig.setup_logging(debug=False, suppress_console=False)

            # Verify root logger configuration
            root_logger = logging.getLogger()
            assert root_logger.level == logging.DEBUG

            # Should have both file and console handlers in normal mode
            handler_types = [
                type(handler).__name__ for handler in root_logger.handlers
            ]
            assert "FileHandler" in handler_types
            assert "StreamHandler" in handler_types

    def test_set_module_level(self) -> None:
        """Test setting logging level for specific module."""
        LoggingConfig.set_module_level("test_module", logging.ERROR)

        test_logger = logging.getLogger("test_module")
        assert test_logger.level == logging.ERROR

    def test_logging_continues_after_file_error(self) -> None:
        """Test that logging continues to work after file operation errors."""
        with patch(
            "semantic_tag_increment.logging_config.Path.mkdir"
        ) as mock_mkdir:
            mock_mkdir.side_effect = OSError("Permission denied")

            # Setup should not raise an exception
            LoggingConfig.setup_logging(debug=True, suppress_console=False)

            # Logger should still work for console output
            test_logger = logging.getLogger("test")

            # This should not raise an exception
            test_logger.info("Test message after file error")

    def test_log_directory_creation(self) -> None:
        """Test that log directory is created with correct structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            fake_home = Path(temp_dir)

            with patch(
                "semantic_tag_increment.logging_config.Path.home",
                return_value=fake_home,
            ):
                LoggingConfig.setup_logging()

            # Verify directory structure
            config_dir = fake_home / ".config"
            app_dir = config_dir / "semantic-tag-increment"
            log_file = app_dir / "semantic-tag-increment.log"

            assert config_dir.exists()
            assert app_dir.exists()
            assert log_file.exists()

    def test_log_file_permissions_error(self) -> None:
        """Test handling of log file permission errors."""
        with tempfile.TemporaryDirectory() as temp_dir:
            fake_home = Path(temp_dir)

            # Create the directory structure but make it read-only
            config_dir = fake_home / ".config" / "semantic-tag-increment"
            config_dir.mkdir(parents=True)
            config_dir.chmod(0o444)  # Read-only

            try:
                with patch(
                    "semantic_tag_increment.logging_config.Path.home",
                    return_value=fake_home,
                ):
                    # Should not raise an exception
                    LoggingConfig.setup_logging()

                # Verify root logger is still configured
                root_logger = logging.getLogger()
                assert root_logger.level == logging.DEBUG
            finally:
                # Restore permissions for cleanup
                config_dir.chmod(0o755)
