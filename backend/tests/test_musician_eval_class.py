"""Tests for MusicianEvaluator orchestration class."""

import pytest

from src.evals.musician_eval import MusicianEvaluator


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_dataset():
    """A small dataset with two styles for evaluation."""
    return [
        {
            "id": 1,
            "song_title": "Test Song 1",
            "style": "jazz",
            "ratings": [
                {"musicality": 4.5, "style_match": 4.0, "fit_to_melody": 4.5},
                {"musicality": 4.0, "style_match": 4.5, "fit_to_melody": 4.0},
                {"musicality": 4.5, "style_match": 4.0, "fit_to_melody": 4.5},
            ],
        },
        {
            "id": 2,
            "song_title": "Test Song 2",
            "style": "pop",
            "ratings": [
                {"musicality": 3.5, "style_match": 3.0, "fit_to_melody": 3.5},
                {"musicality": 3.0, "style_match": 3.5, "fit_to_melody": 3.0},
                {"musicality": 3.5, "style_match": 3.0, "fit_to_melody": 3.5},
            ],
        },
        {
            "id": 3,
            "song_title": "Test Song 3",
            "style": "jazz",
            "ratings": [
                {"musicality": 5.0, "style_match": 5.0, "fit_to_melody": 5.0},
                {"musicality": 5.0, "style_match": 5.0, "fit_to_melody": 5.0},
                {"musicality": 4.5, "style_match": 4.5, "fit_to_melody": 4.5},
            ],
        },
    ]


@pytest.fixture
def evaluator():
    """Create a MusicianEvaluator instance."""
    return MusicianEvaluator()


# ---------------------------------------------------------------------------
# Tests: MusicianEvaluator
# ---------------------------------------------------------------------------

class TestMusicianEvaluator:
    """Test the evaluation orchestration class."""

    def test_evaluate_returns_dict(self, evaluator, sample_dataset):
        """evaluate() should return a dictionary report."""
        report = evaluator.evaluate(sample_dataset)
        assert isinstance(report, dict)

    def test_report_has_overall_mean(self, evaluator, sample_dataset):
        """Report should contain an overall_mean field."""
        report = evaluator.evaluate(sample_dataset)
        assert "overall_mean" in report
        assert isinstance(report["overall_mean"], float)

    def test_report_has_kramers_alpha(self, evaluator, sample_dataset):
        """Report should contain Kramer's alpha per dimension."""
        report = evaluator.evaluate(sample_dataset)
        assert "kramers_alpha" in report
        assert "musicality" in report["kramers_alpha"]
        assert "style_match" in report["kramers_alpha"]
        assert "fit_to_melody" in report["kramers_alpha"]

    def test_report_has_per_style(self, evaluator, sample_dataset):
        """Report should contain per-style breakdown."""
        report = evaluator.evaluate(sample_dataset)
        assert "per_style" in report
        assert "jazz" in report["per_style"]
        assert "pop" in report["per_style"]

    def test_report_has_total_entries(self, evaluator, sample_dataset):
        """Report should contain total_entries count."""
        report = evaluator.evaluate(sample_dataset)
        assert "total_entries" in report
        assert report["total_entries"] == 3

    def test_report_has_dimension_means(self, evaluator, sample_dataset):
        """Report should contain per-dimension mean ratings."""
        report = evaluator.evaluate(sample_dataset)
        assert "dimension_means" in report
        for dim in ("musicality", "style_match", "fit_to_melody"):
            assert dim in report["dimension_means"]

    def test_overall_mean_in_valid_range(self, evaluator, sample_dataset):
        """The overall mean should be between 1.0 and 5.0."""
        report = evaluator.evaluate(sample_dataset)
        assert 1.0 <= report["overall_mean"] <= 5.0

    def test_report_has_pass_fail(self, evaluator, sample_dataset):
        """Report should contain a pass/fail indicator."""
        report = evaluator.evaluate(sample_dataset)
        assert "passes_threshold" in report
        assert isinstance(report["passes_threshold"], bool)

    def test_empty_dataset_handled(self, evaluator):
        """Evaluating an empty dataset should not crash."""
        report = evaluator.evaluate([])
        assert isinstance(report, dict)
        assert report["total_entries"] == 0

    def test_threshold_defaults(self, evaluator):
        """Default thresholds should match project quality gates."""
        assert evaluator.mean_threshold == 4.0
        assert evaluator.alpha_threshold == 0.85

    def test_custom_thresholds(self, sample_dataset):
        """Custom thresholds should be respected."""
        evaluator = MusicianEvaluator(mean_threshold=3.0, alpha_threshold=0.5)
        report = evaluator.evaluate(sample_dataset)
        assert evaluator.mean_threshold == 3.0
        assert evaluator.alpha_threshold == 0.5
