# src/connectors/kraken_client.py
from kraken.spot import User, Market, Trade
from config.settings import KRAKEN_API_KEY, KRAKEN_API_SECRET
import logging
import time

class KrakenClient:
    """
    Our system's only interface to the Kraken exchange.
    Handles all API connections, error handling, and rate limits.
    Based on research doc Part 6.1.
    """
    def __init__(self):
        try:
            if not KRAKEN_API_KEY or not KRAKEN_API_SECRET:
                logging.error("Kraken API Key/Secret not configured. Client will not initialize.")
                self.client = None
                self.user = None
                self.market = None
                self.trade = None
                return

            # Initialize the three main API clients
            self.user = User(key=KRAKEN_API_KEY, secret=KRAKEN_API_SECRET)
            self.market = Market(key=KRAKEN_API_KEY, secret=KRAKEN_API_SECRET)
            self.trade = Trade(key=KRAKEN_API_KEY, secret=KRAKEN_API_SECRET)
            self.client = self.user  # For backwards compatibility

            # Test connection
            self.user.get_account_balance()
            logging.info("KrakenClient initialized and connection tested.")
        except Exception as e:
            logging.error(f"Failed to initialize KrakenClient: {e}")
            self.client = None
            self.user = None
            self.market = None
            self.trade = None

    def get_account_balance(self) -> dict:
        """Fetches the user's account balance."""
        if not self.client:
            logging.error("Kraken client not initialized.")
            return {}
        try:
            return self.client.get_account_balance()
        except Exception as e:
            logging.error(f"Error fetching account balance: {e}")
            return {}

    def get_market_data(self, pair: str) -> dict:
        """Fetches the latest ticker information for a given pair."""
        if not self.market:
            logging.error("Kraken client not initialized.")
            return {}
        try:
            # Use the Market client to get ticker data
            result = self.market.get_ticker(pair=pair)
            if result and isinstance(result, dict) and pair in result:
                return result[pair]
            return result if result else {}
        except Exception as e:
            logging.error(f"Error fetching market data for {pair}: {e}")
            return {}

    def place_order(self, pair: str, order_type: str, direction: str, amount: float, price: float = None) -> dict:
        """
        Places a new order on the exchange.
        direction: 'buy' or 'sell'
        order_type: 'market' or 'limit'
        """
        if not self.trade:
            logging.error("Kraken client not initialized. Order cancelled.")
            return {"status": "error", "message": "Client not initialized."}

        try:
            # Build order parameters for the new SDK
            order_params = {
                'ordertype': order_type,
                'side': direction,
                'pair': pair,
                'volume': amount,
                'validate': True  # Test order before executing
            }
            if order_type == 'limit' and price:
                order_params['price'] = price

            # Use create_order from Trade client
            result = self.trade.create_order(**order_params)
            logging.info(f"Order placed: {result}")
            return result
        except Exception as e:
            logging.error(f"Error placing order: {e}")
            return {"status": "error", "message": str(e)}
