#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Performance test script for semantic tag increment optimizations.

This script benchmarks the performance improvements made to:
1. Regex pattern matching in the parser
2. Version existence checking with caching in the incrementer
"""

import sys
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from semantic_tag_increment.incrementer import VersionIncrementer
from semantic_tag_increment.parser import SemanticVersion


def generate_test_versions(count: int) -> list[str]:
    """Generate a large set of test version strings."""
    versions = []
    for major in range(10):
        for minor in range(10):
            for patch in range(count // 100):
                versions.append(f"v{major}.{minor}.{patch}")
                if len(versions) >= count:
                    return versions
    return versions


def benchmark_regex_performance():
    """Benchmark regex parsing performance."""
    print("🚀 Benchmarking Regex Performance")
    print("=" * 50)

    # Test version strings
    test_versions = [
        "v1.2.3",
        "2.0.0-alpha.1",
        "1.0.0-beta.2+build.123",
        "3.1.4-rc.1-SNAPSHOT",
        "0.1.0-dev.20231201",
        "v10.20.30-pre.1.2.3+meta.data.here",
    ] * 1000  # Repeat to get meaningful timing

    print(f"Testing with {len(test_versions)} version strings...")

    # Time the parsing
    start_time = time.perf_counter()

    parsed_count = 0
    for version_str in test_versions:
        try:
            SemanticVersion.parse(version_str)
            parsed_count += 1
        except ValueError:
            pass

    end_time = time.perf_counter()

    duration = end_time - start_time
    rate = len(test_versions) / duration

    print(f"✅ Parsed {parsed_count}/{len(test_versions)} versions")
    print(f"⏱️  Time taken: {duration:.4f} seconds")
    print(f"🏃 Parse rate: {rate:.0f} versions/second")
    print()


def benchmark_version_checking_performance():
    """Benchmark version existence checking with caching."""
    print("🚀 Benchmarking Version Checking Performance")
    print("=" * 50)

    # Generate a large set of existing tags
    existing_tags = generate_test_versions(10000)
    print(f"Generated {len(existing_tags)} existing tags...")

    # Create incrementer with caching
    incrementer = VersionIncrementer(existing_tags=set(existing_tags))

    # Test versions to check
    test_checks = []
    for i in range(1000):
        if i % 2 == 0:
            # Existing version (should be found in cache)
            test_checks.append(
                SemanticVersion.parse(existing_tags[i % len(existing_tags)])
            )
        else:
            # Non-existing version
            test_checks.append(SemanticVersion.parse(f"v999.{i}.999"))

    print(f"Testing {len(test_checks)} version existence checks...")

    # Time the version checking
    start_time = time.perf_counter()

    exists_count = 0
    for version in test_checks:
        if incrementer._version_exists(version):
            exists_count += 1

    end_time = time.perf_counter()

    duration = end_time - start_time
    rate = len(test_checks) / duration

    print(f"✅ Found {exists_count}/{len(test_checks)} existing versions")
    print(f"⏱️  Time taken: {duration:.4f} seconds")
    print(f"🏃 Check rate: {rate:.0f} checks/second")
    print()


def benchmark_cache_efficiency():
    """Benchmark the cache efficiency by comparing with and without cache."""
    print("🚀 Benchmarking Cache Efficiency")
    print("=" * 50)

    existing_tags = generate_test_versions(5000)

    # Test version checks
    test_version = SemanticVersion.parse("v1.2.3")
    num_checks = 1000

    # With cache (normal incrementer)
    incrementer_cached = VersionIncrementer(existing_tags=set(existing_tags))

    print(f"Testing {num_checks} repeated checks of the same version...")

    # First run builds the cache
    incrementer_cached._version_exists(test_version)

    # Time cached lookups
    start_time = time.perf_counter()
    for _ in range(num_checks):
        incrementer_cached._version_exists(test_version)
    cached_time = time.perf_counter() - start_time

    # Simulate old approach (rebuild normalization each time)
    start_time = time.perf_counter()
    for _ in range(num_checks):
        # Simulate the old approach without caching
        incrementer_cached._normalize_version_string(
            test_version.to_string(include_prefix=False)
        )
        # Simulate checking each tag individually
        for tag in existing_tags[
            :100
        ]:  # Check first 100 to keep test reasonable
            incrementer_cached._normalize_version_string(tag)
    uncached_time = time.perf_counter() - start_time

    print(f"⚡ Cached approach: {cached_time:.6f} seconds")
    print(f"🐌 Simulated old approach: {uncached_time:.6f} seconds")
    print(f"🏆 Speedup: {uncached_time / cached_time:.1f}x faster")
    print()


def main():
    """Run all performance benchmarks."""
    print("🧪 Semantic Tag Increment Performance Tests")
    print("=" * 50)
    print()

    benchmark_regex_performance()
    benchmark_version_checking_performance()
    benchmark_cache_efficiency()

    print("✨ Performance testing completed!")


if __name__ == "__main__":
    main()
