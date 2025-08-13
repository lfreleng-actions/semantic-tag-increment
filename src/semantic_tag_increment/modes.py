# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Operation modes module.

This module defines the operation mode for the semantic tag increment tool.
The tool now only supports string mode for direct tag incrementing.
"""

import logging
from enum import Enum
from typing import Optional, NoReturn

from .exceptions import ErrorReporter

logger = logging.getLogger(__name__)


class OperationMode(Enum):
    """Supported operation mode for the semantic tag increment tool."""

    STRING = "string"


class ModeValidator:
    """Validates inputs for string mode operation."""

    @staticmethod
    def validate_mode_inputs(
        mode: OperationMode,
        tag: Optional[str] = None,
        path: Optional[str] = None,
        check_tags: bool = True
    ) -> None:
        """
        Validate inputs for string mode.

        Args:
            mode: The operation mode (must be STRING)
            tag: The input tag string (required)
            path: The input path string (ignored)
            check_tags: Whether tag checking is enabled (ignored)

        Raises:
            ValidationError: If the inputs are invalid
        """
        if mode != OperationMode.STRING:
            ModeValidator._raise_unsupported_mode_error(mode)

        if not tag or not tag.strip():
            ErrorReporter.log_and_raise_validation_error(
                "String mode requires a non-empty 'tag' input"
            )

        # Warn about ignored parameters
        if path and path.strip() and path.strip() != ".":
            logger.warning(
                "String mode: 'path' input is ignored in this mode"
            )

    @staticmethod
    def _raise_unsupported_mode_error(mode: OperationMode) -> NoReturn:
        """Raise an error for unsupported operation mode."""
        ErrorReporter.log_and_raise_validation_error(
            f"Unsupported operation mode: {mode.value}. Only 'string' mode is supported."
        )


class ModeHelper:
    """Helper utilities for working with string mode."""

    @staticmethod
    def parse_mode(mode_str: str) -> OperationMode:
        """
        Parse a mode string into an OperationMode enum.

        Args:
            mode_str: The mode string to parse (must be 'string')

        Returns:
            OperationMode.STRING

        Raises:
            ValidationError: If the mode string is not 'string'
        """
        if not mode_str or not isinstance(mode_str, str):
            ErrorReporter.log_and_raise_validation_error(
                "Mode must be a non-empty string"
            )

        mode_str = mode_str.strip().lower()

        if mode_str != "string":
            ModeHelper._raise_invalid_mode_error(mode_str)

        return OperationMode.STRING

    @staticmethod
    def get_mode_description(mode: OperationMode) -> str:
        """
        Get a human-readable description of the operation mode.

        Args:
            mode: The operation mode (must be STRING)

        Returns:
            Description string
        """
        if mode == OperationMode.STRING:
            return (
                "String mode: Standalone tag incrementing based purely on input string. "
                "No project context or file extraction is performed."
            )

        # This should never happen with current enum values, but keeping for future extensibility
        raise ValueError(f"Unknown mode: {mode.value}")

    @staticmethod
    def should_check_git_tags(mode: OperationMode, check_tags: bool) -> bool:
        """
        Determine if Git tag checking should be performed.

        Args:
            mode: The operation mode (must be STRING)
            check_tags: The check_tags setting

        Returns:
            True if Git tag checking should be performed
        """
        if mode == OperationMode.STRING:
            return check_tags

        # This should never be reached with valid enum values
        raise AssertionError(f"Unhandled mode: {mode}")

    @staticmethod
    def get_effective_path(mode: OperationMode, path: Optional[str]) -> str:
        """
        Get the effective path to use for Git operations.

        Args:
            mode: The operation mode (must be STRING)
            path: The input path (if any)

        Returns:
            The effective path to use (current directory for string mode)
        """
        if mode == OperationMode.STRING:
            # Use provided path or default to current directory for Git operations
            return path.strip() if path and path.strip() else "."

        # This should never be reached with valid enum values
        raise AssertionError(f"Unhandled mode: {mode}")

    @staticmethod
    def log_mode_operation(mode: OperationMode, tag: Optional[str], path: Optional[str]) -> None:
        """
        Log information about the selected mode and operation.

        Args:
            mode: The operation mode (must be STRING)
            tag: The input tag (required for string mode)
            path: The input path (used for Git operations)
        """
        if mode == OperationMode.STRING:
            logger.info(f"Operation mode: {mode.value}")
            logger.debug(f"Mode description: {ModeHelper.get_mode_description(mode)}")
            logger.info(f"Using explicit tag: {tag}")
            if path and path.strip() and path.strip() != ".":
                logger.info(f"Git operations path: {path}")
        else:
            raise AssertionError(f"Unhandled mode: {mode}")

    @staticmethod
    def _raise_invalid_mode_error(mode_str: str) -> NoReturn:
        """Raise an error for invalid mode string."""
        ErrorReporter.log_and_raise_validation_error(
            f"Invalid mode: '{mode_str}'. Only 'string' mode is supported."
        )
