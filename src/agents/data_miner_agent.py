# src/agents/data_miner_agent.py
import logging
from .base_agent import MycelialAgent
import time
import pandas as pd
import numpy as np

# --- Technical Indicator Calculations (New) ---
def calculate_features(df: pd.DataFrame, period=14):
    """Calculates common technical features (RSI, ATR, MOM) on a DataFrame of closing prices."""
    if df.empty or len(df) < period + 1:
        return None

    # Calculate Price Change
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

    # Calculate RSI
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # Calculate ATR (Approximate method using High/Low/PrevClose)
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df['ATR'] = ranges.ewm(span=period, adjust=False).mean()

    # Calculate Momentum (Simple Rate of Change)
    df['MOM'] = df['close'].pct_change(periods=5) # 5-period rate of change

    # Return only the latest, enriched data point
    return df.iloc[-1].to_dict()

class DataMinerAgent(MycelialAgent):
    """
    This agent fetches market data, ENRICHES it with calculated features (RSI, ATR, MOM),
    and publishes the rich feature set to the Redis network.
    It is the system's "Data Engineer."
    """
    def __init__(self, model, pair_to_watch: str):
        super().__init__(model)
        self.pair = pair_to_watch
        self.channel = f"market-data:{self.pair.replace('/', '-')}"
        self.name = f"DataEngineer_{self.unique_id}" # Simplified name
        logging.info(f"[{self.name}] Initialized. Watching {self.pair} on channel {self.channel}")

        # Data storage buffer for calculating features (needs high, low, close)
        self.history_buffer = pd.DataFrame(columns=['close', 'high', 'low'])
        self.period = 14 # Standard period for calculations

    def step(self):
        logging.debug(f"[{self.name}] Fetching market data for {self.pair}...")
        try:
            market_data = self.kraken_client.get_market_data(self.pair)

            if market_data and 'c' in market_data:
                # 1. Extract raw prices (Kraken data is nested)
                close_price = float(market_data['c'][0])
                high_price = float(market_data['h'][0])
                low_price = float(market_data['l'][0])

                # 2. Add raw prices to history buffer
                new_row = pd.DataFrame({
                    'close': [close_price],
                    'high': [high_price],
                    'low': [low_price]
                })
                self.history_buffer = pd.concat([self.history_buffer, new_row], ignore_index=True)

                # Maintain buffer size (period * 3 for stability)
                if len(self.history_buffer) > self.period * 3:
                    self.history_buffer = self.history_buffer.iloc[-(self.period * 3):].reset_index(drop=True)

                # 3. Calculate enriched features
                enriched_data = calculate_features(self.history_buffer, self.period)

                if enriched_data:
                    # Prepare the message with full feature set
                    message = {
                        "source": self.name,
                        "pair": self.pair,
                        "timestamp": time.time(),
                        "features": enriched_data # This is the rich data moat
                    }
                    # 4. Publish enriched data
                    self.publish(self.channel, message)
                else:
                    logging.info(f"[{self.name}] Building history buffer. Length: {len(self.history_buffer)}")

            else:
                logging.warning(f"[{self.name}] No market data returned or invalid structure for {self.pair}")

        except Exception as e:
            logging.error(f"[{self.name}] Error in step: {e}")
