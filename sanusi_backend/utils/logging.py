
import sys
from django.conf import settings
from loguru import logger
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.django import DjangoInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter, SimpleSpanProcessor
from opentelemetry.sdk.resources import Resource, SERVICE_NAME


def setup_logging():
    """Configure Loguru logging"""
    # Remove default handler
    logger.remove()
    
    # Add console handler with custom format
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>",
        level="INFO",
        colorize=True,
        serialize=False
    )
    
    # Add file handler for errors
    logger.add(
        "logs/error.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        level="ERROR",
        rotation="10 MB",
        retention="30 days",
        compression="gz"
    )
    
    # Add structured JSON log file
    logger.add(
        "logs/app.json",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        level="INFO",
        rotation="50 MB",
        retention="30 days",
        serialize=True  # JSON format
    )


def setup_telemetry():
    """Configure OpenTelemetry"""
    try:
        # Set up the tracer provider
        resource = Resource.create({SERVICE_NAME: "sanusi-api"})
        tracer_provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(tracer_provider)
        print("✅ Tracer provider set up")
        
        # Configure Jaeger exporter
        # jaeger_exporter = JaegerExporter(
        #     agent_host_name="localhost",
        #     agent_port=6831,
        #     # Add timeout to prevent hangs
        #     timeout=5000,  # 5 seconds
        # )
        jaeger_exporter = JaegerExporter(
            collector_endpoint="http://localhost:14268/api/traces",
            timeout=5000,  # 5 seconds
        )
        print("✅ Jaeger exporter configured")
        
        # Add batch processor with debug options
        span_processor = BatchSpanProcessor(
            jaeger_exporter,
            max_queue_size=1000,
            schedule_delay_millis=5000,
        )
        trace.get_tracer_provider().add_span_processor(span_processor)
        print("✅ Batch span processor added")

         # Add console exporter for local debugging
        if settings.DEBUG:  # Only in development
            console_processor = SimpleSpanProcessor(ConsoleSpanExporter())
            tracer_provider.add_span_processor(console_processor)
            print("✅ Console exporter added for debugging")
        
        # Auto-instrument Django
        DjangoInstrumentor().instrument()
        
        # Auto-instrument database calls
        Psycopg2Instrumentor().instrument()
        
        # Auto-instrument HTTP requests
        RequestsInstrumentor().instrument()
        print("✅ All instrumentations complete")
        
        print("🚀 Telemetry setup complete!")
    except Exception as e:
        print(f"🔥 Telemetry setup failed: {str(e)}")
        import traceback
        traceback.print_exc()