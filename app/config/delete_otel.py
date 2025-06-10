import time

from opentelemetry import metrics as otel_metrics
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Set up resource attributes (service name, etc.)
resource = Resource.create(attributes={"service.name": "otel-python-test"})

# ---- TRACING ----
trace.set_tracer_provider(TracerProvider(resource=resource))
tracer = trace.get_tracer_provider().get_tracer("test-tracer")

otlp_exporter = OTLPSpanExporter(endpoint="http://otel-collector:4317", insecure=True)
span_processor = BatchSpanProcessor(otlp_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

# ---- METRICS ----
metric_reader = PeriodicExportingMetricReader(
    OTLPMetricExporter(endpoint="http://otel-collector:4317", insecure=True),
    export_interval_millis=5000,  # every 5 seconds
)
meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
otel_metrics.set_meter_provider(meter_provider)
meter = otel_metrics.get_meter("test-meter")

# Create a counter metric
counter = meter.create_counter(
    name="demo_counter",
    description="A simple counter metric for testing",
    unit="1",
)

# ---- SEND SOME TRACES AND METRICS ----
with tracer.start_as_current_span("parent-span") as span:
    print("Starting parent span...")
    span.set_attribute("test.attribute", "value")

    # Record some metrics
    for i in range(10):
        counter.add(1, {"iteration": str(i)})
        print(f"Sent metric iteration {i}")
        time.sleep(1)

    # Create a child span
    with tracer.start_as_current_span("child-span") as child:
        child.set_attribute("child.attribute", "value")
        print("Child span active for 2 seconds...")
        time.sleep(2)

print("Test script completed!")
