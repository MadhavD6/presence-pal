import structlog
import logging
import sys

from backend.core.trace import get_request_id

def add_request_id(logger, method_name, event_dict):
    """Add the request_id to the event dict."""
    req_id = get_request_id()
    if req_id and req_id != "unknown":
        event_dict["request_id"] = req_id
    return event_dict

def configure_logger():
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
        force=True, # access to root logger
    )

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            add_request_id, # Add Trace ID
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

logger = structlog.get_logger()
