import contextvars
from typing import Optional
import uuid

# Context variable to hold the Request ID
request_id_ctx_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "request_id", default=None
)

def get_request_id() -> str:
    """
    Get the current request ID from context. 
    If none exists, it implicitly returns 'unknown' or handles gracefully in logger.
    """
    return request_id_ctx_var.get() or "unknown"
