# src/agents/technical_analysis_agent.py - BIG ROCK 43: Dynamic TA Baseline (Rule of 3)
import logging
from .base_agent import MycelialAgent
import time
import random
import json
import numpy as np
from collections import deque

class TechnicalAnalysisAgent(MycelialAgent):
    """
    BIG ROCK 43: Dynamic Technical Analysis Agent - Rule of 3 Baseline

    Deployed in teams of 3 per asset by the Builder Agent.
    Calculates REAL TA indicators (RSI, MACD, Bollinger Bands) from market data.
    Provides competitive baseline for Mycelial AI patterns.

    Key Innovation from Original:
    - NO RANDOM SIGNALS: All signals calculated from actual market data
    - Dynamic pair support: `pair_to_watch` parameter (not hardcoded)
    - Subscribes to market-data:{pair} channels for real-time data
    - Slight parameter randomization for team diversity (Rule of 3)
    """
    def __init__(self, model, pair_to_watch: str, team_id: int):
        super().__init__(model)
        self.pair = pair_to_watch
        self.team_id = team_id
        self.name = f"TA_{pair_to_watch}_{team_id}"

        # Subscribe to market data for this specific pair
        self.market_channel = f"market-data:{pair_to_watch.replace('/', '-')}"
        self._register_listener(self.market_channel, self.handle_market_data)

        # TA parameters (Rule of 3: slight randomization for diversity)
        self.rsi_period = 14 + random.randint(-2, 2)  # 12-16 period
        self.macd_fast = 12 + random.randint(-1, 1)   # 11-13 fast
        self.macd_slow = 26 + random.randint(-2, 2)   # 24-28 slow
        self.macd_signal = 9
        self.bb_period = 20 + random.randint(-2, 2)   # 18-22 period
        self.bb_std_dev = 2.0

        # Market data buffer (need 50+ ticks for indicators)
        self.market_buffer = deque(maxlen=100)  # Store last 100 ticks

        # Previous indicator values (for crossover detection)
        self.prev_rsi = None
        self.prev_macd = None
        self.prev_signal_line = None

        # Signal tracking
        self.total_signals = 0
        self.last_signal_time = 0
        self.signal_cooldown = 10  # Minimum 10 seconds between signals

        logging.info(
            f"[{self.name}] TA Agent initialized for {pair_to_watch} | "
            f"RSI={self.rsi_period} MACD=({self.macd_fast},{self.macd_slow},{self.macd_signal}) BB={self.bb_period}"
        )

    def step(self):
        """
        Purely reactive agent - signals generated from handle_market_data callbacks
        """
        pass

    def handle_market_data(self, message: dict):
        """
        CRITICAL FIX: Real TA calculations (not random)

        Triggered by market data ticks from DataMinerAgent.
        Calculates RSI, MACD, and Bollinger Bands from actual price data.
        """
        try:
            features = message.get('features')
            if not features:
                return

            # Add to rolling buffer
            tick_data = {
                'close': features.get('close', 0),
                'high': features.get('high', features.get('close', 0)),
                'low': features.get('low', features.get('close', 0)),
                'timestamp': message.get('timestamp', time.time())
            }

            self.market_buffer.append(tick_data)

            # Need at least 26 periods for MACD (slowest indicator)
            if len(self.market_buffer) < max(self.macd_slow, self.rsi_period):
                return

            # Extract price series
            close_prices = np.array([t['close'] for t in self.market_buffer])
            high_prices = np.array([t['high'] for t in self.market_buffer])
            low_prices = np.array([t['low'] for t in self.market_buffer])

            # Calculate indicators
            current_rsi = self._calculate_rsi(close_prices, self.rsi_period)
            macd_line, signal_line = self._calculate_macd(
                close_prices,
                self.macd_fast,
                self.macd_slow,
                self.macd_signal
            )
            upper_bb, lower_bb, middle_bb = self._calculate_bollinger_bands(
                close_prices,
                self.bb_period,
                self.bb_std_dev
            )

            current_price = close_prices[-1]

            # Generate signal based on REAL indicators
            signal = self._generate_signal_from_indicators(
                current_rsi,
                macd_line,
                signal_line,
                current_price,
                upper_bb,
                lower_bb,
                middle_bb
            )

            # Update previous values for next crossover detection
            self.prev_rsi = current_rsi
            self.prev_macd = macd_line
            self.prev_signal_line = signal_line

            # Publish signal if generated
            if signal:
                # Check cooldown
                time_since_last = time.time() - self.last_signal_time
                if time_since_last < self.signal_cooldown:
                    return  # Too soon after last signal

                self.publish(f"baseline-trade-ideas:{self.pair}", signal)
                self.total_signals += 1
                self.last_signal_time = time.time()

                logging.info(
                    f"[{self.name}] {signal['signal_type']}: {signal['direction'].upper()} | "
                    f"Confidence: {signal['confidence']:.2%} | "
                    f"RSI={current_rsi:.1f} MACD={macd_line:.4f} Price=${current_price:.2f}"
                )

        except Exception as e:
            logging.error(f"[{self.name}] Error in TA calculation: {e}", exc_info=True)

    def _generate_signal_from_indicators(
        self,
        rsi: float,
        macd: float,
        signal: float,
        price: float,
        upper_bb: float,
        lower_bb: float,
        middle_bb: float
    ) -> dict:
        """
        Real TA signal generation logic based on multiple indicators

        Generates signals when:
        - RSI oversold (<30) or overbought (>70)
        - MACD crossover (bullish/bearish)
        - Bollinger Band bounce (price at bands)
        - Moving average crossover (price vs middle BB)

        Returns strongest signal or None
        """
        signals = []

        # 1. RSI Signals
        if rsi < 30:
            # Oversold - buy signal
            confidence = (30 - rsi) / 30.0  # 0-1 scale (lower RSI = higher confidence)
            signals.append({
                "signal_type": "RSI Oversold",
                "direction": "buy",
                "confidence": min(confidence, 0.9),  # Cap at 90%
                "indicator_value": rsi
            })

        elif rsi > 70:
            # Overbought - sell signal
            confidence = (rsi - 70) / 30.0
            signals.append({
                "signal_type": "RSI Overbought",
                "direction": "sell",
                "confidence": min(confidence, 0.9),
                "indicator_value": rsi
            })

        # 2. MACD Crossover Signals
        if self.prev_macd is not None and self.prev_signal_line is not None:
            # Bullish crossover (MACD crosses above signal line)
            if macd > signal and self.prev_macd <= self.prev_signal_line:
                crossover_strength = abs(macd - signal)
                confidence = min(crossover_strength * 10, 0.85)  # Scale and cap

                signals.append({
                    "signal_type": "MACD Bullish Cross",
                    "direction": "buy",
                    "confidence": max(confidence, 0.55),  # Minimum 55%
                    "indicator_value": macd
                })

            # Bearish crossover (MACD crosses below signal line)
            elif macd < signal and self.prev_macd >= self.prev_signal_line:
                crossover_strength = abs(macd - signal)
                confidence = min(crossover_strength * 10, 0.85)

                signals.append({
                    "signal_type": "MACD Bearish Cross",
                    "direction": "sell",
                    "confidence": max(confidence, 0.55),
                    "indicator_value": macd
                })

        # 3. Bollinger Band Signals
        # Lower band bounce (oversold)
        if price <= lower_bb:
            # Distance from lower band indicates strength
            distance_pct = abs(price - lower_bb) / price * 100
            confidence = 0.70 if distance_pct < 0.1 else 0.60

            signals.append({
                "signal_type": "BB Lower Bounce",
                "direction": "buy",
                "confidence": confidence,
                "indicator_value": lower_bb
            })

        # Upper band bounce (overbought)
        elif price >= upper_bb:
            distance_pct = abs(price - upper_bb) / price * 100
            confidence = 0.70 if distance_pct < 0.1 else 0.60

            signals.append({
                "signal_type": "BB Upper Bounce",
                "direction": "sell",
                "confidence": confidence,
                "indicator_value": upper_bb
            })

        # 4. Moving Average Crossover (Price vs Middle BB)
        if price > middle_bb * 1.02:  # 2% above MA
            signals.append({
                "signal_type": "MA Breakout",
                "direction": "buy",
                "confidence": 0.65,
                "indicator_value": middle_bb
            })

        elif price < middle_bb * 0.98:  # 2% below MA
            signals.append({
                "signal_type": "MA Breakdown",
                "direction": "sell",
                "confidence": 0.65,
                "indicator_value": middle_bb
            })

        # Select strongest signal (highest confidence)
        if not signals:
            return None

        best_signal = max(signals, key=lambda s: s['confidence'])

        # Format for baseline-trade-ideas channel
        return {
            "sender": self.name,
            "pair": self.pair,
            "signal_type": best_signal['signal_type'],
            "direction": best_signal['direction'],
            "confidence": best_signal['confidence'],
            "order_type": "market",
            "amount": 0.001,
            "current_price": price,
            "source": "baseline",
            "indicator_value": best_signal['indicator_value'],
            "timestamp": time.time()
        }

    def _calculate_rsi(self, prices: np.ndarray, period: int = 14) -> float:
        """
        Calculate Relative Strength Index (RSI)

        RSI = 100 - (100 / (1 + RS))
        RS = Average Gain / Average Loss

        Returns: RSI value (0-100)
        """
        try:
            if len(prices) < period + 1:
                return 50.0  # Neutral

            # Calculate price deltas
            deltas = np.diff(prices[-period-1:])

            # Separate gains and losses
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)

            # Calculate average gain/loss
            avg_gain = np.mean(gains)
            avg_loss = np.mean(losses)

            if avg_loss == 0:
                return 100.0  # All gains

            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))

            return float(rsi)

        except Exception as e:
            logging.error(f"[{self.name}] RSI calculation error: {e}")
            return 50.0

    def _calculate_macd(
        self,
        prices: np.ndarray,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9
    ) -> tuple:
        """
        Calculate MACD (Moving Average Convergence Divergence)

        MACD Line = EMA(fast) - EMA(slow)
        Signal Line = EMA(MACD, signal_period)

        Returns: (macd_line, signal_line)
        """
        try:
            if len(prices) < slow_period:
                return (0.0, 0.0)

            # Calculate EMAs
            ema_fast = self._calculate_ema(prices, fast_period)
            ema_slow = self._calculate_ema(prices, slow_period)

            # MACD line
            macd_line = ema_fast - ema_slow

            # Calculate signal line (EMA of MACD)
            # For simplicity, use SMA as approximation
            if len(prices) >= slow_period + signal_period:
                macd_values = []
                for i in range(len(prices) - slow_period + 1):
                    window = prices[i:i+slow_period]
                    fast = self._calculate_ema(window, fast_period)
                    slow = self._calculate_ema(window, slow_period)
                    macd_values.append(fast - slow)

                macd_array = np.array(macd_values)
                signal_line = np.mean(macd_array[-signal_period:])
            else:
                signal_line = macd_line

            return (float(macd_line), float(signal_line))

        except Exception as e:
            logging.error(f"[{self.name}] MACD calculation error: {e}")
            return (0.0, 0.0)

    def _calculate_ema(self, prices: np.ndarray, period: int) -> float:
        """
        Calculate Exponential Moving Average (EMA)

        EMA = Price(today) * k + EMA(yesterday) * (1 - k)
        k = 2 / (period + 1)
        """
        try:
            if len(prices) < period:
                return float(np.mean(prices))

            # Use SMA as initial EMA value
            ema = float(np.mean(prices[:period]))

            # Calculate k (smoothing factor)
            k = 2.0 / (period + 1)

            # Calculate EMA for remaining values
            for price in prices[period:]:
                ema = (price * k) + (ema * (1 - k))

            return ema

        except Exception as e:
            logging.error(f"[{self.name}] EMA calculation error: {e}")
            return float(np.mean(prices))

    def _calculate_bollinger_bands(
        self,
        prices: np.ndarray,
        period: int = 20,
        std_dev: float = 2.0
    ) -> tuple:
        """
        Calculate Bollinger Bands

        Middle Band = SMA(period)
        Upper Band = Middle + (std_dev * standard deviation)
        Lower Band = Middle - (std_dev * standard deviation)

        Returns: (upper_band, lower_band, middle_band)
        """
        try:
            if len(prices) < period:
                mid = float(np.mean(prices))
                return (mid, mid, mid)

            # Calculate middle band (SMA)
            middle_band = float(np.mean(prices[-period:]))

            # Calculate standard deviation
            std = float(np.std(prices[-period:]))

            # Calculate bands
            upper_band = middle_band + (std_dev * std)
            lower_band = middle_band - (std_dev * std)

            return (upper_band, lower_band, middle_band)

        except Exception as e:
            logging.error(f"[{self.name}] Bollinger Bands calculation error: {e}")
            mid = float(np.mean(prices))
            return (mid, mid, mid)
