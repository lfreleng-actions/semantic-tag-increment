<!--
SPDX-License-Identifier: Apache-2.0
SPDX-FileCopyrightText: 2025 The Linux Foundation
-->

# Semantic Tag Increment

A simple, focused tool for incrementing semantic version tags. This tool takes
an explicit semantic version tag as input and increments it according to
semantic versioning rules.

## semantic-tag-increment

## Features

- **String-based tag incrementing**: Provide a semantic version tag and
increment type
- **Semantic versioning compliant**: Follows [SemVer](https://semver.org/)
specification
- **Complex pre-release support**: Handles multiple pre-release identifiers
- **GitHub Actions integration**: Easy to use in CI/CD workflows
- **Conflict detection**: Optional checking against existing Git tags
- **Flexible output formats**: Full version with prefix or numeric output

## Supported Version Patterns

The tool supports standard semantic versioning patterns:

- **Basic versions**: `1.0.0`, `v2.1.3`
- **Pre-release versions**: `1.0.0-alpha.1`, `v2.1.0-beta.2`, `1.5.0-rc.1`
- **Development versions**: `1.0.0-dev.1`, `v1.2.3-dev.5`
- **Custom pre-release types**: `1.0.0-snapshot.1`, `v1.0.0-nightly.1`
- **Build metadata**: `1.0.0+20230101` (configurable preservation)
- **Mixed case prefixes**: `V1.0.0`, `v1.0.0`

## Installation

### From PyPI (when published)

```bash
pip install semantic-tag-increment
```

### From Source

```bash
git clone https://github.com/your-org/semantic-tag-increment.git
cd semantic-tag-increment
pip install .
```

### Development Installation

```bash
git clone https://github.com/your-org/semantic-tag-increment.git
cd semantic-tag-increment
pip install -e .
```

## Usage

### Command Line Interface

The tool provides a simple command-line interface for incrementing version
tags:

```bash
# Increment patch version
semantic-tag-increment --tag "v1.2.3" --increment "patch"
# Output: v1.2.4

# Increment minor version
semantic-tag-increment --tag "v1.2.3" --increment "minor"
# Output: v1.3.0

# Increment major version
semantic-tag-increment --tag "v1.2.3" --increment "major"
# Output: v2.0.0

# Add pre-release version
semantic-tag-increment --tag "v1.2.3" --increment "prerelease"
# Output: v1.2.4-dev.1

# Increment with custom pre-release type
semantic-tag-increment --tag "v1.2.3" --increment "prerelease" \
  --prerelease-type "alpha"
# Output: v1.2.4-alpha.1

# Preserve build metadata during increment
semantic-tag-increment --tag "v1.2.3+build.123" --increment "patch" \
  --preserve-metadata
# Output: v1.2.4+build.123

# Strip build metadata (default behavior)
semantic-tag-increment --tag "v1.2.3+build.123" --increment "patch"
# Output: v1.2.4
```

#### Understanding Increment Types

- **patch**: Increments the patch version (1.2.3 → 1.2.4)
- **minor**: Increments the minor version and resets patch (1.2.3 → 1.3.0)
- **major**: Increments the major version and resets minor/patch (1.2.3 → 2.0.0)
- **prerelease/dev**: Adds or increments pre-release version (1.2.3 → 1.2.4-dev.1)

#### Validation Mode

Use the `--validate` flag to check if a tag is a valid semantic version without incrementing:

```bash
# Validate basic version
semantic-tag-increment --tag "v1.2.3" --validate

# Validate complex version with prerelease and metadata
semantic-tag-increment --tag "v1.2.3-alpha.1+build.123" --validate
```

#### Version Validation

```bash
# Validate a semantic version
semantic-tag-increment --tag "v1.2.3-alpha.1" --validate
```

#### Get Version Suggestions

Use the `--suggest` flag to see multiple possible next versions:

```bash
# Get suggestions for prerelease versions (default when using --suggest)
semantic-tag-increment --tag "v1.2.3" --suggest

# Get suggestions for specific increment type
semantic-tag-increment --tag "v1.2.3" --increment "prerelease" --suggest

# See suggestions for other increment types
semantic-tag-increment --tag "v1.2.3" --increment "patch" --suggest
```

#### CLI Options

- `--tag, -t`: The existing semantic tag to increment (required)
- `--increment, -i`: Increment type: major, minor, patch, prerelease, dev
  (defaults: dev for increment, prerelease for --suggest, not required with --validate)
- `--prerelease-type, -p`: Custom prerelease identifier (alpha, beta, rc, etc.)
- `--preserve-metadata/--no-preserve-metadata`: Preserve or strip build metadata
  during increments (default: strip)
- `--validate`: Validate the semantic version tag format without incrementing
- `--suggest`: Show multiple possible next versions for the given increment type
- `--check-conflicts/--no-check-conflicts`: Enable/disable Git tag conflict
  checking
- `--output-format, -f`: Output format: full, numeric, both (default: full)
- `--path`: Directory for Git operations (default: current directory)
- `--debug`: Enable debug logging

### GitHub Actions

#### Basic Usage

```yaml
name: Increment Version
on:
  push:
    branches: [main]

jobs:
  increment-version:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Increment patch version
        id: increment
        uses: your-org/semantic-tag-increment@v1
        with:
          tag: 'v1.2.3'
          increment: 'patch'

      - name: Use new version
        run: |
          echo "New version: ${{ steps.increment.outputs.tag }}"
          echo "Numeric: ${{ steps.increment.outputs.numeric_tag }}"
```

#### Advanced Examples

```yaml
# Increment with pre-release type
- name: Create alpha release
  uses: your-org/semantic-tag-increment@v1
  with:
    tag: 'v1.2.3'
    increment: 'prerelease'
    prerelease_type: 'alpha'

# Increment with conflict checking disabled
- name: Fast increment
  uses: your-org/semantic-tag-increment@v1
  with:
    tag: 'v1.2.3'
    increment: 'minor'
    check_tags: 'false'

# Increment in a subdirectory
- name: Increment with custom path
  uses: your-org/semantic-tag-increment@v1
  with:
    tag: 'v1.2.3'
    increment: 'patch'
    path: './project-subdirectory'

# Preserve build metadata during increment
- name: Increment preserving metadata
  uses: your-org/semantic-tag-increment@v1
  with:
    tag: 'v1.2.3+build.123'
    increment: 'patch'
    preserve_metadata: 'true'
    # Output: v1.2.4+build.123
```

#### Action Inputs

<!-- markdownlint-disable MD013 -->

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `tag` | The existing semantic tag for incrementing | Yes | - |
| `increment` | Increment type: major, minor, patch, prerelease, dev | No | `dev` |
| `prerelease_type` | Prerelease type (alpha, beta, rc, etc.) | No | - |
| `path` | Directory location for git operations | No | `.` |
| `debug` | Enable verbose debug output | No | `false` |
| `check_tags` | Check against existing repository tags | No | `true` |
| `preserve_metadata` | Preserve build metadata during increments | No | `false` |

<!-- markdownlint-enable MD013 -->

#### Action Outputs

<!-- markdownlint-disable MD013 -->

| Output | Description |
|--------|-------------|
| `tag` | The incremented tag string with any original prefix |
| `numeric_tag` | Numeric tag stripped of any v/V prefix |

<!-- markdownlint-enable MD013 -->

## Implementation Details

### Architecture

The tool uses a modular architecture:

- **Parser**: Robust semantic version parsing with prefix preservation
- **Incrementer**: Core increment logic with conflict resolution
- **Git Operations**: Optional integration with Git for tag conflict checking
- **CLI Interface**: Clean command-line interface using Typer
- **GitHub Actions**: Native GitHub Actions integration

### Smart Pre-release Handling

The tool intelligently handles pre-release versions:

- Automatically detects existing pre-release components
- Increments numeric components when present
- Preserves custom pre-release identifiers
- Supports complex pre-release patterns like `1.0.0-alpha.1.beta.2`

### Build Metadata Handling

The tool provides configurable handling of build metadata:

- **Default behavior**: Build metadata gets stripped during increments
  - `v1.2.3+build.123` → `v1.2.4` (when incrementing patch)
- **Preserve metadata**: Use `--preserve-metadata` flag to maintain build metadata
  - `v1.2.3+build.123` → `v1.2.4+build.123` (when incrementing patch with preservation)
- **Semantic versioning compliance**: Build metadata doesn't affect version precedence
- **CI/CD flexibility**: Choose behavior based on your workflow needs

#### Why Strip Metadata by Default?

Build metadata is typically specific to a particular build and becomes outdated
when the version gets incremented. The default behavior of stripping metadata
follows common practices where:

- New versions get fresh build metadata from the current build
- Outdated build information doesn't carry forward
- Clean version increments without stale metadata

#### When to Preserve Metadata?

Preserve metadata when:

- The metadata contains persistent information (not build-specific)
- Your workflow requires maintaining certain metadata across increments
- You have custom metadata that should persist through version changes

### Version Comparison

With conflict checking enabled, the tool:

- Fetches existing Git tags from the repository
- Compares semantic versions semantically (not lexicographically)
- Finds the next available version to avoid conflicts
- Respects semantic versioning precedence rules

## Development

### Setting Up Development Environment

```bash
# Clone the repository
git clone https://github.com/your-org/semantic-tag-increment.git
cd semantic-tag-increment

# Install in development mode
pip install -e .

# Install development dependencies
pip install -e ".[dev]"

# Set up pre-commit hooks
pre-commit install
```

### Testing

```bash
# Run unit tests
pytest

# Run with coverage
pytest --cov=semantic_tag_increment

# Run integration tests
pytest tests/test_integration.py

# Run performance tests
pytest tests/test_performance_optimizations.py
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Type checking
mypy src/

# Security checks
bandit -r src/
```

### Performance

The tool optimizes for performance:

- Efficient regex-based version parsing
- Minimal Git operations with conflict checking enabled
- Lazy loading of dependencies
- Optimized for CI/CD environments

## Examples

### Real-world Release Workflow

```yaml
name: Release Workflow
on:
  push:
    branches: [main]

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Get current version
        id: current
        run: |
          CURRENT_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.0.0")
          echo "tag=$CURRENT_TAG" >> $GITHUB_OUTPUT

      - name: Increment version
        id: increment
        uses: your-org/semantic-tag-increment@v1
        with:
          tag: ${{ steps.current.outputs.tag }}
          increment: 'patch'

      - name: Create and push tag
        run: |
          git tag ${{ steps.increment.outputs.tag }}
          git push origin ${{ steps.increment.outputs.tag }}

      - name: Create GitHub release
        uses: actions/create-release@v1
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          tag_name: ${{ steps.increment.outputs.tag }}
          release_name: Release ${{ steps.increment.outputs.tag }}
```

### Complex Pre-release Patterns

```bash
# Start with a base version
semantic-tag-increment --tag "v1.0.0" --increment "prerelease" \
  --prerelease-type "alpha"
# Output: v1.0.1-alpha.1

# Increment the alpha
semantic-tag-increment --tag "v1.0.1-alpha.1" --increment "prerelease"
# Output: v1.0.1-alpha.2

# Move to beta
semantic-tag-increment --tag "v1.0.1-alpha.2" \
  --increment "prerelease" --prerelease-type "beta"
# Output: v1.0.1-beta.1

# Move to release candidate
semantic-tag-increment --tag "v1.0.1-beta.1" \
  --increment "prerelease" --prerelease-type "rc"
# Output: v1.0.1-rc.1

# Final release
semantic-tag-increment --tag "v1.0.1-rc.1" --increment "patch"
# Output: v1.0.1
```

## Contributing

We welcome contributions! See our [Contributing Guide](CONTRIBUTING.md) for details.

### Code Standards

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style
- Use type hints for all public APIs
- Write comprehensive tests for new features
- Update documentation for user-facing changes

## License

This project uses the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Semantic Versioning](https://semver.org/) specification
- Python packaging community for best practices

## Support

- **Issues**: [GitHub Issues](https://github.com/your-org/semantic-tag-increment/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/semantic-tag-increment/discussions)
- **Documentation**: This README and inline code documentation
