"""Style template definitions for piano accompaniment generation.

Each template captures the musical characteristics of a style:
- chord_extensions: which chord extensions (7ths, 9ths, etc.) to use
- rhythm_pattern: beat subdivisions as quarter-note durations
- density: average number of notes sounding per beat (higher = busier)
- voicing_rules: style-specific parameters for the voicing generator
"""

from typing import Any

STYLE_TEMPLATES: dict[str, dict[str, Any]] = {
    "jazz": {
        "name": "jazz",
        "description": "Extended harmony with 7ths, 9ths, and 13ths. "
        "Syncopated rhythms, walking bass lines, and shell voicings.",
        "chord_extensions": ["7", "9", "13", "maj7", "min7", "dim7"],
        "rhythm_pattern": [1.0, 0.5, 0.5, 1.0, 0.5, 0.5],
        "density": 5,
        "voicing_rules": {
            "note_count": 4,
            "extensions": True,
            "add_seventh": True,
            "shell_voicing": True,
            "spread": "wide",
        },
    },
    "soulful": {
        "name": "soulful",
        "description": "Warm extended voicings with smooth voice leading. "
        "Emphasis on 7ths and 9ths with a relaxed groove feel.",
        "chord_extensions": ["7", "9", "maj7", "min7"],
        "rhythm_pattern": [1.0, 1.0, 0.5, 0.5, 1.0],
        "density": 4,
        "voicing_rules": {
            "note_count": 4,
            "extensions": True,
            "add_seventh": True,
            "shell_voicing": False,
            "spread": "close",
        },
    },
    "rnb": {
        "name": "rnb",
        "description": "Rich extended voicings with color tones. "
        "Syncopated rhythm with emphasis on 2 and 4, lush chord stacks.",
        "chord_extensions": ["7", "9", "11", "maj7", "min7", "add9"],
        "rhythm_pattern": [0.5, 0.5, 1.0, 0.5, 0.5, 1.0],
        "density": 4,
        "voicing_rules": {
            "note_count": 4,
            "extensions": True,
            "add_seventh": True,
            "shell_voicing": False,
            "spread": "close",
        },
    },
    "pop": {
        "name": "pop",
        "description": "Simple triads with clean voicings. "
        "Straight eighth-note patterns, emphasis on root-position chords.",
        "chord_extensions": [],
        "rhythm_pattern": [1.0, 1.0, 1.0, 1.0],
        "density": 3,
        "voicing_rules": {
            "note_count": 3,
            "extensions": False,
            "add_seventh": False,
            "shell_voicing": False,
            "spread": "close",
        },
    },
    "classical": {
        "name": "classical",
        "description": "Four-part SATB-style harmony with proper voice leading. "
        "Arpeggiated patterns, Alberti bass, and traditional cadences.",
        "chord_extensions": [],
        "rhythm_pattern": [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5],
        "density": 4,
        "voicing_rules": {
            "note_count": 4,
            "extensions": False,
            "add_seventh": False,
            "double_root": True,
            "shell_voicing": False,
            "spread": "wide",
        },
    },
}


def get_template(style_name: str) -> dict[str, Any]:
    """Look up a style template by name.

    Args:
        style_name: One of 'jazz', 'soulful', 'rnb', 'pop', 'classical'.

    Returns:
        The corresponding style template dictionary.

    Raises:
        KeyError: If the style name is not recognized.
    """
    if style_name not in STYLE_TEMPLATES:
        raise KeyError(
            f"Unknown style '{style_name}'. "
            f"Available styles: {', '.join(sorted(STYLE_TEMPLATES.keys()))}"
        )
    return STYLE_TEMPLATES[style_name]
