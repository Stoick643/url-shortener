import time
from collections import defaultdict

from fastapi import HTTPException, Request, status

from app.config import settings

# In-memory store: IP -> list of request timestamps
_requests: dict[str, list[float]] = defaultdict(list)


def check_rate_limit(request: Request) -> None:
    """Dependency: enforce rate limit on the caller's IP."""
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    window = settings.RATE_LIMIT_WINDOW_SECONDS

    # Prune old timestamps
    _requests[client_ip] = [
        ts for ts in _requests[client_ip] if now - ts < window
    ]

    if len(_requests[client_ip]) >= settings.RATE_LIMIT_REQUESTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Try again later.",
        )

    _requests[client_ip].append(now)


def reset_rate_limits() -> None:
    """Reset all rate limit data. Useful for testing."""
    _requests.clear()
