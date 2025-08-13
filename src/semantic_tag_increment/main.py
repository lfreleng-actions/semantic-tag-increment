# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Main entry point module.

This module provides the main entry point that intelligently routes execution
between CLI and GitHub Actions modes based on context detection.
"""

from .app_context import ContextDetector
from .cli_interface import app
from .github_actions import GitHubActionsRunner


def main() -> None:
    """
    Main entry point - handles both GitHub Actions and CLI usage.

    Uses context detection to determine the appropriate execution mode
    rather than relying on hardcoded command-line argument checks.
    """
    # Detect application context
    context = ContextDetector.detect_context()

    if context.is_cli_mode:
        # Running as CLI tool - use Typer interface
        app()
    else:
        # Running in GitHub Actions mode
        runner = GitHubActionsRunner(debug_mode=context.debug_mode)
        runner.run()


if __name__ == "__main__":
    main()
