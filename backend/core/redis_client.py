import redis
from .config import settings

redis_client = redis.from_url(
    settings.redis_url,
    decode_responses=True,
    socket_connect_timeout=5,
    socket_keepalive=True
)

def get_redis():
    return redis_client
