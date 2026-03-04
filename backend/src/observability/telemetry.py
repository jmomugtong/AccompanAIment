"""Basic OpenTelemetry setup for the AccompanAIment backend.

Provides a setup_telemetry function that initializes a TracerProvider
with an in-memory span exporter suitable for development and testing.
For production, swap in an OTLP exporter targeting your collector.
"""

from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter


def setup_telemetry(
    service_name: str = "accompanAIment-backend",
) -> TracerProvider:
    """Initialize and return an OpenTelemetry TracerProvider.

    Creates a TracerProvider configured with an in-memory exporter.
    In production, replace the exporter with an OTLP exporter pointing
    at your OpenTelemetry Collector or observability backend.

    Args:
        service_name: The logical name of this service, used in traces.

    Returns:
        A configured TracerProvider instance.
    """
    resource = Resource.create({"service.name": service_name})

    provider = TracerProvider(resource=resource)

    # In-memory exporter for development/testing.
    # Replace with OTLPSpanExporter for production.
    exporter = InMemorySpanExporter()
    processor = SimpleSpanProcessor(exporter)
    provider.add_span_processor(processor)

    return provider
