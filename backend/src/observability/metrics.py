"""Prometheus metrics for the AccompanAIment backend.

Provides custom metrics for tracking melody extraction duration,
generation latency, musician ratings, API request counts, and
Celery task counts.

Module-level singletons use the default Prometheus registry.
Use create_metrics() with a custom registry for isolated testing.
"""

from prometheus_client import CollectorRegistry, Counter, Histogram


def create_metrics(registry: CollectorRegistry) -> dict:
    """Create a complete set of Prometheus metrics on the given registry.

    Args:
        registry: The Prometheus CollectorRegistry to register metrics on.

    Returns:
        A dictionary mapping metric names to their metric objects.
    """
    melody_extraction_duration = Histogram(
        "melody_extraction_duration_seconds",
        "Duration of melody extraction in seconds",
        labelnames=["model"],
        buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0),
        registry=registry,
    )

    generation_latency = Histogram(
        "generation_latency_seconds",
        "End-to-end latency of piano accompaniment generation in seconds",
        labelnames=["style"],
        buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0),
        registry=registry,
    )

    musician_rating = Histogram(
        "musician_rating",
        "Musician evaluation ratings (1-5 scale)",
        labelnames=["style", "dimension"],
        buckets=(1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0),
        registry=registry,
    )

    api_requests_total = Counter(
        "api_requests_total",
        "Total number of API requests",
        labelnames=["method", "endpoint", "status"],
        registry=registry,
    )

    celery_tasks_total = Counter(
        "celery_tasks_total",
        "Total number of Celery tasks executed",
        labelnames=["task_name", "status"],
        registry=registry,
    )

    return {
        "melody_extraction_duration": melody_extraction_duration,
        "generation_latency": generation_latency,
        "musician_rating": musician_rating,
        "api_requests_total": api_requests_total,
        "celery_tasks_total": celery_tasks_total,
    }


# Module-level singletons (default registry)
# These are imported directly by application code.

MELODY_EXTRACTION_DURATION = Histogram(
    "melody_extraction_duration_seconds",
    "Duration of melody extraction in seconds",
    labelnames=["model"],
    buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0),
)

GENERATION_LATENCY = Histogram(
    "generation_latency_seconds",
    "End-to-end latency of piano accompaniment generation in seconds",
    labelnames=["style"],
    buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0),
)

MUSICIAN_RATING = Histogram(
    "musician_rating",
    "Musician evaluation ratings (1-5 scale)",
    labelnames=["style", "dimension"],
    buckets=(1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0),
)

API_REQUESTS_TOTAL = Counter(
    "api_requests_total",
    "Total number of API requests",
    labelnames=["method", "endpoint", "status"],
)

CELERY_TASKS_TOTAL = Counter(
    "celery_tasks_total",
    "Total number of Celery tasks executed",
    labelnames=["task_name", "status"],
)
