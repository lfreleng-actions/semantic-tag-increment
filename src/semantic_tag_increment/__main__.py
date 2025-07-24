# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Main entry point for the semantic tag increment tool.

This module allows the package to be executed as a module using:
    python -m semantic_tag_increment
"""

from .cli import main

if __name__ == "__main__":
    main()
