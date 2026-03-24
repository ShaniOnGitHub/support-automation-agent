import logging
import uuid
from contextvars import ContextVar
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.core.config import settings

# Context variable to store request ID
request_id_context: ContextVar[str] = ContextVar("request_id", default="N/A")

class RequestIdFilter(logging.Filter):
    def filter(self, record):
        record.request_id = request_id_context.get()
        return True

class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_id = str(uuid.uuid4())
        request_id_context.set(request_id)
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

def configure_logging():
    logging.basicConfig(
        level=settings.LOG_LEVEL,
        format="%(asctime)s - %(name)s - %(levelname)s - [Request ID: %(request_id)s] - %(message)s",
    )
    # Add filter to root logger
    logging.getLogger().addFilter(RequestIdFilter())
    # Also add to uvicorn loggers if needed, though basicConfig covers root
    # For uvicorn specifically, we might want to propagate or attach filters
    for logger_name in ["uvicorn", "uvicorn.access", "uvicorn.error"]:
        logger = logging.getLogger(logger_name)
        logger.addFilter(RequestIdFilter())

