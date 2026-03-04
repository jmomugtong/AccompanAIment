"""CI gate script: check that evaluation metrics meet quality thresholds.

Thresholds:
  - Average rating > 4.0 / 5.0
  - Kramer's alpha > 0.85 (all dimensions)

Usage:
    python scripts/check_eval_thresholds.py
    python scripts/check_eval_thresholds.py --dataset-path datasets/accompaniments_50.json
    python scripts/check_eval_thresholds.py --min-rating 4.0 --min-alpha 0.85
    python scripts/check_eval_thresholds.py --help

Exit codes:
    0 - All thresholds met
    1 - One or more thresholds not met
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.evals.dataset import load_dataset, validate_dataset
from src.evals.report_generator import generate_report


DEFAULT_DATASET = os.path.join(
    os.path.dirname(__file__), "..", "datasets", "accompaniments_50.json"
)

DEFAULT_MIN_RATING = 4.0
DEFAULT_MIN_ALPHA = 0.85


def parse_args(argv=None):
    """Parse command-line arguments.

    Args:
        argv: Argument list (defaults to sys.argv[1:]).

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="Check evaluation thresholds for CI gating.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python scripts/check_eval_thresholds.py\n"
            "  python scripts/check_eval_thresholds.py --min-rating 3.5 --min-alpha 0.80\n"
        ),
    )
    parser.add_argument(
        "--dataset-path",
        type=str,
        default=DEFAULT_DATASET,
        help=f"Path to the dataset JSON file (default: {DEFAULT_DATASET}).",
    )
    parser.add_argument(
        "--min-rating",
        type=float,
        default=DEFAULT_MIN_RATING,
        help=f"Minimum required average rating (default: {DEFAULT_MIN_RATING}).",
    )
    parser.add_argument(
        "--min-alpha",
        type=float,
        default=DEFAULT_MIN_ALPHA,
        help=f"Minimum required Kramer's alpha (default: {DEFAULT_MIN_ALPHA}).",
    )
    return parser.parse_args(argv)


def main(argv=None):
    """Entry point for threshold checking.

    Args:
        argv: Optional argument list for testing.

    Returns:
        Exit code (0 = pass, 1 = fail).
    """
    args = parse_args(argv)
    dataset_path = os.path.abspath(args.dataset_path)

    print(f"Loading dataset: {dataset_path}")

    try:
        dataset = load_dataset(dataset_path)
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    errors = validate_dataset(dataset)
    if errors:
        print("Dataset validation failed:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    report = generate_report(dataset)

    passed = True

    # Check overall mean rating
    overall_mean = report["overall_mean"]
    if overall_mean > args.min_rating:
        print(f"[PASS] Overall mean rating: {overall_mean:.3f} > {args.min_rating}")
    else:
        print(f"[FAIL] Overall mean rating: {overall_mean:.3f} <= {args.min_rating}")
        passed = False

    # Check Kramer's alpha per dimension
    for dim, alpha in report["kramers_alpha"].items():
        if alpha > args.min_alpha:
            print(f"[PASS] Kramer's alpha ({dim}): {alpha:.4f} > {args.min_alpha}")
        else:
            print(
                f"[FAIL] Kramer's alpha ({dim}): {alpha:.4f} <= {args.min_alpha}"
            )
            passed = False

    if passed:
        print("\nAll thresholds met. Ready to deploy.")
        return 0
    else:
        print("\nThreshold check FAILED. Blocking deployment.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
