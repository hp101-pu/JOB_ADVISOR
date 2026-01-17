import redis
import os

_r = redis.Redis(
    host="localhost",
    port=6380,
    decode_responses=True,
    socket_connect_timeout=2,
)

redis_client = None

# Try to connect to Redis in non-blocking way
def _try_connect_redis():
    global redis_client
    try:
        _r.ping()
        print("🟢 Redis connected on port 6380")
        redis_client = _r
    except Exception as e:
        print(f"⚠️  Redis unavailable ({e}). Conversation memory disabled — chat still works.")
        redis_client = None

# Only block on startup if REDIS_REQUIRED is set
if os.getenv("REDIS_REQUIRED") == "true":
    _try_connect_redis()
else:
    # Non-blocking: try to connect but don't fail if unavailable
    try:
        _r.ping()
        print("🟢 Redis connected on port 6380")
        redis_client = _r
    except:
        print("⚠️  Redis unavailable (optional). Chat memory disabled but app will still work.")
