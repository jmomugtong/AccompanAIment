"""FastAPI middleware for request logging and rate limiting."""

import logging
import time
from collections import defaultdict
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs HTTP method, path, status code, and response duration for every request.

    Example log line:
        GET /songs/upload 200 12.34ms
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request, measure duration, and log the result.

        Args:
            request: The incoming HTTP request.
            call_next: The next middleware/route handler.

        Returns:
            The HTTP response.
        """
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000.0

        logger.info(
            "%s %s %d %.2fms",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiter by client IP address.

    Tracks request counts per IP within a sliding window. When a client
    exceeds the configured maximum, the middleware returns 429 Too Many
    Requests with a Retry-After header.

    Args:
        app: The ASGI application.
        max_requests: Maximum number of requests allowed per window.
        window_seconds: Length of the rate-limit window in seconds.
    """

    def __init__(
        self,
        app: object,
        max_requests: int = 60,
        window_seconds: int = 60,
    ) -> None:
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # Maps IP -> list of request timestamps
        self._requests: dict[str, list[float]] = defaultdict(list)

    def _get_client_ip(self, request: Request) -> str:
        """Extract the client IP address from the request.

        Args:
            request: The incoming HTTP request.

        Returns:
            The client IP address as a string.
        """
        if request.client is not None:
            return request.client.host
        return "unknown"

    def _cleanup_old_requests(self, ip: str, now: float) -> None:
        """Remove request timestamps that fall outside the current window.

        Args:
            ip: The client IP address.
            now: The current time as a float (seconds since epoch).
        """
        cutoff = now - self.window_seconds
        self._requests[ip] = [
            ts for ts in self._requests[ip] if ts > cutoff
        ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check rate limit before forwarding the request.

        Args:
            request: The incoming HTTP request.
            call_next: The next middleware/route handler.

        Returns:
            The HTTP response, or a 429 response if the limit is exceeded.
        """
        ip = self._get_client_ip(request)
        now = time.time()

        self._cleanup_old_requests(ip, now)

        if len(self._requests[ip]) >= self.max_requests:
            # Calculate how long until the oldest request expires
            oldest = self._requests[ip][0]
            retry_after = int(self.window_seconds - (now - oldest)) + 1
            retry_after = max(retry_after, 1)

            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please try again later."},
                headers={"retry-after": str(retry_after)},
            )

        self._requests[ip].append(now)
        response = await call_next(request)
        return response
