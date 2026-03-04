"""Generate evaluation reports from musician rating datasets."""

from typing import Any

from src.evals.metrics import kramers_alpha, mean_rating, per_style_ratings


def _build_dimension_matrix(
    dataset: list[dict[str, Any]], dimension: str
) -> list[list[float]]:
    """Extract a ratings matrix for a single dimension across all entries.

    Args:
        dataset: The evaluation dataset.
        dimension: One of 'musicality', 'style_match', 'fit_to_melody'.

    Returns:
        A matrix of shape (n_items, n_raters) for the given dimension.
    """
    matrix: list[list[float]] = []
    for entry in dataset:
        row = [r[dimension] for r in entry["ratings"]]
        matrix.append(row)
    return matrix


def generate_report(dataset: list[dict[str, Any]]) -> dict[str, Any]:
    """Generate a full evaluation report from a rated dataset.

    The report includes:
      - total_entries: number of evaluated accompaniments
      - overall_mean: grand mean across all ratings
      - dimension_means: per-dimension (musicality, style_match, fit_to_melody) averages
      - kramers_alpha: interrater agreement per dimension
      - per_style: per-style rating breakdowns

    Args:
        dataset: List of evaluation entries with ratings.

    Returns:
        A dictionary containing all report fields.
    """
    overall = mean_rating(dataset)

    # Per-dimension means
    dimensions = ("musicality", "style_match", "fit_to_melody")
    dimension_means: dict[str, float] = {}
    for dim in dimensions:
        total = 0.0
        count = 0
        for entry in dataset:
            for rating in entry["ratings"]:
                total += rating[dim]
                count += 1
        dimension_means[dim] = total / count if count > 0 else 0.0

    # Kramer's alpha per dimension
    alpha_scores: dict[str, float] = {}
    for dim in dimensions:
        matrix = _build_dimension_matrix(dataset, dim)
        alpha_scores[dim] = kramers_alpha(matrix)

    # Per-style breakdown
    style_breakdown = per_style_ratings(dataset)

    return {
        "total_entries": len(dataset),
        "overall_mean": overall,
        "dimension_means": dimension_means,
        "kramers_alpha": alpha_scores,
        "per_style": style_breakdown,
    }
