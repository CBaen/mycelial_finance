# verify_vectordb.py
import redis
import json

# Connect to Redis
r = redis.Redis(host='localhost', port=6379, decode_responses=True)

# Get all policy keys
keys = r.keys("policy:*")
print(f"Found {len(keys)} agent prediction logs in Vector DB")

# Show first 5
for key in keys[:5]:
    data = r.get(key)
    if data:
        policy = json.loads(data)
        print(f"\n{key}:")
        print(f"  Prediction Score: {policy.get('score', 'N/A'):.3f}")
        print(f"  RSI Threshold: {policy.get('rsi_thresh', 'N/A')}")
        print(f"  Close Price: ${policy.get('close_price', 0):.2f}")
