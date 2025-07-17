# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
CLI interface module.

This module provides the clean command-line interface using Typer,
separated from GitHub Actions and other concerns.
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
from .project_detector import ProjectDetector
from .version_extractor import VersionExtractor
from .version_source import VersionSourceFactory, VersionSource, VersionExtractionResult

logger = logging.getLogger(__name__)

app = typer.Typer(
    help="A Python tool to increment semantic version tags.",
    context_settings={"help_option_names": ["-h", "--help"]},
)


@app.callback()
def main_callback(
    debug: Annotated[
        bool,
        typer.Option("--debug", help="Enable debug logging output to terminal"),
    ] = False,
) -> None:
    """
    Semantic Tag Increment Tool

    A tool for intelligently incrementing semantic version tags with support
    for complex pre-release patterns and GitHub Actions integration.
    """
    LoggingConfig.setup_logging(debug, suppress_console=False)


@app.command("increment")
@handle_cli_errors
def increment_version(
    tag: Annotated[
        Optional[str],
        typer.Option(
            "--tag", "-t", help="The existing semantic tag to be incremented (optional in some modes)"
        ),
    ] = None,
    increment: Annotated[
        str,
        typer.Option(
            "--increment",
            "-i",
            help="Increment type: major, minor, patch, prerelease/dev",
        ),
    ] = "dev",
    prerelease_type: Annotated[
        str | None,
        typer.Option(
            "--prerelease-type",
            "-p",
            help="Type of prerelease identifier (dev, alpha, beta, rc, etc.)",
        ),
    ] = None,
    mode: Annotated[
        str,
        typer.Option(
            "--mode",
            "-m",
            help="Operation mode: string, path, combined, auto",
        ),
    ] = "auto",
    check_conflicts: Annotated[
        bool,
        typer.Option(
            "--check-conflicts/--no-check-conflicts",
            help="Check for conflicts with existing git tags",
        ),
    ] = True,
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
    path: Annotated[
        str,
        typer.Option(
            "--path",
            help="Directory location containing project code",
        ),
    ] = ".",
) -> None:
    """
    Increment a semantic version tag.

    This command supports multiple operation modes for different workflows:

    • string: Use explicit tag input only
    • path: Auto-detect version from project files
    • combined: Use explicit tag with repository context
    • auto: Fully automatic with heuristics (default)

    Examples:
        semantic-tag-increment increment --tag "v1.2.3" --increment "patch" --mode "string"
        semantic-tag-increment increment --increment "minor" --mode "path" --path "/path/to/project"
        semantic-tag-increment increment --tag "1.0.0" --increment "major" --mode "combined"
        semantic-tag-increment increment --increment "prerelease" --mode "auto"
    """
    # Parse and validate mode
    operation_mode = ModeHelper.parse_mode(mode)

    # Validate all inputs based on mode
    _validate_increment_inputs(operation_mode, tag, increment, output_format, prerelease_type, path, check_conflicts)

    # Configure logging if needed
    _configure_increment_logging(suppress_cli_logging)

    # Process the version increment
    result = _process_version_increment(operation_mode, tag, increment, prerelease_type, check_conflicts, path)

    # Output results in specified format
    _output_increment_results(result, output_format)

    logger.info("Version increment completed successfully")


def _validate_increment_inputs(
    mode: OperationMode,
    tag: Optional[str],
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

    # Validate path exists and is a directory (handled by ModeValidator for most cases)
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
    tag: Optional[str],
    increment: str,
    prerelease_type: Optional[str],
    check_conflicts: bool,
    path: str
) -> dict[str, SemanticVersion]:
    """Process the version increment operation."""
    # Log mode information
    ModeHelper.log_mode_operation(mode, tag, path)

    # Get effective path
    effective_path = ModeHelper.get_effective_path(mode, path)

    # Create version source based on mode
    version_source = _create_version_source(mode, tag, effective_path)

    # Get the version to increment
    original_version = version_source.get_version()
    logger.info(f"Using version: {original_version} from {version_source.get_source_description()}")

    # Determine increment type
    increment_type = VersionIncrementer.determine_increment_type(increment)
    logger.info(f"Increment type: {increment_type.value}")

    # Get existing tags if conflict checking is enabled
    should_check_tags = ModeHelper.should_check_git_tags(mode, check_conflicts)
    existing_tags: set[str] = GitOperations.get_existing_tags(effective_path) if should_check_tags else set()

    # Create incrementer and perform increment
    incrementer = VersionIncrementer(existing_tags)
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


def _create_version_source(mode: OperationMode, tag: Optional[str], path: str) -> VersionSource:
    """Create appropriate version source based on mode."""
    if mode == OperationMode.STRING:
        if not tag:
            ErrorReporter.log_and_raise_validation_error("String mode requires a tag input")
        assert tag is not None  # for mypy
        return VersionSourceFactory.create_string_source(tag)

    elif mode == OperationMode.PATH:
        # Extract version from project files
        extraction_result = _extract_version_from_path(path)
        if not extraction_result:
            ErrorReporter.log_and_raise_validation_error(
                f"No version found in project files at {path}"
            )
        assert extraction_result is not None  # for mypy
        return VersionSourceFactory.create_extracted_source(extraction_result)

    elif mode == OperationMode.COMBINED:
        if not tag:
            ErrorReporter.log_and_raise_validation_error("Combined mode requires a tag input")
        assert tag is not None  # for mypy
        return VersionSourceFactory.create_string_source(tag)

    elif mode == OperationMode.AUTO:
        # Try extraction first, then fall back to string if provided
        extraction_result = _extract_version_from_path(path)
        return VersionSourceFactory.create_auto_source(tag, extraction_result)

    # This should never be reached with valid enum values
    raise AssertionError(f"Unhandled mode: {mode}")


def _extract_version_from_path(path: str) -> Optional[VersionExtractionResult]:
    """Extract version from project files at the given path."""
    try:
        # Detect project files
        detector = ProjectDetector(path)
        project_files = detector.find_project_files()

        if not project_files:
            logger.debug(f"No project files found in {path}")
            return None

        # Extract version from the first suitable file
        extractor = VersionExtractor()
        result = extractor.find_best_version(project_files)

        if result:
            logger.info(f"Extracted version {result.version} from {result.source_file}")
        else:
            logger.debug(f"No valid version found in project files at {path}")

        return result

    except Exception as e:
        logger.debug(f"Version extraction failed for {path}: {e}")
        return None


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





@app.command("validate")
@handle_cli_errors
def validate_version(
    tag: Annotated[
        str,
        typer.Option(
            "--tag", "-t", help="The semantic version tag to validate"
        ),
    ],
) -> None:
    """
    Validate a semantic version tag.

    Check if the provided tag is a valid semantic version according to the
    semantic versioning specification.

    Examples:
        semantic-tag-increment validate --tag "v1.2.3"
        semantic-tag-increment validate --tag "1.0.0-alpha.1+build.123"
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


@app.command("suggest")
@handle_cli_errors
def suggest_versions(
    tag: Annotated[
        str, typer.Option("--tag", "-t", help="The current semantic tag")
    ],
    increment: Annotated[
        str,
        typer.Option(
            "--increment", "-i", help="Increment type for suggestions"
        ),
    ] = "prerelease",
) -> None:
    """
    Suggest possible next versions for a given increment type.

    This command provides multiple suggestions for the next version, which
    can be helpful when working with pre-release versions.

    Examples:
        semantic-tag-increment suggest --tag "v1.2.3" --increment "prerelease"
    """
    logger.info(f"Generating suggestions for: {tag}")
    version = SemanticVersion.parse(tag)
    increment_type = VersionIncrementer.determine_increment_type(increment)

    existing_tags = GitOperations.get_existing_tags()
    incrementer = VersionIncrementer(existing_tags)

    suggestions = incrementer.suggest_next_version(version, increment_type)

    typer.echo(
        f"Suggestions for {increment_type.value} increment of {version}:"
    )
    for i, suggestion in enumerate(suggestions, 1):
        typer.echo(f"  {i}. {suggestion}")

    logger.info(f"Generated {len(suggestions)} suggestions")


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
