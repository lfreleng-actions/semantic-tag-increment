# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Operation modes module.

This module defines the different operation modes for the semantic tag increment tool
and provides validation logic for each mode.
"""

import logging
from enum import Enum
from typing import Optional, NoReturn

from .exceptions import ErrorReporter

logger = logging.getLogger(__name__)


class OperationMode(Enum):
    """Supported operation modes for the semantic tag increment tool."""

    STRING = "string"
    PATH = "path"
    COMBINED = "combined"
    AUTO = "auto"


class ModeValidator:
    """Validates inputs based on the selected operation mode."""

    @staticmethod
    def validate_mode_inputs(
        mode: OperationMode,
        tag: Optional[str] = None,
        path: Optional[str] = None,
        check_tags: bool = True
    ) -> None:
        """
        Validate inputs for the specified mode.

        Args:
            mode: The operation mode to validate for
            tag: The input tag string (optional)
            path: The input path string (optional)
            check_tags: Whether tag checking is enabled

        Raises:
            ValidationError: If the inputs are invalid for the specified mode
        """
        if mode == OperationMode.STRING:
            ModeValidator._validate_string_mode(tag, path)
        elif mode == OperationMode.PATH:
            ModeValidator._validate_path_mode(tag, path)
        elif mode == OperationMode.COMBINED:
            ModeValidator._validate_combined_mode(tag, path, check_tags)
        elif mode == OperationMode.AUTO:
            ModeValidator._validate_auto_mode(tag, path)
        else:
            ModeValidator._raise_unsupported_mode_error(mode)

    @staticmethod
    def _validate_string_mode(tag: Optional[str], path: Optional[str]) -> None:
        """Validate inputs for string mode."""
        if not tag or not tag.strip():
            ErrorReporter.log_and_raise_validation_error(
                "String mode requires a non-empty 'tag' input"
            )

        if path and path.strip() and path.strip() != ".":
            logger.warning(
                "String mode: 'path' input will be ignored as it's not used in this mode"
            )

    @staticmethod
    def _validate_path_mode(tag: Optional[str], path: Optional[str]) -> None:
        """Validate inputs for path mode."""
        if tag and tag.strip():
            logger.warning(
                "Path mode: 'tag' input will be ignored as version will be auto-detected from project files"
            )

        # Path will default to current directory if not provided
        if path and path.strip():
            import os
            if not os.path.exists(path):
                ErrorReporter.log_and_raise_validation_error(
                    f"Path mode: specified path does not exist: {path}"
                )
            if not os.path.isdir(path):
                ErrorReporter.log_and_raise_validation_error(
                    f"Path mode: specified path is not a directory: {path}"
                )

    @staticmethod
    def _validate_combined_mode(
        tag: Optional[str],
        path: Optional[str],
        check_tags: bool
    ) -> None:
        """Validate inputs for combined mode."""
        if not tag or not tag.strip():
            ErrorReporter.log_and_raise_validation_error(
                "Combined mode requires a non-empty 'tag' input"
            )

        # Path will default to current directory if not provided
        if path and path.strip():
            import os
            if not os.path.exists(path):
                ErrorReporter.log_and_raise_validation_error(
                    f"Combined mode: specified path does not exist: {path}"
                )
            if not os.path.isdir(path):
                ErrorReporter.log_and_raise_validation_error(
                    f"Combined mode: specified path is not a directory: {path}"
                )

        # Warn if check_tags is disabled - makes path redundant
        if not check_tags:
            logger.warning(
                "Combined mode with check_tags=false: the path component is redundant. "
                "Consider using 'string' mode instead, as you've disabled repository context behaviors."
            )

    @staticmethod
    def _validate_auto_mode(tag: Optional[str], path: Optional[str]) -> None:
        """Validate inputs for auto mode."""
        # Auto mode is the most flexible - both tag and path are optional
        # Path will default to current directory if not provided
        if path and path.strip():
            import os
            if not os.path.exists(path):
                ErrorReporter.log_and_raise_validation_error(
                    f"Auto mode: specified path does not exist: {path}"
                )
            if not os.path.isdir(path):
                ErrorReporter.log_and_raise_validation_error(
                    f"Auto mode: specified path is not a directory: {path}"
                )

        # If tag is provided, log that it will take precedence over auto-detection
        if tag and tag.strip():
            logger.info(
                "Auto mode: explicit tag provided, will use this instead of auto-detection"
            )

    @staticmethod
    def _raise_unsupported_mode_error(mode: OperationMode) -> NoReturn:
        """Raise an error for unsupported operation mode."""
        ErrorReporter.log_and_raise_validation_error(
            f"Unsupported operation mode: {mode.value}"
        )


class ModeHelper:
    """Helper utilities for working with operation modes."""

    @staticmethod
    def parse_mode(mode_str: str) -> OperationMode:
        """
        Parse a mode string into an OperationMode enum.

        Args:
            mode_str: The mode string to parse

        Returns:
            OperationMode enum value

        Raises:
            ValidationError: If the mode string is invalid
        """
        if not mode_str or not isinstance(mode_str, str):
            ErrorReporter.log_and_raise_validation_error(
                "Mode must be a non-empty string"
            )

        mode_str = mode_str.strip().lower()

        try:
            return OperationMode(mode_str)
        except ValueError:
            valid_modes = [mode.value for mode in OperationMode]
            ModeHelper._raise_invalid_mode_error(mode_str, valid_modes)

    @staticmethod
    def get_mode_description(mode: OperationMode) -> str:
        """
        Get a human-readable description of an operation mode.

        Args:
            mode: The operation mode

        Returns:
            Description string
        """
        descriptions = {
            OperationMode.STRING: (
                "String mode: Standalone tag incrementing based purely on input string. "
                "No project context or file extraction is performed."
            ),
            OperationMode.PATH: (
                "Path mode: Auto-detect project type and extract version from project files. "
                "No explicit tag input is required."
            ),
            OperationMode.COMBINED: (
                "Combined mode: Use explicit tag input with repository context for conflict checking. "
                "Both tag and path inputs are used."
            ),
            OperationMode.AUTO: (
                "Auto mode: Fully automatic operation using heuristics. "
                "Auto-detects project type and version, with optional Git tag conflict checking."
            )
        }
        return descriptions.get(mode, f"Unknown mode: {mode.value}")

    @staticmethod
    def should_extract_version(mode: OperationMode, tag: Optional[str]) -> bool:
        """
        Determine if version extraction should be performed based on mode and inputs.

        Args:
            mode: The operation mode
            tag: The input tag (if any)

        Returns:
            True if version extraction should be performed
        """
        if mode == OperationMode.STRING:
            return False
        elif mode == OperationMode.PATH:
            return True
        elif mode == OperationMode.COMBINED:
            return False
        elif mode == OperationMode.AUTO:
            # Only extract if no explicit tag is provided
            return not (tag and tag.strip())

        # This should never be reached with valid enum values
        raise AssertionError(f"Unhandled mode: {mode}")

    @staticmethod
    def should_check_git_tags(mode: OperationMode, check_tags: bool) -> bool:
        """
        Determine if Git tag checking should be performed based on mode and settings.

        Args:
            mode: The operation mode
            check_tags: The check_tags setting

        Returns:
            True if Git tag checking should be performed
        """
        if mode == OperationMode.STRING:
            return False
        elif mode in (OperationMode.PATH, OperationMode.COMBINED, OperationMode.AUTO):
            return check_tags

        # This should never be reached with valid enum values
        raise AssertionError(f"Unhandled mode: {mode}")

    @staticmethod
    def get_effective_path(mode: OperationMode, path: Optional[str]) -> str:
        """
        Get the effective path to use based on mode and input.

        Args:
            mode: The operation mode
            path: The input path (if any)

        Returns:
            The effective path to use
        """
        if mode == OperationMode.STRING:
            # Path is not used in string mode, but return current directory for consistency
            return "."

        # For all other modes, use provided path or default to current directory
        return path.strip() if path and path.strip() else "."

    @staticmethod
    def log_mode_operation(mode: OperationMode, tag: Optional[str], path: Optional[str]) -> None:
        """
        Log information about the selected mode and operation.

        Args:
            mode: The operation mode
            tag: The input tag (if any)
            path: The input path (if any)
        """
        logger.info(f"Operation mode: {mode.value}")
        logger.debug(f"Mode description: {ModeHelper.get_mode_description(mode)}")

        if mode == OperationMode.STRING:
            logger.info(f"Using explicit tag: {tag}")
        elif mode == OperationMode.PATH:
            effective_path = ModeHelper.get_effective_path(mode, path)
            logger.info(f"Auto-detecting version from path: {effective_path}")
        elif mode == OperationMode.COMBINED:
            effective_path = ModeHelper.get_effective_path(mode, path)
            logger.info(f"Using explicit tag: {tag} with path context: {effective_path}")
        elif mode == OperationMode.AUTO:
            effective_path = ModeHelper.get_effective_path(mode, path)
            if tag and tag.strip():
                logger.info(f"Using explicit tag: {tag} with path context: {effective_path}")
            else:
                logger.info(f"Auto-detecting version from path: {effective_path}")

    @staticmethod
    def _raise_invalid_mode_error(mode_str: str, valid_modes: list[str]) -> NoReturn:
        """Raise an error for invalid mode string."""
        ErrorReporter.log_and_raise_validation_error(
            f"Invalid mode: '{mode_str}'. Valid modes are: {', '.join(valid_modes)}"
        )
