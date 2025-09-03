# app/middleware/rate_limit.py
import os
from fastapi.responses import JSONResponse

try:
    # Camino normal: usar starlette-limiter + Redis
    from starlette_limiter import Limiter, RateLimitExceeded, default_identifier

    REDIS_URI = os.environ.get("REDIS_URL", "redis://redis:6379/0")
    limiter = Limiter(
        key_func=default_identifier,
        storage_uri=REDIS_URI,
        strategy="moving-window",
    )

    def rate_limited(rule: str):
        # Uso por decorator: @rate_limited("20/minute")
        return limiter.limit(rule)

    async def rate_limit_handler(request, exc: RateLimitExceeded):
        return JSONResponse({"detail": "Too many requests"}, status_code=429)

except Exception:
    # Fallback: si no está la lib o Redis, NO rompemos el arranque.
    class _NoopLimiter:
        async def init(self, app):
            pass

        def limit(self, rule: str):
            def _wrap(func):
                return func
            return _wrap

    limiter = _NoopLimiter()

    def rate_limited(rule: str):
        def _wrap(func):
            return func
        return _wrap

    async def rate_limit_handler(request, exc):
        return JSONResponse({"detail": "Too many requests"}, status_code=429)
