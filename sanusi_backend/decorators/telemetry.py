from functools import wraps
from opentelemetry import trace
from loguru import logger

def with_telemetry(span_name, sensitive_keys=None):
    """
    Decorator for adding telemetry to Django view methods.
    
    Args:
        span_name (str): Name for the telemetry span
        sensitive_keys (list): Keys to exclude from request data logging
    """
    if sensitive_keys is None:
        sensitive_keys = ['password', 'token', 'secret', 'key', 'access', 'refresh']
    
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(self, request, *args, **kwargs):
            tracer = trace.get_tracer(__name__)
            with tracer.start_as_current_span(span_name) as span:
                try:
                    # Set common attributes
                    span.set_attributes({
                        "user.id": str(request.user.id),
                        "user.email": request.user.email,
                        "request.path": request.path,
                        "request.method": request.method
                    })
                    
                    # Log safe request data keys
                    safe_data = {k: v for k, v in request.data.items() 
                                 if k not in sensitive_keys}
                    span.set_attribute("request.data_keys", list(safe_data.keys()))
                    
                    # Execute the view function
                    return view_func(self, request, *args, current_span=span, **kwargs)
                
                except Exception as e:
                    # Handle errors
                    span.set_attributes({
                        "operation.success": False,
                        "error.type": type(e).__name__,
                        "error.unexpected": True
                    })
                    raise
                finally:
                    # Ensure traces are flushed
                    try:
                        trace.get_tracer_provider().force_flush()
                    except Exception as flush_error:
                        logger.error(f"Failed to flush traces: {str(flush_error)}")
        return wrapper
    return decorator