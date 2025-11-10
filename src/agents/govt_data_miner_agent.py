# src/agents/govt_data_miner_agent.py
import logging
from .base_agent import MycelialAgent
import time
import random

class GovtDataMinerAgent(MycelialAgent):
    """
    The Data Engineer for the Government Policy Swarm.
    Simulates fetching and enriching government policy, regulatory, and legislative data.
    (P4: Government/Policy Moat)
    """
    def __init__(self, model, target_region: str = "US-Federal"):
        super().__init__(model)
        self.target = target_region
        self.channel = f"govt-data:{self.target}"
        self.name = f"GovtDataMiner_{self.unique_id}"
        logging.info(f"[{self.name}] Initialized. Watching Government Policy for {self.target}.")

    def step(self):
        """
        Simulates fetching and enriching government policy data.
        """
        try:
            # --- Simulate Unique Government Data Moat Features ---
            regulatory_intensity = random.uniform(1.0, 10.0)  # 1=low regulation, 10=high
            policy_stability = random.uniform(0.0, 100.0)  # 0=unstable, 100=stable
            legislative_velocity = random.uniform(0.0, 50.0)  # Bills per session

            # --- Simulated Data for the Pattern Swarm ---
            enriched_data = {
                "close": regulatory_intensity * 10,  # Use close for chart plotting (scaled up)
                "RegulatoryIntensity": regulatory_intensity,
                "PolicyStability": policy_stability,
                "LegislativeVelocity": legislative_velocity,
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
