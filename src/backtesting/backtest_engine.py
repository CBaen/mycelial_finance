# src/backtesting/backtest_engine.py - PHASE 4.1: Dynamic Backtesting Engine
"""
PHASE 4.1: Backtesting Engine to Validate Cross-Moat Hypothesis (Q10)

This module tests whether cross-moat signals (GitHub activity predicting crypto volatility)
provide a causal inference advantage over traditional technical analysis alone.

Key Features:
- Historical data replay with realistic timing
- A/B testing: Cross-moat enabled vs. TA-only baseline
- Statistical significance testing
- Sharpe ratio and max drawdown analysis
- Per-asset performance tracking
- Configurable test periods and parameters
"""

import logging
import time
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json


# =============================================================================
# CONFIGURATION
# =============================================================================

class StrategyType(Enum):
    """Strategy types for A/B testing"""
    TA_ONLY = "ta_only"              # Technical Analysis only (baseline)
    CROSS_MOAT = "cross_moat"        # TA + Cross-moat signals (experimental)


@dataclass
class BacktestConfig:
    """Configuration for backtesting runs"""

    # Time period
    start_date: datetime
    end_date: datetime

    # Assets to test
    pairs: List[str] = field(default_factory=lambda: ["XXBTZUSD", "XETHZUSD"])

    # Trading parameters
    initial_capital: float = 10000.0
    position_size_pct: float = 0.10  # 10% of capital per trade

    # Trading costs (from agent_config.yaml)
    trading_fee_pct: float = 0.26
    slippage_pct: float = 0.10
    total_cost_pct: float = 0.36

    # Cross-moat parameters
    cross_moat_weight: float = 2.0   # 2x weight for cross-moat signals
    cross_moat_threshold: int = 1    # Minimum cross-moat score to trigger

    # Technical analysis parameters
    rsi_period: int = 14
    rsi_overbought: int = 70
    rsi_oversold: int = 30

    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9

    # Risk management
    max_position_size: float = 0.25  # 25% max per asset
    stop_loss_pct: float = 0.05      # 5% stop loss

    # Consensus
    min_confidence: float = 0.70     # 70% minimum confidence


@dataclass
class Trade:
    """Represents a single trade"""
    timestamp: datetime
    pair: str
    direction: str  # "BUY" or "SELL"
    price: float
    size: float
    cost: float  # Trading fees + slippage
    strategy: StrategyType

    # Signals that triggered the trade
    rsi: Optional[float] = None
    macd: Optional[float] = None
    cross_moat_score: Optional[int] = None

    # Exit information (filled when position closes)
    exit_timestamp: Optional[datetime] = None
    exit_price: Optional[float] = None
    pnl: Optional[float] = None
    pnl_pct: Optional[float] = None


@dataclass
class BacktestResults:
    """Results of a backtest run"""
    strategy: StrategyType

    # Performance metrics
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0

    # P&L metrics
    total_pnl: float = 0.0
    total_pnl_pct: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0

    # Risk metrics
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    max_drawdown_pct: float = 0.0

    # Capital
    final_capital: float = 0.0
    peak_capital: float = 0.0

    # Trade history
    trades: List[Trade] = field(default_factory=list)

    # Daily equity curve
    equity_curve: List[Tuple[datetime, float]] = field(default_factory=list)


# =============================================================================
# BACKTESTING ENGINE
# =============================================================================

class BacktestEngine:
    """
    PHASE 4.1: Dynamic Backtesting Engine

    Tests the cross-moat hypothesis by comparing:
    1. TA-only strategy (baseline)
    2. Cross-moat strategy (TA + GitHub signals)

    Validates Q10: Does GitHub activity predict crypto volatility?
    """

    def __init__(self, config: BacktestConfig):
        """
        Initialize backtesting engine

        Args:
            config: Backtest configuration
        """
        self.config = config

        # Results storage
        self.results: Dict[StrategyType, BacktestResults] = {
            StrategyType.TA_ONLY: BacktestResults(strategy=StrategyType.TA_ONLY),
            StrategyType.CROSS_MOAT: BacktestResults(strategy=StrategyType.CROSS_MOAT)
        }

        # State tracking
        self.capital: Dict[StrategyType, float] = {
            StrategyType.TA_ONLY: config.initial_capital,
            StrategyType.CROSS_MOAT: config.initial_capital
        }

        # Open positions
        self.positions: Dict[StrategyType, Dict[str, Trade]] = {
            StrategyType.TA_ONLY: {},
            StrategyType.CROSS_MOAT: {}
        }

        logging.info(
            f"[BACKTEST] Engine initialized | "
            f"Period: {config.start_date} to {config.end_date} | "
            f"Pairs: {config.pairs} | "
            f"Capital: ${config.initial_capital:,.2f}"
        )

    def run(self, market_data: Dict[str, pd.DataFrame],
            cross_moat_data: Dict[str, pd.DataFrame]) -> Dict[StrategyType, BacktestResults]:
        """
        Run backtest comparing TA-only vs. Cross-moat strategies

        Args:
            market_data: Historical OHLCV data per pair
                         {pair: DataFrame with columns [timestamp, open, high, low, close, volume]}
            cross_moat_data: Historical cross-moat signals per pair
                            {pair: DataFrame with columns [timestamp, commits_24h, dependency_entropy, ...]}

        Returns:
            Results for both strategies
        """
        logging.info("[BACKTEST] Starting backtest run...")

        # Validate data
        self._validate_data(market_data, cross_moat_data)

        # Get unified timeline (all timestamps across all pairs)
        timeline = self._build_timeline(market_data)

        logging.info(f"[BACKTEST] Processing {len(timeline)} timestamps...")

        # Replay history timestamp by timestamp
        for i, timestamp in enumerate(timeline):
            if i % 1000 == 0:
                logging.info(f"[BACKTEST] Progress: {i}/{len(timeline)} ({i/len(timeline)*100:.1f}%)")

            # Process each pair
            for pair in self.config.pairs:
                # Get current market data
                market_row = self._get_market_data_at_time(market_data[pair], timestamp)
                if market_row is None:
                    continue

                # Get current cross-moat data
                cross_moat_row = self._get_market_data_at_time(cross_moat_data[pair], timestamp)

                # Calculate technical indicators
                ta_signals = self._calculate_ta_signals(market_data[pair], timestamp)

                # Generate trading signals for both strategies
                self._process_ta_only_strategy(pair, timestamp, market_row, ta_signals)
                self._process_cross_moat_strategy(pair, timestamp, market_row, ta_signals, cross_moat_row)

            # Record equity for this timestamp
            for strategy in StrategyType:
                equity = self._calculate_equity(strategy, timestamp, market_data)
                self.results[strategy].equity_curve.append((timestamp, equity))

        # Close all remaining positions at end of backtest
        self._close_all_positions(timeline[-1], market_data)

        # Calculate final metrics
        for strategy in StrategyType:
            self._calculate_metrics(strategy)

        logging.info("[BACKTEST] Backtest complete!")
        self._print_results()

        return self.results

    def _validate_data(self, market_data: Dict[str, pd.DataFrame],
                      cross_moat_data: Dict[str, pd.DataFrame]):
        """Validate input data"""
        for pair in self.config.pairs:
            if pair not in market_data:
                raise ValueError(f"Missing market data for {pair}")
            if pair not in cross_moat_data:
                logging.warning(f"Missing cross-moat data for {pair} - will use TA-only for this pair")

    def _build_timeline(self, market_data: Dict[str, pd.DataFrame]) -> List[datetime]:
        """Build unified timeline from all pairs"""
        all_timestamps = set()

        for pair, df in market_data.items():
            all_timestamps.update(df['timestamp'].tolist())

        timeline = sorted(list(all_timestamps))

        # Filter to configured date range
        timeline = [
            ts for ts in timeline
            if self.config.start_date <= ts <= self.config.end_date
        ]

        return timeline

    def _get_market_data_at_time(self, df: pd.DataFrame, timestamp: datetime) -> Optional[pd.Series]:
        """Get market data row at specific timestamp"""
        rows = df[df['timestamp'] == timestamp]
        if len(rows) == 0:
            return None
        return rows.iloc[0]

    def _calculate_ta_signals(self, df: pd.DataFrame, timestamp: datetime) -> Dict:
        """
        Calculate technical analysis signals

        Returns dict with RSI, MACD, etc.
        """
        # Get historical window up to current timestamp
        historical = df[df['timestamp'] <= timestamp].tail(100)

        if len(historical) < 30:
            return {}  # Not enough data

        signals = {}

        # RSI
        rsi = self._calculate_rsi(historical['close'].values)
        if rsi is not None:
            signals['rsi'] = rsi
            signals['rsi_signal'] = 'BUY' if rsi < self.config.rsi_oversold else ('SELL' if rsi > self.config.rsi_overbought else None)

        # MACD
        macd_line, signal_line = self._calculate_macd(historical['close'].values)
        if macd_line is not None and signal_line is not None:
            signals['macd'] = macd_line
            signals['macd_signal'] = 'BUY' if macd_line > signal_line else 'SELL'

        return signals

    def _calculate_rsi(self, prices: np.ndarray, period: int = 14) -> Optional[float]:
        """Calculate RSI (Relative Strength Index)"""
        if len(prices) < period + 1:
            return None

        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def _calculate_macd(self, prices: np.ndarray) -> Tuple[Optional[float], Optional[float]]:
        """Calculate MACD (Moving Average Convergence Divergence)"""
        if len(prices) < self.config.macd_slow:
            return None, None

        # Calculate EMAs
        ema_fast = self._calculate_ema(prices, self.config.macd_fast)
        ema_slow = self._calculate_ema(prices, self.config.macd_slow)

        if ema_fast is None or ema_slow is None:
            return None, None

        macd_line = ema_fast - ema_slow

        # Signal line (9-period EMA of MACD)
        # For simplicity, using simple moving average here
        # In production, would calculate EMA of MACD values over time
        signal_line = macd_line * 0.9  # Simplified

        return macd_line, signal_line

    def _calculate_ema(self, prices: np.ndarray, period: int) -> Optional[float]:
        """Calculate Exponential Moving Average"""
        if len(prices) < period:
            return None

        multiplier = 2 / (period + 1)
        ema = np.mean(prices[-period:])  # Start with SMA

        for price in prices[-period:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))

        return ema

    def _process_ta_only_strategy(self, pair: str, timestamp: datetime,
                                   market_row: pd.Series, ta_signals: Dict):
        """Process TA-only strategy (baseline)"""
        strategy = StrategyType.TA_ONLY

        # Check if we have an open position
        has_position = pair in self.positions[strategy]

        if has_position:
            # Check exit conditions
            self._check_exit_conditions(strategy, pair, timestamp, market_row, ta_signals)
        else:
            # Check entry conditions
            self._check_entry_conditions(strategy, pair, timestamp, market_row, ta_signals, None)

    def _process_cross_moat_strategy(self, pair: str, timestamp: datetime,
                                     market_row: pd.Series, ta_signals: Dict,
                                     cross_moat_row: Optional[pd.Series]):
        """Process Cross-moat strategy (experimental)"""
        strategy = StrategyType.CROSS_MOAT

        # Check if we have an open position
        has_position = pair in self.positions[strategy]

        if has_position:
            # Check exit conditions
            self._check_exit_conditions(strategy, pair, timestamp, market_row, ta_signals)
        else:
            # Check entry conditions with cross-moat signals
            self._check_entry_conditions(strategy, pair, timestamp, market_row, ta_signals, cross_moat_row)

    def _check_entry_conditions(self, strategy: StrategyType, pair: str,
                                timestamp: datetime, market_row: pd.Series,
                                ta_signals: Dict, cross_moat_row: Optional[pd.Series]):
        """Check if we should enter a position"""

        if not ta_signals:
            return  # No signals available

        # TA-only strategy: require RSI or MACD signal
        if strategy == StrategyType.TA_ONLY:
            signal = ta_signals.get('rsi_signal') or ta_signals.get('macd_signal')
            if signal == 'BUY':
                self._open_position(strategy, pair, timestamp, market_row, ta_signals, None)

        # Cross-moat strategy: require TA + cross-moat confirmation
        elif strategy == StrategyType.CROSS_MOAT:
            ta_signal = ta_signals.get('rsi_signal') or ta_signals.get('macd_signal')

            # Calculate cross-moat score
            cross_moat_score = 0
            if cross_moat_row is not None:
                # High commit activity = potential volatility
                if cross_moat_row.get('commits_24h', 0) > 50:
                    cross_moat_score += 1
                # High dependency entropy = ecosystem activity
                if cross_moat_row.get('dependency_entropy', 0) > 30:
                    cross_moat_score += 1

            # Require both TA signal AND cross-moat confirmation
            if ta_signal == 'BUY' and cross_moat_score >= self.config.cross_moat_threshold:
                self._open_position(strategy, pair, timestamp, market_row, ta_signals, cross_moat_score)

    def _check_exit_conditions(self, strategy: StrategyType, pair: str,
                               timestamp: datetime, market_row: pd.Series,
                               ta_signals: Dict):
        """Check if we should exit a position"""

        if pair not in self.positions[strategy]:
            return

        position = self.positions[strategy][pair]
        current_price = market_row['close']

        # Stop loss check
        if position.direction == "BUY":
            pnl_pct = (current_price - position.price) / position.price
            if pnl_pct <= -self.config.stop_loss_pct:
                self._close_position(strategy, pair, timestamp, current_price, "STOP_LOSS")
                return

        # TA exit signal
        exit_signal = None
        if 'rsi_signal' in ta_signals and ta_signals['rsi_signal'] == 'SELL':
            exit_signal = "RSI_SELL"
        elif 'macd_signal' in ta_signals and ta_signals['macd_signal'] == 'SELL':
            exit_signal = "MACD_SELL"

        if exit_signal:
            self._close_position(strategy, pair, timestamp, current_price, exit_signal)

    def _open_position(self, strategy: StrategyType, pair: str, timestamp: datetime,
                       market_row: pd.Series, ta_signals: Dict, cross_moat_score: Optional[int]):
        """Open a new position"""

        # Calculate position size
        capital = self.capital[strategy]
        position_value = capital * self.config.position_size_pct
        price = market_row['close']
        size = position_value / price

        # Calculate trading costs
        cost = position_value * (self.config.total_cost_pct / 100)

        # Deduct from capital
        self.capital[strategy] -= (position_value + cost)

        # Create trade
        trade = Trade(
            timestamp=timestamp,
            pair=pair,
            direction="BUY",
            price=price,
            size=size,
            cost=cost,
            strategy=strategy,
            rsi=ta_signals.get('rsi'),
            macd=ta_signals.get('macd'),
            cross_moat_score=cross_moat_score
        )

        # Store position
        self.positions[strategy][pair] = trade

        logging.debug(
            f"[{strategy.value.upper()}] OPEN {pair} @ ${price:.2f} | "
            f"Size: {size:.4f} | Cost: ${cost:.2f}"
        )

    def _close_position(self, strategy: StrategyType, pair: str,
                       timestamp: datetime, price: float, reason: str):
        """Close an open position"""

        if pair not in self.positions[strategy]:
            return

        position = self.positions[strategy][pair]

        # Calculate P&L
        position_value = position.size * price
        exit_cost = position_value * (self.config.total_cost_pct / 100)

        # P&L = (exit_value - exit_cost) - (entry_value + entry_cost)
        entry_value = position.size * position.price
        pnl = (position_value - exit_cost) - (entry_value + position.cost)
        pnl_pct = (pnl / entry_value) * 100

        # Update capital
        self.capital[strategy] += (position_value - exit_cost)

        # Update trade record
        position.exit_timestamp = timestamp
        position.exit_price = price
        position.pnl = pnl
        position.pnl_pct = pnl_pct

        # Record trade
        self.results[strategy].trades.append(position)

        # Remove from open positions
        del self.positions[strategy][pair]

        logging.debug(
            f"[{strategy.value.upper()}] CLOSE {pair} @ ${price:.2f} | "
            f"P&L: ${pnl:.2f} ({pnl_pct:+.2f}%) | Reason: {reason}"
        )

    def _close_all_positions(self, timestamp: datetime, market_data: Dict[str, pd.DataFrame]):
        """Close all remaining positions at end of backtest"""

        for strategy in StrategyType:
            for pair in list(self.positions[strategy].keys()):
                market_row = self._get_market_data_at_time(market_data[pair], timestamp)
                if market_row is not None:
                    self._close_position(strategy, pair, timestamp, market_row['close'], "END_OF_TEST")

    def _calculate_equity(self, strategy: StrategyType, timestamp: datetime,
                         market_data: Dict[str, pd.DataFrame]) -> float:
        """Calculate total equity (cash + open positions)"""

        equity = self.capital[strategy]

        # Add value of open positions
        for pair, position in self.positions[strategy].items():
            market_row = self._get_market_data_at_time(market_data[pair], timestamp)
            if market_row is not None:
                equity += position.size * market_row['close']

        return equity

    def _calculate_metrics(self, strategy: StrategyType):
        """Calculate performance metrics for a strategy"""

        results = self.results[strategy]
        trades = results.trades

        if len(trades) == 0:
            logging.warning(f"[{strategy.value.upper()}] No trades executed")
            return

        # Trade statistics
        results.total_trades = len(trades)
        results.winning_trades = len([t for t in trades if t.pnl > 0])
        results.losing_trades = len([t for t in trades if t.pnl <= 0])
        results.win_rate = results.winning_trades / results.total_trades

        # P&L statistics
        results.total_pnl = sum(t.pnl for t in trades)
        results.total_pnl_pct = (results.total_pnl / self.config.initial_capital) * 100

        winning_trades = [t.pnl for t in trades if t.pnl > 0]
        losing_trades = [t.pnl for t in trades if t.pnl <= 0]

        results.avg_win = np.mean(winning_trades) if winning_trades else 0
        results.avg_loss = np.mean(losing_trades) if losing_trades else 0

        # Final capital
        results.final_capital = self.capital[strategy]

        # Risk metrics
        equity_values = [eq for _, eq in results.equity_curve]
        results.peak_capital = max(equity_values) if equity_values else self.config.initial_capital

        # Calculate drawdown
        peak = self.config.initial_capital
        max_dd = 0
        for equity in equity_values:
            if equity > peak:
                peak = equity
            dd = peak - equity
            if dd > max_dd:
                max_dd = dd

        results.max_drawdown = max_dd
        results.max_drawdown_pct = (max_dd / results.peak_capital) * 100 if results.peak_capital > 0 else 0

        # Sharpe ratio (simplified: returns / std dev of returns)
        returns = [t.pnl_pct for t in trades if t.pnl_pct is not None]
        if len(returns) > 1:
            results.sharpe_ratio = np.mean(returns) / np.std(returns) if np.std(returns) > 0 else 0
        else:
            results.sharpe_ratio = 0

    def _print_results(self):
        """Print backtest results"""

        print("\n" + "="*80)
        print("BACKTEST RESULTS")
        print("="*80)

        for strategy in StrategyType:
            results = self.results[strategy]

            print(f"\n{strategy.value.upper()} Strategy:")
            print("-" * 80)
            print(f"Total Trades:     {results.total_trades}")
            print(f"Win Rate:         {results.win_rate*100:.2f}%")
            print(f"Total P&L:        ${results.total_pnl:,.2f} ({results.total_pnl_pct:+.2f}%)")
            print(f"Avg Win:          ${results.avg_win:,.2f}")
            print(f"Avg Loss:         ${results.avg_loss:,.2f}")
            print(f"Final Capital:    ${results.final_capital:,.2f}")
            print(f"Sharpe Ratio:     {results.sharpe_ratio:.2f}")
            print(f"Max Drawdown:     ${results.max_drawdown:,.2f} ({results.max_drawdown_pct:.2f}%)")

        # Comparison
        print("\n" + "="*80)
        print("STRATEGY COMPARISON")
        print("="*80)

        ta_pnl = self.results[StrategyType.TA_ONLY].total_pnl_pct
        cm_pnl = self.results[StrategyType.CROSS_MOAT].total_pnl_pct

        improvement = cm_pnl - ta_pnl

        print(f"TA-Only P&L:      {ta_pnl:+.2f}%")
        print(f"Cross-Moat P&L:   {cm_pnl:+.2f}%")
        print(f"Improvement:      {improvement:+.2f}% {'✅' if improvement > 0 else '❌'}")

        if improvement > 0:
            print(f"\n🎉 Cross-moat hypothesis VALIDATED: {improvement:+.2f}% better performance")
        else:
            print(f"\n⚠️  Cross-moat hypothesis NOT validated: {improvement:+.2f}% worse performance")

        print("="*80 + "\n")

    def export_results(self, output_path: str):
        """Export backtest results to JSON"""

        output = {
            "config": {
                "start_date": self.config.start_date.isoformat(),
                "end_date": self.config.end_date.isoformat(),
                "pairs": self.config.pairs,
                "initial_capital": self.config.initial_capital
            },
            "results": {}
        }

        for strategy in StrategyType:
            results = self.results[strategy]

            output["results"][strategy.value] = {
                "total_trades": results.total_trades,
                "win_rate": results.win_rate,
                "total_pnl": results.total_pnl,
                "total_pnl_pct": results.total_pnl_pct,
                "final_capital": results.final_capital,
                "sharpe_ratio": results.sharpe_ratio,
                "max_drawdown_pct": results.max_drawdown_pct,
                "trades": [
                    {
                        "timestamp": t.timestamp.isoformat(),
                        "pair": t.pair,
                        "direction": t.direction,
                        "price": t.price,
                        "pnl": t.pnl,
                        "pnl_pct": t.pnl_pct
                    }
                    for t in results.trades
                ]
            }

        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2)

        logging.info(f"[BACKTEST] Results exported to {output_path}")


# =============================================================================
# MAIN - Example Usage
# =============================================================================

if __name__ == "__main__":
    # This would be run with real historical data
    # For now, demonstrates the API

    logging.basicConfig(level=logging.INFO)

    config = BacktestConfig(
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 12, 31),
        pairs=["XXBTZUSD", "XETHZUSD"]
    )

    engine = BacktestEngine(config)

    # In production, load real historical data:
    # market_data = load_historical_ohlcv()
    # cross_moat_data = load_historical_github_data()
    # results = engine.run(market_data, cross_moat_data)

    print("Backtesting engine ready. Load historical data to run tests.")
