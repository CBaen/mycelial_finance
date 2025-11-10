# src/agents/pattern_learner_agent.py
import logging
from .base_agent import MycelialAgent
import pandas as pd
import time
import random
import numpy as np  # NEW IMPORT for vector data
import json  # NEW IMPORT for Vector DB serialization

class PatternLearnerAgent(MycelialAgent):
    """
    This is the "brain" of the system. It now analyzes the rich feature set
    (RSI, ATR, Momentum) to make trading decisions, preparing for FRL.
    """
    def __init__(self, model, pair_to_trade: str = "XXBTZUSD", product_focus: str = "Finance", rsi_threshold: int = 70, atr_multiplier: float = 1.0, parent_id: int | None = None, generation: int = 0):
        super().__init__(model)
        self.pair = pair_to_trade
        self.product_focus = product_focus  # "Finance", "Code", or "Logistics"
        self.name = f"SwarmBrain_{self.unique_id}_{product_focus}"

        # --- NEW: Lineage Tracking for Evolution Moat (Big Rock 10) ---
        self.parent_id = parent_id  # None for initial generation
        self.generation = generation  # 0 for initial, increments with evolution
        self.birth_timestamp = time.time()  # Track agent lifecycle

        # Strategy parameters (using features instead of SMAs)
        # We add randomization for strategy variance (Crucial for FRL)
        self.rsi_threshold = rsi_threshold + random.randint(-5, 5)
        self.atr_multiplier = atr_multiplier * random.uniform(0.8, 1.2)
        self.position = "FLAT"

        # Channels - Subscribe to appropriate data source based on product focus (5 PILLARS)
        if product_focus == "Finance":
            self.market_data_channel = f"market-data:{self.pair.replace('/', '-')}"
        elif product_focus == "Code":
            self.market_data_channel = "repo-data:Python"  # RepoScraper channel
        elif product_focus == "Logistics":
            self.market_data_channel = "logistics-data:US-West"  # LogisticsMiner channel
        elif product_focus == "Government":
            self.market_data_channel = "govt-data:US-Federal"  # GovtDataMiner channel
        elif product_focus == "Corporations":
            self.market_data_channel = "corp-data:Tech"  # CorpDataMiner channel
        else:
            self.market_data_channel = f"market-data:{self.pair.replace('/', '-')}"

        self.order_channel = "trade-orders"
        self.control_channel = "system-control"

        # Listen to market data and control channels
        self._register_listener(self.market_data_channel, self.handle_market_data)
        self._register_listener(self.control_channel, self.handle_system_control)

        self.trading_halted = False
        self.prediction_score = 0.5  # Starts neutral (50% confidence)

    def step(self):
        """This agent is reactive to market data ticks."""
        pass

    def handle_system_control(self, message: dict):
        if message.get("command") == "HALT_TRADING":
            self.trading_halted = True
            logging.critical(f"[{self.name}] TRADING HALTED by Risk Manager. Reason: {message.get('reason')}")

    def handle_market_data(self, message: dict):
        """
        Callback for new market data. Now uses the rich 'features' set with FRL logging.
        """
        if self.trading_halted:
            return

        try:
            features = message.get('features')
            if not features:
                return  # Ignore if features are still building up

            # 1. Extract Rich Features
            current_rsi = features.get('RSI', 50)
            current_mom = features.get('MOM', 0)
            current_atr = features.get('ATR', 1)
            current_close = features.get('close', 0)

            # --- FRL LOGGING (Crucial for the Swarm) ---
            # 1. Prediction Score (Simulated: Confidence increases with Volatility + Momentum)
            self.prediction_score = np.clip(0.5 + (abs(current_mom) * 2) - (current_atr * 0.05), 0.1, 0.9)

            # 2. Create Strategy Vector (Belief State Moat)
            # This vector is the heart of the clustering/FRL logic.
            # It represents the agent's current belief about the market.
            # Vector elements: [RSI Threshold, ATR Multiplier, Current Momentum, RSI Confidence]
            strategy_vector = [
                self.rsi_threshold,
                self.atr_multiplier,
                current_mom,
                100 - abs(50 - current_rsi) * 2  # Higher confidence when extreme RSI
            ]

            # 3. Log Prediction and Strategy to Vector DB
            # The swarm writes its current belief state (VectorDB access)
            log_data = {
                'prediction_score': self.prediction_score,
                'strategy_vector': strategy_vector,
                'close_price': current_close,
                # --- NEW: Lineage Tracking (Big Rock 10) ---
                'parent_id': self.parent_id,
                'generation': self.generation,
                'birth_timestamp': self.birth_timestamp,
                'agent_id': self.unique_id,
                # --- NEW: Product Moat Diversity (Big Rock 16) ---
                'product_focus': self.product_focus
            }
            # The Vector DB writes the current prediction for peers and dashboard to read
            if self.vector_db:  # type: ignore
                self.vector_db.set(f"policy:{self.name}", json.dumps(log_data))  # type: ignore

            # --- 4. Check for Missing Tools (Autonomous Request) ---
            # If the swarm hits a high-volatility zone but lacks data features, it requests a tool.
            if current_atr > 10 and 45 < current_rsi < 55:
                # Trigger the Builder Agent for the missing Logistics API (Product 3)
                self.publish("system-build-request", {
                    "tool_needed": "LogisticsRoutingAPI",
                    "reason": f"High volatility (ATR: {current_atr:.1f}) detected, requiring external logistics data for causal correlation."
                })

            # --- 5. Trading Logic (BIG ROCK 28: Prediction Score Threshold) ---
            # DECISION FILTER: Only act when prediction confidence exceeds 80%
            if self.prediction_score > 0.8 and self.position == "FLAT":
                # High confidence BUY signal
                if current_rsi < 30 and current_mom > 0:
                    self.position = "LONG"
                    self.send_order(direction="buy", current_close=current_close)
            elif self.position == "LONG" and current_rsi > self.rsi_threshold:
                # Exit LONG position
                self.position = "FLAT"
                self.send_order(direction="sell", current_close=current_close)

        except Exception as e:
            logging.error(f"[{self.name}] Error in strategy logic: {e}")

    def send_order(self, direction: str, current_close: float = 0):
        """
        BIG ROCK 28: Send order with Interestingness Score for Trader filtering.
        Calculates local interestingness based on agent's performance metrics.
        """
        # Calculate simplified Interestingness Score (0-100 scale)
        # Components:
        # 1. Performance (50%): Prediction score scaled to 0-50
        # 2. Confidence (30%): How extreme the decision is (scaled to 0-30)
        # 3. Activity (20%): Generation bonus (scaled to 0-20)

        performance_score = self.prediction_score * 50  # 0-50 range
        confidence_score = min(abs(self.prediction_score - 0.5) * 60, 30)  # How far from neutral (0-30)
        activity_score = min(self.generation * 2 + 10, 20)  # Evolution bonus (0-20)

        interestingness_score = performance_score + confidence_score + activity_score

        order_message = {
            "source": self.name,
            "pair": self.pair,
            "order_type": "market",
            "direction": direction,
            "amount": 0.001,
            # BIG ROCK 28: Include scores for Trader filtering
            "prediction_score": self.prediction_score,
            "interestingness_score": interestingness_score,
            "current_price": current_close,
            "agent_generation": self.generation,
            "product_focus": self.product_focus
        }

        logging.info(f"[{self.name}] Sending {direction} order with Interestingness={interestingness_score:.1f}, Prediction={self.prediction_score:.2f}")
        self.publish(self.order_channel, order_message)

    def simulate_peer_review(self):
        """
        Future FRL Evolution Hook: Agents review peer strategies and evolve.
        This method will be triggered when agents want to learn from high-performing peers.
        The offspring will inherit parent strategy parameters with small mutations.
        """
        try:
            if not self.vector_db:  # type: ignore
                return

            # Fetch all peer policies from Vector DB
            peer_keys = [k.decode('utf-8') if isinstance(k, bytes) else k
                        for k in self.vector_db.keys("policy:SwarmBrain_*")]  # type: ignore

            if len(peer_keys) < 5:
                return  # Not enough peers to learn from yet

            # Sample top-performing peers based on prediction scores
            peer_scores = []
            for key in peer_keys[:20]:  # Sample first 20 for performance
                data = self.vector_db.get(key)  # type: ignore
                if data:
                    policy = json.loads(data)  # type: ignore
                    peer_scores.append((key, policy.get('prediction_score', 0.5)))

            # Sort by prediction score (descending)
            peer_scores.sort(key=lambda x: x[1], reverse=True)

            # Log the top performer for potential evolution
            if peer_scores:
                top_peer_key, top_score = peer_scores[0]
                logging.info(f"[{self.name}] FRL: Top peer is {top_peer_key} with score {top_score:.3f}")
                # Future: Trigger agent creation with this parent's strategies

        except Exception as e:
            logging.error(f"[{self.name}] Error in peer review: {e}")
