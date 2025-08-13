# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
GitHub Actions integration module.

This module handles GitHub Actions specific logic and execution flow
for string-mode tag incrementing only.
"""

import logging
import time
from typing import Any

from .app_context import GitHubActionsConfig
from .exceptions import handle_github_actions_errors
from .git_operations import GitOperations
from .incrementer import VersionIncrementer
from .io_operations import IOOperations
from .logging_config import LoggingConfig, SemanticLogger
from .modes import OperationMode, ModeValidator
from .parser import SemanticVersion

logger = logging.getLogger(__name__)


class GitHubActionsRunner:
    """Handles GitHub Actions execution mode for string-based tag incrementing."""

    def __init__(self, debug_mode: bool = False):
        """
        Initialize GitHub Actions runner.

        Args:
            debug_mode: Enable debug mode
        """
        self.debug_mode = debug_mode
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Configure logging for GitHub Actions mode."""
        LoggingConfig.setup_logging(
            debug=self.debug_mode,
            suppress_console=not self.debug_mode
        )

        if not self.debug_mode:
            # Suppress excessive logging in non-debug mode
            LoggingConfig.set_module_level("semantic_tag_increment", logging.WARNING)

    @handle_github_actions_errors
    def run(self) -> None:
        """Run in GitHub Actions mode."""
        start_time = time.time()
        SemanticLogger.operation_start("github_actions_execution", {"debug_mode": self.debug_mode})

        logger.info("Running in GitHub Actions mode")

        # Get and validate configuration
        config = GitHubActionsConfig.get_inputs()
        self._validate_github_actions_inputs(config)

        # Print startup information
        self._print_startup_banner(config)

        # Execute the increment operation with timing
        SemanticLogger.operation_start("version_increment", {
            "tag": config.get("tag"),
            "increment": config.get("increment", "dev")
        })

        result = self._execute_increment(config)

        SemanticLogger.operation_success("version_increment", {
            "original": str(result["original_version"]),
            "incremented": str(result["incremented_version"])
        })

        # Output results and exit successfully
        self._output_results(result)
        self._print_success_banner()

        total_time = time.time() - start_time
        SemanticLogger.operation_success("github_actions_execution", {
            "total_time_seconds": f"{total_time:.3f}"
        })
        SemanticLogger.performance_metric("github_actions_total_time", total_time * 1000, "ms")

    def _validate_github_actions_inputs(self, config: dict[str, str | None]) -> None:
        """Validate GitHub Actions inputs for string mode."""
        # Only string mode is supported
        operation_mode = OperationMode.STRING

        # Validate inputs for string mode
        tag = config.get("tag")
        if not tag or not tag.strip():
            raise ValueError("String mode requires a non-empty 'tag' input")

        # Validate other inputs
        ModeValidator.validate_mode_inputs(
            operation_mode,
            tag,
            config.get("path"),
            True  # check_tags parameter (not used in string mode)
        )

    def _print_startup_banner(self, config: dict[str, str | None]) -> None:
        """Print startup banner and configuration."""
        print("::group::Semantic Tag Increment Configuration")
        print("Semantic Tag Increment")
        print("=" * 50)
        print("Configuration:")
        print("   Mode: string")
        print(f"   Tag: {config.get('tag', 'Not specified')}")
        print(f"   Increment: {config.get('increment', 'dev')}")
        if config.get("prerelease_type"):
            print(f"   Prerelease Type: {config['prerelease_type']}")
        print(f"   Path: {config.get('path', '.')}")
        print(f"   Check Tags: {config.get('check_tags', 'true')}")
        print(f"   Preserve Metadata: {config.get('preserve_metadata', 'false')}")
        print(f"   Fetch Timeout: {config.get('fetch_timeout', '120')} seconds")
        print("=" * 50)
        print("::endgroup::")
        print()

    def _execute_increment(self, config: dict[str, str | None]) -> dict[str, Any]:
        """
        Execute the version increment operation.

        Args:
            config: Configuration dictionary

        Returns:
            Dictionary containing the increment results
        """
        # Parse input tag
        print("::group::Version Source")
        tag = config.get("tag")
        if not tag:
            raise ValueError("Tag is required for string mode")

        original_version = SemanticVersion.parse(tag)
        print("Version source: input tag")
        print(f"Version: {original_version}")

        increment_str = config.get("increment", "dev")
        if increment_str is None:
            increment_str = "dev"
        increment_type = VersionIncrementer.determine_increment_type(increment_str)
        print(f"Increment type: {increment_type.value}")
        print("::endgroup::")

        # Get existing tags for conflict checking (conditional)
        existing_tags: set[str]
        check_tags_str = config.get("check_tags", "true")
        check_tags = check_tags_str is not None and check_tags_str.lower() == "true"
        path = config.get("path", ".") or "."

        # Get preserve_metadata setting
        preserve_metadata_str = config.get("preserve_metadata", "false")
        preserve_metadata = preserve_metadata_str is not None and preserve_metadata_str.lower() == "true"

        # Get fetch_timeout setting
        fetch_timeout_str = config.get("fetch_timeout", "120")
        try:
            fetch_timeout = int(fetch_timeout_str) if fetch_timeout_str else 120
        except ValueError:
            logger.warning(f"Invalid fetch_timeout value: {fetch_timeout_str}, using default 120")
            fetch_timeout = 120

        print("::group::Git Operations")
        if check_tags:
            try:
                tag_start_time = time.time()
                existing_tags = GitOperations.get_existing_tags(path, timeout=fetch_timeout)
                tag_time = time.time() - tag_start_time

                print(f"Retrieved {len(existing_tags)} existing git tags")
                SemanticLogger.performance_metric("git_tag_retrieval", tag_time * 1000, "ms")

                incrementer = VersionIncrementer(existing_tags, preserve_metadata=preserve_metadata)
            except Exception as e:
                logger.warning(f"Error with git operations: {e}")
                print(f"Git operation failed: {e}")
                print("Proceeding without conflict checking")
                existing_tags = set()
                incrementer = VersionIncrementer(existing_tags, preserve_metadata=preserve_metadata)
        else:
            print("Tag checking disabled - proceeding without conflict checking")
            existing_tags = set()
            incrementer = VersionIncrementer(existing_tags, preserve_metadata=preserve_metadata)
        print("::endgroup::")

        # Perform increment
        print("::group::Version Increment")
        increment_start_time = time.time()
        incremented_version = incrementer.increment(
            original_version, increment_type, config.get("prerelease_type")
        )
        increment_time = time.time() - increment_start_time

        print("Incremented version successfully")
        SemanticLogger.performance_metric("version_increment", increment_time * 1000, "ms")
        SemanticLogger.version_operation("increment", str(original_version), str(incremented_version))
        print("::endgroup::")

        # Log operation details
        self._log_operation_details(
            original_version, incremented_version, existing_tags
        )

        return {
            "original_version": original_version,
            "incremented_version": incremented_version,
            "increment_type": increment_type,
            "existing_tags": existing_tags,
        }

    def _output_results(
        self,
        result: dict[str, Any]
    ) -> None:
        """Output results to GitHub Actions."""
        print("::group::Results")
        incremented_version = result["incremented_version"]

        # Prepare outputs
        full_version = incremented_version.to_string(include_prefix=True)
        numeric_version = incremented_version.numeric_version()

        # Write GitHub Actions outputs
        IOOperations.write_outputs_to_github(full_version, numeric_version)

        # Print results with GitHub Actions formatting
        print(f"Original version: {result['original_version']}")
        print(f"Next version:     {full_version}")
        print(f"Numeric version:  {numeric_version}")

        # Add GitHub Actions notice for visibility
        print(f"::notice title=Version Increment Complete::Original: {result['original_version']} -> New: {full_version}")
        print("::endgroup::")

    def _print_success_banner(self) -> None:
        """Print success banner."""
        print()
        print("::group::Success")
        print("Semantic Tag Increment")
        print("=" * 50)
        print("Version increment completed successfully!")
        print("::endgroup::")
        logger.info("GitHub Actions execution completed successfully")

    def _log_operation_details(
        self,
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
