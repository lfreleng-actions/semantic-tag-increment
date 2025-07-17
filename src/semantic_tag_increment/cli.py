# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
CLI interface for semantic tag incrementing.

This module provides the command-line interface using Typer for both standalone
CLI usage and GitHub Actions integration.
"""

# Import the new main entry point
from .main import main
from .github_actions import GitHubActionsRunner
from .app_context import ContextDetector
from .cli_interface import app


def run_github_action() -> None:
    """
    Run in GitHub Actions mode.

    This function provides backwards compatibility for tests while using
    the new refactored GitHub Actions runner.
    """
    context = ContextDetector.detect_context()
    runner = GitHubActionsRunner(debug_mode=context.debug_mode)
    runner.run()


# Re-export for backwards compatibility
__all__ = ["main", "run_github_action", "app"]
