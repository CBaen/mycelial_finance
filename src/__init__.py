"""
Mycelial Finance - Main Source Package
Based on Research Document: "Mycelial Finance: A Framework for Decentralized,
Recursive Multi-Agent Reinforcement Learning in Algorithmic Trading"

This package contains the core implementation of the Mycelial Finance framework:

Architecture Components:
- agents/: Mesa-based agent implementations (Part 4.1)
- connectors/: External system interfaces - Kraken & Redis (Part 4.2, 6.1)
- core/: Mesa Model and simulation environment (Part 4.1)

Key Concepts:
- Mycelial P2P Learning: Agents share policies via FRL (Part 3.2)
- Three-Layer Redis: Streams/Pub-Sub/Key-Value backbone (Part 4.2)
- MARL Engine: VDN for credit assignment, HAVEN for coordination (Part 3.3, 3.4)
"""

__version__ = "0.1.0"
__author__ = "Mycelial Finance Development Team"
