# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Application context module.

This module handles application context detection and configuration for
string-mode tag incrementing in different execution modes (CLI vs GitHub Actions).
"""

import sys
from dataclasses import dataclass

from .io_operations import IOOperations


@dataclass
class AppContext:
    """Application execution context."""

    is_github_actions: bool
    is_cli_mode: bool
    debug_mode: bool
    has_cli_command: bool


class ContextDetector:
    """Detects and configures application execution context."""

    CLI_COMMANDS = {"increment", "validate", "suggest", "help", "--help", "-h"}

    @staticmethod
    def detect_context() -> AppContext:
        """
        Detect the current application execution context.

        Returns:
            AppContext with detected settings
        """
        is_github_actions = IOOperations.is_github_actions()
        has_cli_command = ContextDetector._has_cli_command()
        debug_mode = ContextDetector._get_debug_mode()

        # CLI mode if:
        # 1. Not in GitHub Actions, OR
        # 2. Help was requested, OR
        # 3. Explicit CLI command provided
        is_cli_mode = (
            not is_github_actions
            or ContextDetector._is_help_requested()
            or has_cli_command
        )

        return AppContext(
            is_github_actions=is_github_actions,
            is_cli_mode=is_cli_mode,
            debug_mode=debug_mode,
            has_cli_command=has_cli_command
        )

    @staticmethod
    def _has_cli_command() -> bool:
        """Check if any CLI commands are present in argv."""
        return any(cmd in sys.argv for cmd in ContextDetector.CLI_COMMANDS)

    @staticmethod
    def _is_help_requested() -> bool:
        """Check if help was requested."""
        return "--help" in sys.argv or "-h" in sys.argv

    @staticmethod
    def _get_debug_mode() -> bool:
        """Determine if debug mode should be enabled."""
        # Check CLI debug flag first
        if "--debug" in sys.argv:
            return True

        # Check GitHub Actions debug input
        if IOOperations.is_github_actions():
            debug_input = IOOperations.get_env_var("INPUT_DEBUG", "false")
            if debug_input:
                return debug_input.lower() in ("true", "1", "yes")

        return False


class GitHubActionsConfig:
    """Configuration for GitHub Actions mode."""

    @staticmethod
    def get_inputs() -> dict[str, str | None]:
        """
        Get GitHub Actions inputs from environment variables.

        Returns:
            Dictionary of input values with defaults applied
        """
        input_mappings = {
            "tag": "INPUT_TAG",
            "increment": "INPUT_INCREMENT",
            "prerelease_type": "INPUT_PRERELEASE_TYPE",
            "path": "INPUT_PATH",
            "debug": "INPUT_DEBUG",
            "check_tags": "INPUT_CHECK_TAGS",
            "preserve_metadata": "INPUT_PRESERVE_METADATA",
            "fetch_timeout": "INPUT_FETCH_TIMEOUT",
        }

        defaults: dict[str, str | None] = {
            "increment": "dev",
            "prerelease_type": None,
            "path": ".",
            "debug": "false",
            "check_tags": "true",
            "preserve_metadata": "false",
            "fetch_timeout": "120",
        }

        config: dict[str, str | None] = {}
        for param, env_var in input_mappings.items():
            value = IOOperations.get_env_var(env_var, defaults.get(param))
            if value is not None and value != "":
                config[param] = value

        return config

    @staticmethod
    def validate_required_inputs(config: dict[str, str | None]) -> None:
        """
        Validate that required inputs are present for string mode.

        Args:
            config: Configuration dictionary

        Raises:
            ValueError: If required inputs are missing
        """
        # Validate required tag input
        tag = config.get("tag")
        if not tag or not tag.strip():
            raise ValueError("String mode requires a non-empty 'tag' input")
