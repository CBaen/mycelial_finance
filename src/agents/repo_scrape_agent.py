# src/agents/repo_scrape_agent.py
import logging
from .base_agent import MycelialAgent
import time
import random

class RepoScrapeAgent(MycelialAgent):
    """
    The Data Engineer for the Code Innovation Swarm.
    It scrapes (simulates) GitHub activity to find novel patterns.
    (P1: Code Innovation Swarm)
    """
    def __init__(self, model, target_language: str = "Python"):
        super().__init__(model)
        self.target = target_language
        self.channel = f"code-data:{self.target}"
        self.name = f"RepoScraper_{self.unique_id}"
        logging.info(f"[{self.name}] Initialized. Watching GitHub for {self.target} activity.")

    def step(self):
        """
        Simulates fetching and enriching code activity data.
        """
        try:
            # --- Simulate Unique Data Moat Features ---
            novelty_score = random.uniform(0.5, 9.5) # 1-10 scale
            dependency_entropy = random.randint(1, 100)

            # --- Simulated Data for the Pattern Swarm ---
            enriched_data = {
                "close": novelty_score, # Use close for chart plotting
                "NoveltyScore": novelty_score,
                "DependencyEntropy": dependency_entropy,
                "Language": self.target,
                "RepoUrl": f"https://github.com/innovate/repo_{self.unique_id}"
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
