# src/agents/pattern_learner_agent.py
import logging
from .base_agent import MycelialAgent
import pandas as pd

class PatternLearnerAgent(MycelialAgent):
    """
    This is the "brain" of the system (Part 3).
    It listens to market data, applies a strategy, and
    publishes trade orders.

    This first version uses a simple SMA Crossover.
    It MUST obey HALT commands from the RiskManagementAgent.
    """
    def __init__(self, unique_id, model, pair_to_trade: str, short_window: int = 10, long_window: int = 30):
        super().__init__(unique_id, model)
        self.pair = pair_to_trade
        self.name = f"PatternLearner_{self.pair}_{unique_id}"

        # Strategy parameters
        self.short_window = short_window
        self.long_window = long_window
        self.prices = []
        self.position = "FLAT" # "FLAT", "LONG"

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
        """Listens for HALT commands from the Risk Manager."""
        if message.get("command") == "HALT_TRADING":
            self.trading_halted = True
            logging.critical(f"[{self.name}] TRADING HALTED by Risk Manager. Reason: {message.get('reason')}")

    def handle_market_data(self, message: dict):
        """
        Callback for new market data. This is the core logic.
        """
        if self.trading_halted:
            logging.warning(f"[{self.name}] Trading is halted. Ignoring market data.")
            return # Do not trade

        try:
            # 'c' is 'last trade' price, in a nested list
            last_price = float(message['data']['c'][0])
            self.prices.append(last_price)

            # Need enough data to calculate SMAs
            if len(self.prices) < self.long_window:
                return

            # Keep price list from growing indefinitely
            if len(self.prices) > self.long_window * 2:
                self.prices.pop(0)

            # Calculate SMAs
            series = pd.Series(self.prices)
            sma_short = series.rolling(window=self.short_window).mean().iloc[-1]
            sma_long = series.rolling(window=self.long_window).mean().iloc[-1]

            # --- Crossover Logic ---
            # Golden Cross (Buy signal)
            if sma_short > sma_long and self.position == "FLAT":
                logging.info(f"[{self.name}] BUY Signal. SMA_Short ({sma_short}) > SMA_Long ({sma_long})")
                self.position = "LONG"
                self.send_order(direction="buy")

            # Death Cross (Sell signal)
            elif sma_short < sma_long and self.position == "LONG":
                logging.info(f"[{self.name}] SELL Signal. SMA_Short ({sma_short}) < SMA_Long ({sma_long})")
                self.position = "FLAT"
                self.send_order(direction="sell")

        except Exception as e:
            logging.error(f"[{self.name}] Error in strategy logic: {e}")

    def send_order(self, direction: str):
        """Publishes a trade order to the 'hands' (TradingAgent)."""
        order_message = {
            "source": self.name,
            "pair": self.pair,
            "order_type": "market",
            "direction": direction,
            "amount": 0.001 # TODO: Use a real position sizing algorithm
        }
        self.publish(self.order_channel, order_message)
