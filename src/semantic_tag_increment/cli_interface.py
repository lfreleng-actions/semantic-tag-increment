# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
CLI interface module.

This module provides the clean command-line interface using Typer,
focused solely on semantic tag incrementing without project detection.
"""

import logging
import os
import re
from typing import Annotated, Optional

import typer

from .exceptions import handle_cli_errors, ErrorReporter
from .git_operations import GitOperations
from .incrementer import VersionIncrementer
from .io_operations import IOOperations
from .logging_config import LoggingConfig
from .modes import OperationMode, ModeValidator, ModeHelper
from .parser import SemanticVersion

logger = logging.getLogger(__name__)

app = typer.Typer(
    help="A Python tool to increment semantic version tags.",
    context_settings={"help_option_names": ["-h", "--help"]},
)


@app.callback(invoke_without_command=True)
@handle_cli_errors
def main_callback(
    ctx: typer.Context,
    debug: Annotated[
        bool,
        typer.Option("--debug", help="Enable debug logging output to terminal"),
    ] = False,
    tag: Annotated[
        Optional[str],
        typer.Option(
            "--tag", "-t", help="The existing semantic tag to be incremented"
        ),
    ] = None,
    increment: Annotated[
        Optional[str],
        typer.Option(
            "--increment",
            "-i",
            help="Increment type: major, minor, patch, prerelease/dev (defaults: dev for increment, prerelease for --suggest, not required with --validate)",
        ),
    ] = None,
    prerelease_type: Annotated[
        str | None,
        typer.Option(
            "--prerelease-type",
            "-p",
            help="Type of prerelease identifier (dev, alpha, beta, rc, etc.)",
        ),
    ] = None,
    check_conflicts: Annotated[
        bool,
        typer.Option(
            "--check-conflicts/--no-check-conflicts",
            help="Check for conflicts with existing git tags",
        ),
    ] = True,
    preserve_metadata: Annotated[
        bool,
        typer.Option(
            "--preserve-metadata/--no-preserve-metadata",
            help="Preserve build metadata during version increments",
        ),
    ] = False,
    output_format: Annotated[
        str,
        typer.Option(
            "--output-format",
            "-f",
            help="Output format: full (with prefix), numeric (without prefix), both",
        ),
    ] = "full",
    suppress_cli_logging: Annotated[
        bool,
        typer.Option(
            "--suppress-cli-logging/--no-suppress-cli-logging",
            help="Suppress CLI logging when running in GitHub Actions mode",
        ),
    ] = False,
    validate_only: Annotated[
        bool,
        typer.Option(
            "--validate",
            help="Validate the semantic version tag format without incrementing",
            show_default=False,
        ),
    ] = False,
    suggest: Annotated[
        bool,
        typer.Option(
            "--suggest",
            help="Show multiple possible next versions for the given increment type",
            show_default=False,
        ),
    ] = False,
    path: Annotated[
        str,
        typer.Option(
            "--path",
            help="Directory location for git operations",
        ),
    ] = ".",
    fetch_timeout: Annotated[
        int,
        typer.Option(
            "--fetch-timeout",
            help="Timeout in seconds for git remote fetch operations",
        ),
    ] = 120,
) -> None:
    """
    Semantic Tag Increment Tool

    A tool for incrementing semantic version tags with support
    for complex pre-release patterns and GitHub Actions integration.

    By default, increments a semantic version tag when --tag is provided.
    Use --validate to validate tag format without incrementing.
    Use --suggest to see multiple possible next versions.

    Examples:
        semantic-tag-increment --tag "v1.2.3" --increment "patch"
        semantic-tag-increment --tag "1.0.0" --increment "major"
        semantic-tag-increment --tag "v2.1.0" --increment "prerelease" --prerelease-type "alpha"
        semantic-tag-increment --tag "v1.2.3" --validate
        semantic-tag-increment --tag "v1.2.3" --increment "prerelease" --suggest
        semantic-tag-increment --tag "v1.2.3" --increment "patch" --fetch-timeout 60
    """
    LoggingConfig.setup_logging(debug, suppress_console=False)

    # If a subcommand is being invoked, don't run main logic
    if ctx.invoked_subcommand is not None:
        return

    # Handle validation-only mode
    if validate_only:
        if tag is None:
            ErrorReporter.log_and_raise_validation_error("Tag parameter is required for validation")
        validate_version_inline(tag)
        return

    # Handle suggest mode
    if suggest:
        if tag is None:
            ErrorReporter.log_and_raise_validation_error("Tag parameter is required for suggestions")
        if increment is None:
            increment = "prerelease"  # Default for suggestions
        suggest_versions_inline(tag, increment, path, fetch_timeout)
        return

    # If no tag is provided and not validating or suggesting, show help
    if tag is None:
        typer.echo(ctx.get_help())
        ctx.exit()

    # For increment mode, increment parameter is required
    if increment is None:
        increment = "dev"  # Default value

    # Run increment logic
    increment_version(
        tag=tag,
        increment=increment,
        prerelease_type=prerelease_type,
        check_conflicts=check_conflicts,
        output_format=output_format,
        suppress_cli_logging=suppress_cli_logging,
        path=path,
        preserve_metadata=preserve_metadata,
        fetch_timeout=fetch_timeout,
    )


def validate_version_inline(tag: str) -> None:
    """
    Validate a semantic version tag and display results.

    Args:
        tag: The semantic version tag to validate
    """
    logger.info(f"Validating version: {tag}")
    version = SemanticVersion.parse(tag)

    typer.echo(f"✅ Valid semantic version: {version}")
    typer.echo(f"   Major:      {version.major}")
    typer.echo(f"   Minor:      {version.minor}")
    typer.echo(f"   Patch:      {version.patch}")

    if version.is_prerelease():
        typer.echo(f"   Pre-release: {version.prerelease}")
        identifiers = version.get_prerelease_identifiers()
        typer.echo(f"   Pre-release identifiers:   {identifiers}")

        numeric_components = version.find_numeric_prerelease_components()
        if numeric_components:
            typer.echo(f"   Numeric components:      {numeric_components}")

    if version.has_metadata():
        typer.echo(f"   Metadata:   {version.metadata}")

    if version.prefix:
        typer.echo(f"   Prefix:     {version.prefix}")

    logger.info("Version validation completed successfully")


def suggest_versions_inline(tag: str, increment: str, path: str = ".", fetch_timeout: int = 120) -> None:
    """
    Suggest multiple possible next versions and display results.

    Args:
        tag: The current semantic tag
        increment: Increment type for suggestions
        path: Directory location for git operations
        fetch_timeout: Timeout in seconds for git remote fetch operations
    """
    logger.info(f"Generating suggestions for: {tag}")
    version = SemanticVersion.parse(tag)
    increment_type = VersionIncrementer.determine_increment_type(increment)

    existing_tags = GitOperations.get_existing_tags(path, timeout=fetch_timeout)
    incrementer = VersionIncrementer(existing_tags)

    suggestions = incrementer.suggest_next_version(version, increment_type)

    typer.echo(
        f"Suggestions for {increment_type.value} increment of {version}:"
    )
    for i, suggestion in enumerate(suggestions, 1):
        typer.echo(f"  {i}. {suggestion}")

    logger.info(f"Generated {len(suggestions)} suggestions")


def increment_version(
    tag: str,
    increment: str = "dev",
    prerelease_type: Optional[str] = None,
    check_conflicts: bool = True,
    output_format: str = "full",
    suppress_cli_logging: bool = False,
    path: str = ".",
    preserve_metadata: bool = False,
    fetch_timeout: int = 120,
) -> None:
    """
    Increment a semantic version tag.

    This function takes an explicit semantic version tag and increments it
    according to the specified increment type.
    """
    # Force string mode (only supported mode)
    operation_mode = OperationMode.STRING

    # Validate all inputs
    _validate_increment_inputs(operation_mode, tag, increment, output_format, prerelease_type, path, check_conflicts)

    # Configure logging if needed
    _configure_increment_logging(suppress_cli_logging)

    # Process the version increment
    result = _process_version_increment(operation_mode, tag, increment, prerelease_type, check_conflicts, path, preserve_metadata, fetch_timeout)

    # Output results in specified format
    _output_increment_results(result, output_format)

    logger.info("Version increment completed successfully")


def _validate_increment_inputs(
    mode: OperationMode,
    tag: str,
    increment: str,
    output_format: str,
    prerelease_type: Optional[str],
    path: str,
    check_conflicts: bool
) -> None:
    """Validate all inputs for the increment command."""
    # Validate mode-specific inputs
    ModeValidator.validate_mode_inputs(mode, tag, path, check_conflicts)

    # Basic input validation
    if not increment or not increment.strip():
        ErrorReporter.log_and_raise_validation_error("Increment type cannot be empty")

    # Validate output format
    valid_formats = ["full", "numeric", "both"]
    if output_format not in valid_formats:
        ErrorReporter.log_and_raise_validation_error(
            f"Invalid output format: {output_format}. Valid formats: {', '.join(valid_formats)}"
        )

    # Validate prerelease type if provided
    if prerelease_type is not None and not prerelease_type.strip():
        ErrorReporter.log_and_raise_validation_error("Prerelease type cannot be empty if provided")

    if (
        prerelease_type
        and not re.fullmatch(r"[a-zA-Z0-9.-]+", prerelease_type)
    ):
        ErrorReporter.log_and_raise_validation_error(
            "Prerelease type must contain only alphanumeric characters, hyphens, and dots"
        )

    # Validate path exists and is a directory
    effective_path = ModeHelper.get_effective_path(mode, path)
    if not os.path.exists(effective_path):
        ErrorReporter.log_and_raise_validation_error(f"Path directory does not exist: {effective_path}")

    if not os.path.isdir(effective_path):
        ErrorReporter.log_and_raise_validation_error(f"Path is not a directory: {effective_path}")


def _configure_increment_logging(suppress_cli_logging: bool) -> None:
    """Configure logging for the increment operation."""
    if suppress_cli_logging and IOOperations.is_github_actions():
        LoggingConfig.set_module_level("semantic_tag_increment", logging.WARNING)


def _process_version_increment(
    mode: OperationMode,
    tag: str,
    increment: str,
    prerelease_type: Optional[str],
    check_conflicts: bool,
    path: str,
    preserve_metadata: bool,
    fetch_timeout: int = 120
) -> dict[str, SemanticVersion]:
    """Process the version increment operation."""
    # Log mode information
    ModeHelper.log_mode_operation(mode, tag, path)

    # Get effective path for Git operations
    effective_path = ModeHelper.get_effective_path(mode, path)

    # Parse the input tag
    original_version = SemanticVersion.parse(tag)
    logger.info(f"Using version: {original_version} from input tag")

    # Determine increment type
    increment_type = VersionIncrementer.determine_increment_type(increment)
    logger.info(f"Increment type: {increment_type.value}")

    # Get existing tags if conflict checking is enabled
    should_check_tags = ModeHelper.should_check_git_tags(mode, check_conflicts)
    existing_tags: set[str] = GitOperations.get_existing_tags(effective_path, timeout=fetch_timeout) if should_check_tags else set()

    # Create incrementer and perform increment
    incrementer = VersionIncrementer(existing_tags, preserve_metadata=preserve_metadata)
    incremented_version = incrementer.increment(
        original_version, increment_type, prerelease_type
    )

    # Log operation details
    _log_operation_details(
        original_version, incremented_version, existing_tags
    )

    return {
        "original_version": original_version,
        "incremented_version": incremented_version
    }


def _output_increment_results(result: dict[str, SemanticVersion], output_format: str) -> None:
    """Output results in the specified format."""
    incremented_version = result["incremented_version"]

    # Generate output versions
    full_version = incremented_version.to_string(include_prefix=True)
    numeric_version = incremented_version.numeric_version()

    # Output based on format
    if output_format == "full":
        typer.echo(full_version)
    elif output_format == "numeric":
        typer.echo(numeric_version)
    elif output_format == "both":
        typer.echo(f"Full version:    {full_version}")
        typer.echo(f"Numeric version: {numeric_version}")

    # Write GitHub Actions outputs if in GitHub Actions context
    if IOOperations.is_github_actions():
        IOOperations.write_outputs_to_github(full_version, numeric_version)








def _log_operation_details(
    original: SemanticVersion,
    incremented: SemanticVersion,
    existing_tags: set[str],
) -> None:
    """Log detailed information about the increment operation."""
    logger.info(f"Original version: {original}")
    logger.info(f"Next version: {incremented}")

    # Only log conflict check if there were actually tags to check
    if existing_tags:
        logger.info(f"Checked {len(existing_tags)} existing tags for conflicts")

    if original.is_prerelease():
        logger.debug(
            f"Original prerelease identifiers: {original.get_prerelease_identifiers()}"
        )
        numeric_components = original.find_numeric_prerelease_components()
        if numeric_components:
            logger.debug(
                f"Found numeric prerelease components: {numeric_components}"
            )

    if incremented.is_prerelease():
        logger.debug(
            f"New prerelease identifiers: {incremented.get_prerelease_identifiers()}"
        )
