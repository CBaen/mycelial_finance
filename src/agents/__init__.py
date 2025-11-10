"""
Mycelial Finance - Agent Package
Based on Research Document: Part 4.1 (Mesa Agent Layer)

This package contains all agent implementations for the Mycelial Finance system.
Each agent is a specialized Mesa agent with specific responsibilities in the
decentralized trading network.

Agent Types:
- BaseAgent: Abstract foundation for all agents
- DataMinerAgent: Consumes market data from Redis Streams (Layer 1)
- TradingAgent: Executes trades on Kraken exchange
- RiskManagementAgent: Monitors system risk (HAVEN coordination layer)
- PatternLearnerAgent: Discovers patterns and shares via FRL

Architecture Reference:
- Part 1: Mycelial Paradigm (P2P Learning Network)
- Part 2: Recursive Thought Process (Game-Theoretic Reasoning)
- Part 3: MARL Learning Engine (FRL/VDN/HAVEN)
"""

from .base_agent import BaseAgent

__all__ = ['BaseAgent']
