# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
GitHub Actions integration module.

This module handles GitHub Actions specific logic and execution flow.
"""

import logging
import sys
import time
from typing import Any, Optional

from .app_context import GitHubActionsConfig
from .exceptions import handle_github_actions_errors
from .git_operations import GitOperations
from .incrementer import VersionIncrementer
from .io_operations import IOOperations
from .logging_config import LoggingConfig, SemanticLogger
from .modes import OperationMode, ModeValidator, ModeHelper
from .parser import SemanticVersion
from .project_detector import ProjectDetector
from .version_extractor import VersionExtractor
from .version_source import VersionSourceFactory, VersionSource, VersionExtractionResult

logger = logging.getLogger(__name__)


class GitHubActionsRunner:
    """Handles GitHub Actions execution mode."""

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
        """Validate GitHub Actions inputs based on mode."""
        # Parse mode (default to auto if not specified)
        mode_str = config.get("mode", "auto") or "auto"
        operation_mode = ModeHelper.parse_mode(mode_str)

        # Validate inputs based on mode
        check_tags_str = config.get("check_tags", "true") or "true"
        ModeValidator.validate_mode_inputs(
            operation_mode,
            config.get("tag"),
            config.get("path_prefix"),
            check_tags_str.lower() == "true"
        )

    def _print_startup_banner(self, config: dict[str, str | None]) -> None:
        """Print startup banner and configuration."""
        print("::group::Semantic Tag Increment Configuration")
        print("Semantic Tag Increment")
        print("=" * 50)
        print("Configuration:")
        print(f"   Mode: {config.get('mode', 'auto')}")
        print(f"   Tag: {config.get('tag', 'Not specified')}")
        print(f"   Increment: {config.get('increment', 'dev')}")
        if config.get("prerelease_type"):
            print(f"   Prerelease Type: {config['prerelease_type']}")
        print(f"   Path: {config.get('path_prefix', '.')}")
        print(f"   Check Tags: {config.get('check_tags', 'true')}")
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
        # Parse mode and create version source
        print("::group::Version Source")
        mode_str = config.get("mode", "auto") or "auto"
        operation_mode = ModeHelper.parse_mode(mode_str)
        path_prefix = config.get("path_prefix") or "."

        ModeHelper.log_mode_operation(operation_mode, config.get("tag"), path_prefix)

        # Create version source based on mode
        version_source = self._create_version_source(operation_mode, config.get("tag"), path_prefix)
        original_version = version_source.get_version()

        print(f"Version source: {version_source.get_source_description()}")
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
        should_check_tags = ModeHelper.should_check_git_tags(operation_mode, check_tags)

        print("::group::Git Operations")
        if should_check_tags:
            try:
                tag_start_time = time.time()
                existing_tags = GitOperations.get_existing_tags(path_prefix)
                tag_time = time.time() - tag_start_time

                print(f"Retrieved {len(existing_tags)} existing git tags")
                SemanticLogger.performance_metric("git_tag_retrieval", tag_time * 1000, "ms")

                incrementer = VersionIncrementer(existing_tags)
            except Exception as e:
                logger.warning(f"Error with git operations: {e}")
                print(f"Git operation failed: {e}")
                print("Proceeding without conflict checking")
                existing_tags = set()
                incrementer = VersionIncrementer(existing_tags)
        else:
            print("Tag checking disabled - proceeding without conflict checking")
            existing_tags = set()
            incrementer = VersionIncrementer(existing_tags)
        print("::endgroup::")

        # Perform increment
        print("::group::Version Increment")
        increment_start_time = time.time()
        incremented_version = incrementer.increment(
            original_version, increment_type, config.get("prerelease_type")
        )
        increment_time = time.time() - increment_start_time

        print(f"Incremented version successfully")
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

    def _create_version_source(self, mode: OperationMode, tag: str | None, path: str) -> VersionSource:
        """Create appropriate version source based on mode."""
        if mode == OperationMode.STRING:
            if not tag:
                raise ValueError("String mode requires a tag input")
            return VersionSourceFactory.create_string_source(tag)

        elif mode == OperationMode.PATH:
            # Extract version from project files
            extraction_result = self._extract_version_from_path(path)
            if not extraction_result:
                raise ValueError(f"No version found in project files at {path}")
            return VersionSourceFactory.create_extracted_source(extraction_result)

        elif mode == OperationMode.COMBINED:
            if not tag:
                raise ValueError("Combined mode requires a tag input")
            return VersionSourceFactory.create_string_source(tag)

        elif mode == OperationMode.AUTO:
            # Try extraction first, then fall back to string if provided
            extraction_result = self._extract_version_from_path(path)
            return VersionSourceFactory.create_auto_source(tag, extraction_result)

        else:
            raise ValueError(f"Unsupported mode: {mode}")

    def _extract_version_from_path(self, path: str) -> Optional[VersionExtractionResult]:
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
                print(f"Extracted version {result.version} from {result.source_file}")
            else:
                logger.debug(f"No valid version found in project files at {path}")

            return result

        except Exception as e:
            logger.debug(f"Version extraction failed for {path}: {e}")
            return None
