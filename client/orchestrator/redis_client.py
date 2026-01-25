import redis
import os
import socket

from dotenv import load_dotenv

load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6380"))
REDIS_REQUIRED = os.getenv("REDIS_REQUIRED", "false").lower() == "true"
REDIS_CONNECT_TIMEOUT = float(os.getenv("REDIS_CONNECT_TIMEOUT", "0.5"))

_r = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True,
    socket_connect_timeout=REDIS_CONNECT_TIMEOUT,
    socket_timeout=REDIS_CONNECT_TIMEOUT,
    protocol=2,
)

redis_client = None


def _is_redis_reachable(host: str, port: int, timeout: float) -> bool:
    """Fast raw-socket check to avoid redis-py hanging on unreachable hosts."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception as e:
        print(f"[REDIS] Reachability check failed for {host}:{port} ({e})")
        return False


def _try_connect_redis():
    """Attempt to connect to Redis. Always leaves the app usable, even on failure."""
    global redis_client
    if not _is_redis_reachable(REDIS_HOST, REDIS_PORT, REDIS_CONNECT_TIMEOUT):
        print(f"[REDIS] Unavailable at {REDIS_HOST}:{REDIS_PORT}. Conversation memory disabled - chat still works.")
        redis_client = None
        return

    try:
        _r.ping()
        print(f"[REDIS] Connected on {REDIS_HOST}:{REDIS_PORT}")
        redis_client = _r
    except Exception as e:
        print(f"[REDIS] Unavailable at {REDIS_HOST}:{REDIS_PORT} ({e}). Conversation memory disabled - chat still works.")
        redis_client = None


# Health-check on import. If Redis is required, log it clearly; either way the app keeps running.
mode = "required" if REDIS_REQUIRED else "optional"
print(f"[REDIS] Redis is {mode}; attempting connection to {REDIS_HOST}:{REDIS_PORT}...")
_try_connect_redis()
