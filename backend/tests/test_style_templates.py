"""Tests for style template definitions and lookup."""

import pytest

from src.music.style_templates import STYLE_TEMPLATES, get_template


# ---------------------------------------------------------------------------
# Tests: STYLE_TEMPLATES dict
# ---------------------------------------------------------------------------

class TestStyleTemplatesDict:
    """Verify that the STYLE_TEMPLATES dictionary is well-formed."""

    EXPECTED_STYLES = ["jazz", "soulful", "rnb", "pop", "classical"]
    REQUIRED_KEYS = [
        "name",
        "description",
        "chord_extensions",
        "rhythm_pattern",
        "density",
        "voicing_rules",
    ]

    def test_all_styles_present(self):
        """STYLE_TEMPLATES should contain entries for every supported style."""
        for style in self.EXPECTED_STYLES:
            assert style in STYLE_TEMPLATES, f"Missing style: {style}"

    def test_each_style_has_required_keys(self):
        """Every style template should have all required fields."""
        for style_name, template in STYLE_TEMPLATES.items():
            for key in self.REQUIRED_KEYS:
                assert key in template, (
                    f"Style '{style_name}' is missing key '{key}'"
                )

    def test_name_matches_key(self):
        """The 'name' field should match the dictionary key."""
        for style_name, template in STYLE_TEMPLATES.items():
            assert template["name"] == style_name

    def test_description_is_nonempty_string(self):
        """Each style description should be a non-empty string."""
        for style_name, template in STYLE_TEMPLATES.items():
            assert isinstance(template["description"], str)
            assert len(template["description"]) > 0

    def test_chord_extensions_is_list(self):
        """chord_extensions should be a list."""
        for style_name, template in STYLE_TEMPLATES.items():
            assert isinstance(template["chord_extensions"], list)

    def test_rhythm_pattern_is_list(self):
        """rhythm_pattern should be a list of floats or ints."""
        for style_name, template in STYLE_TEMPLATES.items():
            assert isinstance(template["rhythm_pattern"], list)
            assert len(template["rhythm_pattern"]) > 0
            for val in template["rhythm_pattern"]:
                assert isinstance(val, (int, float))

    def test_density_is_positive_number(self):
        """density should be a positive number."""
        for style_name, template in STYLE_TEMPLATES.items():
            assert isinstance(template["density"], (int, float))
            assert template["density"] > 0

    def test_voicing_rules_is_dict(self):
        """voicing_rules should be a dictionary."""
        for style_name, template in STYLE_TEMPLATES.items():
            assert isinstance(template["voicing_rules"], dict)

    def test_jazz_has_extensions(self):
        """Jazz template should include chord extensions like 7ths and 9ths."""
        jazz = STYLE_TEMPLATES["jazz"]
        assert len(jazz["chord_extensions"]) > 0

    def test_pop_has_simpler_voicing(self):
        """Pop template should have simpler voicing rules than jazz."""
        pop = STYLE_TEMPLATES["pop"]
        jazz = STYLE_TEMPLATES["jazz"]
        assert pop["density"] <= jazz["density"]


# ---------------------------------------------------------------------------
# Tests: get_template function
# ---------------------------------------------------------------------------

class TestGetTemplate:
    """Test the get_template lookup function."""

    def test_returns_correct_template(self):
        """get_template should return the matching template dict."""
        template = get_template("jazz")
        assert template["name"] == "jazz"

    def test_all_styles_retrievable(self):
        """Every known style should be retrievable via get_template."""
        for style in ["jazz", "soulful", "rnb", "pop", "classical"]:
            template = get_template(style)
            assert template is not None
            assert template["name"] == style

    def test_unknown_style_raises(self):
        """Requesting a non-existent style should raise a KeyError."""
        with pytest.raises(KeyError):
            get_template("dubstep")

    def test_returns_dict(self):
        """get_template should return a dictionary."""
        template = get_template("pop")
        assert isinstance(template, dict)
