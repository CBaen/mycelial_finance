"""
Mycelial Finance - Configuration Package
Based on Research Document: Part 4 (Architectural Blueprint)

This package handles all system configuration, including:
- Environment variable loading
- API credentials management
- Redis connection parameters
- System-wide constants
"""

from .settings import (
    KRAKEN_API_KEY,
    KRAKEN_API_SECRET,
    REDIS_HOST,
    REDIS_PORT
)

__all__ = [
    'KRAKEN_API_KEY',
    'KRAKEN_API_SECRET',
    'REDIS_HOST',
    'REDIS_PORT'
]
