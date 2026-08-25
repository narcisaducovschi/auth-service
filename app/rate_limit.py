import redis
from app.config import settings

redis_client = redis.from_url(settings.redis_url, decode_responses=True)

MAX_ATTEMPTS = 5
WINDOW_SECONDS = 60


def check_rate_limit(identifier: str) -> tuple[bool, int]:
    key = f"login_attempts:{identifier}"

    current = redis_client.get(key)

    if current is None:
        redis_client.set(key, 1, ex=WINDOW_SECONDS)
        return True, MAX_ATTEMPTS - 1

    current = int(current)

    if current >= MAX_ATTEMPTS:
        return False, 0

    redis_client.incr(key)
    return True, MAX_ATTEMPTS - current - 1


def reset_rate_limit(identifier: str) -> None:
    key = f"login_attempts:{identifier}"
    redis_client.delete(key)