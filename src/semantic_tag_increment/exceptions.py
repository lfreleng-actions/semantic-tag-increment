# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Centralized exception handling for semantic tag increment operations.

This module provides custom exception classes and error handling utilities
to improve error reporting and debugging throughout the application.
"""

import functools
import logging
import sys
from typing import Any, Callable, Dict, TypeVar, NoReturn

import click
import typer

logger = logging.getLogger(__name__)

# Type variable for decorated functions
F = TypeVar('F', bound=Callable[..., Any])


class SemanticVersionError(Exception):
    """Base exception for all semantic version operations."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        """
        Initialize semantic version error.

        Args:
            message: Error message
            details: Optional dictionary with additional error details
        """
        super().__init__(message)
        self.details = details or {}
        self.message = message


class ValidationError(SemanticVersionError):
    """Exception raised when validation fails."""
    pass


class ParseError(ValueError, SemanticVersionError):
    """Exception raised when parsing semantic version fails."""
    pass


class IncrementError(SemanticVersionError):
    """Exception raised when version increment operation fails."""
    pass


class GitOperationError(SemanticVersionError):
    """Exception raised when git operations fail."""
    pass


class ConfigurationError(SemanticVersionError):
    """Exception raised when configuration is invalid."""
    pass


class SecurityError(SemanticVersionError):
    """Exception raised when security validation fails."""
    pass


class ProjectDetectionError(SemanticVersionError):
    """Exception raised when project detection fails."""
    pass


class VersionExtractionError(SemanticVersionError):
    """Exception raised when version extraction fails."""
    pass


def handle_cli_errors(func: F) -> F:
    """
    Decorator for CLI command error handling.

    Provides consistent error handling and logging for CLI commands.
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except SemanticVersionError as e:
            return _handle_semantic_error_cli(e, func.__name__)
        except (typer.Exit, click.exceptions.Exit):
            # Re-raise Exit exceptions (including help, etc.)
            raise
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}", exc_info=True)
            typer.echo(f"Unexpected Error: {e}", err=True)
            raise typer.Exit(1) from e

    return wrapper  # type: ignore[return-value]


def _handle_semantic_error_cli(error: SemanticVersionError, func_name: str) -> None:
    """Handle semantic version errors for CLI commands."""
    error_type = type(error).__name__.replace("Error", "")
    logger.error(f"{error_type} error in {func_name}: {error}")
    if error.details:
        logger.debug(f"Error details: {error.details}")
    typer.echo(f"{error_type} Error: {error}", err=True)
    raise typer.Exit(1) from error


def handle_github_actions_errors(func: F) -> F:
    """
    Decorator for GitHub Actions error handling.

    Provides consistent error handling for GitHub Actions mode.
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except SemanticVersionError as e:
            return _handle_semantic_error_gha(e)
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            print(f"::error::Unexpected Error: {e}")
            sys.exit(1)

    return wrapper  # type: ignore[return-value]


def _handle_semantic_error_gha(error: SemanticVersionError) -> None:
    """Handle semantic version errors for GitHub Actions."""
    error_type = type(error).__name__.replace("Error", "")
    logger.error(f"{error_type} error: {error}")
    if error.details:
        logger.debug(f"Error details: {error.details}")
    print(f"::error::{error_type} Error: {error}")
    sys.exit(1)


def wrap_validation_error(original_error: Exception, context: str) -> ValidationError:
    """
    Wrap a generic exception as a ValidationError with context.

    Args:
        original_error: The original exception
        context: Context information about where the error occurred

    Returns:
        ValidationError with context and original error details
    """
    return ValidationError(
        f"{context}: {original_error}",
        details={
            "original_error_type": type(original_error).__name__,
            "original_error_message": str(original_error),
            "context": context
        }
    )


def wrap_parse_error(original_error: Exception, version_string: str) -> ParseError:
    """
    Wrap a generic exception as a ParseError with version context.

    Args:
        original_error: The original exception
        version_string: The version string that failed to parse

    Returns:
        ParseError with version context and original error details
    """
    return ParseError(
        f"Failed to parse version '{version_string}': {original_error}",
        details={
            "original_error_type": type(original_error).__name__,
            "original_error_message": str(original_error),
            "version_string": version_string,
            "version_length": len(version_string) if version_string else 0
        }
    )


def wrap_increment_error(
    original_error: Exception,
    version: str,
    increment_type: str,
    prerelease_type: str | None = None
) -> IncrementError:
    """
    Wrap a generic exception as an IncrementError with operation context.

    Args:
        original_error: The original exception
        version: The version being incremented
        increment_type: The type of increment being performed
        prerelease_type: Optional prerelease type

    Returns:
        IncrementError with operation context and original error details
    """
    return IncrementError(
        f"Failed to increment version '{version}' with type '{increment_type}': {original_error}",
        details={
            "original_error_type": type(original_error).__name__,
            "original_error_message": str(original_error),
            "version": version,
            "increment_type": increment_type,
            "prerelease_type": prerelease_type
        }
    )


def wrap_git_error(original_error: Exception, operation: str, path: str = ".") -> GitOperationError:
    """
    Wrap a generic exception as a GitOperationError with operation context.

    Args:
        original_error: The original exception
        operation: The git operation that failed
        path: The repository path

    Returns:
        GitOperationError with operation context and original error details
    """
    return GitOperationError(
        f"Git operation '{operation}' failed in '{path}': {original_error}",
        details={
            "original_error_type": type(original_error).__name__,
            "original_error_message": str(original_error),
            "operation": operation,
            "path": path
        }
    )


def wrap_security_error(original_error: Exception, security_check: str, value: str) -> SecurityError:
    """
    Wrap a generic exception as a SecurityError with security context.

    Args:
        original_error: The original exception
        security_check: The security check that failed
        value: The value that failed validation

    Returns:
        SecurityError with security context and original error details
    """
    return SecurityError(
        f"Security check '{security_check}' failed for value '{value}': {original_error}",
        details={
            "original_error_type": type(original_error).__name__,
            "original_error_message": str(original_error),
            "security_check": security_check,
            "value": value,
            "value_length": len(value) if isinstance(value, str) else None
        }
    )


class ErrorReporter:
    """Utility class for consistent error reporting."""

    @staticmethod
    def log_and_raise_validation_error(message: str, details: dict[str, Any] | None = None) -> NoReturn:
        """Log and raise a validation error."""
        error = ValidationError(message, details)
        logger.error(f"Validation error: {message}")
        if details:
            logger.debug(f"Error details: {details}")
        raise error

    @staticmethod
    def log_and_raise_parse_error(message: str, version_string: str) -> None:
        """Log and raise a parse error."""
        details = {
            "version_string": version_string,
            "version_length": len(version_string) if version_string else 0
        }
        error = ParseError(message, details)
        logger.error(f"Parse error: {message}")
        logger.debug(f"Error details: {details}")
        raise error

    @staticmethod
    def log_and_raise_increment_error(
        message: str,
        version: str,
        increment_type: str,
        prerelease_type: str | None = None
    ) -> None:
        """Log and raise an increment error."""
        details = {
            "version": version,
            "increment_type": increment_type,
            "prerelease_type": prerelease_type
        }
        error = IncrementError(message, details)
        logger.error(f"Increment error: {message}")
        logger.debug(f"Error details: {details}")
        raise error

    @staticmethod
    def log_and_raise_git_error(message: str, operation: str, path: str = ".") -> None:
        """Log and raise a git operation error."""
        details = {
            "operation": operation,
            "path": path
        }
        error = GitOperationError(message, details)
        logger.error(f"Git operation error: {message}")
        logger.debug(f"Error details: {details}")
        raise error

    @staticmethod
    def log_and_raise_security_error(message: str, security_check: str, value: str) -> None:
        """Log and raise a security error."""
        details = {
            "security_check": security_check,
            "value": value,
            "value_length": len(value) if isinstance(value, str) else None
        }
        error = SecurityError(message, details)
        logger.error(f"Security error: {message}")
        logger.debug(f"Error details: {details}")
        raise error
