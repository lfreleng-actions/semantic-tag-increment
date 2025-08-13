# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Configuration management module.

This module handles basic configuration file management for the semantic tag increment tool.
Since the tool now only supports string mode, most configuration functionality has been removed.
"""

import logging
import os
import yaml
from pathlib import Path
from typing import Dict, Optional, Any

from .exceptions import ConfigurationError

logger = logging.getLogger(__name__)


class ConfigurationManager:
    """
    Manages basic configuration files for the semantic tag increment tool.

    This is a simplified configuration manager that handles general settings
    but no longer supports project mappings since the tool only operates in string mode.
    """

    # Configuration directory and file names
    CONFIG_DIR_NAME = "semantic_tag_increment"
    USER_CONFIG_FILE = "config.yaml"

    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize the configuration manager.

        Args:
            config_dir: Optional custom configuration directory path
        """
        self.config_dir = Path(config_dir) if config_dir else self._get_default_config_dir()
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

    def get_config_info(self) -> Dict[str, Any]:
        """
        Get information about the current configuration.

        Returns:
            Dictionary with configuration information
        """
        info = {
            'config_dir': str(self.config_dir),
            'config_dir_exists': self.config_dir.exists(),
            'user_config_file': str(self.user_config_file),
            'user_config_file_exists': self.user_config_file.exists(),
        }

        return info

    def validate_configuration(self) -> list[str]:
        """
        Validate the current configuration and return any issues found.

        Returns:
            List of validation issues (empty if no issues)
        """
        issues = []

        # Check if configuration directory is writable
        if not os.access(self.config_dir, os.W_OK):
            issues.append(f"Configuration directory is not writable: {self.config_dir}")

        # Validate general configuration file
        try:
            self.load_general_config()
        except Exception as e:
            issues.append(f"Failed to validate general configuration: {e}")

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
    return _config_manager
