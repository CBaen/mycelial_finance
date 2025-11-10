# src/core/model.py
import mesa
from src.connectors.redis_client import RedisClient
from src.connectors.kraken_client import KrakenClient
from src.agents.data_miner_agent import DataMinerAgent
from src.agents.trading_agent import TradingAgent
from src.agents.risk_management_agent import RiskManagementAgent
from src.agents.pattern_learner_agent import PatternLearnerAgent
import logging

class MycelialModel(mesa.Model):
    """
    The main Mesa model that creates, holds, and steps all agents.
    It also holds the shared, single-instance clients for
    Redis and Kraken (as per Part 4.1).
    """
    def __init__(self, pairs_to_trade: list, num_traders: int = 1, num_risk_managers: int = 1):
        super().__init__()
        self.running = True
        # Mesa 3.x uses built-in agent management (no scheduler needed)

        # Initialize shared clients
        logging.info("Initializing shared clients...")
        self.redis_client = RedisClient()
        self.kraken_client = KrakenClient()

        if not self.redis_client.connection or not self.kraken_client.client:
            logging.critical("Failed to initialize clients. Model will not start.")
            self.running = False
            return

        # --- Create Agent Population ---
        # Mesa 3.x: unique_id is auto-generated, no need to track it

        # Create Data Miners (one for each pair)
        for pair in pairs_to_trade:
            miner = DataMinerAgent(self, pair_to_watch=pair)
            self.register_agent(miner)

        # Create Pattern Learners (one for each pair)
        for pair in pairs_to_trade:
            learner = PatternLearnerAgent(self, pair_to_trade=pair)
            self.register_agent(learner)

        # Create Trading Agents (the "hands")
        for i in range(num_traders):
            trader = TradingAgent(self)
            self.register_agent(trader)

        # Create Risk Managers (the "guardians")
        for i in range(num_risk_managers):
            risker = RiskManagementAgent(self, max_drawdown=0.05) # 5% drawdown
            self.register_agent(risker)

        logging.info(f"Model initialized with {len(self.agents)} agents.")

    def step(self):
        """
        Advances the model by one step.
        This "ticks" all the agents in a random order.
        Mesa 3.x: We manually step through agents using the built-in agents list.
        """
        if not self.running:
            return

        try:
            # Step each agent in random order
            import random
            agents_list = list(self.agents)
            random.shuffle(agents_list)
            for agent in agents_list:
                agent.step()
        except Exception as e:
            logging.error(f"Error during model step: {e}")
            self.running = False
