# src/agents/market_explorer_agent.py - BIG ROCK 43: The "Rule of 3" Prospecting Engine
import logging
from .base_agent import MycelialAgent
from typing import Literal
import time
import random
import json
import numpy as np

class MarketExplorerAgent(MycelialAgent):
    """
    BIG ROCK 43: "Rule of 3" Prospecting Engine - Dynamic Asset Discovery

    Organized into 3 specialist teams (3 agents each):
    - HFT Prospectors: High-frequency trading opportunities (minutes-hours)
    - Day-Trade Prospectors: Intraday opportunities (hours-days)
    - Swing-Trade Prospectors: Multi-day opportunities (days-weeks)

    Teams reach 2/3 consensus (>70% confidence) before triggering Builder Agent
    to dynamically deploy agent teams for discovered assets.

    Innovation: Cross-moat signals weighted 2x (Q6) - assets with Code/Gov/Logistics/Corp
    activity receive priority, creating informational edge over pure price-based systems.
    """
    def __init__(self, model, team_type: Literal["HFT", "DayTrade", "Swing"], team_id: int):
        super().__init__(model)
        self.team_type = team_type
        self.team_id = team_id
        self.name = f"MEA_{team_type}_{team_id}"

        # Q8: Team-specific cross-moat preferences based on timeframe
        self.moat_weights = self._get_moat_weights()

        # Prospecting parameters
        self.scan_frequency = 60  # Scan every 60 seconds (1 step = 1 second)
        self.steps_since_scan = 0
        self.confidence_threshold = 0.70  # Q1: 70% confidence minimum

        # Channels
        self.proposal_channel = f"prospecting-proposals:{team_type}"
        self.consensus_channel = "prospecting-consensus"

        # Discovery tracking
        self.total_proposals = 0
        self.successful_consensus = 0

        logging.info(
            f"[{self.name}] Market Explorer initialized | Team: {team_type} | "
            f"Moat weights: Code={self.moat_weights['code']:.1f} Gov={self.moat_weights['government']:.1f} "
            f"Logistics={self.moat_weights['logistics']:.1f} Corp={self.moat_weights['corporate']:.1f}"
        )

    def _get_moat_weights(self):
        """
        Q8: MEA team specialization for cross-moat signals
        Different teams prioritize different moats based on trading timeframe

        HFT: Fast-moving moats only (Code, Corporate)
        Day-Trade: Mix of fast and medium moats
        Swing: Slow-moving macro moats (Government, Logistics)
        """
        if self.team_type == "HFT":
            return {
                "code": 0.5,        # GitHub activity = fast-moving
                "corporate": 0.5,    # M&A activity = fast-moving
                "government": 0.0,   # Policy too slow for HFT
                "logistics": 0.0     # Supply chain too slow for HFT
            }
        elif self.team_type == "DayTrade":
            return {
                "code": 0.7,
                "corporate": 0.7,
                "government": 0.3,
                "logistics": 0.3
            }
        else:  # Swing
            return {
                "code": 0.3,
                "corporate": 0.3,
                "government": 1.0,   # Macro structural changes
                "logistics": 1.0     # Supply chain shifts
            }

    def step(self):
        """Scan Kraken markets every 60 steps (60 seconds)"""
        self.steps_since_scan += 1

        if self.steps_since_scan >= self.scan_frequency:
            self._scan_markets()
            self.steps_since_scan = 0

    def _scan_markets(self):
        """
        Scan all tradeable pairs on Kraken and calculate prospecting scores
        """
        try:
            # Fetch all tradeable pairs from Kraken
            tradeable_pairs = self._get_tradeable_pairs()

            if not tradeable_pairs:
                logging.warning(f"[{self.name}] No tradeable pairs returned from Kraken")
                return

            proposals_this_scan = 0

            for pair in tradeable_pairs:
                # Skip if already active (Q3: model tracks max 15 assets)
                if hasattr(self.model, 'active_assets') and pair in self.model.active_assets:
                    continue

                # Calculate prospecting score (0-8 scale)
                score_data = self._calculate_prospecting_score(pair)

                # Threshold: 4/8 points minimum
                if score_data['total_score'] >= 4:
                    # Publish proposal to team-specific channel
                    proposal = {
                        "source": self.name,
                        "team_type": self.team_type,
                        "team_id": self.team_id,
                        "pair": pair,
                        "score": score_data['total_score'],
                        "confidence": score_data['confidence'],
                        "breakdown": score_data['breakdown'],
                        "timestamp": time.time()
                    }

                    self.publish(self.proposal_channel, proposal)
                    proposals_this_scan += 1
                    self.total_proposals += 1

                    logging.info(
                        f"[{self.name}] Proposing {pair} | Score: {score_data['total_score']}/8 | "
                        f"Cross-Moat: {score_data['breakdown']['cross_moat']}/2 | "
                        f"Confidence: {score_data['confidence']:.2%}"
                    )

            if proposals_this_scan > 0:
                logging.info(f"[{self.name}] Scan complete: {proposals_this_scan} proposals submitted")

        except Exception as e:
            logging.error(f"[{self.name}] Error scanning markets: {e}")

    def _get_tradeable_pairs(self):
        """
        Fetch all tradeable pairs from Kraken API
        Returns list of pairs like ["XXBTZUSD", "XETHZUSD", "ADAUSD", ...]
        """
        try:
            # Get tradeable asset pairs from Kraken
            tradeable_pairs_data = self.kraken_client.market.get_tradable_asset_pairs()

            if not tradeable_pairs_data or 'result' not in tradeable_pairs_data:
                return []

            # Extract pairs that trade against USD
            usd_pairs = []
            for pair_name, pair_info in tradeable_pairs_data['result'].items():
                # Filter for USD pairs only
                if 'USD' in pair_name and pair_info.get('status') == 'online':
                    usd_pairs.append(pair_name)

            logging.debug(f"[{self.name}] Found {len(usd_pairs)} USD trading pairs on Kraken")
            return usd_pairs

        except Exception as e:
            logging.error(f"[{self.name}] Error fetching tradeable pairs: {e}")
            # Fallback to known pairs if API fails
            return ["XXBTZUSD", "XETHZUSD", "ADAUSD", "SOLUSD", "MATICUSD", "LINKUSD"]

    def _calculate_prospecting_score(self, pair: str) -> dict:
        """
        Calculate 8-point prospecting score:
        - 1 point each: volatility, volume, liquidity, momentum, novelty (5 criteria)
        - 0-2 points: cross-moat signal (Q6: double weight)

        Total: 0-8 scale
        """
        breakdown = {}

        try:
            # Fetch ticker data for this pair
            ticker_data = self._get_ticker_data(pair)

            if not ticker_data:
                return {"total_score": 0, "confidence": 0.0, "breakdown": {}}

            # 1. Volatility Score (ATR-based)
            atr = self._calculate_atr(ticker_data)
            breakdown['volatility'] = 1 if atr > 2.0 else 0

            # 2. Volume Score (daily USD volume > $10M)
            daily_volume_usd = self._calculate_daily_volume(ticker_data)
            breakdown['volume'] = 1 if daily_volume_usd > 10_000_000 else 0

            # 3. Liquidity Score (bid-ask spread < 0.5%)
            spread_pct = self._calculate_spread(ticker_data)
            breakdown['liquidity'] = 1 if spread_pct < 0.5 else 0

            # 4. Momentum Score (30-day price change > ±15%)
            momentum_30d = self._calculate_momentum(pair)
            breakdown['momentum'] = 1 if abs(momentum_30d) > 15 else 0

            # 5. Novelty Score (not already tracked)
            is_novel = pair not in getattr(self.model, 'active_assets', {})
            breakdown['novelty'] = 1 if is_novel else 0

            # 6. Cross-Moat Signal (0-2 points, Q6: double weight)
            cross_moat_score = self._query_cross_moat_signals(pair)
            breakdown['cross_moat'] = cross_moat_score

            # Total score (max 8 points: 5 criteria + 2 for cross-moat + 1 novelty)
            # Actually: 5 base + up to 2 cross-moat = 7, but we'll keep 8 scale for clarity
            total_score = sum(breakdown.values())

            # Confidence = normalized score (0-1 scale)
            confidence = total_score / 8.0

            return {
                "total_score": total_score,
                "confidence": confidence,
                "breakdown": breakdown
            }

        except Exception as e:
            logging.error(f"[{self.name}] Error calculating prospecting score for {pair}: {e}")
            return {"total_score": 0, "confidence": 0.0, "breakdown": {}}

    def _get_ticker_data(self, pair: str):
        """
        Fetch ticker data for specific pair from Kraken
        """
        try:
            ticker = self.kraken_client.market.get_ticker(pair=pair)
            if ticker and 'result' in ticker:
                return ticker['result'].get(pair, {})
            return None
        except Exception as e:
            logging.debug(f"[{self.name}] Error fetching ticker for {pair}: {e}")
            return None

    def _calculate_atr(self, ticker_data):
        """
        Calculate Average True Range (volatility measure)
        Simplified: use 24h high-low range as proxy
        """
        try:
            high = float(ticker_data.get('h', [0, 0])[1])  # 24h high
            low = float(ticker_data.get('l', [0, 0])[1])   # 24h low
            close = float(ticker_data.get('c', [0])[0])    # Current close

            if close > 0:
                atr_pct = ((high - low) / close) * 100
                return atr_pct
            return 0.0
        except Exception as e:
            logging.debug(f"[{self.name}] Error calculating ATR: {e}")
            return 0.0

    def _calculate_daily_volume(self, ticker_data):
        """
        Calculate 24-hour volume in USD
        """
        try:
            volume_24h = float(ticker_data.get('v', [0, 0])[1])  # 24h volume
            current_price = float(ticker_data.get('c', [0])[0])  # Current price

            volume_usd = volume_24h * current_price
            return volume_usd
        except Exception as e:
            logging.debug(f"[{self.name}] Error calculating volume: {e}")
            return 0.0

    def _calculate_spread(self, ticker_data):
        """
        Calculate bid-ask spread as percentage
        """
        try:
            bid = float(ticker_data.get('b', [0])[0])
            ask = float(ticker_data.get('a', [0])[0])

            if bid > 0:
                spread_pct = ((ask - bid) / bid) * 100
                return spread_pct
            return 999.0  # Invalid spread
        except Exception as e:
            logging.debug(f"[{self.name}] Error calculating spread: {e}")
            return 999.0

    def _calculate_momentum(self, pair: str):
        """
        Calculate 30-day price momentum
        Simplified: use current price vs opening price from ticker
        """
        try:
            ticker_data = self._get_ticker_data(pair)
            if not ticker_data:
                return 0.0

            current_price = float(ticker_data.get('c', [0])[0])
            open_price = float(ticker_data.get('o', [current_price])[0])

            if open_price > 0:
                momentum_pct = ((current_price - open_price) / open_price) * 100
                return momentum_pct
            return 0.0
        except Exception as e:
            logging.debug(f"[{self.name}] Error calculating momentum: {e}")
            return 0.0

    def _query_cross_moat_signals(self, pair: str) -> int:
        """
        Q4 + Q6 + Q8: Calculate cross-moat signal score (0-2 points)

        Uses team-specific moat weights to prioritize different data sources.
        Returns 0, 1, or 2 based on weighted moat activity.

        This is the INNOVATION: We look for causal signals in external data
        (GitHub, government, logistics, corporate) that predict crypto moves
        BEFORE they show up in price data.
        """
        moat_activity = 0.0

        try:
            # Extract base asset (e.g., "BTC" from "XXBTZUSD", "ETH" from "XETHZUSD")
            base_asset = self._extract_base_asset(pair)

            # Check Code Moat (GitHub activity) - Smart contract platforms
            if base_asset in ["ETH", "LINK", "MATIC", "AVAX", "SOL", "DOT", "ADA"]:
                code_signal = self._get_redis_signal("code-data:Python:dependency_entropy")
                if code_signal > 0.7:  # High GitHub activity
                    moat_activity += self.moat_weights["code"]
                    logging.debug(f"[{self.name}] {pair} has strong Code moat signal (entropy={code_signal:.2f})")

            # Check Government Moat (regulatory environment) - Institutional targets
            if base_asset in ["BTC", "ETH", "USDT", "USDC", "XRP", "LTC"]:
                policy_signal = self._get_redis_signal("govt-data:US-Federal:policy_stability")
                if policy_signal > 0.7:  # Favorable policy environment
                    moat_activity += self.moat_weights["government"]
                    logging.debug(f"[{self.name}] {pair} has strong Gov moat signal (stability={policy_signal:.2f})")

            # Check Logistics Moat (supply chain/mining) - PoW coins
            if base_asset in ["BTC", "LTC", "BCH", "DOGE", "ZEC", "XMR"]:
                logistics_signal = self._get_redis_signal("logistics-data:US-West:inventory_velocity")
                if logistics_signal > 0.8:  # High supply chain activity
                    moat_activity += self.moat_weights["logistics"]
                    logging.debug(f"[{self.name}] {pair} has strong Logistics moat signal (velocity={logistics_signal:.2f})")

            # Check Corporate Moat (M&A, institutional activity) - Exchange/DeFi tokens
            if base_asset in ["BNB", "UNI", "AAVE", "CRV", "SUSHI", "COMP", "MKR"]:
                corp_signal = self._get_redis_signal("corp-data:Tech:MA_Activity")
                if corp_signal > 0.6:  # High M&A activity
                    moat_activity += self.moat_weights["corporate"]
                    logging.debug(f"[{self.name}] {pair} has strong Corp moat signal (M&A={corp_signal:.2f})")

            # Return 0, 1, or 2 points based on weighted moat activity
            if moat_activity >= 1.5:
                return 2  # Strong cross-moat signal (Q6: double weight)
            elif moat_activity >= 0.5:
                return 1  # Weak cross-moat signal
            else:
                return 0  # No cross-moat signal

        except Exception as e:
            logging.error(f"[{self.name}] Error querying cross-moat signals for {pair}: {e}")
            return 0

    def _extract_base_asset(self, pair: str) -> str:
        """
        Extract base asset from Kraken pair name
        Examples:
        - "XXBTZUSD" -> "BTC"
        - "XETHZUSD" -> "ETH"
        - "ADAUSD" -> "ADA"
        - "SOLUSD" -> "SOL"
        """
        # Kraken uses X prefix for some assets, Z for fiat
        pair_clean = pair.replace('X', '').replace('Z', '')

        # Remove USD suffix
        if 'USD' in pair_clean:
            base = pair_clean.replace('USD', '')
        else:
            base = pair_clean[:3]  # First 3 chars

        # Known mappings
        mappings = {
            "BT": "BTC",
            "XBT": "BTC",
            "ETH": "ETH",
            "ADA": "ADA",
            "SOL": "SOL",
            "MATIC": "MATIC",
            "LINK": "LINK",
            "DOT": "DOT",
            "AVAX": "AVAX"
        }

        return mappings.get(base, base)

    def _get_redis_signal(self, key: str) -> float:
        """
        Query Redis for moat signal data
        Returns float 0-1 representing signal strength
        """
        try:
            # Check if vector_db (Redis connection) exists
            if not hasattr(self, 'vector_db') or self.vector_db is None:
                return 0.0

            # Query Redis for the moat signal
            data = self.vector_db.get(key)

            if data:
                # Parse JSON data
                signal_data = json.loads(data) if isinstance(data, (str, bytes)) else data

                # Extract signal value (assuming it's stored as 'close' or direct value)
                if isinstance(signal_data, dict):
                    signal_value = signal_data.get('features', {}).get('close', 0.0)
                    if signal_value == 0.0:
                        # Try alternative keys
                        signal_value = signal_data.get('close', 0.0)
                else:
                    signal_value = float(signal_data)

                return float(signal_value)

            return 0.0

        except Exception as e:
            logging.debug(f"[{self.name}] Error getting Redis signal for {key}: {e}")
            return 0.0
