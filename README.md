<!--
SPDX-License-Identifier: Apache-2.0
SPDX-FileCopyrightText: 2025 The Linux Foundation
-->

# Semantic Tag Increment

[![Build/Test Workflow](https://github.com/lfreleng-actions/semantic-tag-increment/actions/workflows/build-test.yaml/badge.svg)](https://github.com/lfreleng-actions/semantic-tag-increment/actions/workflows/build-test.yaml)
[![Release Workflow](https://github.com/lfreleng-actions/semantic-tag-increment/actions/workflows/build-test-release.yaml/badge.svg)](https://github.com/lfreleng-actions/semantic-tag-increment/actions/workflows/build-test-release.yaml)
[![CodeQL](https://github.com/lfreleng-actions/semantic-tag-increment/actions/workflows/codeql.yml/badge.svg)](https://github.com/lfreleng-actions/semantic-tag-increment/actions/workflows/codeql.yml)

A Python tool for intelligently incrementing semantic version tags with GitHub
Actions support. This tool provides comprehensive semantic versioning capabilities
including complex pre-release pattern handling, automatic project type detection,
and conflict resolution across 35+ programming languages and ecosystems.

## Features

- **Four Operation Modes**: Choose from string, path, combined, or auto mode
  for different workflows
- **Automatic Project Detection**: Supports 50+ project types across 35+ ecosystems
  including Python, JavaScript, Java, C#, Go, Rust, Ruby, PHP, Swift, and more
- **Comprehensive Semantic Version Support**: Handles all valid semantic version
  patterns including complex pre-release identifiers and build metadata
- **Intelligent Pre-release Incrementing**: Smart detection and incrementing of
  numeric components in pre-release versions
- **Conflict Resolution**: Automatic detection of existing git tags to avoid
  version conflicts
- **User-Extensible Configuration**: Add custom project types and version patterns
- **Dual Interfaces**: Both CLI tool and GitHub Actions composite action
- **Extensive Validation**: Strict semantic version validation following the
  semver.org specification
- **Performance Optimized**: Lightweight design for fast CI/CD execution

## Supported Version Patterns

The tool supports all semantic version patterns from the
[official specification](https://semver.org/), including complex examples:

- Basic versions: `1.2.3`, `10.20.30`
- Pre-release versions: `1.0.0-alpha`, `1.0.0-alpha.1`, `1.0.0-beta.2`
- Build metadata: `1.0.0+build.123`, `1.0.0-alpha.1+build.456`
- Complex patterns: `1.2.3----RC-SNAPSHOT.12.9.1--.12+788`
- Version prefixes: `v1.2.3`, `V2.0.0`
- Large numbers: `99999999999999999999999.999999999999999999.99999999999999999`

## Installation

### From PyPI (when published)

```bash
pip install semantic-tag-increment
```

### From Source

```bash
git clone https://github.com/lfreleng-actions/semantic-tag-increment.git
cd semantic-tag-increment
pip install .
```

### Development Installation

```bash
git clone https://github.com/lfreleng-actions/semantic-tag-increment.git
cd semantic-tag-increment
make dev-setup
```

## Usage

### Command Line Interface

The tool provides a comprehensive CLI interface with four operation modes:

#### Operation Modes

The tool supports four operation modes to handle different workflows:

1. **String Mode** (`--mode string`): Standalone tag incrementing based purely
on input string
2. **Path Mode** (`--mode path`): Auto-detect project type and extract version
from project files
3. **Combined Mode** (`--mode combined`): Use explicit tag with repository
context for conflict checking
4. **Auto Mode** (`--mode auto`, default): Fully automatic operation using
heuristics

#### Mode Examples

```bash
# String mode - explicit tag input
semantic-tag-increment increment --tag "v1.2.3" --increment "patch" --mode "string"

# Path mode - auto-detect version from project files
semantic-tag-increment increment --increment "minor" --mode "path"
semantic-tag-increment increment --increment "minor" --mode "path" --path "/path/to/project"

# Combined mode - explicit tag with repository context
semantic-tag-increment increment --tag "1.0.0" --increment "major" --mode "combined"

# Auto mode (default) - intelligent automatic operation
semantic-tag-increment increment --increment "prerelease"
semantic-tag-increment increment --tag "1.2.3" --increment "patch"  # tag takes precedence
```

#### Traditional Usage (Auto Mode)

```bash
# Basic increment operations (auto mode is default)
semantic-tag-increment increment --tag "v1.2.3" --increment "patch"
semantic-tag-increment increment --tag "1.2.3" --increment "minor"
semantic-tag-increment increment --tag "v1.2.3" --increment "major"

# Working with a specific project directory
semantic-tag-increment increment --tag "v1.2.3" --increment "patch" --path "my-project"

# Pre-release increments
semantic-tag-increment increment --tag "1.2.3" --increment "prerelease"
semantic-tag-increment increment --tag "1.2.3" --increment "prerelease" \
  --prerelease-type "alpha"

# Increment existing pre-release
semantic-tag-increment increment --tag "1.2.3-alpha.1" --increment "prerelease"
```

#### Project Type Detection

The tool automatically detects project types and extracts versions from:

**Python Projects:**

- `pyproject.toml` (PEP 518)
- `setup.py`, `setup.cfg`
- `__init__.py`, `version.py`

**JavaScript/Node.js Projects:**

- `package.json`
- `bower.json`

**Java Projects:**

- `pom.xml` (Maven)
- `build.gradle`, `build.gradle.kts` (Gradle)

**C#/.NET Projects:**

- `*.csproj`
- `global.json`

**Go Projects:**

- `go.mod`
- `version.go`

**Rust Projects:**

- `Cargo.toml`

**And 40+ more project types!**

See the [Project Support](#project-support) section for the complete list.

#### Understanding Increment Types

The tool supports these increment types with key behaviors:

- **major**: Increments the major version (X.0.0) and resets minor and patch to 0
- **minor**: Increments the minor version (X.Y.0) and resets patch to 0
- **patch**: Increments the patch version (X.Y.Z)
- **prerelease**: Creates or increments a pre-release version
  - Requires `--prerelease-type` parameter to specify identifier (alpha, beta, rc)
  - When applied to a non-prerelease version, increments patch and adds prerelease
  - When applied to an existing prerelease, increments the rightmost numeric component
- **dev**: Alias for prerelease with "dev" as the default prerelease type
  - Same as using `--increment "prerelease" --prerelease-type "dev"`
  - This is the default increment type if not specified

Example of the difference between dev and prerelease:

```bash
# These two commands produce identical results:
semantic-tag-increment increment --tag "1.2.3" --increment "dev"
semantic-tag-increment increment --tag "1.2.3" --increment "prerelease" \
  --prerelease-type "dev"
# Output: 1.2.4-dev.1
```

#### Version Validation

```bash
# Check semantic versions
semantic-tag-increment validate --tag "1.2.3"
semantic-tag-increment validate --tag "v1.2.3-alpha.1+build.123"
semantic-tag-increment validate --tag \
  "1.2.3-RC-SNAPSHOT.9.1-alpha"
```

#### Get Version Suggestions

```bash
# Get increment suggestions
semantic-tag-increment suggest --tag "1.2.3" --increment "prerelease"
```

#### CLI Options

The `increment` command supports these options:

<!-- markdownlint-disable MD013 -->

| Option | Description | Default |
|--------|-------------|---------|
| `--tag`, `-t` | The existing semantic tag to increment (optional in some modes) | |
| `--increment`, `-i` | Increment type: `major`, `minor`, `patch`, `prerelease`, `dev` | `dev` |
| `--prerelease-type`, `-p` | Prerelease identifier (e.g., `alpha`, `beta`, `rc`) | |
| `--mode`, `-m` | Operation mode: `string`, `path`, `combined`, `auto` | `auto` |
| `--check-conflicts/--no-check-conflicts` | Check for conflicts with existing git tags | `true` |
| `--path` | Directory location containing project code | `.` |
| `--output-format`, `-f` | Output format: `full`, `numeric`, `both` | `full` |

<!-- markdownlint-enable MD013 -->

### GitHub Actions

Use as a composite action in your workflows with four operation modes:

#### Basic Usage (Auto Mode)

```yaml
name: Version Increment Example
on: [push]

jobs:
  increment-version:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Increment version
        id: version
        uses: lfreleng-actions/semantic-tag-increment@main
        with:
          tag: "v1.2.3"
          increment: "patch"

      - name: Use incremented version
        run: |
          echo "New version: ${{ steps.version.outputs.tag }}"
          echo "Numeric version: ${{ steps.version.outputs.numeric_tag }}"
```

#### Mode-Specific Examples

```yaml
# String mode - explicit tag input
- name: Increment version (string mode)
  uses: lfreleng-actions/semantic-tag-increment@main
  with:
    mode: "string"
    tag: "v1.2.3"
    increment: "patch"

# Path mode - auto-detect version from project files
- name: Increment version (path mode)
  uses: lfreleng-actions/semantic-tag-increment@main
  with:
    mode: "path"
    increment: "minor"
    path_prefix: "my-project"

# Combined mode - explicit tag with repository context
- name: Increment version (combined mode)
  uses: lfreleng-actions/semantic-tag-increment@main
  with:
    mode: "combined"
    tag: "1.0.0"
    increment: "major"
    check_tags: true

# Auto mode - intelligent automatic operation
- name: Increment version (auto mode)
  uses: lfreleng-actions/semantic-tag-increment@main
  with:
    mode: "auto"
    increment: "prerelease"
    prerelease_type: "alpha"
```

#### Action Inputs

<!-- markdownlint-disable MD013 -->

| Input             | Description                                           | Required | Default |
|-------------------|-------------------------------------------------------|----------|---------|
| `mode`            | Operation mode: `string`, `path`, `combined`, `auto` | No       | `auto`  |
| `tag`             | The existing semantic tag to increment (optional in some modes) | No | |
| `increment`       | Types: `major`, `minor`, `patch`, `prerelease`, `dev` | No       | `dev`   |
| `prerelease_type` | Prerelease identifier (e.g., `alpha`, `beta`)         | No       |         |
| `path_prefix`     | Directory location containing project code            | No       | `.`     |
| `check_tags`      | Whether to fetch and check against repository tags    | No       | `true`  |

<!-- markdownlint-enable MD013 -->

#### Action Outputs

<!-- markdownlint-disable MD013 -->

| Output | Description |
|--------|-------------|
| `tag` | The incremented tag string with any original prefix |
| `numeric_tag` | Numeric tag stripped of any v/V prefix |

<!-- markdownlint-enable MD013 -->

## Project Support

The tool supports **50+ project types** across **35+ ecosystems**:

### Top Priority (Most Common)

- **Python**: `pyproject.toml`, `setup.py`, `setup.cfg`, `__init__.py`, `version.py`
- **JavaScript/Node.js**: `package.json`, `bower.json`, `component.json`
- **Java**: `pom.xml`, `build.gradle`, `build.gradle.kts`, `gradle.properties`
- **C#/.NET**: `*.csproj`, `global.json`, `Directory.Build.props`
- **Go**: `go.mod`, `version.go`
- **Rust**: `Cargo.toml`

### Other Ecosystems

- **Ruby**: `Gemfile`, `*.gemspec`, `version.rb`
- **PHP**: `composer.json`
- **Swift/iOS**: `Package.swift`, `*.podspec`, `Info.plist`
- **C/C++**: `CMakeLists.txt`, `conanfile.txt`, `conanfile.py`, `vcpkg.json`
- **Dart/Flutter**: `pubspec.yaml`
- **Scala**: `build.sbt`
- **Clojure**: `project.clj`, `deps.edn`
- **Haskell**: `*.cabal`, `package.yaml`
- **Elixir**: `mix.exs`
- **Erlang**: `rebar.config`
- **Lua**: `*.rockspec`
- **R**: `DESCRIPTION`
- **Perl**: `META.json`, `META.yml`
- **Kubernetes/Helm**: `Chart.yaml`
- **Docker**: `Dockerfile`
- **Web Frontend**: `angular.json`

### Generic/Universal Files

- `VERSION`, `version.txt`, `version.json`, `version.yaml`
- `manifest.json`, `app.json`

### User-Extensible Configuration

Users can add custom project mappings in `~/.config/semantic_tag_increment/project_mappings.yaml`:

```yaml
project_mappings:
  - name: "Custom - my-project.json"
    priority: 1
    patterns: ["my-project.json"]
    regex: ['"version":\s*"([^"]+)"']
    description: "Custom project file"
```

## Implementation Details

### Architecture

The tool has a modular architecture consisting of:

- **Parser Module** (`parser.py`): Comprehensive semantic version parsing and
  validation
- **Incrementer Module** (`incrementer.py`): Intelligent version incrementing logic
- **Modes Module** (`modes.py`): Operation mode handling and validation
- **Project Detection** (`project_detector.py`): Automatic project type detection
- **Version Extraction** (`version_extractor.py`): Regex-based version extraction
- **Configuration Management** (`config.py`): User-extensible configuration
- **CLI Module** (`cli_interface.py`): Typer-based command-line interface
- **GitHub Actions Integration** (`github_actions.py`): Composite action support

### Smart Pre-release Handling

The tool uses intelligent heuristics to handle complex pre-release patterns:

1. **Numeric Component Detection**: Identifies numeric components in pre-release
   identifiers
2. **Rightmost Increment**: Increments the rightmost numeric component found
3. **Conflict Resolution**: Automatically finds next available version when
   conflicts exist
4. **Pattern Preservation**: Maintains the structure of complex pre-release patterns

### Version Comparison

Follows semantic versioning precedence rules:

- Core version comparison (major.minor.patch)
- Pre-release versions have lower precedence than normal versions
- Numeric identifiers undergo numerical comparison
- Alphanumeric identifiers undergo lexical comparison
- Precedence comparison excludes build metadata

## Development

### Setting Up Development Environment

```bash
# Clone repository
git clone https://github.com/lfreleng-actions/semantic-tag-increment.git
cd semantic-tag-increment

# Set up development environment
make dev-setup

# Run tests
make test

# Run linting
make lint

# Run all checks
make all
```

### Testing

The project includes comprehensive test coverage:

```bash
# Run unit tests
make test-unit

# Run integration tests
make test-integration

# Run property-based tests
make test-property

# Generate coverage report
make coverage-html
```

### Code Quality

Code quality tools include:

- **ruff**: Python linting and code formatting (replacing Black, isort, and flake8)
- **mypy**: Type checking
- **markdownlint**: Markdown linting
- **yamllint**: YAML linting
- **shellcheck**: Shell script linting
- **actionlint**: GitHub Actions workflow linting
- **codespell**: Documentation spell checking
- **reuse-tool**: License checking
- **pre-commit**: Automated quality checks

### Performance

The tool delivers CI/CD performance through:

- Pure Python implementation using GitPython for git operations
- Efficient regex-based parsing
- Minimal memory footprint
- Fast execution (typically <1 second for most operations)

## Examples

### Real-world Release Workflow

```bash
# Current version: v1.2.3
# Create development version
semantic-tag-increment increment --tag "v1.2.3" --increment "prerelease" \
  --prerelease-type "dev"
# Output: v1.2.4-dev.1

# Move to alpha
semantic-tag-increment increment --tag "v1.2.4-dev.5" --increment "prerelease" \
  --prerelease-type "alpha"
# Output: v1.2.4-alpha.1

# Increment alpha
semantic-tag-increment increment --tag "v1.2.4-alpha.1" --increment "prerelease"
# Output: v1.2.4-alpha.2

# Move to beta
semantic-tag-increment increment \
  --tag "v1.2.4-alpha.2" \
  --increment "pre" \
  --pre-type "beta"
# Output: v1.2.4-beta.1

# Release candidate
semantic-tag-increment increment \
  --tag "v1.2.4-beta.1" \
  --increment "pre" \
  --pre-type "rc"
# Output: v1.2.4-rc.1

# Final release
semantic-tag-increment increment --tag "v1.2.4-rc.1" --increment "patch"
# Output: v1.2.4
```

### Complex Pre-release Patterns

```bash
# Handle complex existing patterns
semantic-tag-increment increment --tag "1.2.3----RC-SNAPSHOT.12.9.1--.12+788" \
  --increment "prerelease"
# Intelligently increments the rightmost numeric component

# Check unusual but valid patterns
semantic-tag-increment check --tag "1.0.0-0A.is.legal"
# Output: ✅ Valid semantic version
```

## GitHub Actions Integration

### Complete CI/CD Example

```yaml
name: Release Workflow
on:
  push:
    branches: [main]

jobs:
  version-and-release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Get latest tag
        id: latest-tag
        run: |
          latest=$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.0.0")
          echo "tag=$latest" >> $GITHUB_OUTPUT

      - name: Increment version for development
        id: dev-version
        uses: lfreleng-actions/semantic-tag-increment@main
        with:
          mode: "auto"
          tag: ${{ steps.latest-tag.outputs.tag }}
          increment: "prerelease"
          prerelease_type: "dev"

      - name: Create development tag
        run: |
          git tag ${{ steps.dev-version.outputs.tag }}
          git push origin ${{ steps.dev-version.outputs.tag }}
```

### Auto-Detection Workflow

```yaml
name: Auto-Detection Example
on:
  push:
    branches: [main]

jobs:
  auto-increment:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      # Auto-detect project type and extract version
      - name: Auto-increment version
        id: version
        uses: lfreleng-actions/semantic-tag-increment@main
        with:
          mode: "path"
          increment: "patch"

      - name: Use detected version
        run: |
          echo "Auto-detected and incremented: ${{ steps.version.outputs.tag }}"
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes following the coding standards
4. Ensure all tests pass and coverage remains above 80%
5. Submit a pull request

### Code Standards

- Follow PEP 8 with 80-character line limit
- Include comprehensive docstrings
- Add unit tests for new functionality
- Maintain type hints for all functions
- Update documentation for user-facing changes

## License

This project uses the Apache License 2.0. See the [LICENSE](LICENSE)
file for details.

## Acknowledgments

- Inspired by [python-semantic-release](https://github.com/python-semantic-release/python-semantic-release)
- Semantic versioning specification: [semver.org](https://semver.org/)
- Regular expression patterns validated using [RegEx101](https://regex101.com/)

## Support

For questions, issues, or contributions:

- [GitHub Issues](https://github.com/lfreleng-actions/semantic-tag-increment/issues)
