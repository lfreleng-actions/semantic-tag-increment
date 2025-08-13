# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Semantic Tag Increment - A Python tool for incrementing semantic version tags.

This package provides both a CLI tool (using Typer) and a GitHub Action interface
for incrementing semantic version tags following the semantic versioning specification.
It supports complex pre-release and metadata patterns beyond basic major.minor.patch.

## CLI Usage Examples

Basic version incrementing:
    $ semantic-tag-increment increment --tag "v1.2.3" --increment "patch"
    v1.2.4

    $ semantic-tag-increment increment --tag "1.0.0" --increment "minor"
    1.1.0

    $ semantic-tag-increment increment --tag "2.1.0" --increment "major"
    3.0.0

Pre-release incrementing:
    $ semantic-tag-increment increment --tag "v1.2.3" --increment "prerelease"
    v1.2.4-dev.1

    $ semantic-tag-increment increment --tag "1.0.0" --increment "prerelease" --prerelease-type "alpha"
    1.0.1-alpha.1

    $ semantic-tag-increment increment --tag "1.0.0-alpha.1" --increment "prerelease"
    1.0.0-alpha.2

Version validation:
    $ semantic-tag-increment validate --tag "v1.2.3-alpha.1+build.123"
    ✅ Valid semantic version: v1.2.3-alpha.1+build.123

Version suggestions:
    $ semantic-tag-increment suggest --tag "v1.2.3" --increment "prerelease"
    Suggestions for prerelease increment of v1.2.3:
      1. v1.2.4-dev.1
      2. v1.2.4-alpha.1
      3. v1.2.4-beta.1

## Python API Usage Examples

Basic usage:
    >>> from semantic_tag_increment import SemanticVersion, VersionIncrementer
    >>> from semantic_tag_increment.incrementer import IncrementType

    >>> # Parse a version
    >>> version = SemanticVersion.parse("v1.2.3")
    >>> print(version.major, version.minor, version.patch)
    1 2 3

    >>> # Increment versions
    >>> incrementer = VersionIncrementer()
    >>> next_version = incrementer.increment(version, IncrementType.PATCH)
    >>> print(next_version)
    v1.2.4

Advanced usage with conflict detection:
    >>> # With existing tags to avoid conflicts
    >>> existing_tags = {"v1.2.3", "v1.2.4", "v1.2.5-dev.1"}
    >>> incrementer = VersionIncrementer(existing_tags)
    >>> next_version = incrementer.increment(version, IncrementType.PATCH)
    >>> print(next_version)  # Will find next available version
    v1.2.5

Pre-release handling:
    >>> # Create pre-release versions
    >>> prerelease = incrementer.increment(
    ...     version, IncrementType.PRERELEASE, "alpha"
    ... )
    >>> print(prerelease)
    v1.2.4-alpha.1

    >>> # Increment existing pre-release
    >>> alpha_version = SemanticVersion.parse("v1.0.0-alpha.1")
    >>> next_alpha = incrementer.increment(alpha_version, IncrementType.PRERELEASE)
    >>> print(next_alpha)
    v1.0.0-alpha.2

## GitHub Actions Usage

Basic workflow step:
    - name: Increment version
      id: increment
      uses: lfreleng-actions/semantic-tag-increment@v1
      with:
        tag: ${{ steps.get_version.outputs.version }}
        increment: 'patch'

    - name: Use incremented version
      run: echo "New version: ${{ steps.increment.outputs.tag }}"

Advanced workflow with pre-release:
    - name: Increment pre-release
      id: increment
      uses: lfreleng-actions/semantic-tag-increment@v1
      with:
        tag: 'v1.2.3'
        increment: 'prerelease'
        prerelease_type: 'rc'

    - name: Create release
      run: |
        echo "Full version: ${{ steps.increment.outputs.tag }}"
        echo "Numeric version: ${{ steps.increment.outputs.numeric_tag }}"

## Supported Version Patterns

The tool supports all valid semantic version patterns including:
- Basic versions: 1.2.3, v1.2.3, V1.2.3
- Pre-release versions: 1.2.3-alpha.1, 1.2.3-beta.2, 1.2.3-rc.1
- Complex pre-release: 1.2.3-alpha.1.2, 1.2.3-dev.20231201
- Build metadata: 1.2.3+build.123, 1.2.3-alpha.1+build.456
- Edge cases: 1.2.3----RC-SNAPSHOT.12.9.1--.12+788

## Features

- ✅ Full semantic versioning specification compliance
- ✅ Intelligent pre-release increment detection
- ✅ Conflict detection with existing git tags
- ✅ Multiple output formats (full, numeric, both)
- ✅ GitHub Actions integration
- ✅ Comprehensive CLI interface
- ✅ Python API for programmatic use
- ✅ Extensive test coverage
- ✅ Type hints and mypy support
"""

__version__ = "1.0.0"

from .cli import main
from .cli_interface import app
from .incrementer import VersionIncrementer
from .parser import SemanticVersion
from .exceptions import (
    SemanticVersionError,
    ValidationError,
    ParseError,
    IncrementError,
    GitOperationError,
    ConfigurationError,
    SecurityError,
    handle_cli_errors,
    handle_github_actions_errors,
    ErrorReporter,
)

__all__ = [
    "SemanticVersion",
    "VersionIncrementer",
    "app",
    "main",
    "__version__",
    # Exception classes
    "SemanticVersionError",
    "ValidationError",
    "ParseError",
    "IncrementError",
    "GitOperationError",
    "ConfigurationError",
    "SecurityError",
    # Error handling utilities
    "handle_cli_errors",
    "handle_github_actions_errors",
    "ErrorReporter",
]
