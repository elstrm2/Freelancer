import redis.asyncio as aioredis
from config.settings import REDIS_SETTINGS

redis = aioredis.from_url(
    f"redis://{REDIS_SETTINGS['host']}:{REDIS_SETTINGS['port']}",
    encoding="utf-8",
    decode_responses=True,
)
