"""Evaluation orchestration for musician rating datasets.

The MusicianEvaluator class wraps the metrics and report_generator
modules, providing a single entry point for running evaluations and
checking quality thresholds.
"""

import logging
from typing import Any

from src.evals.metrics import kramers_alpha, mean_rating
from src.evals.report_generator import generate_report

logger = logging.getLogger(__name__)


class MusicianEvaluator:
    """Orchestrates musician evaluation: generates a report and checks thresholds.

    Quality gates (from the project spec):
        - Average overall rating > mean_threshold (default 4.0/5)
        - Kramer's alpha > alpha_threshold (default 0.85)

    Args:
        mean_threshold: Minimum acceptable overall mean rating.
        alpha_threshold: Minimum acceptable Kramer's alpha value.
    """

    def __init__(
        self,
        mean_threshold: float = 4.0,
        alpha_threshold: float = 0.85,
    ) -> None:
        self.mean_threshold = mean_threshold
        self.alpha_threshold = alpha_threshold

    def evaluate(self, dataset: list[dict[str, Any]]) -> dict[str, Any]:
        """Run a full evaluation on the given dataset.

        Generates a report using metrics.py and report_generator.py,
        then appends a passes_threshold indicator based on the
        configured quality gates.

        Args:
            dataset: List of evaluation entries, each with 'ratings'
                containing per-rater scores for musicality, style_match,
                and fit_to_melody.

        Returns:
            A report dictionary with all fields from generate_report,
            plus:
              - passes_threshold (bool): True if the overall mean and
                all Kramer's alpha values meet the configured thresholds.
        """
        if len(dataset) == 0:
            logger.warning("Empty dataset provided for evaluation.")
            return {
                "total_entries": 0,
                "overall_mean": 0.0,
                "dimension_means": {},
                "kramers_alpha": {},
                "per_style": {},
                "passes_threshold": False,
            }

        report = generate_report(dataset)

        # Check thresholds
        mean_passes = report["overall_mean"] >= self.mean_threshold

        alpha_passes = True
        for dim, alpha_val in report["kramers_alpha"].items():
            if alpha_val < self.alpha_threshold:
                alpha_passes = False
                logger.info(
                    "Kramer's alpha for '%s' (%.3f) below threshold (%.3f)",
                    dim,
                    alpha_val,
                    self.alpha_threshold,
                )

        passes = mean_passes and alpha_passes
        report["passes_threshold"] = passes

        logger.info(
            "Evaluation complete: overall_mean=%.3f, passes=%s",
            report["overall_mean"],
            passes,
        )

        return report
