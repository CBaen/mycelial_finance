# src/agents/market_explorer_agent.py - BIG ROCK 39: Market Discovery Layer
import logging
from .base_agent import MycelialAgent
import time
import random
import json

class MarketExplorerAgent(MycelialAgent):
    """
    Explores alternative markets and assets beyond the primary trading pairs.
    Provides market diversification intelligence and opportunity discovery.

    Purpose: Identifies new market opportunities, correlations, and risk diversification options.
    Helps the system discover patterns across multiple asset classes.
    """
    def __init__(self, model):
        super().__init__(model)
        self.name = f"Explorer_{self.unique_id}"
        self.exploration_frequency = 10  # Steps between explorations
        self.steps_since_exploration = 0
        self.last_discovery = None
        self.total_discoveries = 0

        # Market categories to explore
        self.market_categories = [
            "Altcoins",
            "DeFi Tokens",
            "NFT Markets",
            "Commodities",
            "Forex Pairs",
            "Stock Indices"
        ]

        logging.info(f"[{self.name}] Initialized. Market exploration active (Exploration frequency: {self.exploration_frequency} steps)")

    def step(self):
        """Explore markets periodically."""
        self.steps_since_exploration += 1

        if self.steps_since_exploration >= self.exploration_frequency:
            self._explore_markets()
            self.steps_since_exploration = 0

    def _explore_markets(self):
        """
        Explore alternative markets and discover opportunities.
        In production, this would query multiple exchanges and analyze market data.
        For now, we simulate market exploration discoveries.
        """
        try:
            # Simulate market exploration
            market_category = random.choice(self.market_categories)

            # Discovery types
            discovery_types = [
                "Correlation Opportunity",
                "Arbitrage Potential",
                "Volatility Spike",
                "Volume Anomaly",
                "Price Divergence",
                "New Listing Alert"
            ]

            discovery_type = random.choice(discovery_types)
            # Market exploration typically has moderate confidence
            confidence = random.uniform(0.55, 0.75)

            self.last_discovery = {
                "market_category": market_category,
                "discovery_type": discovery_type,
                "confidence": confidence,
                "timestamp": time.time()
            }

            self.total_discoveries += 1

            # Publish market discovery to Redis for dashboard visualization
            message = {
                "sender": self.name,
                "market_category": market_category,
                "discovery_type": discovery_type,
                "confidence": confidence,
                "timestamp": time.time()
            }
            self.publish("market-exploration", message)

            if self.total_discoveries % 10 == 1:  # Log periodically
                logging.info(f"[{self.name}] {discovery_type} in {market_category} (Confidence: {confidence:.2f}) - Total discoveries: {self.total_discoveries}")
            else:
                logging.debug(f"[{self.name}] {discovery_type} in {market_category} (Confidence: {confidence:.2f})")

        except Exception as e:
            logging.error(f"[{self.name}] Error exploring markets: {e}")
