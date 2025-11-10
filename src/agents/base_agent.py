# src/agents/base_agent.py
import mesa
from src.connectors.redis_client import RedisClient
from src.connectors.kraken_client import KrakenClient
import logging

class MycelialAgent(mesa.Agent):
    """
    The base class for all agents in our system.
    It inherits from mesa.Agent and adds the "mycelial"
    communication and market interface capabilities.
    """
    def __init__(self, unique_id: int, model: mesa.Model):
        super().__init__(unique_id, model)

        # Give every agent access to the shared system components
        # The 'model' (Mesa's Model) will hold the single-instance clients.
        if not hasattr(model, 'redis_client') or not hasattr(model, 'kraken_client'):
            raise AttributeError("Model must have 'redis_client' and 'kraken_client' attributes.")

        self.redis_client: RedisClient = self.model.redis_client
        self.kraken_client: KrakenClient = self.model.kraken_client
        self.name = f"Agent_{unique_id}"

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
