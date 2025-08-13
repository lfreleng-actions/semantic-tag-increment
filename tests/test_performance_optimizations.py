#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Unit tests for performance optimizations in semantic tag increment.

Tests the specific optimizations made to:
1. Regex pattern efficiency in parser.py
2. Version existence checking with caching in incrementer.py
"""

import re
import time
import unittest

from semantic_tag_increment.incrementer import VersionIncrementer
from semantic_tag_increment.parser import SemanticVersion


class TestPerformanceOptimizations(unittest.TestCase):
    """Test performance optimization features."""

    def test_regex_performance_with_ascii_flag(self):
        """Test that the regex uses ASCII flag for better performance."""
        # The regex should be compiled with re.ASCII flag
        pattern = SemanticVersion.SEMVER_PATTERN

        # Use re.ASCII constant instead of magic number for better readability
        self.assertEqual(
            pattern.flags & re.ASCII,
            re.ASCII,
            "Regex should use ASCII flag for performance",
        )

    def test_version_cache_initialization(self):
        """Test that version cache is properly initialized."""
        incrementer = VersionIncrementer({"v1.0.0", "v2.0.0", "v3.0.0"})

        # Cache should start as None
        self.assertIsNone(incrementer._normalized_tags_cache)

    def test_version_cache_building(self):
        """Test that version cache is built on first access."""
        existing_tags = {"v1.0.0", "v2.0.0", "v3.0.0"}
        incrementer = VersionIncrementer(existing_tags)

        # First call should build the cache
        test_version = SemanticVersion.parse("v1.0.0")
        result = incrementer._version_exists(test_version)

        # Cache should now be populated
        self.assertIsNotNone(incrementer._normalized_tags_cache)
        self.assertEqual(
            len(incrementer._normalized_tags_cache), len(existing_tags)
        )
        self.assertTrue(result)

    def test_version_cache_invalidation(self):
        """Test that cache is invalidated when tags are updated."""
        initial_tags = {"v1.0.0", "v2.0.0"}
        incrementer = VersionIncrementer(initial_tags)

        # Build cache
        test_version = SemanticVersion.parse("v1.0.0")
        incrementer._version_exists(test_version)
        self.assertIsNotNone(incrementer._normalized_tags_cache)

        # Update tags should invalidate cache
        new_tags = {"v3.0.0", "v4.0.0"}
        incrementer.update_existing_tags(new_tags)
        self.assertIsNone(incrementer._normalized_tags_cache)

        # Next access should rebuild cache with new tags
        incrementer._version_exists(test_version)
        self.assertIsNotNone(incrementer._normalized_tags_cache)
        self.assertEqual(len(incrementer._normalized_tags_cache), len(new_tags))

    def test_normalized_version_performance(self):
        """Test that version normalization is efficient."""
        incrementer = VersionIncrementer()

        # Test cases for normalization
        test_cases = [
            ("v1.2.3", "1.2.3"),
            ("V2.0.0", "2.0.0"),
            ("1.0.0+build.123", "1.0.0"),
            ("v1.0.0-alpha+build.456", "1.0.0-alpha"),
            ("", ""),
        ]

        for input_version, expected in test_cases:
            with self.subTest(input_version=input_version):
                result = incrementer._normalize_version_string(input_version)
                self.assertEqual(result, expected)

    def test_cache_performance_improvement(self):
        """Test that caching provides measurable performance improvement."""
        # Create a moderately large set of existing tags for testing
        large_tag_set = {f"v{i}.0.0" for i in range(1000)}
        incrementer = VersionIncrementer(large_tag_set)

        test_version = SemanticVersion.parse("v500.0.0")

        # Measure first call time (cache building) - single measurement should be sufficient
        start_time = time.perf_counter()
        result1 = incrementer._version_exists(test_version)
        first_call_time = time.perf_counter() - start_time

        # Measure subsequent call time (cache usage) - average of a few calls
        second_call_times: list[float] = []
        for _ in range(3):  # Just 3 iterations for averaging
            start_time = time.perf_counter()
            result2 = incrementer._version_exists(test_version)
            second_call_times.append(time.perf_counter() - start_time)

        # Both should return the same result
        self.assertEqual(result1, result2)
        self.assertTrue(result1)  # v500.0.0 should exist

        # Calculate average time for subsequent calls
        avg_second_call_time = sum(second_call_times) / len(second_call_times)

        # Second call should be significantly faster
        # Allow for some variance in timing, but should be at least 1.5x faster
        if first_call_time > 0:  # Avoid division by zero
            speedup = first_call_time / avg_second_call_time
            self.assertGreater(
                speedup,
                1.5,  # Reduced threshold for more reliable testing
                f"Cache should provide speedup, got {speedup:.1f}x",
            )

    def test_update_existing_tags_method(self):
        """Test the new update_existing_tags method."""
        initial_tags = {"v1.0.0", "v2.0.0"}
        new_tags = {"v3.0.0", "v4.0.0", "v5.0.0"}

        incrementer = VersionIncrementer(initial_tags)

        # Update tags
        incrementer.update_existing_tags(new_tags)

        # Verify tags are updated
        self.assertEqual(incrementer.existing_tags, new_tags)

        # Verify cache is invalidated
        self.assertIsNone(incrementer._normalized_tags_cache)

    def test_regex_pattern_optimization(self):
        """Test that the optimized regex pattern works correctly."""
        # Test cases that should parse successfully
        valid_versions = [
            "1.0.0",
            "v2.1.3",
            "V3.0.0-alpha",
            "1.2.3-beta.1",
            "2.0.0+build.123",
            "1.0.0-alpha.1+meta.data",
        ]

        for version_str in valid_versions:
            with self.subTest(version=version_str):
                try:
                    version = SemanticVersion.parse(version_str)
                    self.assertIsInstance(version, SemanticVersion)
                except ValueError:
                    self.fail(
                        f"Valid version '{version_str}' should parse successfully"
                    )

    def test_version_exists_with_prefixes(self):
        """Test that version checking works correctly with and without prefixes."""
        existing_tags = {"v1.0.0", "2.0.0", "V3.0.0"}
        incrementer = VersionIncrementer(existing_tags)

        # Test variations of the same version
        test_cases = [
            (SemanticVersion.parse("v1.0.0"), True),
            (SemanticVersion.parse("1.0.0"), True),  # Should match v1.0.0
            (SemanticVersion.parse("2.0.0"), True),
            (SemanticVersion.parse("v2.0.0"), True),  # Should match 2.0.0
            (SemanticVersion.parse("3.0.0"), True),  # Should match V3.0.0
            (SemanticVersion.parse("4.0.0"), False),  # Should not exist
        ]

        for version, expected in test_cases:
            with self.subTest(version=version.to_string()):
                result = incrementer._version_exists(version)
                self.assertEqual(
                    result,
                    expected,
                    f"Version {version.to_string()} existence check failed",
                )


if __name__ == "__main__":
    unittest.main()
