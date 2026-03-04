"""Agent fine-tuning script for AccompanAIment LLM agent.

Loads user feedback data from a dataset file and prepares the local
LLM agent for fine-tuning. Currently implements logging and
configuration validation with placeholder hooks for actual training
logic (e.g., LoRA fine-tuning via Ollama or direct model adaptation).
"""

import argparse
import json
import logging
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

SUPPORTED_MODELS = ["mistral", "neural-chat", "llama2", "codellama"]


def load_feedback_dataset(dataset_path: Path) -> list[dict]:
    """Load feedback data from a JSON dataset file.

    Expected format: a JSON array of objects, each containing at minimum
    'generation_id', 'rating', and optionally 'musicality_score',
    'style_match_score', 'fit_to_melody_score', and 'comment'.

    Args:
        dataset_path: Path to the JSON feedback dataset.

    Returns:
        List of feedback records.

    Raises:
        FileNotFoundError: If the dataset file does not exist.
        json.JSONDecodeError: If the file contains invalid JSON.
    """
    logger.info("Loading feedback dataset from '%s'", dataset_path)
    with open(dataset_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("Dataset must be a JSON array of feedback objects")

    logger.info("Loaded %d feedback record(s)", len(data))
    return data


def validate_dataset(records: list[dict]) -> tuple[int, int]:
    """Validate feedback records and count usable entries.

    A record is considered usable if it has a 'rating' field with an
    integer value between 1 and 5.

    Args:
        records: List of feedback record dictionaries.

    Returns:
        Tuple of (valid_count, invalid_count).
    """
    valid = 0
    invalid = 0
    for record in records:
        rating = record.get("rating")
        if isinstance(rating, int) and 1 <= rating <= 5:
            valid += 1
        else:
            invalid += 1
    return valid, invalid


def log_training_config(
    model: str,
    epochs: int,
    dataset_path: Path,
    record_count: int,
    valid_count: int,
) -> None:
    """Log the training configuration summary.

    Args:
        model: Name of the target LLM model.
        epochs: Number of training epochs.
        dataset_path: Path to the feedback dataset.
        record_count: Total number of records in the dataset.
        valid_count: Number of valid (usable) records.
    """
    logger.info("--- Training Configuration ---")
    logger.info("  Model:         %s", model)
    logger.info("  Epochs:        %d", epochs)
    logger.info("  Dataset:       %s", dataset_path)
    logger.info("  Total records: %d", record_count)
    logger.info("  Valid records: %d", valid_count)
    logger.info("------------------------------")


def run_training(
    model: str,
    epochs: int,
    dataset: list[dict],
    dry_run: bool = False,
) -> None:
    """Execute agent fine-tuning (placeholder).

    In production this would:
    1. Filter dataset to high-quality examples (rating >= 4).
    2. Extract the LLM prompts and generated music21 code for each example.
    3. Construct training pairs (prompt, preferred_output) for RLHF or DPO.
    4. Connect to Ollama and push fine-tuning data via the model API.
    5. Run training for the specified number of epochs.
    6. Validate the fine-tuned model against a held-out evaluation set.

    Args:
        model: Target LLM model identifier.
        epochs: Number of training epochs.
        dataset: List of validated feedback records.
        dry_run: If True, log what would happen without executing.
    """
    high_quality = [r for r in dataset if r.get("rating", 0) >= 4]
    low_quality = [r for r in dataset if r.get("rating", 0) <= 2]

    logger.info("High-quality examples (rating >= 4): %d", len(high_quality))
    logger.info("Low-quality examples (rating <= 2):  %d", len(low_quality))

    if dry_run:
        logger.info("DRY-RUN: Would fine-tune '%s' for %d epoch(s)", model, epochs)
        logger.info("DRY-RUN: Would use %d positive and %d negative examples",
                     len(high_quality), len(low_quality))
        logger.info("DRY-RUN: No changes made.")
        return

    # --- Placeholder: actual training logic goes here ---
    logger.info("Starting fine-tuning of '%s'...", model)
    for epoch in range(1, epochs + 1):
        logger.info(
            "  Epoch %d/%d -- processing %d training pairs (placeholder)",
            epoch, epochs, len(high_quality),
        )
    logger.info("Fine-tuning complete (placeholder -- no actual model changes made).")
    logger.info(
        "To implement real training, integrate with Ollama's model creation API "
        "or use a LoRA adapter framework."
    )


def main() -> None:
    """CLI entry point for agent fine-tuning."""
    parser = argparse.ArgumentParser(
        description=(
            "Fine-tune the AccompanAIment LLM agent using user feedback data. "
            "Currently a placeholder that logs configuration and validates data."
        )
    )
    parser.add_argument(
        "--dataset-path",
        type=str,
        required=True,
        help="Path to the JSON feedback dataset file",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="mistral",
        choices=SUPPORTED_MODELS,
        help="Target LLM model to fine-tune (default: mistral)",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=3,
        help="Number of training epochs (default: 3)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Log what would be done without executing training",
    )
    args = parser.parse_args()

    dataset_path = Path(args.dataset_path)
    if not dataset_path.exists():
        logger.error("Dataset file not found: %s", dataset_path)
        sys.exit(1)

    if args.model not in SUPPORTED_MODELS:
        logger.error("Unsupported model: %s. Choose from: %s",
                     args.model, ", ".join(SUPPORTED_MODELS))
        sys.exit(1)

    # Load and validate dataset
    try:
        dataset = load_feedback_dataset(dataset_path)
    except (json.JSONDecodeError, ValueError) as exc:
        logger.error("Failed to load dataset: %s", exc)
        sys.exit(1)

    valid_count, invalid_count = validate_dataset(dataset)
    if invalid_count > 0:
        logger.warning("%d record(s) have invalid or missing ratings", invalid_count)

    if valid_count == 0:
        logger.error("No valid feedback records found. Aborting.")
        sys.exit(1)

    log_training_config(
        model=args.model,
        epochs=args.epochs,
        dataset_path=dataset_path,
        record_count=len(dataset),
        valid_count=valid_count,
    )

    # Run training
    run_training(
        model=args.model,
        epochs=args.epochs,
        dataset=dataset,
        dry_run=args.dry_run,
    )

    logger.info("Done.")


if __name__ == "__main__":
    main()
