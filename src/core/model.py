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
        self.schedule = mesa.time.RandomActivation(self)

        # Initialize shared clients
        logging.info("Initializing shared clients...")
        self.redis_client = RedisClient()
        self.kraken_client = KrakenClient()

        if not self.redis_client.connection or not self.kraken_client.client:
            logging.critical("Failed to initialize clients. Model will not start.")
            self.running = False
            return

        # --- Create Agent Population ---
        agent_id = 0

        # Create Data Miners (one for each pair)
        for pair in pairs_to_trade:
            miner = DataMinerAgent(agent_id, self, pair_to_watch=pair)
            self.schedule.add(miner)
            agent_id += 1

        # Create Pattern Learners (one for each pair)
        for pair in pairs_to_trade:
            learner = PatternLearnerAgent(agent_id, self, pair_to_trade=pair)
            self.schedule.add(learner)
            agent_id += 1

        # Create Trading Agents (the "hands")
        for i in range(num_traders):
            trader = TradingAgent(agent_id, self)
            self.schedule.add(trader)
            agent_id += 1

        # Create Risk Managers (the "guardians")
        for i in range(num_risk_managers):
            risker = RiskManagementAgent(agent_id, self, max_drawdown=0.05) # 5% drawdown
            self.schedule.add(risker)
            agent_id += 1

        logging.info(f"Model initialized with {agent_id} agents.")

    def step(self):
        """
        Advances the model by one step.
        This "ticks" all the agents in a random order.
        """
        if not self.running:
            return

        try:
            self.schedule.step()
        except Exception as e:
            logging.error(f"Error during model step: {e}")
            self.running = False
