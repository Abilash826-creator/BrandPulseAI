import logging
import sys
from contextvars import ContextVar
from typing import Optional

# Context variable to track request ID across async tasks
request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


def get_request_id() -> str:
    return request_id_var.get()


def set_request_id(req_id: str):
    request_id_var.set(req_id)


class RequestIdFilter(logging.Filter):
    """
    Injects request_id from contextvar into every log record.
    """
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        return True


def setup_logging(level: int = logging.INFO):
    """
    Configures structured root logging with timestamp, level, request_id, and logger name.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Avoid adding duplicate handlers if already configured
    if not any(isinstance(f, RequestIdFilter) for h in root_logger.handlers for f in h.filters):
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [request_id=%(request_id)s] [%(name)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        handler.addFilter(RequestIdFilter())
        
        # Replace existing handlers
        root_logger.handlers = [handler]
    else:
        for handler in root_logger.handlers:
            if not any(isinstance(f, RequestIdFilter) for f in handler.filters):
                handler.addFilter(RequestIdFilter())


logger = logging.getLogger("brandpulse")
