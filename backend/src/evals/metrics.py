"""Evaluation metrics: Kramer's alpha, mean ratings, per-style breakdowns."""

from collections import defaultdict
from typing import Any


def kramers_alpha(ratings_matrix: list[list[float]]) -> float:
    """Compute Krippendorff's alpha (interval metric) for interrater agreement.

    This implements the standard Krippendorff's alpha calculation for
    interval-level data.  Despite the function name using "Kramer's" (as
    per the project spec), the underlying statistic is Krippendorff's alpha,
    which is the appropriate measure for ordinal/interval rating data with
    multiple raters.

    Args:
        ratings_matrix: A list of lists where each inner list contains the
            ratings from all raters for a single item.  Shape is
            (n_items, n_raters).  All inner lists must have the same length.

    Returns:
        The alpha coefficient as a float.  1.0 indicates perfect agreement,
        0.0 indicates agreement at chance level, and negative values
        indicate systematic disagreement.
    """
    n_items = len(ratings_matrix)
    if n_items == 0:
        return 0.0

    n_raters = len(ratings_matrix[0])
    if n_raters < 2:
        return 1.0

    # Collect all observed values
    all_values: list[float] = []
    for row in ratings_matrix:
        all_values.extend(row)

    total_n = len(all_values)
    if total_n == 0:
        return 0.0

    grand_mean = sum(all_values) / total_n

    # Compute observed disagreement (Do)
    # For interval data: Do = sum over all pairs within each unit of (v_i - v_j)^2
    # divided by (n_raters * (n_raters - 1) * n_items)
    observed_disagreement = 0.0
    pair_count = 0
    for row in ratings_matrix:
        for i in range(len(row)):
            for j in range(i + 1, len(row)):
                observed_disagreement += (row[i] - row[j]) ** 2
                pair_count += 1

    if pair_count == 0:
        return 1.0

    do = observed_disagreement / pair_count

    # Compute expected disagreement (De)
    # For interval data: De = variance of all observed values
    # = sum of (v - grand_mean)^2 / (total_n - 1)
    if total_n <= 1:
        return 1.0

    variance_sum = sum((v - grand_mean) ** 2 for v in all_values)
    de = variance_sum / (total_n - 1)

    if de == 0.0:
        # All values are identical -- perfect agreement by convention
        return 1.0

    alpha = 1.0 - (do / de)
    return float(alpha)


def mean_rating(dataset: list[dict[str, Any]]) -> float:
    """Compute the grand mean rating across all entries, raters, and dimensions.

    Args:
        dataset: List of evaluation entries, each containing a 'ratings' list
            with dicts having 'musicality', 'style_match', 'fit_to_melody'.

    Returns:
        The overall mean rating as a float.
    """
    total = 0.0
    count = 0
    for entry in dataset:
        for rating in entry["ratings"]:
            for dim in ("musicality", "style_match", "fit_to_melody"):
                total += rating[dim]
                count += 1

    if count == 0:
        return 0.0

    return total / count


def per_style_ratings(
    dataset: list[dict[str, Any]],
) -> dict[str, dict[str, float]]:
    """Compute average ratings broken down by style.

    Args:
        dataset: List of evaluation entries with 'style' and 'ratings' fields.

    Returns:
        A dictionary keyed by style name.  Each value is a dict with keys
        'musicality', 'style_match', 'fit_to_melody' (float averages) and
        'count' (int number of entries for that style).
    """
    accumulators: dict[str, dict[str, float]] = defaultdict(
        lambda: {
            "musicality": 0.0,
            "style_match": 0.0,
            "fit_to_melody": 0.0,
            "rating_count": 0.0,
            "count": 0.0,
        }
    )

    for entry in dataset:
        style = entry["style"]
        accumulators[style]["count"] += 1
        for rating in entry["ratings"]:
            accumulators[style]["musicality"] += rating["musicality"]
            accumulators[style]["style_match"] += rating["style_match"]
            accumulators[style]["fit_to_melody"] += rating["fit_to_melody"]
            accumulators[style]["rating_count"] += 1

    result: dict[str, dict[str, float]] = {}
    for style, acc in accumulators.items():
        n = acc["rating_count"]
        if n == 0:
            continue
        result[style] = {
            "musicality": acc["musicality"] / n,
            "style_match": acc["style_match"] / n,
            "fit_to_melody": acc["fit_to_melody"] / n,
            "count": int(acc["count"]),
        }

    return result
