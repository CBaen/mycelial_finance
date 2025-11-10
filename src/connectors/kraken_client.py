# src/connectors/kraken_client.py
import kraken_sdk
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
                return

            self.client = kraken_sdk.Client(KRAKEN_API_KEY, KRAKEN_API_SECRET)
            # Test connection
            self.client.get_account_balance()
            logging.info("KrakenClient initialized and connection tested.")
        except Exception as e:
            logging.error(f"Failed to initialize KrakenClient: {e}")
            self.client = None

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
        if not self.client:
            logging.error("Kraken client not initialized.")
            return {}
        try:
            # The v1 'Ticker' endpoint is good for this
            result = self.client.get_ticker_information(pair)
            if 'result' in result:
                # The structure is a bit nested
                pair_key = list(result['result'].keys())[0]
                return result['result'][pair_key]
            return {}
        except Exception as e:
            logging.error(f"Error fetching market data for {pair}: {e}")
            return {}

    def place_order(self, pair: str, order_type: str, direction: str, amount: float, price: float = None) -> dict:
        """
        Places a new order on the exchange.
        direction: 'buy' or 'sell'
        order_type: 'market' or 'limit'
        """
        if not self.client:
            logging.error("Kraken client not initialized. Order cancelled.")
            return {"status": "error", "message": "Client not initialized."}

        params = {
            'pair': pair,
            'type': direction,
            'ordertype': order_type,
            'volume': str(amount),
            'validate': True # Test order before executing
        }
        if order_type == 'limit' and price:
            params['price'] = str(price)

        try:
            # We use 'add_order' from the SDK
            result = self.client.add_order(params)
            logging.info(f"Order placed: {result}")
            return result
        except Exception as e:
            logging.error(f"Error placing order: {e}")
            return {"status": "error", "message": str(e)}
