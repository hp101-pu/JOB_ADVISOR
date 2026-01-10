"""
flush_chat_history.py
Run from project root with venv activated:
    python flush_chat_history.py
"""
import redis

r = redis.Redis(host="localhost", port=6380, decode_responses=True)
r.ping()
print("Connected to Redis")

keys = r.keys("seekr:conversation:*")
if keys:
    r.delete(*keys)
    print(f"Deleted {len(keys)} poisoned conversation key(s):")
    for k in keys:
        print(f"  - {k}")
else:
    print("No conversation keys found.")

print("Done.")
