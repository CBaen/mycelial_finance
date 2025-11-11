# src/agents/pattern_learner_agent.py - BIG ROCK 41: Alpha Tournament (ProfitSeekerAgent)
import logging
from .base_agent import MycelialAgent
import pandas as pd
import time
import random
import numpy as np
import json
from collections import deque

class PatternLearnerAgent(MycelialAgent):
    """
    BIG ROCK 41: ProfitSeekerAgent - The Alpha Tournament Engine

    This agent now calculates Simulated P&L for every pattern and publishes
    high-P&L trade ideas to the 'trade-ideas' channel for the Trading Agent
    to execute after cross-referencing with TA signals.
    """
    def __init__(self, model, pair_to_trade: str = "XXBTZUSD", product_focus: str = "Finance", rsi_threshold: int = 70, atr_multiplier: float = 1.0, parent_id: int | None = None, generation: int = 0):
        super().__init__(model)
        self.pair = pair_to_trade
        self.product_focus = product_focus
        self.name = f"SwarmBrain_{self.unique_id}_{product_focus}"

        # Lineage Tracking for Evolution Moat
        self.parent_id = parent_id
        self.generation = generation
        self.birth_timestamp = time.time()

        # Strategy parameters with randomization for variance
        self.rsi_threshold = rsi_threshold + random.randint(-5, 5)
        self.atr_multiplier = atr_multiplier * random.uniform(0.8, 1.2)
        self.position = "FLAT"

        # BIG ROCK 41: P&L Tracking for Profit-Seeking
        self.trade_history = deque(maxlen=100)  # Last 100 simulated trades
        self.total_pnl = 0.0
        self.win_rate = 0.0
        self.entry_price = 0.0
        self.trade_count = 0

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
            # BIG ROCK 33: Pattern Decay Management
            current_time = time.time()
            pattern_age_seconds = current_time - self.birth_timestamp
            pattern_age_minutes = pattern_age_seconds / 60.0

            # Pattern decay: 5% value loss per 10 minutes
            decay_rate = 0.05 / 10.0  # 0.5% per minute
            pattern_decay_factor = max(0.0, 1.0 - (pattern_age_minutes * decay_rate))
            pattern_current_value = self.prediction_score * pattern_decay_factor * 100  # 0-100 scale

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
                'product_focus': self.product_focus,
                # --- NEW: Pattern Decay (Big Rock 33) ---
                'pattern_age_minutes': round(pattern_age_minutes, 2),
                'pattern_decay_factor': round(pattern_decay_factor, 3),
                'pattern_current_value': round(pattern_current_value, 1),
                'pattern_created_timestamp': self.birth_timestamp,
                # --- RAW FEATURE DATA (Big Rock 32) ---
                'raw_features': {
                    'RSI': round(current_rsi, 2),
                    'ATR': round(current_atr, 2),
                    'MOM': round(current_mom, 4),
                    'close': round(current_close, 2)
                }
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

    def calculate_simulated_pnl(self, direction: str, current_price: float):
        """
        BIG ROCK 41: Backtest the trade and calculate Simulated P&L

        This function simulates what would happen if we executed this trade,
        tracking P&L to determine if this pattern is worth executing.
        """
        simulated_pnl = 0.0

        if direction == "buy":
            # Opening a LONG position
            self.entry_price = current_price
            self.trade_count += 1
            # P&L is 0 on entry
            simulated_pnl = 0.0

        elif direction == "sell" and self.entry_price > 0:
            # Closing a LONG position - calculate realized P&L
            # P&L = (Exit Price - Entry Price) / Entry Price * 100 (percentage)
            simulated_pnl = ((current_price - self.entry_price) / self.entry_price) * 100

            # Update cumulative stats
            self.total_pnl += simulated_pnl
            self.trade_history.append({
                'timestamp': time.time(),
                'direction': direction,
                'entry_price': self.entry_price,
                'exit_price': current_price,
                'pnl': simulated_pnl
            })

            # Update win rate
            wins = sum(1 for trade in self.trade_history if trade['pnl'] > 0)
            self.win_rate = (wins / len(self.trade_history)) * 100 if self.trade_history else 0.0

            # Reset entry price
            self.entry_price = 0.0

        return simulated_pnl

    def send_order(self, direction: str, current_close: float = 0):
        """
        BIG ROCK 41: Send order with Simulated P&L to 'trade-ideas' channel.
        Only high-P&L ideas are published for the Profit Gateway to evaluate.
        """
        # BIG ROCK 41: Calculate Simulated P&L via backtesting
        simulated_pnl = self.calculate_simulated_pnl(direction, current_close)

        # Calculate Interestingness Score (now includes P&L performance)
        # Components:
        # 1. Performance (40%): Prediction score scaled to 0-40
        # 2. P&L History (40%): Total P&L contribution (0-40)
        # 3. Confidence (20%): How extreme the decision is (0-20)

        performance_score = self.prediction_score * 40  # 0-40 range
        pnl_score = min(max(self.total_pnl, -20), 20) + 20  # Normalize -20 to +20 -> 0 to 40
        confidence_score = min(abs(self.prediction_score - 0.5) * 40, 20)  # 0-20

        interestingness_score = performance_score + pnl_score + confidence_score

        # BIG ROCK 41: Only publish high-P&L trade ideas (Profit-Seeking Filter)
        # Minimum P&L threshold: Only send if total P&L > -5% (not hemorrhaging money)
        if self.total_pnl < -5.0 and self.trade_count > 5:
            logging.warning(
                f"[{self.name}] Trade idea SUPPRESSED: Total P&L={self.total_pnl:.2f}% is too negative "
                f"(Win Rate: {self.win_rate:.1f}%)"
            )
            return  # Don't publish losing strategies

        # Create trade idea message for the Alpha Tournament
        trade_idea = {
            "source": self.name,
            "pair": self.pair,
            "order_type": "market",
            "direction": direction,
            "amount": 0.001,
            # BIG ROCK 41: Alpha Tournament Metrics
            "prediction_score": self.prediction_score,
            "interestingness_score": interestingness_score,
            "simulated_pnl": simulated_pnl,  # NEW: This trade's expected P&L
            "total_pnl": self.total_pnl,  # NEW: Agent's cumulative P&L
            "win_rate": self.win_rate,  # NEW: Win percentage
            "trade_count": self.trade_count,  # NEW: Number of trades executed
            "current_price": current_close,
            "agent_generation": self.generation,
            "product_focus": self.product_focus
        }

        logging.info(
            f"[{self.name}] Publishing trade idea: {direction} | "
            f"Interestingness={interestingness_score:.1f} | "
            f"Simulated P&L={simulated_pnl:.2f}% | "
            f"Total P&L={self.total_pnl:.2f}% | "
            f"Win Rate={self.win_rate:.1f}%"
        )

        # BIG ROCK 41 (Corrected): Publish to 'mycelial-trade-ideas' channel
        # The TradingAgent will look for Signal Collisions with baseline-trade-ideas
        self.publish("mycelial-trade-ideas", trade_idea)

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
