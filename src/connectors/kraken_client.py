# src/connectors/kraken_client.py
import kraken.spot
from config.settings import KRAKEN_API_KEY, KRAKEN_API_SECRET
import logging
import threading
import time
# Import specific Kraken exceptions (KrakenException doesn't exist in current API)
from kraken.exceptions import (
    KrakenAuthenticationError,
    KrakenBadRequestError,
    KrakenRateLimitExceededError,
    KrakenServiceUnavailableError
)

class KrakenClient:
    """
    Our system's only interface to the Kraken exchange.
    Includes threading lock to prevent EAPI:Invalid nonce errors.

    PHASE 2.4: Added error recovery with exponential backoff and automatic reconnection.
    """
    def __init__(self):
        self.nonce_lock = threading.Lock()  # Nonce lock for thread safety
        self.max_retries = 3
        self.base_delay = 2.0  # seconds
        self.initialized = False

        try:
            if not KRAKEN_API_KEY or not KRAKEN_API_SECRET:
                logging.error("[KRAKEN] API Key/Secret not configured")
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
            self.initialized = True
            logging.info("[KRAKEN] Client initialized and connection tested")
        except Exception as e:
            logging.error(f"[KRAKEN] Failed to initialize: {e}")
            self.user = None
            self.market = None
            self.trade = None

    def _retry_with_backoff(self, operation, *args, **kwargs):
        """
        PHASE 2.4: Execute operation with exponential backoff retry logic

        Handles transient errors (network issues, rate limits) with automatic retry.
        Permanent errors (auth failures) are not retried.
        """
        for attempt in range(self.max_retries):
            try:
                return operation(*args, **kwargs)

            except (KrakenAuthenticationError, KrakenBadRequestError,
                    KrakenRateLimitExceededError, KrakenServiceUnavailableError) as e:
                error_msg = str(e).lower()

                # Don't retry authentication/permission errors
                if isinstance(e, KrakenAuthenticationError) or any(x in error_msg for x in ['permission', 'invalid key', 'invalid signature']):
                    logging.error(f"[KRAKEN] Auth error (not retrying): {e}")
                    raise

                # Retry transient errors
                if attempt < self.max_retries - 1:
                    delay = self.base_delay * (2 ** attempt)
                    logging.warning(
                        f"[KRAKEN] Error (attempt {attempt + 1}/{self.max_retries}): {e} | "
                        f"Retrying in {delay}s..."
                    )
                    time.sleep(delay)
                else:
                    logging.error(f"[KRAKEN] Failed after {self.max_retries} attempts: {e}")
                    raise

            except Exception as e:
                # Catch-all for unexpected errors (graceful degradation)
                logging.warning(f"[KRAKEN] Unexpected error: {type(e).__name__}: {e}")
                if attempt < self.max_retries - 1:
                    delay = self.base_delay * (2 ** attempt)
                    logging.warning(f"Retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    logging.error(f"[KRAKEN] Failed after {self.max_retries} attempts with unexpected error")
                    return None  # Graceful degradation: return None instead of crashing

            except (ConnectionError, TimeoutError) as e:
                if attempt < self.max_retries - 1:
                    delay = self.base_delay * (2 ** attempt)
                    logging.warning(
                        f"[KRAKEN] Connection error (attempt {attempt + 1}/{self.max_retries}): {e} | "
                        f"Retrying in {delay}s..."
                    )
                    time.sleep(delay)
                else:
                    logging.error(f"[KRAKEN] Connection failed after {self.max_retries} attempts")
                    return {}

            except Exception as e:
                logging.error(f"[KRAKEN] Unexpected error: {e}")
                if attempt < self.max_retries - 1:
                    delay = self.base_delay * (2 ** attempt)
                    time.sleep(delay)
                else:
                    return {}

    def get_account_balance(self) -> dict:
        """
        PHASE 2.4: Fetches the user's account balance with retry logic.
        Uses lock for thread safety and automatic retry on transient failures.
        """
        if not self.user:
            logging.error("[KRAKEN] Client not initialized")
            return {}

        def _fetch_balance():
            with self.nonce_lock:
                result = self.user.get_account_balance()
                time.sleep(0.5)  # Nonce sequencing delay
                return result

        try:
            return self._retry_with_backoff(_fetch_balance)
        except Exception as e:
            logging.error(f"[KRAKEN] Failed to fetch account balance: {e}")
            return {}

    def get_market_data(self, pair: str) -> dict:
        """
        PHASE 2.4: Fetches the latest ticker information with retry logic.
        Market endpoint does not need lock, but includes automatic retry.
        """
        if not self.market:
            logging.error("[KRAKEN] Market client not initialized")
            return {}

        def _fetch_ticker():
            result = self.market.get_ticker(pair=pair)
            if result and isinstance(result, dict) and pair in result:
                return result[pair]
            return result if result else {}

        try:
            return self._retry_with_backoff(_fetch_ticker)
        except Exception as e:
            logging.error(f"[KRAKEN] Failed to fetch market data for {pair}: {e}")
            return {}

    def place_order(self, pair: str, order_type: str, direction: str, amount: float, price: float = None) -> dict:
        """
        PHASE 2.4: Places a new order with retry logic.
        Uses lock for thread safety and automatic retry on transient failures.
        """
        if not self.trade:
            logging.error("[KRAKEN] Trade client not initialized")
            return {"status": "error", "message": "Client not initialized"}

        order_params = {
            'ordertype': order_type,
            'side': direction,
            'pair': pair,
            'volume': amount,
            'validate': True
        }
        if order_type == 'limit' and price:
            order_params['price'] = price

        def _create_order():
            with self.nonce_lock:
                result = self.trade.create_order(**order_params)
                time.sleep(0.5)  # Nonce sequencing delay
                return result

        try:
            return self._retry_with_backoff(_create_order)
        except Exception as e:
            logging.error(f"[KRAKEN] Failed to place order: {e}")
            return {"status": "error", "message": str(e)}
