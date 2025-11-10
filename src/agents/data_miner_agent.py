# src/agents/data_miner_agent.py
import logging
from .base_agent import MycelialAgent
import time

class DataMinerAgent(MycelialAgent):
    """
    This agent's sole purpose is to fetch market data and
    publish it to the Redis network for other agents to use.
    It is the system's "sensory organ."
    """
    def __init__(self, unique_id, model, pair_to_watch: str):
        super().__init__(unique_id, model)
        self.pair = pair_to_watch
        # Sanitize pair for channel name
        self.channel = f"market-data:{self.pair.replace('/', '-')}"
        self.name = f"DataMiner_{self.pair}_{unique_id}"
        logging.info(f"[{self.name}] Initialized. Watching {self.pair} on channel {self.channel}")

    def step(self):
        """
        On its "heartbeat," this agent fetches market data
        and publishes it to its designated channel.
        """
        logging.debug(f"[{self.name}] Fetching market data for {self.pair}...")
        try:
            market_data = self.kraken_client.get_market_data(self.pair)

            if market_data:
                # Prepare the message for other agents
                message = {
                    "source": self.name,
                    "pair": self.pair,
                    "timestamp": time.time(),
                    "data": market_data  # This will contain 'a' (ask), 'b' (bid), 'c' (last trade), etc.
                }
                # Publish to the network
                self.publish(self.channel, message)
            else:
                logging.warning(f"[{self.name}] No market data returned for {self.pair}")

        except Exception as e:
            logging.error(f"[{self.name}] Error in step: {e}")
