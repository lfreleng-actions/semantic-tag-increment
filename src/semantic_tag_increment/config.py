# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Configuration management module.

This module handles configuration file management, user-extensible project mappings,
and configuration validation for the semantic tag increment tool.
"""

import logging
import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import asdict

from .exceptions import ConfigurationError
from .project_mappings import ProjectMapping

logger = logging.getLogger(__name__)


class ConfigurationManager:
    """
    Manages configuration files and user-extensible project mappings.

    Handles loading, saving, and validation of configuration files,
    with support for user-defined project type mappings.
    """

    # Configuration directory and file names
    CONFIG_DIR_NAME = "semantic_tag_increment"
    PROJECT_MAPPINGS_FILE = "project_mappings.yaml"
    USER_CONFIG_FILE = "config.yaml"

    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize the configuration manager.

        Args:
            config_dir: Optional custom configuration directory path
        """
        self.config_dir = Path(config_dir) if config_dir else self._get_default_config_dir()
        self.project_mappings_file = self.config_dir / self.PROJECT_MAPPINGS_FILE
        self.user_config_file = self.config_dir / self.USER_CONFIG_FILE

        # Ensure configuration directory exists
        self._ensure_config_dir()

    def _get_default_config_dir(self) -> Path:
        """Get the default configuration directory path."""
        if os.name == 'nt':  # Windows
            config_base = Path(os.environ.get('APPDATA', Path.home() / 'AppData' / 'Roaming'))
        else:  # Unix-like systems
            config_base = Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config'))

        return config_base / self.CONFIG_DIR_NAME

    def _ensure_config_dir(self) -> None:
        """Ensure the configuration directory exists."""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Configuration directory: {self.config_dir}")
        except OSError as e:
            raise ConfigurationError(f"Failed to create configuration directory: {e}")

    def load_user_project_mappings(self) -> List[ProjectMapping]:
        """
        Load user-defined project mappings from the configuration file.

        Returns:
            List of user-defined ProjectMapping objects

        Raises:
            ConfigurationError: If the configuration file is invalid
        """
        if not self.project_mappings_file.exists():
            logger.debug("No user project mappings file found")
            return []

        try:
            with open(self.project_mappings_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            if not data or 'project_mappings' not in data:
                logger.debug("No project mappings found in configuration file")
                return []

            mappings = []
            for mapping_data in data['project_mappings']:
                try:
                    self._validate_mapping_data(mapping_data)
                    mapping = ProjectMapping(**mapping_data)
                    mappings.append(mapping)
                except Exception as e:
                    logger.warning(f"Skipping invalid mapping {mapping_data.get('name', 'unknown')}: {e}")

            logger.info(f"Loaded {len(mappings)} user project mappings")
            return mappings

        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML in project mappings file: {e}")
        except Exception as e:
            raise ConfigurationError(f"Failed to load user project mappings: {e}")

    def save_user_project_mappings(self, mappings: List[ProjectMapping]) -> None:
        """
        Save user-defined project mappings to the configuration file.

        Args:
            mappings: List of ProjectMapping objects to save

        Raises:
            ConfigurationError: If the mappings cannot be saved
        """
        try:
            # Convert mappings to serializable format
            mappings_data = []
            for mapping in mappings:
                mapping_dict = asdict(mapping)
                # Remove fields that shouldn't be in the config file
                mapping_dict.pop('file_encoding', None)
                mapping_dict.pop('case_sensitive', None)
                mapping_dict.pop('multiline', None)
                mapping_dict.pop('max_file_size', None)
                mappings_data.append(mapping_dict)

            config_data = {
                'project_mappings': mappings_data,
                'metadata': {
                    'version': '1.0',
                    'description': 'User-defined project mappings for semantic-tag-increment',
                    'created_by': 'semantic-tag-increment configuration manager'
                }
            }

            with open(self.project_mappings_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)

            logger.info(f"Saved {len(mappings)} user project mappings")

        except Exception as e:
            raise ConfigurationError(f"Failed to save user project mappings: {e}")

    def add_user_mapping(self, mapping: ProjectMapping) -> None:
        """
        Add a new user-defined project mapping.

        Args:
            mapping: The ProjectMapping to add

        Raises:
            ConfigurationError: If the mapping cannot be added
        """
        existing_mappings = self.load_user_project_mappings()

        # Check for duplicate names
        for existing in existing_mappings:
            if existing.name == mapping.name:
                raise ConfigurationError(f"Mapping with name '{mapping.name}' already exists")

        existing_mappings.append(mapping)
        self.save_user_project_mappings(existing_mappings)

    def remove_user_mapping(self, name: str) -> bool:
        """
        Remove a user-defined project mapping by name.

        Args:
            name: The name of the mapping to remove

        Returns:
            True if a mapping was removed, False if not found

        Raises:
            ConfigurationError: If the mapping cannot be removed
        """
        existing_mappings = self.load_user_project_mappings()

        for i, mapping in enumerate(existing_mappings):
            if mapping.name == name:
                existing_mappings.pop(i)
                self.save_user_project_mappings(existing_mappings)
                return True

        return False

    def create_example_config(self) -> None:
        """Create an example configuration file for users to customize."""
        example_mappings = [
            {
                "name": "Custom - my-project.json",
                "priority": 1,
                "patterns": ["my-project.json"],
                "regex": ['"version":\\s*"([^"]+)"'],
                "description": "Custom project file example"
            },
            {
                "name": "Custom - VERSION.txt",
                "priority": 2,
                "patterns": ["VERSION.txt"],
                "regex": ['^v?([0-9]+\\.[0-9]+\\.[0-9]+(?:[-+][^\\s]*)?)\\s*$'],
                "description": "Custom version file example"
            }
        ]

        config_data = {
            'project_mappings': example_mappings,
            'metadata': {
                'version': '1.0',
                'description': 'Example user-defined project mappings',
                'note': 'Customize this file to add your own project type mappings'
            }
        }

        example_file = self.config_dir / "example_project_mappings.yaml"

        try:
            with open(example_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)

            logger.info(f"Created example configuration file: {example_file}")

        except Exception as e:
            logger.warning(f"Failed to create example configuration: {e}")

    def load_general_config(self) -> Dict[str, Any]:
        """
        Load general configuration settings.

        Returns:
            Dictionary of configuration settings
        """
        if not self.user_config_file.exists():
            return {}

        try:
            with open(self.user_config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.warning(f"Failed to load general configuration: {e}")
            return {}

    def save_general_config(self, config: Dict[str, Any]) -> None:
        """
        Save general configuration settings.

        Args:
            config: Dictionary of configuration settings to save
        """
        try:
            with open(self.user_config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)

            logger.debug("Saved general configuration")

        except Exception as e:
            logger.warning(f"Failed to save general configuration: {e}")

    def _validate_mapping_data(self, mapping_data: Dict[str, Any]) -> None:
        """
        Validate a project mapping data structure.

        Args:
            mapping_data: The mapping data to validate

        Raises:
            ConfigurationError: If the mapping data is invalid
        """
        required_fields = ['name', 'priority', 'patterns', 'regex', 'description']

        for field in required_fields:
            if field not in mapping_data:
                raise ConfigurationError(f"Missing required field: {field}")

        # Validate field types
        if not isinstance(mapping_data['name'], str) or not mapping_data['name'].strip():
            raise ConfigurationError("Field 'name' must be a non-empty string")

        if not isinstance(mapping_data['priority'], int) or mapping_data['priority'] < 0:
            raise ConfigurationError("Field 'priority' must be a non-negative integer")

        if not isinstance(mapping_data['patterns'], list) or not mapping_data['patterns']:
            raise ConfigurationError("Field 'patterns' must be a non-empty list")

        if not isinstance(mapping_data['regex'], list) or not mapping_data['regex']:
            raise ConfigurationError("Field 'regex' must be a non-empty list")

        if not isinstance(mapping_data['description'], str) or not mapping_data['description'].strip():
            raise ConfigurationError("Field 'description' must be a non-empty string")

        # Validate patterns
        for pattern in mapping_data['patterns']:
            if not isinstance(pattern, str) or not pattern.strip():
                raise ConfigurationError("All patterns must be non-empty strings")

        # Validate regex patterns
        import re
        for regex_pattern in mapping_data['regex']:
            if not isinstance(regex_pattern, str) or not regex_pattern.strip():
                raise ConfigurationError("All regex patterns must be non-empty strings")
            try:
                re.compile(regex_pattern)
            except re.error as e:
                raise ConfigurationError(f"Invalid regex pattern '{regex_pattern}': {e}")

    def get_config_info(self) -> Dict[str, Any]:
        """
        Get information about the current configuration.

        Returns:
            Dictionary with configuration information
        """
        info = {
            'config_dir': str(self.config_dir),
            'config_dir_exists': self.config_dir.exists(),
            'project_mappings_file': str(self.project_mappings_file),
            'project_mappings_file_exists': self.project_mappings_file.exists(),
            'user_config_file': str(self.user_config_file),
            'user_config_file_exists': self.user_config_file.exists(),
        }

        # Add user mappings count
        try:
            user_mappings = self.load_user_project_mappings()
            info['user_mappings_count'] = len(user_mappings)
        except Exception:
            info['user_mappings_count'] = 0

        return info

    def validate_configuration(self) -> List[str]:
        """
        Validate the current configuration and return any issues found.

        Returns:
            List of validation issues (empty if no issues)
        """
        issues = []

        # Check if configuration directory is writable
        if not os.access(self.config_dir, os.W_OK):
            issues.append(f"Configuration directory is not writable: {self.config_dir}")

        # Validate user project mappings
        try:
            user_mappings = self.load_user_project_mappings()

            # Check for duplicate names
            names = set()
            for mapping in user_mappings:
                if mapping.name in names:
                    issues.append(f"Duplicate mapping name: {mapping.name}")
                names.add(mapping.name)

            # Check for duplicate priorities
            priorities: Dict[int, str] = {}
            for mapping in user_mappings:
                if mapping.priority in priorities:
                    issues.append(
                        f"Duplicate priority {mapping.priority}: "
                        f"{mapping.name} and {priorities[mapping.priority]}"
                    )
                priorities[mapping.priority] = mapping.name

        except Exception as e:
            issues.append(f"Failed to validate user project mappings: {e}")

        return issues


# Global configuration manager instance
_config_manager: Optional[ConfigurationManager] = None


def get_config_manager() -> ConfigurationManager:
    """Get the global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigurationManager()
    return _config_manager


def initialize_config(config_dir: Optional[str] = None) -> ConfigurationManager:
    """
    Initialize the configuration system.

    Args:
        config_dir: Optional custom configuration directory

    Returns:
        Initialized ConfigurationManager instance
    """
    global _config_manager
    _config_manager = ConfigurationManager(config_dir)

    # Create example configuration if it doesn't exist
    try:
        _config_manager.create_example_config()
    except Exception as e:
        logger.debug(f"Failed to create example configuration: {e}")

    return _config_manager
