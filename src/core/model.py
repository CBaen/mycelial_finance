# src/core/model.py - BIG ROCK 39: Final 123-Agent Architecture
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
# BIG ROCK 32: New Collaborative Agents
from src.agents.mycelial_instigator_agent import MycelialInstigatorAgent
from src.agents.deep_research_agent import DeepResearchAgent
# BIG ROCK 39: Technical Analysis and Market Explorer Agents
from src.agents.technical_analysis_agent import TechnicalAnalysisAgent
from src.agents.market_explorer_agent import MarketExplorerAgent
# BIG ROCK 45: Learning Loop Components
from src.storage.trade_database import TradeDatabase
from src.agents.memory_agent import MemoryAgent
import logging
import random
import sqlite3  # BIG ROCK 31: SQL Persistence
import json
import time
import threading  # BIG ROCK 31: Graceful Shutdown
import queue  # PHASE 2.2: Thread-safe SQLite write queue

class MycelialModel(mesa.Model):
    """
    The main Mesa model that creates, holds, and steps all agents.
    BIG ROCK 39: Final 123-Agent Architecture with TA and Market Explorer layers.
    - HAVEN Framework: Risk governance and policy contagion controls
    - SQL Persistence: High-value pattern archiving
    - Graceful Shutdown: Emergency stop mechanism
    - Rule of 3: Collaborative decision enforcement (Instigator Agents)
    - Redundant Validation: Pattern quality verification (Deep Research Agents)
    - Technical Analysis: Competitive baseline validation (TA Agents)
    - Market Exploration: Multi-market opportunity discovery (Explorer Agents)
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
                 regulatory_compliance_check: bool = False,
                 # BIG ROCK 32: Collaborative Architecture Parameters
                 num_instigators: int = 3,  # Rule of 3 Collaboration Enforcement
                 num_research_agents: int = 3,  # Redundant Pattern Validation
                 # BIG ROCK 39: Technical Analysis and Market Explorer Parameters
                 num_ta_agents: int = 3,  # Technical Analysis Competitive Baseline
                 num_explorer_agents: int = 3):  # Market Exploration and Discovery
        super().__init__()
        self.running = True

        # BIG ROCK 33: Pattern Archiving Tracking
        self.step_counter = 0
        self.archived_pattern_count = 0
        self.archive_check_interval = 300  # Check every 5 minutes (300 steps)

        # BIG ROCK 43: Active asset tracking (Q3: max 15 assets)
        self.active_assets = {}  # {pair: {"team_type": str, "confidence": float, "status": str, "deployed_at": float}}
        self.max_active_assets = 15

        # Initialize with bootstrap assets (BTC, ETH)
        self.active_assets["XXBTZUSD"] = {
            "team_type": "Bootstrap",
            "confidence": 1.0,
            "status": "active",
            "deployed_at": time.time()
        }
        self.active_assets["XETHZUSD"] = {
            "team_type": "Bootstrap",
            "confidence": 1.0,
            "status": "active",
            "deployed_at": time.time()
        }

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

        # PHASE 2.2: SQL Database Initialization with Thread-Safe Write Queue
        self.db_connection = None
        self.db_cursor = None
        self.db_write_queue = queue.Queue()  # Thread-safe write queue
        self.db_writer_thread = None  # Background writer thread

        try:
            # PHASE 2.2: Remove check_same_thread=False (was dangerous)
            # Connection only used by dedicated writer thread
            self.db_connection = sqlite3.connect('mycelial_patterns.db', check_same_thread=True)
            self.db_cursor = self.db_connection.cursor()

            # Create patterns table if it doesn't exist
            self.db_cursor.execute('''
                CREATE TABLE IF NOT EXISTS patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id INTEGER NOT NULL,
                    timestamp REAL NOT NULL,
                    pattern_value REAL NOT NULL,
                    raw_features TEXT NOT NULL,
                    age_minutes REAL NOT NULL,
                    decay_factor REAL NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            self.db_connection.commit()
            logging.info("[SQL] Pattern database initialized: mycelial_patterns.db")
        except Exception as e:
            logging.error(f"[SQL] Failed to initialize database: {e}")
            self.db_connection = None
            self.db_cursor = None

        # BIG ROCK 45: Initialize Trade Database (Learning Loop)
        try:
            self.trade_db = TradeDatabase("./trades.db")
            logging.info("[TRADE-DB] Trade database initialized successfully")
        except Exception as e:
            logging.error(f"[TRADE-DB] Failed to initialize trade database: {e}")
            self.trade_db = None

        # BIG ROCK 31: Graceful Shutdown Listener (Emergency Stop)
        try:
            self.redis_client.pubsub.subscribe(**{"system-control": self._handle_system_control})
            logging.info("[SHUTDOWN] Emergency shutdown listener registered on 'system-control' channel")
        except Exception as e:
            logging.warning(f"[SHUTDOWN] Failed to register shutdown listener: {e}")

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

        # 7. Create Trading Agents (Hands) - BIG ROCK 45: Pass trade_db for learning loop
        for i in range(num_traders):
            trader = TradingAgent(self, trade_db=self.trade_db)
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

        # 10. BIG ROCK 32: Create MYCELIAL INSTIGATOR AGENTS (Rule of 3 Collaboration)
        for i in range(num_instigators):
            instigator = MycelialInstigatorAgent(self)
            self.register_agent(instigator)

        # 11. BIG ROCK 32: Create DEEP RESEARCH AGENTS (Redundant Pattern Validation)
        for i in range(num_research_agents):
            researcher = DeepResearchAgent(self)
            self.register_agent(researcher)

        # 12. BIG ROCK 43: Create MARKET EXPLORER AGENT TEAMS (Rule of 3 Prospecting)
        # Deploy 9 MEAs in 3 specialized teams: HFT, DayTrade, Swing
        logging.info("Deploying 9 Market Explorer Agents (3 teams of 3 for Rule of 3)...")

        for team_id in range(1, 4):  # 3 agents per team
            # HFT Team (fast-moving assets, prioritize Code/Corporate moats)
            hft_explorer = MarketExplorerAgent(self, team_type="HFT", team_id=team_id)
            self.register_agent(hft_explorer)

            # DayTrade Team (balanced approach)
            daytrade_explorer = MarketExplorerAgent(self, team_type="DayTrade", team_id=team_id)
            self.register_agent(daytrade_explorer)

            # Swing Team (longer-term, prioritize Gov/Logistics moats)
            swing_explorer = MarketExplorerAgent(self, team_type="Swing", team_id=team_id)
            self.register_agent(swing_explorer)

        logging.info("[BIG ROCK 43] 9 MEAs deployed: 3 HFT + 3 DayTrade + 3 Swing teams")

        # Note: Technical Analysis Agents are now deployed dynamically per asset by BuilderAgent
        # No longer deployed globally at startup

        agent_count = len(self.agents)
        logging.info(f"Mycelial Swarm created. Model initialized with {agent_count} total agents, covering ALL 5 Product Pillars: Finance, Code, Logistics, Government, and Corporations.")
        logging.info(f"[BIG ROCK 32] Collaborative Architecture: {num_instigators} Instigator Agents + {num_research_agents} Deep Research Agents deployed")
        logging.info(f"[BIG ROCK 43] Dynamic Prospecting Architecture: 9 MEA teams + 1 Builder Agent (TA agents deployed per-asset)")

        # BIG ROCK 43: Start consensus checking thread (Q1: 2/3 majority with >70% confidence)
        self.consensus_thread = threading.Thread(target=self._consensus_checking_loop, daemon=True)
        self.consensus_thread.start()
        logging.info("[BIG ROCK 43] Consensus checking thread started (checks every 5 seconds)")

        # PHASE 2.2: Start SQLite writer thread (thread-safe writes)
        self.db_writer_thread = threading.Thread(target=self._db_writer_loop, daemon=True)
        self.db_writer_thread.start()
        logging.info("[PHASE 2.2] SQLite writer thread started (thread-safe write queue)")

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

    def _handle_system_control(self, message: dict):
        """
        BIG ROCK 31: Graceful Shutdown Handler.
        Listens for EMERGENCY_SHUTDOWN command and halts all operations safely.
        """
        try:
            command = message.get('command', '')

            if command == 'EMERGENCY_SHUTDOWN':
                reason = message.get('reason', 'User initiated')
                logging.critical("=" * 80)
                logging.critical("[EMERGENCY SHUTDOWN] System halt initiated!")
                logging.critical(f"[EMERGENCY SHUTDOWN] Reason: {reason}")
                logging.critical("=" * 80)

                # Broadcast HALT_TRADING to all agents
                self.redis_client.publish("system-control", {
                    "command": "HALT_TRADING",
                    "reason": f"Emergency shutdown: {reason}"
                })

                # Archive final patterns before shutdown
                logging.info("[SHUTDOWN] Archiving final patterns...")
                self._archive_high_value_patterns()

                # Close database connection
                if self.db_connection:
                    self.db_connection.commit()
                    self.db_connection.close()
                    logging.info("[SHUTDOWN] Database connection closed safely")

                # Stop model execution
                self.running = False
                logging.critical("[SHUTDOWN] Model stopped. System is safe to exit.")

        except Exception as e:
            logging.error(f"[SHUTDOWN] Error during emergency shutdown: {e}")

    def register_active_asset(self, pair: str, team_type: str, confidence: float):
        """
        BIG ROCK 43: Register new asset as active after Builder Agent deploys team
        """
        self.active_assets[pair] = {
            "team_type": team_type,
            "confidence": confidence,
            "status": "active",
            "deployed_at": time.time()
        }
        logging.info(
            f"[MODEL] Registered {pair} as active | "
            f"Team: {team_type} | Confidence: {confidence:.2%} | "
            f"Active assets: {len(self.active_assets)}/{self.max_active_assets}"
        )

    def hibernate_asset(self, pair: str):
        """
        BIG ROCK 43 (Q9): Hibernate asset after 90 days probation

        Hibernation preserves learned patterns while freeing compute resources:
        1. Mark asset as "hibernated" (not fully removed)
        2. Kill all agents for this pair (1 miner + 3 TAA + 15 learners)
        3. Archive patterns to SQLite/ChromaDB
        4. Asset can be "reawakened" if MEA consensus re-triggers
        """
        if pair not in self.active_assets:
            logging.warning(f"[MODEL] Cannot hibernate {pair} - not in active_assets")
            return

        # Update status
        self.active_assets[pair]["status"] = "hibernated"
        self.active_assets[pair]["hibernated_at"] = time.time()

        # Kill agents for this pair
        agents_to_remove = []
        for agent in list(self.agents):
            if hasattr(agent, 'pair') and agent.pair == pair:
                agents_to_remove.append(agent)

        for agent in agents_to_remove:
            self.schedule.remove(agent)

        # Archive patterns before hibernation
        self._archive_asset_patterns(pair)

        logging.info(
            f"[MODEL] Hibernated {pair} | "
            f"Removed {len(agents_to_remove)} agents | "
            f"Status: {self.active_assets[pair]['status']}"
        )

    def _archive_asset_patterns(self, pair: str):
        """
        BIG ROCK 43 (Q9): Archive all patterns for hibernated asset

        This preserves learned causal relationships so if the asset
        becomes interesting again, we can "reawaken" with historical context.
        """
        try:
            # PHASE 2.3: Query Redis for all patterns using non-blocking SCAN
            pattern_keys = self._scan_patterns("policy:*")
            archived_count = 0

            for key in pattern_keys:
                policy_data = self.redis_client.connection.get(key)
                if policy_data:
                    policy = json.loads(policy_data)
                    agent_id = policy.get('agent_id')

                    # Check if this agent was working on the hibernated pair
                    # (Agent names contain pair, e.g., "SwarmBrain_42_Finance")
                    # For Finance agents, store all patterns as they may have traded this pair
                    if policy.get('product_focus') == 'Finance':
                        # PHASE 2.2: Archive to SQLite via thread-safe queue
                        try:
                            self._queue_db_write(
                                """INSERT INTO patterns
                                   (agent_id, timestamp, pattern_value, raw_features, age_minutes, decay_factor)
                                   VALUES (?, ?, ?, ?, ?, ?)""",
                                (
                                    agent_id,
                                    time.time(),
                                    policy.get('pattern_current_value', 0),
                                    json.dumps(policy.get('raw_features', {})),
                                    policy.get('pattern_age_minutes', 0),
                                    policy.get('pattern_decay_factor', 1.0)
                                )
                            )
                            archived_count += 1
                        except Exception as insert_error:
                            logging.error(f"[ARCHIVE] Failed to queue pattern for {agent_id}: {insert_error}")

            # PHASE 2.2: Queue commit instead of direct execution
            self._queue_db_commit()

            logging.info(f"[ARCHIVE] Archived {archived_count} patterns for hibernated asset {pair}")

        except Exception as e:
            logging.error(f"[ARCHIVE] Error archiving patterns for {pair}: {e}")

    def _consensus_checking_loop(self):
        """
        BIG ROCK 43 (Q1): Background thread that checks for MEA consensus

        Runs every 5 seconds, checking if 2/3 agents in any team agree
        with >70% confidence on a prospecting opportunity.

        This is the "heartbeat" of the dynamic prospecting engine.
        """
        import time as time_module
        from collections import defaultdict

        logging.info("[CONSENSUS] Consensus checking loop started")

        while self.running:
            try:
                time_module.sleep(5)  # Check every 5 seconds

                # Check each team type for consensus
                for team_type in ["HFT", "DayTrade", "Swing"]:
                    self._check_team_consensus(team_type)

            except Exception as e:
                logging.error(f"[CONSENSUS] Error in consensus checking loop: {e}")

        logging.info("[CONSENSUS] Consensus checking loop stopped")

    def _check_team_consensus(self, team_type: str):
        """
        BIG ROCK 43 (Q1): Check if 2/3 agents in team agree on asset

        Rule of 3 Logic:
        - Need at least 2 out of 3 agents agreeing (2/3 majority)
        - Average confidence must exceed 70%
        - Proposals must be within 60-second window
        """
        from collections import defaultdict

        try:
            # Fetch recent proposals from Redis channel
            # In production, this would scan a Redis sorted set with timestamps
            # For now, we simulate by checking if agents have published recently

            # Get recent proposals (last 60 seconds)
            proposals = self._get_recent_proposals(team_type, window=60)

            if not proposals:
                return

            # Group proposals by pair
            pair_votes = defaultdict(list)
            for proposal in proposals:
                pair = proposal.get('pair')
                if pair:
                    pair_votes[pair].append({
                        'agent': proposal.get('source'),
                        'confidence': proposal.get('confidence', 0),
                        'timestamp': proposal.get('timestamp', 0)
                    })

            # Check each pair for consensus
            for pair, votes in pair_votes.items():
                # Q1: Need at least 2/3 agents (2 out of 3)
                if len(votes) >= 2:
                    # Calculate average confidence
                    avg_confidence = sum(v['confidence'] for v in votes) / len(votes)

                    # Q1: Confidence must exceed 70%
                    if avg_confidence > 0.70:
                        logging.info(
                            f"[CONSENSUS] ✓ {team_type} CONSENSUS REACHED for {pair} | "
                            f"Votes: {len(votes)}/3 | Confidence: {avg_confidence:.2%}"
                        )

                        # Publish consensus to Builder Agent
                        self.redis_client.publish("prospecting-consensus", {
                            "pair": pair,
                            "team_type": team_type,
                            "votes": len(votes),
                            "confidence": avg_confidence,
                            "timestamp": time.time()
                        })

        except Exception as e:
            logging.error(f"[CONSENSUS] Error checking {team_type} consensus: {e}")

    def _get_recent_proposals(self, team_type: str, window: int = 60) -> list:
        """
        BIG ROCK 43: Fetch recent MEA proposals from Redis

        In production, this would query a Redis sorted set with timestamps.
        For now, we scan the prospecting-proposals:{team_type} channel history.

        Returns: List of proposal messages within the time window
        """
        try:
            # In production: Redis sorted set with ZRANGEBYSCORE
            # For simulation: Return empty list (agents publish directly)
            # The real implementation would look like:
            #
            # current_time = time.time()
            # min_timestamp = current_time - window
            # proposals = self.redis_client.connection.zrangebyscore(
            #     f"proposals:{team_type}",
            #     min_timestamp,
            #     current_time
            # )
            # return [json.loads(p) for p in proposals]

            # TEMP: For Phase 1, return empty (consensus happens via direct pubsub)
            return []

        except Exception as e:
            logging.error(f"[CONSENSUS] Error fetching proposals for {team_type}: {e}")
            return []

    def _db_writer_loop(self):
        """
        PHASE 2.2: Dedicated SQLite writer thread

        This thread is the ONLY thread that writes to SQLite, eliminating
        all thread safety issues. Other threads submit write requests via
        the thread-safe queue.

        Queue message format: ('INSERT', sql_query, params) or ('COMMIT',)
        """
        import time as time_module

        logging.info("[DB_WRITER] SQLite writer thread started")

        while self.running:
            try:
                # Block with 1-second timeout to allow graceful shutdown
                try:
                    task = self.db_write_queue.get(timeout=1.0)
                except queue.Empty:
                    continue

                if task[0] == 'INSERT':
                    _, sql_query, params = task
                    try:
                        self.db_cursor.execute(sql_query, params)
                    except Exception as insert_error:
                        logging.error(f"[DB_WRITER] Failed to execute INSERT: {insert_error}")

                elif task[0] == 'COMMIT':
                    try:
                        self.db_connection.commit()
                    except Exception as commit_error:
                        logging.error(f"[DB_WRITER] Failed to COMMIT: {commit_error}")

                elif task[0] == 'SHUTDOWN':
                    # Final commit before shutdown
                    try:
                        self.db_connection.commit()
                    except Exception as e:
                        logging.error(f"[DB_WRITER] Failed final commit: {e}")
                    break

                self.db_write_queue.task_done()

            except Exception as e:
                logging.error(f"[DB_WRITER] Error in writer loop: {e}")

        logging.info("[DB_WRITER] SQLite writer thread stopped")

    def _queue_db_write(self, sql_query: str, params: tuple):
        """
        PHASE 2.2: Submit write request to thread-safe queue

        This method is called from any thread to safely write to SQLite.
        The actual write is performed by the dedicated writer thread.
        """
        try:
            self.db_write_queue.put(('INSERT', sql_query, params))
        except Exception as e:
            logging.error(f"[DB_WRITE] Error queuing write: {e}")

    def _queue_db_commit(self):
        """
        PHASE 2.2: Submit commit request to thread-safe queue
        """
        try:
            self.db_write_queue.put(('COMMIT',))
        except Exception as e:
            logging.error(f"[DB_COMMIT] Error queuing commit: {e}")

    def _scan_patterns(self, pattern: str) -> list:
        """
        PHASE 2.3: Non-blocking Redis pattern scan

        Replaces blocking KEYS command with incremental SCAN.
        SCAN iterates through the keyspace in chunks, yielding control
        between batches to prevent Redis from blocking.

        Args:
            pattern: Redis key pattern (e.g., "policy:*")

        Returns:
            List of matching keys
        """
        cursor = 0
        keys = []

        try:
            while True:
                # SCAN returns (cursor, batch) tuple
                # cursor=0 means iteration complete
                cursor, batch = self.redis_client.connection.scan(
                    cursor=cursor,
                    match=pattern,
                    count=100  # Batch size (Redis default)
                )

                # Decode bytes to strings if needed
                decoded_batch = [
                    k.decode('utf-8') if isinstance(k, bytes) else k
                    for k in batch
                ]
                keys.extend(decoded_batch)

                # cursor=0 signals end of iteration
                if cursor == 0:
                    break

            logging.debug(f"[SCAN] Found {len(keys)} keys matching '{pattern}'")
            return keys

        except Exception as e:
            logging.error(f"[SCAN] Error scanning pattern '{pattern}': {e}")
            return []

    def _archive_high_value_patterns(self):
        """
        BIG ROCK 31: Pattern Archiving with SQL Persistence.
        BIG ROCK 34: Archive threshold lowered to 40 for faster pattern discovery.
        Scans Redis for high-value patterns (pattern_current_value > 40) and persists
        them to SQLite database for long-term historical analysis.

        Process:
        1. Query Redis for all policy:* keys
        2. Parse pattern data
        3. Filter by pattern_current_value > 40 (after decay) - BIG ROCK 34: Lowered from 50 to 40
        4. INSERT into SQL: patterns(agent_id, timestamp, pattern_value, raw_features, age_minutes, decay_factor)
        5. Commit transaction for durability
        """
        try:
            # PHASE 2.3: Scan for all agent policies using non-blocking SCAN
            pattern_keys = self._scan_patterns("policy:*")
            high_value_patterns = []

            for key in pattern_keys:
                policy_data = self.redis_client.connection.get(key)
                if policy_data:
                    policy = json.loads(policy_data)
                    pattern_value = policy.get('pattern_current_value', 0)

                    # Archive threshold: 40+ value (after decay) - BIG ROCK 34
                    if pattern_value >= 40:
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
                           f"Found {len(high_value_patterns)} high-value patterns (>40 after decay). "
                           f"Total archived: {self.archived_pattern_count}")

                # PHASE 2.2: SQL Persistence via Thread-Safe Queue
                for pattern in high_value_patterns:
                    try:
                        self._queue_db_write(
                            """INSERT INTO patterns
                               (agent_id, timestamp, pattern_value, raw_features, age_minutes, decay_factor)
                               VALUES (?, ?, ?, ?, ?, ?)""",
                            (
                                pattern['agent_id'],
                                time.time(),
                                pattern['pattern_value'],
                                json.dumps(pattern['raw_features']),
                                pattern['age_minutes'],
                                pattern['decay_factor']
                            )
                        )
                    except Exception as insert_error:
                        logging.error(f"[ARCHIVE] Failed to queue pattern for agent {pattern['agent_id']}: {insert_error}")

                # Queue commit for all inserts
                self._queue_db_commit()
                logging.info(f"[SQL] {len(high_value_patterns)} patterns queued for persistence")

                # BIG ROCK 40: Send validation requests to Deep Research agents
                for pattern in high_value_patterns:
                    validation_request = {
                        'pattern_id': f"{pattern['agent_id']}_{int(time.time())}",
                        'pattern_data': {
                            'agent_id': pattern['agent_id'],
                            'pattern_value': pattern['pattern_value'],
                            'prediction_score': pattern['pattern_value'] / 100.0,  # Normalize to 0-1
                            'interestingness_score': min(pattern['pattern_value'] * 1.2, 100),  # Boost for archived patterns
                            'raw_features': pattern['raw_features'],
                            'age_minutes': pattern['age_minutes'],
                            'decay_factor': pattern['decay_factor']
                        },
                        'timestamp': time.time()
                    }
                    self.redis_client.publish("pattern-validation-request", json.dumps(validation_request))

                logging.info(f"[VALIDATION] Sent {len(high_value_patterns)} validation requests to Deep Research agents")
            else:
                elapsed_minutes = self.step_counter // 60
                logging.info(f"[ARCHIVE] Step {self.step_counter} ({elapsed_minutes}min): No high-value patterns to archive (threshold: 40)")

        except Exception as e:
            logging.error(f"[ARCHIVE] Error during pattern archiving: {e}")
