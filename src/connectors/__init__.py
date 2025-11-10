"""
Mycelial Finance - Connector Package
Based on Research Document: Part 4.2 (Redis) & Part 6.1 (Kraken)

This package provides interfaces to external systems:

1. KrakenClient: Market interface for order execution
   - Based on Part 6.1: Target Exchange Analysis
   - Handles API rate limits and maker-taker fee optimization

2. RedisClient: Three-layer "nervous system"
   - Layer 1: Market data ingestion (Redis Streams)
   - Layer 2: Inter-agent communication (Redis Pub/Sub)
   - Layer 3: Agent state and memory (Redis Key-Value)
   - Based on Part 4.2: The "Nervous System" Architecture
"""

# Lazy imports to avoid dependency issues during testing
__all__ = ['KrakenClient', 'RedisClient']

def __getattr__(name):
    if name == "KrakenClient":
        from .kraken_client import KrakenClient
        return KrakenClient
    elif name == "RedisClient":
        from .redis_client import RedisClient
        return RedisClient
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
