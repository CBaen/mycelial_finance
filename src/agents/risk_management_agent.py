# src/agents/risk_management_agent.py
import logging
from .base_agent import MycelialAgent

class RiskManagementAgent(MycelialAgent):
    """
    This agent is the "guardian." Its job is to monitor
    all system activity and prevent catastrophe (Part 7.2).
    It listens to trade confirmations and enforces risk rules.
    This is a simple implementation of the HAVEN concept (Part 3.4).
    """
    def __init__(self, model, max_drawdown: float = 0.10, halt_channel: str = "system-control"):
        super().__init__(model)
        self.name = f"RiskManager_{self.unique_id}"
        self.confirmation_channel = "trade-confirmations"
        self.halt_channel = halt_channel

        self.max_drawdown = max_drawdown
        # TODO: In a real system, this would be fetched from Kraken
        self.initial_portfolio_value = 10000.0
        self.current_portfolio_value = self.initial_portfolio_value
        self.peak_portfolio_value = self.initial_portfolio_value
        self.is_halted = False

        # Listen for trade confirmations
        self._register_listener(self.confirmation_channel, self.handle_trade_confirmation)

    def step(self):
        """
        The Risk Manager's step is for checking global state.
        For now, it's also reactive, but in the future,
        it could proactively check portfolio value.
        """
        pass

    def handle_trade_confirmation(self, message: dict):
        """
        Callback to process a trade confirmation and update P&L.
        """
        if self.is_halted:
            return # System is already halted

        try:
            logging.info(f"[{self.name}] Processing trade confirmation: {message}")

            # TODO: Add logic to update `self.current_portfolio_value`
            # This is complex and requires tracking fills, fees, and asset prices.
            # For now, we'll simulate a loss for testing in a later step.
            # Example (simulated loss):
            # if message['execution_result'].get('status') == 'success':
            #     self.current_portfolio_value -= 10 # Simulate a $10 loss per trade

            # Update peak portfolio value
            if self.current_portfolio_value > self.peak_portfolio_value:
                self.peak_portfolio_value = self.current_portfolio_value

            # Check drawdown
            drawdown = (self.peak_portfolio_value - self.current_portfolio_value) / self.peak_portfolio_value

            logging.debug(f"[{self.name}] Current Value: {self.current_portfolio_value}, Peak: {self.peak_portfolio_value}, Drawdown: {drawdown:.2%}")

            if drawdown > self.max_drawdown and not self.is_halted:
                self.trigger_system_halt(drawdown)

        except Exception as e:
            logging.error(f"[{self.name}] Error handling trade confirmation: {e}")

    def trigger_system_halt(self, drawdown: float):
        """
        Issues a system-wide HALT command via Redis.
        This is the "circuit breaker."
        """
        self.is_halted = True
        halt_message = {
            "source": self.name,
            "command": "HALT_TRADING",
            "reason": f"Maximum drawdown {self.max_drawdown * 100}% breached. Current drawdown: {drawdown * 100:.2f}%"
        }
        self.publish(self.halt_channel, halt_message)
        logging.critical(f"[{self.name}] SYSTEM HALT TRIGGERED! {halt_message['reason']}")
