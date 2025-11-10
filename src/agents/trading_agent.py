# src/agents/trading_agent.py
import logging
from .base_agent import MycelialAgent

class TradingAgent(MycelialAgent):
    """
    This agent is the "hands" of the system. It is reactive
    and "dumb" on purpose. It only listens to the 'trade-orders'
    channel and executes trades via the Kraken client.
    It does not have its own "step" logic.
    """
    def __init__(self, model):
        super().__init__(model)
        self.name = f"Trader_{self.unique_id}"
        self.order_channel = "trade-orders"
        self.confirmation_channel = "trade-confirmations"

        # CRITICAL: Register the listener on initialization.
        self._register_listener(self.order_channel, self.handle_trade_order)

    def step(self):
        """
        This agent is purely reactive, so its step does nothing.
        Its logic is handled by the `handle_trade_order` callback.
        """
        pass

    def handle_trade_order(self, message: dict):
        """
        BIG ROCK 28: Filter orders by Interestingness Score (>75 threshold).
        This is the callback function triggered by a new message
        on the 'trade-orders' channel.
        """
        logging.info(f"[{self.name}] Received trade order: {message}")
        try:
            # Basic validation of the order message
            required_keys = ['pair', 'order_type', 'direction', 'amount']
            if not all(key in message for key in required_keys):
                logging.warning(f"[{self.name}] Invalid order received: {message}")
                return

            # BIG ROCK 28: HIGH-VALUE FILTER (Interestingness Score > 75)
            interestingness_score = message.get('interestingness_score', 0)
            if interestingness_score < 75:
                source_agent = message.get('source', 'Unknown')
                logging.warning(
                    f"[{self.name}] Order REJECTED from {source_agent}: "
                    f"Interestingness Score {interestingness_score:.1f} < 75 threshold"
                )
                return

            # Log HIGH-VALUE execution
            source_agent = message.get('source', 'Unknown')
            prediction_score = message.get('prediction_score', 0)
            logging.info(
                f"[{self.name}] Order APPROVED from {source_agent}: "
                f"Interestingness={interestingness_score:.1f}, Prediction={prediction_score:.2f}"
            )

            # Extract order details
            pair = message['pair']
            order_type = message['order_type']
            direction = message['direction']
            amount = float(message['amount'])
            price = message.get('price') # Optional, for limit orders

            # Execute the trade
            result = self.kraken_client.place_order(
                pair=pair,
                order_type=order_type,
                direction=direction,
                amount=amount,
                price=price
            )

            # Publish the result/confirmation for other agents (like Risk)
            confirmation_message = {
                "source": self.name,
                "original_order": message,
                "execution_result": result,
                "interestingness_score": interestingness_score  # Include for tracking
            }
            self.publish(self.confirmation_channel, confirmation_message)

        except Exception as e:
            logging.error(f"[{self.name}] Error handling trade order: {e}")
