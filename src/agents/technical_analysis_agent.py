# src/agents/technical_analysis_agent.py - BIG ROCK 39: TA Competitive Advantage Layer
import logging
from .base_agent import MycelialAgent
import time
import random
import json

class TechnicalAnalysisAgent(MycelialAgent):
    """
    Executes standard technical analysis patterns (RSI, MACD, Bollinger Bands, etc.)
    to provide baseline validation and competitive metrics.

    Purpose: Provides a competitive baseline for the AI-discovered patterns.
    If Mycelial patterns outperform TA signals, we have provable competitive advantage.
    """
    def __init__(self, model):
        super().__init__(model)
        self.name = f"TA_{self.unique_id}"
        self.signal_frequency = 5  # Steps between analysis
        self.steps_since_signal = 0
        self.last_signal = None
        self.total_signals = 0

        logging.info(f"[{self.name}] Initialized. Technical Analysis baseline active (Signal frequency: {self.signal_frequency} steps)")

    def step(self):
        """Generate TA signals periodically."""
        self.steps_since_signal += 1

        if self.steps_since_signal >= self.signal_frequency:
            self._generate_ta_signal()
            self.steps_since_signal = 0

    def _generate_ta_signal(self):
        """
        BIG ROCK 41: Generate TA signals with direction for Profit Gateway cross-reference.

        In production, this would pull real market data and calculate actual TA indicators.
        For now, we simulate realistic TA signals with typical confidence ranges.
        """
        try:
            # Simulate standard TA signal types
            signal_types = [
                ("MACD Cross", "buy"),
                ("RSI Oversold", "buy"),
                ("RSI Overbought", "sell"),
                ("Momentum Breakout", "buy"),
                ("Bollinger Band Squeeze", "buy"),
                ("Moving Average Crossover", "buy")
            ]

            signal_type, direction = random.choice(signal_types)
            # TA signals typically have 50-70% confidence
            confidence = random.uniform(0.50, 0.70)

            # BIG ROCK 41: Include trading pairs for cross-reference
            pairs = ["XXBTZUSD", "XETHZUSD"]
            pair = random.choice(pairs)

            self.last_signal = {
                "type": signal_type,
                "direction": direction,
                "pair": pair,
                "confidence": confidence,
                "timestamp": time.time()
            }

            self.total_signals += 1

            # BIG ROCK 41 (Corrected): Publish TA baseline trade ideas
            message = {
                "sender": self.name,
                "signal_type": signal_type,
                "direction": direction,  # 'buy' or 'sell'
                "pair": pair,  # Trading pair
                "order_type": "market",
                "amount": 0.001,
                "confidence": confidence,
                "source": "baseline",  # Mark as baseline TA signal
                "timestamp": time.time()
            }
            self.publish("baseline-trade-ideas", message)

            if self.total_signals % 10 == 1:  # Log periodically
                logging.info(
                    f"[{self.name}] {signal_type} signal: {direction.upper()} {pair} "
                    f"(Confidence: {confidence:.2f}) - Total signals: {self.total_signals}"
                )
            else:
                logging.debug(f"[{self.name}] {signal_type} signal: {direction.upper()} {pair} (Confidence: {confidence:.2f})")

        except Exception as e:
            logging.error(f"[{self.name}] Error generating TA signal: {e}")
