# src/services/pnl_tracker.py - PHASE 3.1: Per-Asset P&L Tracking with Probation/Hibernation
import logging
import time
from collections import defaultdict
from typing import Dict, Optional
import json

class PnLTracker:
    """
    PHASE 3.1: Per-Asset P&L Tracking Service

    Implements Q2 (Probation System) and Q9 (Hibernation Trigger):
    - Tracks cumulative P&L for each active asset
    - Implements probation: reduces position size for losing assets
    - Triggers hibernation after 90 days of negative performance
    - Integrates with model.active_assets for lifecycle management

    Probation Tiers (Q2):
    - Normal: P&L > -5% (position size 100%)
    - Probation Level 1: -5% to -10% (position size 50%)
    - Probation Level 2: -10% to -15% (position size 25%)
    - Hibernation Candidate: < -15% for 90 days (triggers Q9)
    """

    def __init__(self, redis_client=None, model=None):
        """
        Initialize the P&L tracker

        Args:
            redis_client: Redis client for pub/sub communication
            model: MycelialModel instance for hibernation callbacks
        """
        self.redis_client = redis_client
        self.model = model

        # Per-asset P&L tracking
        self.asset_pnl: Dict[str, Dict] = defaultdict(lambda: {
            'cumulative_pnl': 0.0,
            'trade_count': 0,
            'win_count': 0,
            'loss_count': 0,
            'probation_level': 0,  # 0=Normal, 1=Probation1, 2=Probation2
            'position_size_multiplier': 1.0,
            'first_trade_timestamp': None,
            'last_trade_timestamp': None,
            'probation_start_timestamp': None,
            'worst_drawdown': 0.0
        })

        # Q2: Probation thresholds
        self.probation_thresholds = {
            1: -5.0,   # -5% triggers Probation Level 1 (50% position size)
            2: -10.0,  # -10% triggers Probation Level 2 (25% position size)
        }

        # Q9: Hibernation criteria
        self.hibernation_pnl_threshold = -15.0  # -15% cumulative P&L
        self.hibernation_duration_days = 90  # 90 days in probation

        # Subscribe to trade confirmations if Redis client provided
        if self.redis_client:
            self.redis_client.subscribe("synthesized-trade-log", self._handle_trade_log)
            logging.info("[PNLTRACKER] Subscribed to synthesized-trade-log channel")

    def record_trade(self, pair: str, pnl_pct: float, direction: str):
        """
        Record a trade and update P&L statistics

        Args:
            pair: Trading pair (e.g., "XXBTZUSD")
            pnl_pct: P&L percentage for this trade
            direction: "buy" or "sell"
        """
        asset = self.asset_pnl[pair]
        current_time = time.time()

        # Initialize timestamps
        if asset['first_trade_timestamp'] is None:
            asset['first_trade_timestamp'] = current_time
        asset['last_trade_timestamp'] = current_time

        # Update cumulative P&L
        asset['cumulative_pnl'] += pnl_pct
        asset['trade_count'] += 1

        # Track wins/losses
        if pnl_pct > 0:
            asset['win_count'] += 1
        elif pnl_pct < 0:
            asset['loss_count'] += 1

        # Update worst drawdown
        if asset['cumulative_pnl'] < asset['worst_drawdown']:
            asset['worst_drawdown'] = asset['cumulative_pnl']

        # Check probation status
        self._update_probation_status(pair)

        # Check hibernation criteria
        self._check_hibernation_trigger(pair)

        # Log status
        win_rate = (asset['win_count'] / asset['trade_count'] * 100) if asset['trade_count'] > 0 else 0
        logging.info(
            f"[PNLTRACKER] {pair} | Trade: {pnl_pct:+.2f}% | "
            f"Cumulative: {asset['cumulative_pnl']:+.2f}% | "
            f"Trades: {asset['trade_count']} | Win Rate: {win_rate:.1f}% | "
            f"Probation Level: {asset['probation_level']}"
        )

    def _update_probation_status(self, pair: str):
        """
        Q2: Update probation level based on cumulative P&L
        """
        asset = self.asset_pnl[pair]
        pnl = asset['cumulative_pnl']
        old_level = asset['probation_level']

        # Determine probation level
        if pnl >= self.probation_thresholds[1]:
            # Normal status
            new_level = 0
            position_multiplier = 1.0
        elif pnl >= self.probation_thresholds[2]:
            # Probation Level 1
            new_level = 1
            position_multiplier = 0.5  # 50% position size
        else:
            # Probation Level 2
            new_level = 2
            position_multiplier = 0.25  # 25% position size

        # Update probation status
        asset['probation_level'] = new_level
        asset['position_size_multiplier'] = position_multiplier

        # Track when probation started
        if new_level > 0 and old_level == 0:
            asset['probation_start_timestamp'] = time.time()
            logging.warning(
                f"[PNLTRACKER] {pair} entered Probation Level {new_level} | "
                f"P&L: {pnl:.2f}% | Position size reduced to {position_multiplier * 100:.0f}%"
            )
        elif new_level == 0 and old_level > 0:
            asset['probation_start_timestamp'] = None
            logging.info(
                f"[PNLTRACKER] {pair} exited probation | "
                f"P&L recovered to {pnl:.2f}%"
            )
        elif new_level > old_level:
            logging.critical(
                f"[PNLTRACKER] {pair} escalated to Probation Level {new_level} | "
                f"P&L: {pnl:.2f}% | Position size: {position_multiplier * 100:.0f}%"
            )

    def _check_hibernation_trigger(self, pair: str):
        """
        Q9: Check if asset should be hibernated

        Hibernation criteria:
        1. Cumulative P&L < -15%
        2. Has been in probation for 90+ days
        """
        asset = self.asset_pnl[pair]

        # Check P&L threshold
        if asset['cumulative_pnl'] >= self.hibernation_pnl_threshold:
            return  # Not bad enough to hibernate

        # Check probation duration
        if asset['probation_start_timestamp'] is None:
            return  # Not in probation

        probation_duration_days = (time.time() - asset['probation_start_timestamp']) / 86400

        if probation_duration_days >= self.hibernation_duration_days:
            # Trigger hibernation
            logging.critical(
                f"[PNLTRACKER] 🛌 HIBERNATION TRIGGER for {pair} | "
                f"P&L: {asset['cumulative_pnl']:.2f}% | "
                f"Probation: {probation_duration_days:.0f} days | "
                f"Initiating hibernation..."
            )

            # Call model's hibernation method
            if self.model and hasattr(self.model, 'hibernate_asset'):
                self.model.hibernate_asset(pair)

            # Publish hibernation notification
            if self.redis_client:
                self.redis_client.publish_message("system-hibernation", {
                    "pair": pair,
                    "reason": "Q9: 90-day probation with negative P&L",
                    "final_pnl": asset['cumulative_pnl'],
                    "probation_days": probation_duration_days,
                    "timestamp": time.time()
                })

    def _handle_trade_log(self, message: dict):
        """
        Handle incoming trade confirmations from synthesized-trade-log channel
        """
        try:
            pair = message.get('pair')
            direction = message.get('direction')

            # Extract P&L from message (if available)
            # Note: This is a placeholder - actual P&L calculation happens in TradingAgent
            # We're just tracking the record here
            if pair and direction:
                # For now, just increment trade count without P&L
                # Full integration requires TradingAgent to publish P&L in message
                logging.debug(f"[PNLTRACKER] Received trade log for {pair}: {direction}")

        except Exception as e:
            logging.error(f"[PNLTRACKER] Error handling trade log: {e}")

    def get_asset_status(self, pair: str) -> dict:
        """
        Get current status for an asset

        Returns:
            dict with P&L stats, probation level, and position size multiplier
        """
        if pair not in self.asset_pnl:
            return {
                'pair': pair,
                'status': 'unknown',
                'cumulative_pnl': 0.0,
                'probation_level': 0,
                'position_size_multiplier': 1.0
            }

        asset = self.asset_pnl[pair]
        win_rate = (asset['win_count'] / asset['trade_count'] * 100) if asset['trade_count'] > 0 else 0

        probation_status = {
            0: "Normal",
            1: "Probation Level 1",
            2: "Probation Level 2"
        }.get(asset['probation_level'], "Unknown")

        return {
            'pair': pair,
            'status': probation_status,
            'cumulative_pnl': asset['cumulative_pnl'],
            'trade_count': asset['trade_count'],
            'win_rate': win_rate,
            'probation_level': asset['probation_level'],
            'position_size_multiplier': asset['position_size_multiplier'],
            'worst_drawdown': asset['worst_drawdown'],
            'days_active': (time.time() - asset['first_trade_timestamp']) / 86400 if asset['first_trade_timestamp'] else 0
        }

    def get_all_assets_summary(self) -> dict:
        """
        Get summary of all tracked assets

        Returns:
            dict with overall statistics
        """
        summary = {
            'total_assets': len(self.asset_pnl),
            'normal': 0,
            'probation_1': 0,
            'probation_2': 0,
            'total_pnl': 0.0,
            'total_trades': 0,
            'assets': []
        }

        for pair in self.asset_pnl.keys():
            asset = self.asset_pnl[pair]
            summary['total_pnl'] += asset['cumulative_pnl']
            summary['total_trades'] += asset['trade_count']

            if asset['probation_level'] == 0:
                summary['normal'] += 1
            elif asset['probation_level'] == 1:
                summary['probation_1'] += 1
            elif asset['probation_level'] == 2:
                summary['probation_2'] += 1

            summary['assets'].append(self.get_asset_status(pair))

        return summary
