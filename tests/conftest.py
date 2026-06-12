"""Pytest configuration for the suite (TASK-163).

Auto-marks every test under `tests/agent/integration/` with the `integration`
marker. Those tests write/read a live Google Sheet and need credentials the CI
runner lacks, so CI runs `pytest -m "not integration"` to skip them without
counting them as failures. Marking by path here means the integration test files
themselves stay untouched.
"""
import pytest


def pytest_collection_modifyitems(config, items):
    for item in items:
        path = str(getattr(item, "fspath", "")).replace("\\", "/")
        if "/tests/agent/integration/" in path:
            item.add_marker(pytest.mark.integration)
