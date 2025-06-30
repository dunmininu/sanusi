import traceback
from rest_framework.response import Response
from rest_framework.views import exception_handler
from loguru import logger
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode


class CustomException(Exception):
    """Base custom exception class"""

    def __init__(
        self,
        message: str,
        error_code: str = None,
        status_code: int = 400,
        extra_data: dict = None,
    ):
        self.message = message
        self.error_code = error_code or "GENERIC_ERROR"
        self.status_code = status_code
        self.extra_data = extra_data or {}
        super().__init__(self.message)


class ValidationException(CustomException):
    """Custom validation exception"""

    def __init__(self, message: str, field: str = None, **kwargs):
        kwargs.setdefault("error_code", "VALIDATION_ERROR")
        kwargs.setdefault("status_code", 400)
        if field:
            kwargs.setdefault("extra_data", {}).update({"field": field})
        super().__init__(message, **kwargs)


class LogicException(CustomException):
    """Custom logic exception"""

    def __init__(self, message: str, **kwargs):
        kwargs.setdefault("error_code", "LOGIC_ERROR")
        kwargs.setdefault("status_code", 422)
        super().__init__(message, **kwargs)


class ErrorHandler:
    """Centralized error handler with logging and telemetry"""

    @staticmethod
    def log_and_raise(
        message: str,
        exception_class: type = ValidationException,
        error_code: str = None,
        status_code: int = None,
        extra_data: dict = None,
        log_level: str = "warning",
        **kwargs,
    ):
        """
        Log error and raise custom exception

        Args:
            message: Error message
            exception_class: Exception class to raise
            error_code: Custom error code
            status_code: HTTP status code
            extra_data: Additional data to include
            log_level: Logging level (debug, info, warning, error, critical)
            **kwargs: Additional arguments for exception
        """
        tracer = trace.get_tracer(__name__)  # noqa: F841
        span = trace.get_current_span()

        # Prepare exception data
        exception_kwargs = {}
        if error_code:
            exception_kwargs["error_code"] = error_code
        if status_code:
            exception_kwargs["status_code"] = status_code
        if extra_data:
            exception_kwargs["extra_data"] = extra_data
        exception_kwargs.update(kwargs)

        # Create exception instance
        exc = exception_class(message, **exception_kwargs)

        # Log the error
        log_data = {
            "error_message": message,
            "error_code": exc.error_code,
            "status_code": exc.status_code,
            "extra_data": exc.extra_data,
            "traceback": traceback.format_stack(),
        }

        # Use appropriate log level
        log_method = getattr(logger, log_level.lower(), logger.warning)
        log_method(f"Error occurred: {message}", **log_data)

        # Add telemetry data
        if span.is_recording():
            span.set_status(Status(StatusCode.ERROR, message))
            span.set_attribute("error.type", exc.__class__.__name__)
            span.set_attribute("error.message", message)
            span.set_attribute("error.code", exc.error_code)
            span.set_attribute("http.status_code", exc.status_code)

            # Add extra data as attributes
            for key, value in exc.extra_data.items():
                span.set_attribute(f"error.extra.{key}", str(value))

        # Raise the exception
        raise exc

    @staticmethod
    def validation_error(message: str, field: str = None, **kwargs):
        """Shortcut for validation errors"""
        ErrorHandler.log_and_raise(
            message=message,
            exception_class=ValidationException,
            field=field,
            log_level="warning",
            **kwargs,
        )

    @staticmethod
    def login_error(message: str, **kwargs):
        """Shortcut for logic errors"""
        ErrorHandler.log_and_raise(
            message=message, exception_class=LogicException, log_level="error", **kwargs
        )


def custom_exception_handler(exc, context):
    """Custom DRF exception handler"""
    tracer = trace.get_tracer(__name__)

    with tracer.start_as_current_span("exception_handler") as span:
        # Handle custom exceptions
        if isinstance(exc, CustomException):
            span.set_attribute("exception.custom", True)
            span.set_attribute("exception.code", exc.error_code)

            logger.error(
                f"Custom exception handled: {exc.message}",
                error_code=exc.error_code,
                status_code=exc.status_code,
                extra_data=exc.extra_data,
                view=context.get("view").__class__.__name__ if context.get("view") else None,
                request_path=context.get("request").path if context.get("request") else None,
            )

            return Response(
                {
                    "error": {
                        "message": exc.message,
                        "code": exc.error_code,
                        "details": exc.extra_data,
                    }
                },
                status=exc.status_code,
            )

        # Call DRF's default exception handler
        response = exception_handler(exc, context)

        if response is not None:
            # Log DRF exceptions
            span.set_attribute("exception.custom", False)
            span.set_attribute("exception.type", exc.__class__.__name__)

            logger.error(
                f"DRF exception handled: {str(exc)}",
                exception_type=exc.__class__.__name__,
                status_code=response.status_code,
                response_data=response.data,
                view=context.get("view").__class__.__name__ if context.get("view") else None,
                request_path=context.get("request").path if context.get("request") else None,
            )

            # Customize response format
            custom_response_data = {
                "error": {
                    "message": "An error occurred",
                    "code": "DRF_ERROR",
                    "details": response.data,
                }
            }
            response.data = custom_response_data

        return response
