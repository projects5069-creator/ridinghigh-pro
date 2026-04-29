#!/usr/bin/env python3
"""
check_sync.py — Quick standalone sync check.

Usage:
    python3 check_sync.py

Runs only check_19 (PK sync verification) from health_audit.py
and prints a clean, colored result. Fast — no Sheets access needed.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from health_audit import check_19_pk_sync, PASSED, WARNING, CRITICAL, INFO


def main():
    result = check_19_pk_sync()

    # Color codes
    colors = {
        PASSED:   "\033[92m",  # green
        INFO:     "\033[94m",  # blue
        WARNING:  "\033[93m",  # yellow
        CRITICAL: "\033[91m",  # red
    }
    reset = "\033[0m"
    color = colors.get(result.status, "")

    print(f"\n{color}[{result.check_id}] {result.status} — {result.name}{reset}")
    print(f"  {result.message}")
    if result.details:
        print(f"  Details: {result.details}")
    print()

    if result.is_critical():
        sys.exit(1)


if __name__ == "__main__":
    main()
