# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Project mappings database module.

This module defines the comprehensive database of project types and their
version extraction patterns, organized by priority and ecosystem.
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ProjectMapping:
    """
    Represents a single project type mapping with file patterns and regex.

    Contains all information needed to detect a project type and extract
    version information from its files.
    """
    name: str
    priority: int
    patterns: List[str]
    regex: List[str]
    description: str
    file_encoding: str = "utf-8"
    case_sensitive: bool = False
    multiline: bool = True
    max_file_size: int = 1024 * 1024  # 1MB default limit

    def __post_init__(self) -> None:
        """Validate the mapping after initialization."""
        if not self.name:
            raise ValueError("Project mapping name cannot be empty")
        if not self.patterns:
            raise ValueError("Project mapping must have at least one file pattern")
        if not self.regex:
            raise ValueError("Project mapping must have at least one regex pattern")
        if self.priority < 0:
            raise ValueError("Project mapping priority must be non-negative")


class ProjectMappingDatabase:
    """
    Manages the ordered list of project mappings for version extraction.

    Provides methods to access, search, and manage project type mappings
    with proper priority ordering and caching.
    """

    # Comprehensive project mappings database
    DEFAULT_MAPPINGS: List[Dict] = [

        # ==== PYTHON ECOSYSTEM ====
        {
            "name": "Python - pyproject.toml (PEP 518)",
            "priority": 1,
            "patterns": ["pyproject.toml"],
            "regex": [
                r'version\s*=\s*["\']([^"\']+)["\']',
                r'version\s*=\s*{[^}]*version\s*=\s*["\']([^"\']+)["\']'
            ],
            "description": "Modern Python packaging standard"
        },
        {
            "name": "Python - setup.py",
            "priority": 2,
            "patterns": ["setup.py"],
            "regex": [
                r'version\s*=\s*["\']([^"\']+)["\']',
                r'__version__\s*=\s*["\']([^"\']+)["\']',
                r'VERSION\s*=\s*["\']([^"\']+)["\']'
            ],
            "description": "Traditional Python packaging"
        },
        {
            "name": "Python - setup.cfg",
            "priority": 3,
            "patterns": ["setup.cfg"],
            "regex": [
                r'version\s*=\s*([^\s]+)',
                r'version\s*=\s*attr:\s*([^.]+)\.([^.]+)'
            ],
            "description": "Configuration-based Python packaging"
        },
        {
            "name": "Python - __init__.py version",
            "priority": 4,
            "patterns": ["__init__.py", "*/__init__.py"],
            "regex": [
                r'__version__\s*=\s*["\']([^"\']+)["\']',
                r'VERSION\s*=\s*["\']([^"\']+)["\']',
                r'version\s*=\s*["\']([^"\']+)["\']'
            ],
            "description": "Python module version declarations"
        },
        {
            "name": "Python - version.py",
            "priority": 5,
            "patterns": ["version.py", "_version.py", "*/version.py", "*/_version.py"],
            "regex": [
                r'__version__\s*=\s*["\']([^"\']+)["\']',
                r'VERSION\s*=\s*["\']([^"\']+)["\']',
                r'version\s*=\s*["\']([^"\']+)["\']'
            ],
            "description": "Dedicated Python version files"
        },

        # ==== JAVASCRIPT/NODE.JS ECOSYSTEM ====
        {
            "name": "Node.js - package.json",
            "priority": 10,
            "patterns": ["package.json"],
            "regex": [
                r'"version"\s*:\s*"([^"]+)"',
                r"'version'\\s*:\\s*'([^']+)'"
            ],
            "description": "NPM package configuration"
        },
        {
            "name": "Bower - bower.json",
            "priority": 11,
            "patterns": ["bower.json"],
            "regex": [
                r'"version"\s*:\s*"([^"]+)"'
            ],
            "description": "Bower package manager (legacy)"
        },
        {
            "name": "Component - component.json",
            "priority": 12,
            "patterns": ["component.json"],
            "regex": [
                r'"version"\s*:\s*"([^"]+)"'
            ],
            "description": "Component package manager"
        },

        # ==== JAVA ECOSYSTEM ====
        {
            "name": "Maven - pom.xml",
            "priority": 20,
            "patterns": ["pom.xml"],
            "regex": [
                r'<version>([^<]+)</version>',
                r'version="([^"]+)"'
            ],
            "description": "Maven project object model"
        },
        {
            "name": "Gradle - build.gradle",
            "priority": 21,
            "patterns": ["build.gradle"],
            "regex": [
                r'version\s*=\s*["\']([^"\']+)["\']',
                r'version\s*["\']([^"\']+)["\']',
                r'version\s*=\s*([^\s]+)'
            ],
            "description": "Gradle build script (Groovy DSL)"
        },
        {
            "name": "Gradle - build.gradle.kts",
            "priority": 22,
            "patterns": ["build.gradle.kts"],
            "regex": [
                r'version\s*=\s*"([^"]+)"',
                r"version\\s*=\\s*'([^']+)'"
            ],
            "description": "Gradle build script (Kotlin DSL)"
        },
        {
            "name": "Gradle - gradle.properties",
            "priority": 23,
            "patterns": ["gradle.properties"],
            "regex": [
                r'version\s*=\s*([^\s]+)',
                r'VERSION\s*=\s*([^\s]+)'
            ],
            "description": "Gradle properties file"
        },

        # ==== C#/.NET ECOSYSTEM ====
        {
            "name": ".NET - *.csproj",
            "priority": 30,
            "patterns": ["*.csproj"],
            "regex": [
                r'<Version>([^<]+)</Version>',
                r'<AssemblyVersion>([^<]+)</AssemblyVersion>',
                r'<FileVersion>([^<]+)</FileVersion>',
                r'<PackageVersion>([^<]+)</PackageVersion>'
            ],
            "description": "C# project file"
        },
        {
            "name": ".NET - global.json",
            "priority": 31,
            "patterns": ["global.json"],
            "regex": [
                r'"version"\s*:\s*"([^"]+)"'
            ],
            "description": ".NET global settings"
        },
        {
            "name": ".NET - Directory.Build.props",
            "priority": 32,
            "patterns": ["Directory.Build.props"],
            "regex": [
                r'<Version>([^<]+)</Version>',
                r'<AssemblyVersion>([^<]+)</AssemblyVersion>'
            ],
            "description": "MSBuild directory properties"
        },

        # ==== GO ECOSYSTEM ====
        {
            "name": "Go - go.mod",
            "priority": 40,
            "patterns": ["go.mod"],
            "regex": [
                r'module\s+[^\s]+\s+go\s+([^\s]+)',
                r'//\s*version:\s*([^\s]+)'
            ],
            "description": "Go module definition"
        },
        {
            "name": "Go - version.go",
            "priority": 41,
            "patterns": ["version.go", "*/version.go"],
            "regex": [
                r'Version\s*=\s*"([^"]+)"',
                r'VERSION\s*=\s*"([^"]+)"',
                r'const\s+Version\s*=\s*"([^"]+)"'
            ],
            "description": "Go version constants"
        },

        # ==== RUST ECOSYSTEM ====
        {
            "name": "Rust - Cargo.toml",
            "priority": 50,
            "patterns": ["Cargo.toml"],
            "regex": [
                r'version\s*=\s*"([^"]+)"',
                r"version\\s*=\\s*'([^']+)'"
            ],
            "description": "Rust package manifest"
        },

        # ==== RUBY ECOSYSTEM ====
        {
            "name": "Ruby - Gemfile",
            "priority": 60,
            "patterns": ["Gemfile"],
            "regex": [
                r'gem\s+["\'][^"\']+["\']\s*,\s*["\']([^"\']+)["\']',
                r'version\s*=\s*["\']([^"\']+)["\']'
            ],
            "description": "Ruby gem dependencies"
        },
        {
            "name": "Ruby - *.gemspec",
            "priority": 61,
            "patterns": ["*.gemspec"],
            "regex": [
                r'version\s*=\s*["\']([^"\']+)["\']',
                r's\.version\s*=\s*["\']([^"\']+)["\']',
                r'spec\.version\s*=\s*["\']([^"\']+)["\']'
            ],
            "description": "Ruby gem specification"
        },
        {
            "name": "Ruby - version.rb",
            "priority": 62,
            "patterns": ["lib/*/version.rb", "version.rb"],
            "regex": [
                r'VERSION\s*=\s*["\']([^"\']+)["\']',
                r'Version\s*=\s*["\']([^"\']+)["\']'
            ],
            "description": "Ruby version files"
        },

        # ==== PHP ECOSYSTEM ====
        {
            "name": "PHP - composer.json",
            "priority": 70,
            "patterns": ["composer.json"],
            "regex": [
                r'"version"\s*:\s*"([^"]+)"'
            ],
            "description": "PHP Composer packages"
        },

        # ==== SWIFT/IOS ECOSYSTEM ====
        {
            "name": "Swift - Package.swift",
            "priority": 80,
            "patterns": ["Package.swift"],
            "regex": [
                r'version:\s*"([^"]+)"',
                r'Version\([^)]*"([^"]+)"'
            ],
            "description": "Swift Package Manager"
        },
        {
            "name": "iOS - *.podspec",
            "priority": 81,
            "patterns": ["*.podspec"],
            "regex": [
                r'version\s*=\s*["\']([^"\']+)["\']',
                r's\.version\s*=\s*["\']([^"\']+)["\']'
            ],
            "description": "CocoaPods specification"
        },
        {
            "name": "iOS - Info.plist",
            "priority": 82,
            "patterns": ["Info.plist", "*/Info.plist"],
            "regex": [
                r'<key>CFBundleShortVersionString</key>\s*<string>([^<]+)</string>',
                r'<key>CFBundleVersion</key>\s*<string>([^<]+)</string>'
            ],
            "description": "iOS application info"
        },

        # ==== C/C++ ECOSYSTEM ====
        {
            "name": "CMake - CMakeLists.txt",
            "priority": 90,
            "patterns": ["CMakeLists.txt"],
            "regex": [
                r'VERSION\s+([^\s)]+)',
                r'set\s*\(\s*VERSION\s+"([^"]+)"\s*\)',
                r'project\s*\([^)]*VERSION\s+([^\s)]+)'
            ],
            "description": "CMake build files"
        },
        {
            "name": "Conan - conanfile.txt",
            "priority": 91,
            "patterns": ["conanfile.txt"],
            "regex": [
                r'version\s*=\s*([^\s]+)'
            ],
            "description": "Conan package manager"
        },
        {
            "name": "Conan - conanfile.py",
            "priority": 92,
            "patterns": ["conanfile.py"],
            "regex": [
                r'version\s*=\s*["\']([^"\']+)["\']'
            ],
            "description": "Conan package manager (Python)"
        },
        {
            "name": "vcpkg - vcpkg.json",
            "priority": 93,
            "patterns": ["vcpkg.json"],
            "regex": [
                r'"version"\s*:\s*"([^"]+)"',
                r'"version-string"\s*:\s*"([^"]+)"'
            ],
            "description": "vcpkg package manager"
        },

        # ==== DART/FLUTTER ECOSYSTEM ====
        {
            "name": "Dart/Flutter - pubspec.yaml",
            "priority": 100,
            "patterns": ["pubspec.yaml"],
            "regex": [
                r'version:\s*([^\s]+)',
                r'version:\s*"([^"]+)"',
                r"version:\\s*'([^']+)'"
            ],
            "description": "Dart/Flutter packages"
        },

        # ==== SCALA ECOSYSTEM ====
        {
            "name": "Scala - build.sbt",
            "priority": 110,
            "patterns": ["build.sbt"],
            "regex": [
                r'version\s*:=\s*"([^"]+)"',
                r"version\\s*:=\\s*'([^']+)'"
            ],
            "description": "SBT build files"
        },

        # ==== CLOJURE ECOSYSTEM ====
        {
            "name": "Clojure - project.clj",
            "priority": 120,
            "patterns": ["project.clj"],
            "regex": [
                r'defproject\s+[^\s]+\s+"([^"]+)"'
            ],
            "description": "Leiningen projects"
        },
        {
            "name": "Clojure - deps.edn",
            "priority": 121,
            "patterns": ["deps.edn"],
            "regex": [
                r':version\s+"([^"]+)"'
            ],
            "description": "Clojure CLI/deps.edn"
        },

        # ==== HASKELL ECOSYSTEM ====
        {
            "name": "Haskell - *.cabal",
            "priority": 130,
            "patterns": ["*.cabal"],
            "regex": [
                r'version:\s*([^\s]+)',
                r'Version:\s*([^\s]+)'
            ],
            "description": "Cabal package files"
        },
        {
            "name": "Haskell - package.yaml",
            "priority": 131,
            "patterns": ["package.yaml"],
            "regex": [
                r'version:\s*([^\s]+)',
                r'version:\s*"([^"]+)"'
            ],
            "description": "hpack package files"
        },

        # ==== ELIXIR ECOSYSTEM ====
        {
            "name": "Elixir - mix.exs",
            "priority": 140,
            "patterns": ["mix.exs"],
            "regex": [
                r'version:\s*"([^"]+)"'
            ],
            "description": "Mix build tool"
        },

        # ==== ERLANG ECOSYSTEM ====
        {
            "name": "Erlang - rebar.config",
            "priority": 150,
            "patterns": ["rebar.config"],
            "regex": [
                r'{vsn,\s*"([^"]+)"}'
            ],
            "description": "Rebar build tool"
        },

        # ==== LUA ECOSYSTEM ====
        {
            "name": "Lua - *.rockspec",
            "priority": 160,
            "patterns": ["*.rockspec"],
            "regex": [
                r'version\s*=\s*"([^"]+)"'
            ],
            "description": "LuaRocks packages"
        },

        # ==== R ECOSYSTEM ====
        {
            "name": "R - DESCRIPTION",
            "priority": 170,
            "patterns": ["DESCRIPTION"],
            "regex": [
                r'Version:\s*([^\s]+)',
                r'VERSION:\s*([^\s]+)'
            ],
            "description": "R package description"
        },

        # ==== PERL ECOSYSTEM ====
        {
            "name": "Perl - META.json",
            "priority": 180,
            "patterns": ["META.json"],
            "regex": [
                r'"version"\s*:\s*"([^"]+)"'
            ],
            "description": "Perl module metadata"
        },
        {
            "name": "Perl - META.yml",
            "priority": 181,
            "patterns": ["META.yml"],
            "regex": [
                r'version:\s*([^\s]+)',
                r'version:\s*"([^"]+)"'
            ],
            "description": "Perl module metadata"
        },

        # ==== KUBERNETES/HELM ECOSYSTEM ====
        {
            "name": "Helm - Chart.yaml",
            "priority": 190,
            "patterns": ["Chart.yaml"],
            "regex": [
                r'version:\s*([^\s]+)',
                r'version:\s*"([^"]+)"',
                r'appVersion:\s*([^\s]+)',
                r'appVersion:\s*"([^"]+)"'
            ],
            "description": "Helm charts"
        },

        # ==== DOCKER ECOSYSTEM ====
        {
            "name": "Docker - Dockerfile",
            "priority": 200,
            "patterns": ["Dockerfile"],
            "regex": [
                r'LABEL\s+version\s*=\s*"([^"]+)"',
                r'LABEL\s+VERSION\s*=\s*"([^"]+)"',
                r'ARG\s+VERSION\s*=\s*([^\s]+)',
                r'ENV\s+VERSION\s*=\s*([^\s]+)'
            ],
            "description": "Docker images"
        },

        # ==== WEB FRONTEND ECOSYSTEM ====
        {
            "name": "Angular - angular.json",
            "priority": 210,
            "patterns": ["angular.json"],
            "regex": [
                r'"version"\s*:\s*"([^"]+)"'
            ],
            "description": "Angular projects"
        },

        # ==== GENERIC/UNIVERSAL VERSION FILES ====
        {
            "name": "Generic - VERSION (text)",
            "priority": 900,
            "patterns": ["VERSION"],
            "regex": [
                r'^v?([0-9]+\.[0-9]+\.[0-9]+(?:[-+][^\s]*)?)\s*$',
                r'^([0-9]+\.[0-9]+\.[0-9]+(?:[-+][^\s]*)?)\s*$'
            ],
            "description": "Plain text version files"
        },
        {
            "name": "Generic - version.txt",
            "priority": 901,
            "patterns": ["version.txt"],
            "regex": [
                r'^v?([0-9]+\.[0-9]+\.[0-9]+(?:[-+][^\s]*)?)\s*$',
                r'^([0-9]+\.[0-9]+\.[0-9]+(?:[-+][^\s]*)?)\s*$'
            ],
            "description": "Plain text version files"
        },
        {
            "name": "Generic - version.json",
            "priority": 902,
            "patterns": ["version.json"],
            "regex": [
                r'"version"\s*:\s*"([^"]+)"',
                r'"Version"\s*:\s*"([^"]+)"'
            ],
            "description": "JSON version files"
        },
        {
            "name": "Generic - version.yaml",
            "priority": 903,
            "patterns": ["version.yaml", "version.yml"],
            "regex": [
                r'version:\s*([^\s]+)',
                r'version:\s*"([^"]+)"',
                r"version:\\s*'([^']+)'"
            ],
            "description": "YAML version files"
        },
        {
            "name": "Generic - manifest.json",
            "priority": 904,
            "patterns": ["manifest.json"],
            "regex": [
                r'"version"\s*:\s*"([^"]+)"',
                r'"manifest_version"\s*:\s*"([^"]+)"'
            ],
            "description": "Generic manifest files"
        },
        {
            "name": "Generic - app.json",
            "priority": 905,
            "patterns": ["app.json"],
            "regex": [
                r'"version"\s*:\s*"([^"]+)"'
            ],
            "description": "Application manifest files"
        }
    ]

    def __init__(self) -> None:
        """Initialize the project mapping database."""
        self._mappings: List[ProjectMapping] = []
        self._mappings_by_name: Dict[str, ProjectMapping] = {}
        self._mappings_by_priority: Dict[int, List[ProjectMapping]] = {}
        self._loaded = False

    def load_default_mappings(self) -> None:
        """Load the default project mappings."""
        if self._loaded:
            return

        for mapping_data in self.DEFAULT_MAPPINGS:
            try:
                mapping = ProjectMapping(**mapping_data)
                self.add_mapping(mapping)
            except Exception as e:
                logger.warning(f"Failed to load mapping {mapping_data.get('name', 'unknown')}: {e}")

        self._loaded = True
        logger.info(f"Loaded {len(self._mappings)} default project mappings")

    def add_mapping(self, mapping: ProjectMapping) -> None:
        """
        Add a project mapping to the database.

        Args:
            mapping: The ProjectMapping to add
        """
        if mapping.name in self._mappings_by_name:
            logger.warning(f"Overriding existing mapping: {mapping.name}")

        self._mappings.append(mapping)
        self._mappings_by_name[mapping.name] = mapping

        if mapping.priority not in self._mappings_by_priority:
            self._mappings_by_priority[mapping.priority] = []
        self._mappings_by_priority[mapping.priority].append(mapping)

        # Re-sort by priority
        self._mappings.sort(key=lambda m: m.priority)

    def get_all_mappings(self) -> List[ProjectMapping]:
        """Get all project mappings ordered by priority."""
        if not self._loaded:
            self.load_default_mappings()
        return self._mappings.copy()

    def get_mapping_by_name(self, name: str) -> Optional[ProjectMapping]:
        """Get a project mapping by name."""
        if not self._loaded:
            self.load_default_mappings()
        return self._mappings_by_name.get(name)

    def get_mappings_by_priority(self, priority: int) -> List[ProjectMapping]:
        """Get all project mappings with a specific priority."""
        if not self._loaded:
            self.load_default_mappings()
        return self._mappings_by_priority.get(priority, []).copy()

    def get_mappings_by_ecosystem(self, ecosystem: str) -> List[ProjectMapping]:
        """Get all project mappings for a specific ecosystem."""
        if not self._loaded:
            self.load_default_mappings()
        ecosystem_lower = ecosystem.lower()
        return [m for m in self._mappings if ecosystem_lower in m.name.lower()]

    def search_mappings(self, query: str) -> List[ProjectMapping]:
        """Search for project mappings by name or description."""
        if not self._loaded:
            self.load_default_mappings()
        query_lower = query.lower()
        return [
            m for m in self._mappings
            if query_lower in m.name.lower() or query_lower in m.description.lower()
        ]

    def get_statistics(self) -> Dict[str, int]:
        """Get statistics about the project mappings database."""
        if not self._loaded:
            self.load_default_mappings()

        ecosystems: Dict[str, int] = {}
        for mapping in self._mappings:
            # Extract ecosystem from name (everything before the first " - ")
            ecosystem = mapping.name.split(" - ")[0] if " - " in mapping.name else "Generic"
            ecosystems[ecosystem] = ecosystems.get(ecosystem, 0) + 1

        return {
            "total_mappings": len(self._mappings),
            "unique_ecosystems": len(ecosystems)
        }


# Global instance
_database_instance: Optional[ProjectMappingDatabase] = None


def get_database() -> ProjectMappingDatabase:
    """Get the global project mapping database instance."""
    global _database_instance
    if _database_instance is None:
        _database_instance = ProjectMappingDatabase()
    return _database_instance
