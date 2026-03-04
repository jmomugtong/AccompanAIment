"""Dataset loading and validation for musician evaluation framework."""

import json
from typing import Any


REQUIRED_ENTRY_KEYS = {"id", "song_title", "style", "ratings"}
REQUIRED_RATING_DIMENSIONS = {"musicality", "style_match", "fit_to_melody"}
RATING_MIN = 1.0
RATING_MAX = 5.0


def load_dataset(path: str) -> list[dict[str, Any]]:
    """Load an evaluation dataset from a JSON file.

    Args:
        path: Filesystem path to a JSON file containing the eval dataset.

    Returns:
        A list of dataset entry dictionaries.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file contains invalid JSON.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Dataset file not found: {path}")

    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in dataset file: {exc}") from exc

    return data


def validate_dataset(data: Any) -> list[str]:
    """Validate the structure and content of an evaluation dataset.

    Checks that every entry has required keys, that ratings are non-empty,
    that each rating has the required dimensions, and that all scores fall
    within the valid 1-5 range.

    Args:
        data: The dataset to validate (should be a list of dicts).

    Returns:
        A list of human-readable error strings.  An empty list means the
        dataset is valid.
    """
    errors: list[str] = []

    if not isinstance(data, list):
        errors.append("Dataset must be a list, got " + type(data).__name__)
        return errors

    if len(data) == 0:
        errors.append("Dataset is empty")
        return errors

    for idx, entry in enumerate(data):
        prefix = f"Entry {idx}"

        # Check required top-level keys
        for key in REQUIRED_ENTRY_KEYS:
            if key not in entry:
                errors.append(f"{prefix}: missing required field '{key}'")

        # Validate ratings
        ratings = entry.get("ratings")
        if ratings is not None:
            if not isinstance(ratings, list) or len(ratings) == 0:
                errors.append(f"{prefix}: 'ratings' must be a non-empty list")
                continue

            for r_idx, rating in enumerate(ratings):
                r_prefix = f"{prefix}, rater {r_idx}"

                for dim in REQUIRED_RATING_DIMENSIONS:
                    if dim not in rating:
                        errors.append(
                            f"{r_prefix}: missing rating dimension '{dim}'"
                        )
                        continue
                    val = rating[dim]
                    if not isinstance(val, (int, float)):
                        errors.append(
                            f"{r_prefix}: '{dim}' must be numeric, got "
                            + type(val).__name__
                        )
                    elif val < RATING_MIN or val > RATING_MAX:
                        errors.append(
                            f"{r_prefix}: '{dim}' value {val} outside "
                            f"range [{RATING_MIN}, {RATING_MAX}]"
                        )

    return errors
