# src/agents/pattern_learner_agent.py
import logging
from .base_agent import MycelialAgent
import pandas as pd
import time
import random

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

    def step(self):
        """This agent is reactive to market data ticks."""
        pass

    def handle_system_control(self, message: dict):
        if message.get("command") == "HALT_TRADING":
            self.trading_halted = True
            logging.critical(f"[{self.name}] TRADING HALTED by Risk Manager. Reason: {message.get('reason')}")

    def handle_market_data(self, message: dict):
        """
        Callback for new market data. Now uses the rich 'features' set.
        """
        if self.trading_halted:
            return

        try:
            features = message.get('features')
            if not features:
                return # Ignore if features are still building up

            # 1. Extract Rich Features
            current_rsi = features.get('RSI')
            current_mom = features.get('MOM')
            current_atr = features.get('ATR')
            current_close = features.get('close')

            # 2. --- Feature-Based FRL Strategy (Initial Swarm Logic) ---

            # Condition 1: RSI shows oversold (Buy pressure)
            buy_condition = current_rsi < 30
            # Condition 2: Momentum confirms upward trend
            mom_condition = current_mom > 0

            # BUY Logic: Oversold AND positive momentum (ignoring ATR for simplicity in this MVP)
            if buy_condition and mom_condition and self.position == "FLAT":
                logging.info(f"[{self.name}] BUY Signal (RSI:{current_rsi:.1f}, MOM:{current_mom:.2f}).")
                self.position = "LONG"
                self.send_order(direction="buy")

            # SELL Logic: Overbought (RSI > randomized threshold) AND position is LONG
            elif current_rsi > self.rsi_threshold and self.position == "LONG":
                logging.info(f"[{self.name}] SELL Signal (RSI:{current_rsi:.1f}).")
                self.position = "FLAT"
                self.send_order(direction="sell")

            # --- FRL LOGGING (Crucial for the Swarm) ---
            # In a future step, this agent will publish its performance metrics
            # and prediction scores here, using the rich feature data.

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
