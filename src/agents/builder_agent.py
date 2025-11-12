# src/agents/builder_agent.py - BIG ROCK 43: Dynamic Agent Factory (Rule of 3)
import logging
from .base_agent import MycelialAgent
from .data_miner_agent import DataMinerAgent
from .technical_analysis_agent import TechnicalAnalysisAgent
from .pattern_learner_agent import PatternLearnerAgent
import time

class BuilderAgent(MycelialAgent):
    """
    BIG ROCK 43: Dynamic Agent Factory - The Autonomous Builder

    Listens for MEA team consensus on `prospecting-consensus` channel.
    When triggered, spawns complete agent teams for newly discovered assets:
    - 1x DataMinerAgent (market data feed)
    - 3x TechnicalAnalysisAgents (Rule of 3 baseline)
    - 15x PatternLearnerAgents (Mycelial swarm)

    This enables the system to dynamically scale to ANY profitable asset,
    not just hardcoded BTC/ETH pairs.

    Original Purpose (BIG ROCK 30): Request deduplication for tool requests
    Enhanced Purpose (BIG ROCK 43): Agent team deployment from consensus
    """
    def __init__(self, model):
        super().__init__(model)
        self.name = f"Builder_{self.unique_id}"

        # Dual-channel listening
        self.request_channel = "system-build-request"  # Legacy tool requests
        self.consensus_channel = "prospecting-consensus"  # New: MEA consensus

        # BIG ROCK 30: Request deduplication (tool requests)
        self.tool_request_cache = {}
        self.request_ttl = 60  # 60-second TTL

        # BIG ROCK 43: Deployment tracking
        self.recent_deployments = {}  # {pair: timestamp}
        self.deployment_cooldown = 3600  # 1 hour cooldown per pair
        self.max_active_assets = 15  # Q3: Hard limit

        # Track deployment statistics
        self.total_deployments = 0
        self.successful_deployments = 0
        self.rejected_deployments = 0

        # Register listeners
        self._register_listener(self.request_channel, self.handle_build_request)
        self._register_listener(self.consensus_channel, self.handle_consensus)

        logging.info(
            f"[{self.name}] Builder Agent initialized | "
            f"Max assets: {self.max_active_assets} | "
            f"Cooldown: {self.deployment_cooldown}s"
        )

    def step(self):
        """The BuilderAgent is purely reactive to consensus/requests."""
        pass

    def handle_consensus(self, message: dict):
        """
        BIG ROCK 43: CRITICAL - Deploy agent teams for MEA consensus

        Triggered when MEA team reaches 2/3 consensus (>70% confidence).
        Spawns complete agent ecosystem for discovered asset.

        This is the HEART of the dynamic prospecting engine.
        """
        try:
            pair = message.get('pair')
            team_type = message.get('team_type')
            confidence = message.get('confidence', 0)
            votes = message.get('votes', 0)

            if not pair:
                logging.warning(f"[{self.name}] Consensus message missing pair: {message}")
                return

            logging.info(
                f"[{self.name}] 🎯 CONSENSUS RECEIVED: {pair} | "
                f"Team: {team_type} | Votes: {votes} | Confidence: {confidence:.2%}"
            )

            # Q3: Check if we're at capacity
            current_asset_count = len(getattr(self.model, 'active_assets', {}))
            if current_asset_count >= self.max_active_assets:
                self.rejected_deployments += 1
                logging.warning(
                    f"[{self.name}] ❌ DEPLOYMENT REJECTED: {pair} | "
                    f"Reason: At max capacity ({current_asset_count}/{self.max_active_assets})"
                )
                return

            # Check deployment cooldown (prevent duplicate deployments)
            current_time = time.time()
            if pair in self.recent_deployments:
                time_since_deploy = current_time - self.recent_deployments[pair]
                if time_since_deploy < self.deployment_cooldown:
                    logging.debug(
                        f"[{self.name}] Deployment for {pair} on cooldown "
                        f"({time_since_deploy:.0f}s / {self.deployment_cooldown}s)"
                    )
                    return

            # Check if already active (in case model.active_assets exists)
            if hasattr(self.model, 'active_assets') and pair in self.model.active_assets:
                logging.debug(f"[{self.name}] {pair} already active, skipping deployment")
                return

            # 🚀 DEPLOY AGENT TEAMS
            logging.critical(
                f"[{self.name}] 🚀 DEPLOYING AGENT TEAMS FOR {pair} 🚀"
            )

            deployment_success = self._deploy_agent_teams(pair, team_type, confidence)

            if deployment_success:
                self.successful_deployments += 1
                self.total_deployments += 1
                self.recent_deployments[pair] = current_time

                # Register with model (if model has active_assets tracking)
                if hasattr(self.model, 'register_active_asset'):
                    self.model.register_active_asset(pair, team_type, confidence)

                logging.critical(
                    f"[{self.name}] ✅ DEPLOYMENT SUCCESSFUL: {pair} | "
                    f"Total deployments: {self.successful_deployments}"
                )
            else:
                self.rejected_deployments += 1
                logging.error(f"[{self.name}] ❌ DEPLOYMENT FAILED: {pair}")

        except Exception as e:
            logging.error(f"[{self.name}] Error handling consensus: {e}", exc_info=True)

    def _deploy_agent_teams(self, pair: str, team_type: str, confidence: float) -> bool:
        """
        BIG ROCK 43: Spawn complete agent ecosystem for new asset

        Deploys:
        1. 1x DataMinerAgent - Fetch OHLCV data from Kraken
        2. 3x TechnicalAnalysisAgents - Calculate RSI/MACD/BB (Rule of 3)
        3. 15x PatternLearnerAgents - Discover causal patterns (Swarm)

        Total: 19 new agents per asset

        Returns: True if successful, False if failed
        """
        try:
            new_agents = []

            # 1. Deploy DataMinerAgent (market data source)
            logging.info(f"[{self.name}]   → Deploying DataMiner for {pair}")
            miner = DataMinerAgent(
                self.model,
                pair_to_watch=pair,
                period=14  # Default TA period
            )
            new_agents.append(miner)
            self.model.schedule.add(miner)

            # 2. Deploy TAA Team (3 agents for Rule of 3 baseline)
            logging.info(f"[{self.name}]   → Deploying 3x TA team for {pair}")
            for team_id in [1, 2, 3]:
                taa = TechnicalAnalysisAgent(
                    self.model,
                    pair_to_watch=pair,
                    team_id=team_id
                )
                new_agents.append(taa)
                self.model.schedule.add(taa)

            # 3. Deploy PatternLearner Swarm (15 agents)
            logging.info(f"[{self.name}]   → Deploying 15x PatternLearner swarm for {pair}")
            for i in range(15):
                learner = PatternLearnerAgent(
                    self.model,
                    pair_to_trade=pair,
                    product_focus="Finance",  # All focus on Finance for trading
                    rsi_threshold=70,  # Default parameters
                    atr_multiplier=1.0,
                    parent_id=None,
                    generation=0
                )
                new_agents.append(learner)
                self.model.schedule.add(learner)

            # Verify all agents registered
            agent_count = len(new_agents)
            if agent_count != 19:  # 1 miner + 3 TAA + 15 learners = 19
                logging.warning(
                    f"[{self.name}] Unexpected agent count: {agent_count} (expected 19)"
                )

            logging.info(
                f"[{self.name}]   ✅ Successfully deployed {agent_count} agents for {pair}"
            )

            return True

        except Exception as e:
            logging.error(
                f"[{self.name}] Error deploying agent teams for {pair}: {e}",
                exc_info=True
            )
            return False

    def handle_build_request(self, message: dict):
        """
        BIG ROCK 30: Legacy handler for tool/data source requests

        Processes requests from Swarm Brains that identify missing tools.
        Implements 60-second deduplication to prevent log spam.

        This is the ORIGINAL BuilderAgent purpose (autonomous code generation).
        Future: Use LLM (Claude) to generate agent code on-demand.
        """
        tool_needed = message.get('tool_needed', 'UNKNOWN')
        reason = message.get('reason', 'None provided')

        # BIG ROCK 30: Deduplication check
        current_time = time.time()

        # Clean up expired cache entries
        expired_tools = [
            tool for tool, timestamp in self.tool_request_cache.items()
            if current_time - timestamp > self.request_ttl
        ]
        for tool in expired_tools:
            del self.tool_request_cache[tool]

        # Check if this tool was recently requested
        if tool_needed in self.tool_request_cache:
            time_since_last = current_time - self.tool_request_cache[tool_needed]
            logging.debug(
                f"[{self.name}] Duplicate tool request for {tool_needed} ignored "
                f"(last request {time_since_last:.1f}s ago)"
            )
            return

        # New unique request - process and cache it
        self.tool_request_cache[tool_needed] = current_time

        logging.critical(f"[{self.name}] 🔧 TOOL BUILD REQUEST RECEIVED! 🔧")
        logging.critical(f"[{self.name}] TARGET: {tool_needed}")
        logging.critical(f"[{self.name}] REASON: {reason}")

        # --- Future Autonomy Logic (Phase 5) ---
        # 1. LLM Integration: Use Claude API to generate agent code
        # 2. Code Execution: Save new agent file to src/agents/
        # 3. Hot Reload: Dynamically import and instantiate new agent
        # 4. Validation: Test agent functionality before full deployment

        # For now, we log for human review
        logging.info(
            f"[{self.name}] Tool request logged. Manual implementation required."
        )

    def get_deployment_stats(self) -> dict:
        """
        Return deployment statistics for dashboard/monitoring
        """
        return {
            "total_deployments": self.total_deployments,
            "successful_deployments": self.successful_deployments,
            "rejected_deployments": self.rejected_deployments,
            "active_cooldowns": len(self.recent_deployments),
            "current_capacity": len(getattr(self.model, 'active_assets', {})),
            "max_capacity": self.max_active_assets
        }
