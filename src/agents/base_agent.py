# src/agents/base_agent.py
import mesa
from src.connectors.redis_client import RedisClient
from src.connectors.kraken_client import KrakenClient
import logging
import random

class MycelialAgent(mesa.Agent):
    """
    The base class for all agents in our system.
    It now includes a VectorDB property for long-term memory (Vector Storage).
    Mesa 3.x: unique_id is auto-generated.
    """
    def __init__(self, model: mesa.Model, **kwargs):
        super().__init__(model, **kwargs)

        if not hasattr(model, 'redis_client') or not hasattr(model, 'kraken_client'):
            raise AttributeError("Model must have 'redis_client' and 'kraken_client' attributes.")

        self.redis_client: RedisClient = self.model.redis_client
        self.kraken_client: KrakenClient = self.model.kraken_client

        # --- NEW: Memory Bank Access (Vector DB) ---
        # The agent uses the Redis connection instance for high-speed memory operations.
        self.vector_db = self.redis_client.connection

        # self.unique_id is available from super().__init__(model)
        self.name = f"Agent_{self.unique_id}"

    def step(self):
        """
        This is the agent's 'heartbeat' or 'tick'.
        Each specialized agent will override this method.
        """
        raise NotImplementedError("Each agent must implement its own step() method.")

    def publish(self, channel: str, message: dict):
        """Helper method to publish a message to the network."""
        logging.debug(f"[{self.name}] Publishing to {channel}")
        self.redis_client.publish_message(channel, message)

    def _register_listener(self, channel: str, callback):
        """Helper method to subscribe to a channel."""
        logging.info(f"[{self.name}] Subscribing to {channel}")
        self.redis_client.subscribe(channel, callback)
