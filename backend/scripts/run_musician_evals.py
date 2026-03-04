"""CLI script to run musician evaluations on accompaniment datasets.

Usage:
    python scripts/run_musician_evals.py --eval-set 50
    python scripts/run_musician_evals.py --dataset-path datasets/accompaniments_50.json
    python scripts/run_musician_evals.py --help
"""

import argparse
import json
import os
import sys

# Allow running from the backend/ directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.evals.dataset import load_dataset, validate_dataset
from src.evals.report_generator import generate_report


DEFAULT_DATASET_DIR = os.path.join(os.path.dirname(__file__), "..", "datasets")


def parse_args(argv=None):
    """Parse command-line arguments.

    Args:
        argv: Argument list (defaults to sys.argv[1:]).

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="Run musician evaluations on accompaniment datasets.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python scripts/run_musician_evals.py --eval-set 50\n"
            "  python scripts/run_musician_evals.py --dataset-path my_dataset.json\n"
        ),
    )
    parser.add_argument(
        "--eval-set",
        type=int,
        default=50,
        help="Number of accompaniments in the eval set (default: 50). "
        "Looks for datasets/accompaniments_<N>.json.",
    )
    parser.add_argument(
        "--dataset-path",
        type=str,
        default=None,
        help="Explicit path to a dataset JSON file. Overrides --eval-set.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to write the JSON report. If not set, prints to stdout.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed per-style breakdowns.",
    )
    return parser.parse_args(argv)


def resolve_dataset_path(args):
    """Determine the dataset file path from parsed arguments.

    Args:
        args: Parsed argparse namespace.

    Returns:
        Absolute path to the dataset file.
    """
    if args.dataset_path:
        return os.path.abspath(args.dataset_path)
    filename = f"accompaniments_{args.eval_set}.json"
    return os.path.abspath(os.path.join(DEFAULT_DATASET_DIR, filename))


def main(argv=None):
    """Entry point for the evaluation runner.

    Args:
        argv: Optional argument list for testing.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    args = parse_args(argv)
    dataset_path = resolve_dataset_path(args)

    print(f"Loading dataset from: {dataset_path}")

    try:
        dataset = load_dataset(dataset_path)
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    errors = validate_dataset(dataset)
    if errors:
        print("Dataset validation errors:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print(f"Dataset loaded: {len(dataset)} entries")

    report = generate_report(dataset)

    print("\n--- Evaluation Report ---")
    print(f"Total entries evaluated: {report['total_entries']}")
    print(f"Overall mean rating: {report['overall_mean']:.3f}")

    print("\nDimension means:")
    for dim, val in report["dimension_means"].items():
        print(f"  {dim}: {val:.3f}")

    print("\nInterrater agreement (Kramer's alpha):")
    for dim, val in report["kramers_alpha"].items():
        print(f"  {dim}: {val:.4f}")

    if args.verbose:
        print("\nPer-style breakdown:")
        for style, stats in report["per_style"].items():
            print(f"\n  {style} (n={stats['count']}):")
            print(f"    musicality:    {stats['musicality']:.3f}")
            print(f"    style_match:   {stats['style_match']:.3f}")
            print(f"    fit_to_melody: {stats['fit_to_melody']:.3f}")

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"\nReport written to: {args.output}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
