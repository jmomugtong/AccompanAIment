"""Style configuration definitions for piano accompaniment generation.

Each style config describes the harmonic and rhythmic characteristics
that guide the LLM agent and rule-based fallback when generating
piano voicings.
"""

from typing import Any, Optional

STYLE_CONFIGS: dict[str, dict[str, Any]] = {
    "jazz": {
        "extensions": ["7", "9", "13", "maj7", "min7", "dim7"],
        "voicing_type": "shell",
        "rhythm": "swing",
        "density": 0.7,
    },
    "soulful": {
        "extensions": ["7", "9", "sus4", "add9"],
        "voicing_type": "open",
        "rhythm": "gospel_groove",
        "density": 0.6,
    },
    "rnb": {
        "extensions": ["7", "9", "11", "min7", "add9"],
        "voicing_type": "close",
        "rhythm": "syncopated",
        "density": 0.8,
    },
    "pop": {
        "extensions": ["sus2", "sus4", "add9"],
        "voicing_type": "close",
        "rhythm": "straight",
        "density": 0.5,
    },
    "classical": {
        "extensions": ["triad", "6", "dim"],
        "voicing_type": "open",
        "rhythm": "arpeggiated",
        "density": 0.4,
    },
}


def get_style_config(style_name: str) -> Optional[dict[str, Any]]:
    """Return the style configuration for the given style name.

    Args:
        style_name: The name of the style (case-insensitive).

    Returns:
        The style configuration dict, or None if the style is unknown.
    """
    return STYLE_CONFIGS.get(style_name.lower())
