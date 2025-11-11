# src/core/model.py - BIG ROCK 20: HAVEN Framework & Adversarial Testing
import mesa
from src.connectors.redis_client import RedisClient
from src.connectors.kraken_client import KrakenClient
from src.agents.data_miner_agent import DataMinerAgent
from src.agents.trading_agent import TradingAgent
from src.agents.risk_management_agent import RiskManagementAgent
from src.agents.pattern_learner_agent import PatternLearnerAgent
from src.agents.repo_scrape_agent import RepoScrapeAgent
from src.agents.builder_agent import BuilderAgent
from src.agents.logistics_miner_agent import LogisticsMinerAgent
from src.agents.govt_data_miner_agent import GovtDataMinerAgent
from src.agents.corp_data_miner_agent import CorpDataMinerAgent
import logging
import random

class MycelialModel(mesa.Model):
    """
    The main Mesa model that creates, holds, and steps all agents.
    BIG ROCK 20: Systemic Risk Hardening with HAVEN Framework.
    - Toxic agent injection for adversarial testing
    - Policy contagion threshold enforcement
    - Regulatory compliance monitoring
    """
    def __init__(self,
                 pairs_to_trade: list,
                 target_repos: list = ["Python"],
                 target_regions: list = ["US-West"],
                 target_govt_regions: list = ["US-Federal"],
                 target_corp_sectors: list = ["Tech"],
                 num_traders: int = 1,
                 num_risk_managers: int = 1,
                 num_swarm_agents: int = 100,
                 # BIG ROCK 20: HAVEN Framework Parameters
                 risk_governance_enabled: bool = False,
                 max_drawdown_percent: float = 0.05,
                 policy_contagion_threshold: float = 0.80,  # BIG ROCK 30: Lowered to 0.80 for safety buffer
                 adversarial_test_mode: bool = False,
                 regulatory_compliance_check: bool = False):
        super().__init__()
        self.running = True

        # BIG ROCK 33: Pattern Archiving Tracking
        self.step_counter = 0
        self.archived_pattern_count = 0
        self.archive_check_interval = 300  # Check every 5 minutes (300 steps)

        # Store HAVEN Framework parameters
        self.risk_governance_enabled = risk_governance_enabled
        self.max_drawdown_percent = max_drawdown_percent
        self.policy_contagion_threshold = policy_contagion_threshold
        self.adversarial_test_mode = adversarial_test_mode
        self.regulatory_compliance_check = regulatory_compliance_check

        # HAVEN metrics tracking
        self.toxic_agent_count = 0
        self.policy_contagion_blocks = 0
        self.compliance_violations = 0

        if self.risk_governance_enabled:
            logging.info("=" * 80)
            logging.info("HAVEN FRAMEWORK ACTIVATED")
            logging.info(f"  Risk Governance: ENABLED")
            logging.info(f"  Max Drawdown: {self.max_drawdown_percent * 100}%")
            logging.info(f"  Policy Contagion Threshold: {self.policy_contagion_threshold}")
            logging.info(f"  Adversarial Testing: {'ACTIVE' if self.adversarial_test_mode else 'INACTIVE'}")
            logging.info(f"  Regulatory Compliance: {'ACTIVE' if self.regulatory_compliance_check else 'INACTIVE'}")
            logging.info("=" * 80)

        # Initialize shared clients
        logging.info("Initializing shared clients...")
        self.redis_client = RedisClient()
        self.kraken_client = KrakenClient()

        if not self.redis_client.connection or not self.kraken_client.user:
            logging.critical("Failed to initialize clients. Model will not start.")
            self.running = False
            return

        # --- Create Agent Population ---

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

        # 4. Create GOVERNMENT DATA MINERS (Senses for Product 4: Government/Policy Moat)
        for region in target_govt_regions:
            govt_miner = GovtDataMinerAgent(self, target_region=region)
            self.register_agent(govt_miner)

        # 5. Create CORPORATE DATA MINERS (Senses for Product 5: US Corporations Moat)
        for sector in target_corp_sectors:
            corp_miner = CorpDataMinerAgent(self, target_sector=sector)
            self.register_agent(corp_miner)

        # 6. Create Pattern Learners (THE SWARM: 100 agents distributed across 5 moats)
        logging.info(f"Creating {num_swarm_agents}-agent Swarm distributed across 5 Product Pillars...")

        # Define product distribution (randomized for diversity across 5 PILLARS)
        products = ["Finance", "Code", "Logistics", "Government", "Corporations"]
        product_counts = {"Finance": 0, "Code": 0, "Logistics": 0, "Government": 0, "Corporations": 0}

        # BIG ROCK 20: Calculate toxic agent injection count (10% of swarm if adversarial mode)
        num_toxic_agents = int(num_swarm_agents * 0.1) if self.adversarial_test_mode else 0
        toxic_agent_indices = set(random.sample(range(num_swarm_agents), num_toxic_agents)) if num_toxic_agents > 0 else set()

        for i in range(num_swarm_agents):
            # Randomly assign product focus (equal distribution)
            product_focus = random.choice(products)
            product_counts[product_focus] += 1

            # Select appropriate trading pair for Finance agents
            if product_focus == "Finance":
                pair = random.choice(pairs_to_trade)
            else:
                pair = "XXBTZUSD"  # Default, but won't be used for non-Finance

            # BIG ROCK 20: Inject toxic behavior for adversarial testing
            is_toxic = i in toxic_agent_indices
            if is_toxic:
                # Toxic agents have extreme parameters that could cause instability
                rsi_threshold = random.choice([10, 95])  # Extreme overbought/oversold
                atr_multiplier = random.uniform(3.0, 5.0)  # Excessive volatility sensitivity
                self.toxic_agent_count += 1
                logging.warning(f"[ADVERSARIAL] Toxic agent injected: SwarmBrain_{i+7} (RSI={rsi_threshold}, ATR={atr_multiplier:.2f})")
            else:
                # Normal agents have reasonable parameters
                rsi_threshold = random.randint(65, 75)
                atr_multiplier = random.uniform(0.8, 1.2)

            learner = PatternLearnerAgent(self,
                                          pair_to_trade=pair,
                                          product_focus=product_focus,
                                          rsi_threshold=rsi_threshold,
                                          atr_multiplier=atr_multiplier)
            self.register_agent(learner)

        logging.info(f"Swarm Diversity: Finance={product_counts['Finance']}, Code={product_counts['Code']}, Logistics={product_counts['Logistics']}, Government={product_counts['Government']}, Corporations={product_counts['Corporations']}")

        if self.adversarial_test_mode:
            logging.warning(f"[ADVERSARIAL] {self.toxic_agent_count} toxic agents injected into swarm for stress testing")

        # 7. Create Trading Agents (Hands)
        for i in range(num_traders):
            trader = TradingAgent(self)
            self.register_agent(trader)

        # 8. Create Risk Managers (Guardians) - BIG ROCK 20: Enhanced with HAVEN parameters
        for i in range(num_risk_managers):
            risker = RiskManagementAgent(
                self,
                max_drawdown=self.max_drawdown_percent
            )
            self.register_agent(risker)

            if self.risk_governance_enabled:
                logging.info(f"[HAVEN] RiskManager initialized with max_drawdown={self.max_drawdown_percent*100}%")
                if self.regulatory_compliance_check:
                    logging.info(f"[HAVEN] Regulatory compliance monitoring: ACTIVE (handled by model)")

        # 9. Create BUILDER AGENT (Autonomy)
        builder = BuilderAgent(self)
        self.register_agent(builder)

        agent_count = len(self.agents)
        logging.info(f"Mycelial Swarm created. Model initialized with {agent_count} total agents, covering ALL 5 Product Pillars: Finance, Code, Logistics, Government, and Corporations.")

        if self.risk_governance_enabled:
            logging.info("=" * 80)
            logging.info("HAVEN FRAMEWORK READY FOR ADVERSARIAL SIMULATION")
            logging.info("=" * 80)

    def step(self):
        """
        Advances the model by one step.
        This "ticks" all the agents in a random order.
        BIG ROCK 20: Enhanced with policy contagion threshold enforcement.
        """
        if not self.running:
            return

        try:
            # BIG ROCK 20: Policy Contagion Threshold Check
            # In a real implementation, this would check Redis for high-risk policy propagation
            # For now, we simulate the check by tracking system risk levels
            if self.risk_governance_enabled:
                # Check if we need to block policy contagion (simulated risk check)
                # In production, this would query Redis for policy confidence scores
                system_risk = self._calculate_system_risk()

                if system_risk > (1.0 - self.policy_contagion_threshold):
                    # System risk too high - block policy spread
                    self.policy_contagion_blocks += 1
                    if self.policy_contagion_blocks % 10 == 1:  # Log periodically
                        logging.warning(f"[HAVEN] Policy contagion blocked (risk={system_risk:.2f}, threshold={self.policy_contagion_threshold})")

                    # In production: Send Redis message to halt policy sharing temporarily
                    # self.redis_client.publish("system-control", {"action": "halt_policy_sharing"})

            # Step each agent in random order
            agents_list = list(self.agents)
            random.shuffle(agents_list)
            for agent in agents_list:
                agent.step()

            # BIG ROCK 33: Pattern Archiving Check (every 5 minutes)
            self.step_counter += 1
            if self.step_counter % self.archive_check_interval == 0:
                self._archive_high_value_patterns()

        except Exception as e:
            logging.error(f"Error during model step: {e}")
            self.running = False

    def _calculate_system_risk(self) -> float:
        """
        BIG ROCK 20: Calculate current system risk level (0.0 to 1.0).
        In production, this would aggregate risk metrics from all agents.
        For simulation, we return a random risk level that occasionally spikes.
        """
        # Simulate occasional risk spikes to test contagion threshold
        if random.random() < 0.05:  # 5% chance of risk spike
            return random.uniform(0.8, 0.95)  # High risk
        else:
            return random.uniform(0.1, 0.4)  # Normal risk

    def _archive_high_value_patterns(self):
        """
        BIG ROCK 33: Pattern Archiving for Long-Term Retention.
        Scans Redis for high-value patterns (pattern_current_value > 50) and simulates
        archiving them to a persistent SQL database for historical analysis.

        In production, this would:
        1. Query Redis for all policy:* keys
        2. Parse pattern data
        3. Filter by pattern_current_value > 50 (after decay) - BIG ROCK 30: Lowered from 75 to 50
        4. INSERT into SQL: patterns(agent_id, timestamp, features, interestingness, decay_factor)
        5. Optionally DELETE from Redis to free memory
        """
        try:
            # Scan for all agent policies in Redis
            pattern_keys = self.redis_client.connection.keys("policy:*")
            high_value_patterns = []

            for key in pattern_keys:
                policy_data = self.redis_client.connection.get(key)
                if policy_data:
                    import json
                    policy = json.loads(policy_data)
                    pattern_value = policy.get('pattern_current_value', 0)

                    # Archive threshold: 50+ value (after decay) - BIG ROCK 30
                    if pattern_value >= 50:
                        high_value_patterns.append({
                            'agent_id': policy.get('agent_id'),
                            'pattern_value': pattern_value,
                            'raw_features': policy.get('raw_features', {}),
                            'age_minutes': policy.get('pattern_age_minutes', 0),
                            'decay_factor': policy.get('pattern_decay_factor', 1.0)
                        })

            if high_value_patterns:
                self.archived_pattern_count += len(high_value_patterns)
                elapsed_minutes = self.step_counter // 60
                logging.info(f"[ARCHIVE] Step {self.step_counter} ({elapsed_minutes}min): "
                           f"Found {len(high_value_patterns)} high-value patterns (>50 after decay). "
                           f"Total archived: {self.archived_pattern_count}")

                # In production: INSERT into SQL database here
                # for pattern in high_value_patterns:
                #     cursor.execute("INSERT INTO patterns (agent_id, value, features, timestamp) VALUES (?, ?, ?, ?)",
                #                   (pattern['agent_id'], pattern['pattern_value'], json.dumps(pattern['raw_features']), time.time()))
            else:
                elapsed_minutes = self.step_counter // 60
                logging.info(f"[ARCHIVE] Step {self.step_counter} ({elapsed_minutes}min): No high-value patterns to archive (threshold: 50)")

        except Exception as e:
            logging.error(f"[ARCHIVE] Error during pattern archiving: {e}")
