"""
Mycelial Finance - Core Package
Based on Research Document: Part 4.1 (Mesa Framework)

This package contains the core Mesa simulation model and supporting infrastructure.

The Mesa Model serves two critical functions:
1. Live Agent Deployment: Orchestrates live trading agents
2. Market Simulation: Provides ACE environment for testing MARL algorithms

Architecture Reference:
- Part 1.3: Agent-Based Computational Economics (ACE)
- Part 4.1: The Agent & Simulation Layer
- Part 7.3: Risk Mitigation via Simulation
"""

from .model import MycelialModel

__all__ = ['MycelialModel']
