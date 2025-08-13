# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Logging configuration module.

This module provides centralized logging configuration for both CLI and
GitHub Actions usage modes.
"""

import logging
import time
from pathlib import Path
from typing import Any, Dict


class LoggingConfig:
    """Handles logging configuration for the application."""

    @staticmethod
    def setup_logging(debug: bool = False, suppress_console: bool = False) -> None:
        """
        Configure logging based on the application mode.

        Args:
            debug: Enable debug-level logging
            suppress_console: Suppress console output (useful for GitHub Actions)
        """
        level = logging.DEBUG if debug else logging.INFO

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        root_logger.handlers.clear()

        # File logging (always detailed)
        log_dir = Path.home() / ".config" / "semantic-tag-increment"
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / "semantic-tag-increment.log"

            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            file_handler.setFormatter(file_formatter)
            root_logger.addHandler(file_handler)
        except OSError:
            # If file logging fails, continue with console-only logging
            # This prevents the application from failing due to log directory
            # permission issues or disk space problems
            pass

        # Console logging (conditional)
        if not suppress_console:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(level)
            console_formatter = logging.Formatter("%(levelname)s: %(message)s")
            console_handler.setFormatter(console_formatter)
            root_logger.addHandler(console_handler)

    @staticmethod
    def set_module_level(module_name: str, level: int) -> None:
        """Set logging level for a specific module."""
        logging.getLogger(module_name).setLevel(level)


class SemanticLogger:
    """Utility class for consistent logging with semantic context."""

    _operation_times: Dict[str, float] = {}

    @staticmethod
    def operation_start(operation: str, details: Dict[str, Any] | None = None) -> None:
        """
        Log the start of an operation with consistent formatting.

        Args:
            operation: Name of the operation being started
            details: Optional dictionary with operation details
        """
        logger = logging.getLogger(__name__)
        message = f"Starting operation: {operation}"

        if details:
            detail_str = ", ".join(f"{k}={v}" for k, v in details.items())
            message += f" ({detail_str})"

        logger.info(message)

        # Store start time for performance tracking
        SemanticLogger._operation_times[operation] = time.time()

    @staticmethod
    def operation_success(operation: str, result: Dict[str, Any] | None = None) -> None:
        """
        Log successful completion of an operation.

        Args:
            operation: Name of the operation that completed
            result: Optional dictionary with operation results
        """
        logger = logging.getLogger(__name__)

        # Calculate elapsed time if available
        elapsed_time = None
        if (SemanticLogger._operation_times and
            operation in SemanticLogger._operation_times):
            elapsed_time = time.time() - SemanticLogger._operation_times[operation]
            del SemanticLogger._operation_times[operation]

        message = f"Completed operation: {operation}"

        if elapsed_time is not None:
            message += f" (took {elapsed_time:.3f}s)"

        if result:
            result_str = ", ".join(f"{k}={v}" for k, v in result.items())
            message += f" -> {result_str}"

        logger.info(message)

    @staticmethod
    def operation_error(operation: str, error: Exception, details: Dict[str, Any] | None = None) -> None:
        """
        Log an operation error with consistent formatting.

        Args:
            operation: Name of the operation that failed
            error: The exception that occurred
            details: Optional dictionary with error context
        """
        logger = logging.getLogger(__name__)

        # Calculate elapsed time if available
        elapsed_time = None
        if (hasattr(SemanticLogger, '_operation_times') and
            operation in SemanticLogger._operation_times):
            elapsed_time = time.time() - SemanticLogger._operation_times[operation]
            del SemanticLogger._operation_times[operation]

        message = f"Failed operation: {operation} - {error}"

        if elapsed_time is not None:
            message += f" (after {elapsed_time:.3f}s)"

        if details:
            detail_str = ", ".join(f"{k}={v}" for k, v in details.items())
            message += f" | Context: {detail_str}"

        logger.error(message, exc_info=True)

    @staticmethod
    def performance_metric(metric_name: str, value: float, unit: str = "ms") -> None:
        """
        Log a performance metric.

        Args:
            metric_name: Name of the performance metric
            value: The measured value
            unit: Unit of measurement (default: ms)
        """
        logger = logging.getLogger(__name__)
        logger.debug(f"Performance metric: {metric_name} = {value:.3f}{unit}")

    @staticmethod
    def security_event(event_type: str, details: Dict[str, Any]) -> None:
        """
        Log a security-related event.

        Args:
            event_type: Type of security event
            details: Dictionary with event details
        """
        logger = logging.getLogger(__name__)
        detail_str = ", ".join(f"{k}={v}" for k, v in details.items())
        logger.warning(f"Security event: {event_type} | {detail_str}")

    @staticmethod
    def version_operation(operation: str, version_before: str, version_after: str | None = None) -> None:
        """
        Log version-specific operations.

        Args:
            operation: The version operation performed
            version_before: The version before the operation
            version_after: The version after the operation (if applicable)
        """
        logger = logging.getLogger(__name__)

        if version_after:
            message = f"Version {operation}: {version_before} -> {version_after}"
        else:
            message = f"Version {operation}: {version_before}"

        logger.info(message)
