"""Tests for musician evaluation framework: dataset loading, metrics, report generation."""

import json
import os
import tempfile

import pytest

from src.evals.dataset import load_dataset, validate_dataset
from src.evals.metrics import kramers_alpha, mean_rating, per_style_ratings
from src.evals.report_generator import generate_report


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_ratings_entry():
    """A single dataset entry with 5 raters."""
    return {
        "id": 1,
        "song_title": "Test Song",
        "style": "jazz",
        "key": "C",
        "tempo": 120,
        "time_signature": "4/4",
        "chord_progression": "Cmaj7 | Dm7 | G7 | Cmaj7",
        "ratings": [
            {"rater": "Rater A", "musicality": 4.0, "style_match": 4.5, "fit_to_melody": 4.0},
            {"rater": "Rater B", "musicality": 4.5, "style_match": 4.0, "fit_to_melody": 4.5},
            {"rater": "Rater C", "musicality": 4.0, "style_match": 4.5, "fit_to_melody": 4.0},
            {"rater": "Rater D", "musicality": 4.5, "style_match": 4.0, "fit_to_melody": 4.5},
            {"rater": "Rater E", "musicality": 4.0, "style_match": 4.5, "fit_to_melody": 4.0},
        ],
    }


@pytest.fixture
def sample_dataset(sample_ratings_entry):
    """A small dataset with multiple entries spanning two styles."""
    entry2 = {
        "id": 2,
        "song_title": "Test Song 2",
        "style": "pop",
        "key": "G",
        "tempo": 100,
        "time_signature": "4/4",
        "chord_progression": "G | Em | C | D",
        "ratings": [
            {"rater": "Rater A", "musicality": 3.5, "style_match": 3.0, "fit_to_melody": 3.5},
            {"rater": "Rater B", "musicality": 3.0, "style_match": 3.5, "fit_to_melody": 3.0},
            {"rater": "Rater C", "musicality": 3.5, "style_match": 3.0, "fit_to_melody": 3.5},
            {"rater": "Rater D", "musicality": 3.0, "style_match": 3.5, "fit_to_melody": 3.0},
            {"rater": "Rater E", "musicality": 3.5, "style_match": 3.0, "fit_to_melody": 3.5},
        ],
    }
    entry3 = {
        "id": 3,
        "song_title": "Test Song 3",
        "style": "jazz",
        "key": "F",
        "tempo": 90,
        "time_signature": "3/4",
        "chord_progression": "Fmaj7 | Em7 | Dm7 | Cmaj7",
        "ratings": [
            {"rater": "Rater A", "musicality": 5.0, "style_match": 5.0, "fit_to_melody": 5.0},
            {"rater": "Rater B", "musicality": 5.0, "style_match": 5.0, "fit_to_melody": 5.0},
            {"rater": "Rater C", "musicality": 4.5, "style_match": 4.5, "fit_to_melody": 4.5},
            {"rater": "Rater D", "musicality": 5.0, "style_match": 5.0, "fit_to_melody": 5.0},
            {"rater": "Rater E", "musicality": 5.0, "style_match": 4.5, "fit_to_melody": 5.0},
        ],
    }
    return [sample_ratings_entry, entry2, entry3]


@pytest.fixture
def dataset_file(sample_dataset):
    """Write sample dataset to a temporary JSON file and return the path."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False
    ) as f:
        json.dump(sample_dataset, f)
        path = f.name
    yield path
    os.unlink(path)


@pytest.fixture
def perfect_agreement_matrix():
    """A ratings matrix where all raters agree perfectly."""
    # 5 items, 3 raters, all give same score
    return [
        [5.0, 5.0, 5.0],
        [4.0, 4.0, 4.0],
        [3.0, 3.0, 3.0],
        [2.0, 2.0, 2.0],
        [1.0, 1.0, 1.0],
    ]


@pytest.fixture
def high_agreement_matrix():
    """A ratings matrix with high but not perfect agreement."""
    return [
        [5.0, 5.0, 4.5],
        [4.0, 4.0, 4.0],
        [3.0, 3.5, 3.0],
        [2.0, 2.0, 2.5],
        [1.0, 1.0, 1.0],
    ]


@pytest.fixture
def no_variance_matrix():
    """A ratings matrix where all items get the same score from everyone."""
    return [
        [4.0, 4.0, 4.0],
        [4.0, 4.0, 4.0],
        [4.0, 4.0, 4.0],
    ]


# ---------------------------------------------------------------------------
# Tests: Dataset loading and validation
# ---------------------------------------------------------------------------

class TestLoadDataset:
    """Test loading evaluation datasets from JSON files."""

    def test_load_dataset_returns_list(self, dataset_file):
        """load_dataset should return a list of entries."""
        data = load_dataset(dataset_file)
        assert isinstance(data, list)

    def test_load_dataset_correct_count(self, dataset_file):
        """Loaded dataset should have the expected number of entries."""
        data = load_dataset(dataset_file)
        assert len(data) == 3

    def test_load_dataset_preserves_structure(self, dataset_file):
        """Each entry should have the required keys."""
        data = load_dataset(dataset_file)
        required_keys = {"id", "song_title", "style", "ratings"}
        for entry in data:
            assert required_keys.issubset(entry.keys())

    def test_load_dataset_file_not_found(self):
        """load_dataset should raise FileNotFoundError for missing files."""
        with pytest.raises(FileNotFoundError):
            load_dataset("/nonexistent/path/missing.json")

    def test_load_dataset_invalid_json(self):
        """load_dataset should raise ValueError for invalid JSON."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            f.write("not valid json {{{")
            path = f.name
        try:
            with pytest.raises(ValueError):
                load_dataset(path)
        finally:
            os.unlink(path)

    def test_load_real_dataset(self):
        """Should successfully load the actual 50-accompaniment eval dataset."""
        real_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "datasets",
            "accompaniments_50.json",
        )
        real_path = os.path.normpath(real_path)
        data = load_dataset(real_path)
        assert len(data) == 50


class TestValidateDataset:
    """Test dataset validation logic."""

    def test_valid_dataset_passes(self, sample_dataset):
        """A well-formed dataset should pass validation."""
        errors = validate_dataset(sample_dataset)
        assert errors == []

    def test_missing_id_field(self, sample_dataset):
        """Entries missing 'id' should be flagged."""
        del sample_dataset[0]["id"]
        errors = validate_dataset(sample_dataset)
        assert len(errors) > 0
        assert any("id" in e.lower() for e in errors)

    def test_missing_ratings_field(self, sample_dataset):
        """Entries missing 'ratings' should be flagged."""
        del sample_dataset[1]["ratings"]
        errors = validate_dataset(sample_dataset)
        assert len(errors) > 0
        assert any("ratings" in e.lower() for e in errors)

    def test_empty_ratings_list(self, sample_dataset):
        """An entry with an empty ratings list should be flagged."""
        sample_dataset[0]["ratings"] = []
        errors = validate_dataset(sample_dataset)
        assert len(errors) > 0

    def test_rating_out_of_range(self, sample_dataset):
        """Ratings outside 1-5 range should be flagged."""
        sample_dataset[0]["ratings"][0]["musicality"] = 6.0
        errors = validate_dataset(sample_dataset)
        assert len(errors) > 0

    def test_rating_below_range(self, sample_dataset):
        """Ratings below 1.0 should be flagged."""
        sample_dataset[0]["ratings"][0]["fit_to_melody"] = 0.0
        errors = validate_dataset(sample_dataset)
        assert len(errors) > 0

    def test_missing_rating_dimension(self, sample_dataset):
        """Ratings missing required dimensions should be flagged."""
        del sample_dataset[0]["ratings"][0]["musicality"]
        errors = validate_dataset(sample_dataset)
        assert len(errors) > 0

    def test_empty_dataset(self):
        """An empty dataset should be flagged."""
        errors = validate_dataset([])
        assert len(errors) > 0

    def test_non_list_input(self):
        """Non-list input should be flagged."""
        errors = validate_dataset("not a list")
        assert len(errors) > 0


# ---------------------------------------------------------------------------
# Tests: Metrics
# ---------------------------------------------------------------------------

class TestKramersAlpha:
    """Test Kramer's alpha interrater agreement calculation."""

    def test_perfect_agreement_returns_one(self, perfect_agreement_matrix):
        """Perfect agreement among all raters should yield alpha = 1.0."""
        alpha = kramers_alpha(perfect_agreement_matrix)
        assert alpha == pytest.approx(1.0, abs=0.01)

    def test_high_agreement_above_threshold(self, high_agreement_matrix):
        """High agreement matrix should yield alpha > 0.8."""
        alpha = kramers_alpha(high_agreement_matrix)
        assert alpha > 0.8

    def test_alpha_range(self, high_agreement_matrix):
        """Alpha should be between -1 and 1 inclusive."""
        alpha = kramers_alpha(high_agreement_matrix)
        assert -1.0 <= alpha <= 1.0

    def test_no_variance_returns_one(self, no_variance_matrix):
        """When all scores are identical across items and raters, alpha should be 1.0."""
        alpha = kramers_alpha(no_variance_matrix)
        # When there's zero variance across items, alpha is undefined;
        # we define it as 1.0 by convention (all raters agree).
        assert alpha == pytest.approx(1.0, abs=0.01)

    def test_random_disagreement_low_alpha(self):
        """Highly varied ratings should yield a low alpha."""
        # Construct a matrix with maximum disagreement
        matrix = [
            [1.0, 5.0, 3.0],
            [5.0, 1.0, 3.0],
            [3.0, 3.0, 1.0],
            [1.0, 5.0, 5.0],
            [5.0, 1.0, 1.0],
        ]
        alpha = kramers_alpha(matrix)
        assert alpha < 0.5

    def test_single_item_matrix(self):
        """A matrix with a single item should not crash."""
        matrix = [[4.0, 4.0, 4.0]]
        alpha = kramers_alpha(matrix)
        # With only one item, there's no between-item variance
        assert isinstance(alpha, float)

    def test_two_raters(self):
        """Should work with exactly two raters."""
        matrix = [
            [4.0, 4.0],
            [3.0, 3.0],
            [5.0, 5.0],
        ]
        alpha = kramers_alpha(matrix)
        assert alpha == pytest.approx(1.0, abs=0.01)


class TestMeanRating:
    """Test mean rating calculation across dataset entries."""

    def test_mean_of_uniform_ratings(self):
        """Mean of uniform ratings should equal that value."""
        ratings_data = [
            {
                "ratings": [
                    {"musicality": 4.0, "style_match": 4.0, "fit_to_melody": 4.0},
                    {"musicality": 4.0, "style_match": 4.0, "fit_to_melody": 4.0},
                ]
            }
        ]
        result = mean_rating(ratings_data)
        assert result == pytest.approx(4.0, abs=0.01)

    def test_mean_across_multiple_entries(self, sample_dataset):
        """Mean should average across all entries, raters, and dimensions."""
        result = mean_rating(sample_dataset)
        assert isinstance(result, float)
        assert 1.0 <= result <= 5.0

    def test_mean_single_entry(self, sample_ratings_entry):
        """Should work with a single entry."""
        result = mean_rating([sample_ratings_entry])
        assert isinstance(result, float)
        assert 1.0 <= result <= 5.0

    def test_mean_returns_expected_value(self):
        """Verify exact calculation with known values."""
        ratings_data = [
            {
                "ratings": [
                    {"musicality": 3.0, "style_match": 4.0, "fit_to_melody": 5.0},
                ]
            }
        ]
        # (3 + 4 + 5) / 3 = 4.0
        result = mean_rating(ratings_data)
        assert result == pytest.approx(4.0, abs=0.01)


class TestPerStyleRatings:
    """Test per-style rating breakdowns."""

    def test_returns_dict(self, sample_dataset):
        """per_style_ratings should return a dictionary keyed by style name."""
        result = per_style_ratings(sample_dataset)
        assert isinstance(result, dict)

    def test_contains_expected_styles(self, sample_dataset):
        """Result should contain keys for each style present in the dataset."""
        result = per_style_ratings(sample_dataset)
        assert "jazz" in result
        assert "pop" in result

    def test_style_has_required_dimensions(self, sample_dataset):
        """Each style entry should have musicality, style_match, fit_to_melody averages."""
        result = per_style_ratings(sample_dataset)
        for style_name, stats in result.items():
            assert "musicality" in stats
            assert "style_match" in stats
            assert "fit_to_melody" in stats
            assert "count" in stats

    def test_style_count_is_correct(self, sample_dataset):
        """Count per style should match the number of entries for that style."""
        result = per_style_ratings(sample_dataset)
        # sample_dataset has 2 jazz entries and 1 pop entry
        assert result["jazz"]["count"] == 2
        assert result["pop"]["count"] == 1

    def test_style_averages_in_range(self, sample_dataset):
        """Per-style averages should be between 1.0 and 5.0."""
        result = per_style_ratings(sample_dataset)
        for style_name, stats in result.items():
            assert 1.0 <= stats["musicality"] <= 5.0
            assert 1.0 <= stats["style_match"] <= 5.0
            assert 1.0 <= stats["fit_to_melody"] <= 5.0


# ---------------------------------------------------------------------------
# Tests: Report generation
# ---------------------------------------------------------------------------

class TestReportGenerator:
    """Test the evaluation report generator."""

    def test_generate_report_returns_dict(self, sample_dataset):
        """generate_report should return a dictionary."""
        report = generate_report(sample_dataset)
        assert isinstance(report, dict)

    def test_report_has_overall_mean(self, sample_dataset):
        """Report should include an overall mean rating."""
        report = generate_report(sample_dataset)
        assert "overall_mean" in report
        assert isinstance(report["overall_mean"], float)

    def test_report_has_kramers_alpha(self, sample_dataset):
        """Report should include Kramer's alpha for each dimension."""
        report = generate_report(sample_dataset)
        assert "kramers_alpha" in report
        assert "musicality" in report["kramers_alpha"]
        assert "style_match" in report["kramers_alpha"]
        assert "fit_to_melody" in report["kramers_alpha"]

    def test_report_has_per_style_breakdown(self, sample_dataset):
        """Report should include per-style rating breakdowns."""
        report = generate_report(sample_dataset)
        assert "per_style" in report
        assert "jazz" in report["per_style"]

    def test_report_has_entry_count(self, sample_dataset):
        """Report should include the number of evaluated entries."""
        report = generate_report(sample_dataset)
        assert "total_entries" in report
        assert report["total_entries"] == 3

    def test_report_has_dimension_means(self, sample_dataset):
        """Report should include per-dimension mean ratings."""
        report = generate_report(sample_dataset)
        assert "dimension_means" in report
        assert "musicality" in report["dimension_means"]
        assert "style_match" in report["dimension_means"]
        assert "fit_to_melody" in report["dimension_means"]

    def test_report_overall_mean_in_range(self, sample_dataset):
        """Overall mean should be between 1.0 and 5.0."""
        report = generate_report(sample_dataset)
        assert 1.0 <= report["overall_mean"] <= 5.0

    def test_report_alpha_values_are_floats(self, sample_dataset):
        """Alpha values should be floats."""
        report = generate_report(sample_dataset)
        for dim, val in report["kramers_alpha"].items():
            assert isinstance(val, float)
