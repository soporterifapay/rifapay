"""Rate limit en memoria (sin dependencias): ventana deslizante por IP."""
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request

_hits: dict[str, deque] = defaultdict(deque)
WINDOW = 60.0


def _client_ip(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for", "")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "?"


def limit(request: Request, max_hits: int, scope: str = "") -> None:
    now = time.monotonic()
    key = f"{scope}:{_client_ip(request)}"
    q = _hits[key]
    while q and now - q[0] > WINDOW:
        q.popleft()
    if len(q) >= max_hits:
        raise HTTPException(429, "Demasiados intentos, esperá un minuto")
    q.append(now)


def limit_orders(request: Request) -> None:
    limit(request, 20, "orders")


def limit_auth(request: Request) -> None:
    limit(request, 10, "auth")


def limit_upload(request: Request) -> None:
    limit(request, 10, "upload")
