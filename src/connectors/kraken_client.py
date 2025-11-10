# src/connectors/kraken_client.py
import kraken.spot
from config.settings import KRAKEN_API_KEY, KRAKEN_API_SECRET
import logging
import threading  # NEW IMPORT
import time

class KrakenClient:
    """
    Our system's only interface to the Kraken exchange.
    Now includes a threading lock to prevent EAPI:Invalid nonce errors.
    """
    def __init__(self):
        self.nonce_lock = threading.Lock()  # Nonce lock for thread safety
        try:
            if not KRAKEN_API_KEY or not KRAKEN_API_SECRET:
                logging.error("Kraken API Key/Secret not configured. Client will not initialize.")
                self.user = None
                self.market = None
                self.trade = None
                return

            # Initialize the three main API clients
            self.user = kraken.spot.User(key=KRAKEN_API_KEY, secret=KRAKEN_API_SECRET)
            self.market = kraken.spot.Market(key=KRAKEN_API_KEY, secret=KRAKEN_API_SECRET)
            self.trade = kraken.spot.Trade(key=KRAKEN_API_KEY, secret=KRAKEN_API_SECRET)

            # Test connection using the lock
            self.get_account_balance()
            logging.info("KrakenClient initialized and connection tested.")
        except Exception as e:
            logging.error(f"Failed to initialize KrakenClient: {e}")
            self.user = None
            self.market = None
            self.trade = None

    def get_account_balance(self) -> dict:
        """Fetches the user's account balance using a lock for thread safety."""
        if not self.user:
            logging.error("Kraken client not initialized.")
            return {}
        try:
            with self.nonce_lock:  # Apply lock here
                result = self.user.get_account_balance()
                time.sleep(0.5)  # Delay to ensure proper nonce sequencing with Kraken's server
                return result
        except Exception as e:
            logging.error(f"Error fetching account balance: {e}")
            return {}

    def get_market_data(self, pair: str) -> dict:
        """Fetches the latest ticker information for a given pair (Market endpoint does not need lock)."""
        if not self.market:
            logging.error("Kraken market client not initialized.")
            return {}
        try:
            result = self.market.get_ticker(pair=pair)
            if result and isinstance(result, dict) and pair in result:
                return result[pair]
            return result if result else {}
        except Exception as e:
            logging.error(f"Error fetching market data for {pair}: {e}")
            return {}

    def place_order(self, pair: str, order_type: str, direction: str, amount: float, price: float = None) -> dict:
        """Places a new order on the exchange using a lock for thread safety."""
        if not self.trade:
            logging.error("Kraken trade client not initialized. Order cancelled.")
            return {"status": "error", "message": "Client not initialized."}

        order_params = {
            'ordertype': order_type,
            'side': direction,
            'pair': pair,
            'volume': amount,
            'validate': True
        }
        if order_type == 'limit' and price:
            order_params['price'] = price

        try:
            with self.nonce_lock:  # Apply lock here
                result = self.trade.create_order(**order_params)
                time.sleep(0.5)  # Delay to ensure proper nonce sequencing with Kraken's server
                return result
        except Exception as e:
            logging.error(f"Error placing order: {e}")
            return {"status": "error", "message": str(e)}
