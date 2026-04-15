import os
import time

from fastapi import Depends, HTTPException, Request, status

try:
    from redis.asyncio import Redis, from_url
except ModuleNotFoundError:  # pragma: no cover
    Redis = object  # type: ignore[assignment,misc]

    def from_url(*args, **kwargs):  # type: ignore[no-redef]
        return None

from services.auth_service import get_current_user

RATE_LIMITS = {
    "anonymous": (2, 60),
    "authenticated": (10, 60),
}

_redis_client = from_url(
    os.getenv("REDIS_URL", "redis://redis:6379/0"),
    encoding="utf-8",
    decode_responses=True,
)


async def get_redis() -> Redis:
    if _redis_client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Rate limiter is unavailable",
        )
    return _redis_client


async def rate_limit(request: Request, user_id: str | None, redis_client: Redis) -> None:
    identity = user_id or (request.client.host if request.client else "unknown")
    limit_type = "authenticated" if user_id else "anonymous"
    limit, period = RATE_LIMITS[limit_type]

    key = f"rate_limit:{limit_type}:{identity}:{request.url.path}"
    now = int(time.time())
    window_start = now - period

    await redis_client.zremrangebyscore(key, min=0, max=window_start)
    request_count = await redis_client.zcard(key)

    if request_count >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests",
        )

    member = f"{now}:{time.time_ns()}"
    await redis_client.zadd(key, {member: now})
    await redis_client.expire(key, period)


async def rate_limit_anonymous(
    request: Request,
    redis_client: Redis = Depends(get_redis),
) -> None:
    await rate_limit(request=request, user_id=None, redis_client=redis_client)


async def rate_limit_authenticated(
    request: Request,
    user_id: str = Depends(get_current_user),
    redis_client: Redis = Depends(get_redis),
) -> None:
    await rate_limit(request=request, user_id=user_id, redis_client=redis_client)
