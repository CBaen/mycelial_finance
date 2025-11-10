# src/agents/logistics_miner_agent.py
import logging
from .base_agent import MycelialAgent
import time
import random

class LogisticsMinerAgent(MycelialAgent):
    """
    The Data Engineer for the Logistics/Supply Chain Swarm.
    Simulates fetching and enriching route congestion data.
    (P3: Logistics/Supply Chain Moat)
    """
    def __init__(self, model, target_region: str = "US-West"):
        super().__init__(model)
        self.target = target_region
        self.channel = f"logistics-data:{self.target}"
        self.name = f"LogisticsMiner_{self.unique_id}"
        logging.info(f"[{self.name}] Initialized. Watching Logistics Flow for {self.target}.")

    def step(self):
        """
        Simulates fetching and enriching logistics flow data.
        """
        try:
            # --- Simulate Unique Data Moat Features ---
            congestion_score = random.uniform(1.0, 10.0) # 1=low, 10=high
            inventory_velocity = random.uniform(50.0, 500.0)

            # --- Simulated Data for the Pattern Swarm ---
            enriched_data = {
                "close": congestion_score * 10, # Use close for chart plotting (scaled up)
                "CongestionScore": congestion_score,
                "InventoryVelocity": inventory_velocity,
                "Region": self.target,
            }

            message = {
                "source": self.name,
                "timestamp": time.time(),
                "features": enriched_data
            }
            # Publish to the network for the Swarm to analyze
            self.publish(self.channel, message)

        except Exception as e:
            logging.error(f"[{self.name}] Error in step: {e}")
