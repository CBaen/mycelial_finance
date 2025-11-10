# src/core/model.py
import mesa
from src.connectors.redis_client import RedisClient
from src.connectors.kraken_client import KrakenClient
from src.agents.data_miner_agent import DataMinerAgent
from src.agents.trading_agent import TradingAgent
from src.agents.risk_management_agent import RiskManagementAgent
from src.agents.pattern_learner_agent import PatternLearnerAgent
from src.agents.repo_scrape_agent import RepoScrapeAgent  # NEW IMPORT
from src.agents.builder_agent import BuilderAgent  # NEW IMPORT
from src.agents.logistics_miner_agent import LogisticsMinerAgent  # NEW IMPORT
import logging
import random  # For randomized swarm strategies

class MycelialModel(mesa.Model):
    """
    The main Mesa model that creates, holds, and steps all agents.
    It now includes all three core product lines (Finance, Code, Logistics, Autonomy).
    """
    def __init__(self, pairs_to_trade: list, target_repos: list = ["Python"], target_regions: list = ["US-West"], num_traders: int = 1, num_risk_managers: int = 1, num_swarm_agents: int = 100):
        super().__init__()
        self.running = True
        # Mesa 3.x uses built-in agent management (no scheduler needed)

        # Initialize shared clients
        logging.info("Initializing shared clients...")
        self.redis_client = RedisClient()
        self.kraken_client = KrakenClient()

        if not self.redis_client.connection or not self.kraken_client.user:
            logging.critical("Failed to initialize clients. Model will not start.")
            self.running = False
            return

        # --- Create Agent Population ---
        # Mesa 3.x: unique_id is auto-generated, no need to track it

        # 1. Create Data Miners (Senses for Product 2: Finance)
        for pair in pairs_to_trade:
            miner = DataMinerAgent(self, pair_to_watch=pair)
            self.register_agent(miner)

        # 2. Create REPO SCRAPERS (Senses for Product 1: Code Moat)
        for target in target_repos:
            scraper = RepoScrapeAgent(self, target_language=target)
            self.register_agent(scraper)

        # 3. Create LOGISTICS MINERS (Senses for Product 3: Logistics Moat)
        for region in target_regions:
            logistics = LogisticsMinerAgent(self, target_region=region)
            self.register_agent(logistics)

        # 4. Create Pattern Learners (THE SWARM: 100 agents for BTC)
        btc_pair = 'XXBTZUSD'
        logging.info(f"Creating {num_swarm_agents}-agent Swarm for {btc_pair}...")
        for i in range(num_swarm_agents):
            # Introduce random seeds for strategy variance (Crucial for FRL)
            rsi_threshold = random.randint(65, 75)
            atr_multiplier = random.uniform(0.8, 1.2)
            learner = PatternLearnerAgent(self,
                                          pair_to_trade=btc_pair,
                                          rsi_threshold=rsi_threshold,
                                          atr_multiplier=atr_multiplier)
            self.register_agent(learner)

        # Optional: Create Pattern Learners for other pairs (if any)
        for pair in pairs_to_trade:
            if pair != btc_pair:
                learner = PatternLearnerAgent(self, pair_to_trade=pair)
                self.register_agent(learner)

        # 5. Create Trading Agents (Hands)
        for i in range(num_traders):
            trader = TradingAgent(self)
            self.register_agent(trader)

        # 6. Create Risk Managers (Guardians)
        for i in range(num_risk_managers):
            risker = RiskManagementAgent(self, max_drawdown=0.05)
            self.register_agent(risker)

        # 7. Create BUILDER AGENT (Autonomy)
        builder = BuilderAgent(self)
        self.register_agent(builder)

        logging.info(f"Mycelial Swarm created. Model initialized with {len(self.agents)} total agents, covering Finance, Code, and Logistics Moats.")

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
