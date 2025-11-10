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
    def __init__(self, model, pair_to_trade: str, rsi_threshold: int = 70, atr_multiplier: float = 1.0):
        super().__init__(model)
        self.pair = pair_to_trade
        self.name = f"SwarmBrain_{self.unique_id}"

        # Strategy parameters (using features instead of SMAs)
        # We add randomization for strategy variance (Crucial for FRL)
        self.rsi_threshold = rsi_threshold + random.randint(-5, 5)
        self.atr_multiplier = atr_multiplier * random.uniform(0.8, 1.2)
        self.position = "FLAT"

        # Channels
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
                'close_price': current_close
            }
            # The Vector DB writes the current prediction for peers and dashboard to read
            self.vector_db.set(f"policy:{self.name}", json.dumps(log_data))

            # --- 4. Check for Missing Tools (Autonomous Request) ---
            # If the swarm hits a high-volatility zone but lacks data features, it requests a tool.
            if current_atr > 10 and 45 < current_rsi < 55:
                # Trigger the Builder Agent for the missing Logistics API (Product 3)
                self.publish("system-build-request", {
                    "tool_needed": "LogisticsRoutingAPI",
                    "reason": f"High volatility (ATR: {current_atr:.1f}) detected, requiring external logistics data for causal correlation."
                })

            # --- 5. Trading Logic ---
            buy_condition = current_rsi < 30
            mom_condition = current_mom > 0

            if buy_condition and mom_condition and self.position == "FLAT":
                self.position = "LONG"
                self.send_order(direction="buy")
            elif current_rsi > self.rsi_threshold and self.position == "LONG":
                self.position = "FLAT"
                self.send_order(direction="sell")

        except Exception as e:
            logging.error(f"[{self.name}] Error in strategy logic: {e}")

    def send_order(self, direction: str):
        order_message = {
            "source": self.name,
            "pair": self.pair,
            "order_type": "market",
            "direction": direction,
            "amount": 0.001
        }
        self.publish(self.order_channel, order_message)
