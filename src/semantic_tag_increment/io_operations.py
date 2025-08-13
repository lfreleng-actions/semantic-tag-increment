# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
I/O operations module.

This module handles file I/O operations and output formatting for different contexts.
"""

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


class IOOperations:
    """Handles I/O operations for the application."""

    @staticmethod
    def write_github_output(key: str, value: str) -> None:
        """
        Write output to GitHub Actions output file.

        Args:
            key: The output key name
            value: The output value
        """
        github_output = os.environ.get("GITHUB_OUTPUT")
        if github_output:
            try:
                with open(github_output, "a", encoding="utf-8") as f:
                    f.write(f"{key}={value}\n")
                logger.debug(f"Wrote GitHub output: {key}={value}")
            except OSError as e:
                logger.error(f"Failed to write GitHub output: {e}")
        else:
            logger.debug("GITHUB_OUTPUT environment variable not set")

    @staticmethod
    def write_outputs_to_github(full_version: str, numeric_version: str) -> None:
        """
        Write both tag outputs to GitHub Actions.

        Args:
            full_version: Version with prefix
            numeric_version: Version without prefix
        """
        IOOperations.write_github_output("tag", full_version)
        IOOperations.write_github_output("numeric_tag", numeric_version)

    @staticmethod
    def get_env_var(name: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get environment variable with optional default.

        Args:
            name: Environment variable name
            default: Default value if not found

        Returns:
            Environment variable value or default
        """
        value = os.environ.get(name, default)
        return value if value and value.strip() else default

    @staticmethod
    def is_github_actions() -> bool:
        """
        Check if running in GitHub Actions environment.

        Returns:
            True if in GitHub Actions, False otherwise
        """
        return os.environ.get("GITHUB_ACTIONS") == "true"
