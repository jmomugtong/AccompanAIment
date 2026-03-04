"""Tests for observability: Prometheus metrics and OpenTelemetry setup."""

import pytest
from prometheus_client import CollectorRegistry

from src.observability.metrics import (
    API_REQUESTS_TOTAL,
    CELERY_TASKS_TOTAL,
    GENERATION_LATENCY,
    MELODY_EXTRACTION_DURATION,
    MUSICIAN_RATING,
    create_metrics,
)
from src.observability.telemetry import setup_telemetry


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def registry():
    """Create a fresh Prometheus registry for isolated tests."""
    return CollectorRegistry()


@pytest.fixture
def metrics(registry):
    """Create a fresh set of metrics bound to an isolated registry."""
    return create_metrics(registry)


# ---------------------------------------------------------------------------
# Tests: Metric creation
# ---------------------------------------------------------------------------

class TestMetricCreation:
    """Test that Prometheus metrics are properly defined."""

    def test_create_metrics_returns_dict(self, metrics):
        """create_metrics should return a dictionary of metric objects."""
        assert isinstance(metrics, dict)

    def test_melody_extraction_duration_exists(self, metrics):
        """Melody extraction duration histogram should be created."""
        assert "melody_extraction_duration" in metrics

    def test_generation_latency_exists(self, metrics):
        """Generation latency histogram should be created."""
        assert "generation_latency" in metrics

    def test_musician_rating_exists(self, metrics):
        """Musician rating histogram should be created."""
        assert "musician_rating" in metrics

    def test_api_requests_total_exists(self, metrics):
        """API requests total counter should be created."""
        assert "api_requests_total" in metrics

    def test_celery_tasks_total_exists(self, metrics):
        """Celery tasks total counter should be created."""
        assert "celery_tasks_total" in metrics


# ---------------------------------------------------------------------------
# Tests: Counter increments
# ---------------------------------------------------------------------------

class TestCounterIncrements:
    """Test that counters increment correctly."""

    def test_api_requests_counter_increments(self, metrics):
        """API requests counter should increment by 1."""
        counter = metrics["api_requests_total"]
        counter.labels(method="GET", endpoint="/health", status="200").inc()
        val = counter.labels(method="GET", endpoint="/health", status="200")._value.get()
        assert val == 1.0

    def test_api_requests_counter_increments_multiple(self, metrics):
        """Counter should accumulate multiple increments."""
        counter = metrics["api_requests_total"]
        counter.labels(method="POST", endpoint="/songs/upload", status="202").inc()
        counter.labels(method="POST", endpoint="/songs/upload", status="202").inc()
        counter.labels(method="POST", endpoint="/songs/upload", status="202").inc()
        val = counter.labels(method="POST", endpoint="/songs/upload", status="202")._value.get()
        assert val == 3.0

    def test_celery_tasks_counter_increments(self, metrics):
        """Celery tasks counter should increment."""
        counter = metrics["celery_tasks_total"]
        counter.labels(task_name="melody_extraction", status="success").inc()
        val = counter.labels(task_name="melody_extraction", status="success")._value.get()
        assert val == 1.0

    def test_different_labels_are_independent(self, metrics):
        """Different label combinations should be tracked independently."""
        counter = metrics["api_requests_total"]
        counter.labels(method="GET", endpoint="/health", status="200").inc()
        counter.labels(method="POST", endpoint="/songs/upload", status="400").inc()
        counter.labels(method="POST", endpoint="/songs/upload", status="400").inc()

        get_val = counter.labels(method="GET", endpoint="/health", status="200")._value.get()
        post_val = counter.labels(method="POST", endpoint="/songs/upload", status="400")._value.get()

        assert get_val == 1.0
        assert post_val == 2.0


# ---------------------------------------------------------------------------
# Tests: Histogram observations
# ---------------------------------------------------------------------------

class TestHistogramObservations:
    """Test that histograms record observations correctly."""

    def test_melody_extraction_duration_observe(self, metrics):
        """Melody extraction histogram should accept observations."""
        histogram = metrics["melody_extraction_duration"]
        histogram.labels(model="crepe").observe(2.5)
        histogram.labels(model="crepe").observe(3.1)
        # Check that the sum reflects our observations
        sample = histogram.labels(model="crepe")._sum.get()
        assert sample == pytest.approx(5.6, abs=0.01)

    def test_generation_latency_observe(self, metrics):
        """Generation latency histogram should record values."""
        histogram = metrics["generation_latency"]
        histogram.labels(style="jazz").observe(1.2)
        sample = histogram.labels(style="jazz")._sum.get()
        assert sample == pytest.approx(1.2, abs=0.01)

    def test_musician_rating_observe(self, metrics):
        """Musician rating histogram should record rating values."""
        histogram = metrics["musician_rating"]
        histogram.labels(style="pop", dimension="musicality").observe(4.5)
        histogram.labels(style="pop", dimension="musicality").observe(3.0)
        sample = histogram.labels(style="pop", dimension="musicality")._sum.get()
        assert sample == pytest.approx(7.5, abs=0.01)

    def test_histogram_count_tracks_observations(self, metrics):
        """Histogram count should match the number of observations."""
        histogram = metrics["melody_extraction_duration"]
        histogram.labels(model="crepe").observe(1.0)
        histogram.labels(model="crepe").observe(2.0)
        histogram.labels(model="crepe").observe(3.0)
        # Extract count from child samples
        samples = histogram.labels(model="crepe")._child_samples()
        count_sample = [s for s in samples if s.name == "_count"]
        assert len(count_sample) == 1
        assert count_sample[0].value == 3.0

    def test_generation_latency_multiple_styles(self, metrics):
        """Different style labels should accumulate independently."""
        histogram = metrics["generation_latency"]
        histogram.labels(style="jazz").observe(1.0)
        histogram.labels(style="classical").observe(2.0)
        histogram.labels(style="jazz").observe(1.5)

        jazz_sum = histogram.labels(style="jazz")._sum.get()
        classical_sum = histogram.labels(style="classical")._sum.get()

        assert jazz_sum == pytest.approx(2.5, abs=0.01)
        assert classical_sum == pytest.approx(2.0, abs=0.01)


# ---------------------------------------------------------------------------
# Tests: Module-level metric singletons
# ---------------------------------------------------------------------------

class TestModuleLevelMetrics:
    """Test that module-level metric singletons are accessible."""

    def test_melody_extraction_duration_is_histogram(self):
        """Module-level MELODY_EXTRACTION_DURATION should be a Histogram."""
        assert MELODY_EXTRACTION_DURATION is not None

    def test_generation_latency_is_histogram(self):
        """Module-level GENERATION_LATENCY should be a Histogram."""
        assert GENERATION_LATENCY is not None

    def test_musician_rating_is_histogram(self):
        """Module-level MUSICIAN_RATING should be a Histogram."""
        assert MUSICIAN_RATING is not None

    def test_api_requests_total_is_counter(self):
        """Module-level API_REQUESTS_TOTAL should be a Counter."""
        assert API_REQUESTS_TOTAL is not None

    def test_celery_tasks_total_is_counter(self):
        """Module-level CELERY_TASKS_TOTAL should be a Counter."""
        assert CELERY_TASKS_TOTAL is not None


# ---------------------------------------------------------------------------
# Tests: OpenTelemetry setup
# ---------------------------------------------------------------------------

class TestTelemetrySetup:
    """Test basic OpenTelemetry initialization."""

    def test_setup_telemetry_returns_provider(self):
        """setup_telemetry should return a TracerProvider."""
        provider = setup_telemetry(service_name="test-service")
        assert provider is not None

    def test_setup_telemetry_creates_tracer(self):
        """The returned provider should be able to create a tracer."""
        provider = setup_telemetry(service_name="test-service")
        tracer = provider.get_tracer("test-tracer")
        assert tracer is not None

    def test_setup_telemetry_with_custom_name(self):
        """setup_telemetry should accept a custom service name."""
        provider = setup_telemetry(service_name="accompanAIment-backend")
        assert provider is not None

    def test_tracer_can_start_span(self):
        """A tracer from the provider should be able to start a span."""
        provider = setup_telemetry(service_name="test-service")
        tracer = provider.get_tracer("test-tracer")
        with tracer.start_as_current_span("test-span") as span:
            assert span is not None
            assert span.is_recording()
