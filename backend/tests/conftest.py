"""Shared test fixtures."""

import pytest


@pytest.fixture
def sample_chord_progression() -> str:
    """A simple chord progression for testing."""
    return "C | F | G | C"


@pytest.fixture
def sample_melody_data() -> dict:
    """Sample extracted melody data for testing."""
    return {
        "notes": [60, 62, 64, 65, 67, 69, 71, 72],
        "timings": [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5],
        "confidence": [0.95, 0.92, 0.88, 0.91, 0.93, 0.90, 0.87, 0.94],
        "duration_seconds": 4.0,
    }
