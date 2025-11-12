# src/backtesting/data_loader.py - PHASE 4.1: Historical Data Loader
"""
Historical data loading utilities for backtesting

Provides functions to:
- Load Kraken OHLCV data
- Load historical GitHub cross-moat signals
- Simulate historical data when real data unavailable
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import datetime, timedelta
import time


def load_kraken_ohlcv_history(
    pairs: List[str],
    start_date: datetime,
    end_date: datetime,
    interval: int = 60
) -> Dict[str, pd.DataFrame]:
    """
    Load historical OHLCV data from Kraken

    Args:
        pairs: List of trading pairs (e.g., ["XXBTZUSD", "XETHZUSD"])
        start_date: Start date for historical data
        end_date: End date for historical data
        interval: Candle interval in minutes (default: 60 = 1 hour)

    Returns:
        Dict mapping pair to DataFrame with columns:
        [timestamp, open, high, low, close, volume]
    """
    from src.services.kraken_client import KrakenClient

    logging.info(
        f"[DATA_LOADER] Loading Kraken OHLCV data | "
        f"Pairs: {pairs} | {start_date} to {end_date}"
    )

    client = KrakenClient()
    data = {}

    for pair in pairs:
        try:
            # Kraken API: Get OHLC data
            # Note: Kraken has rate limits, may need to batch requests
            since = int(start_date.timestamp())

            ohlc_data = client.client.query_public('OHLC', {
                'pair': pair,
                'interval': interval,
                'since': since
            })

            if 'result' in ohlc_data and pair in ohlc_data['result']:
                raw_data = ohlc_data['result'][pair]

                # Parse OHLC data
                # Format: [time, open, high, low, close, vwap, volume, count]
                df = pd.DataFrame(raw_data, columns=[
                    'timestamp', 'open', 'high', 'low', 'close',
                    'vwap', 'volume', 'count'
                ])

                # Convert timestamp to datetime
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')

                # Convert price columns to float
                df['open'] = df['open'].astype(float)
                df['high'] = df['high'].astype(float)
                df['low'] = df['low'].astype(float)
                df['close'] = df['close'].astype(float)
                df['volume'] = df['volume'].astype(float)

                # Filter to date range
                df = df[(df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)]

                data[pair] = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]

                logging.info(f"[DATA_LOADER] Loaded {len(df)} candles for {pair}")

            else:
                logging.warning(f"[DATA_LOADER] No data returned for {pair}")
                # Use simulated data as fallback
                data[pair] = simulate_ohlcv_data(pair, start_date, end_date, interval)

        except Exception as e:
            logging.error(f"[DATA_LOADER] Error loading {pair}: {e}")
            # Use simulated data as fallback
            data[pair] = simulate_ohlcv_data(pair, start_date, end_date, interval)

    return data


def simulate_ohlcv_data(
    pair: str,
    start_date: datetime,
    end_date: datetime,
    interval: int = 60
) -> pd.DataFrame:
    """
    Simulate OHLCV data for backtesting when real data unavailable

    Args:
        pair: Trading pair
        start_date: Start date
        end_date: End date
        interval: Candle interval in minutes

    Returns:
        DataFrame with simulated OHLCV data
    """
    logging.warning(f"[DATA_LOADER] Simulating OHLCV data for {pair}")

    # Generate timestamps
    timestamps = []
    current = start_date
    while current <= end_date:
        timestamps.append(current)
        current += timedelta(minutes=interval)

    # Simulate realistic price movement
    # Start with pair-specific base prices
    base_prices = {
        "XXBTZUSD": 40000.0,
        "XETHZUSD": 2500.0,
        "XLTCZUSD": 80.0,
        "XXRPZUSD": 0.50
    }

    base_price = base_prices.get(pair, 100.0)

    # Geometric Brownian Motion for realistic price simulation
    np.random.seed(hash(pair) % 2**32)  # Deterministic but pair-specific

    drift = 0.0001  # Slight upward drift
    volatility = 0.02  # 2% volatility

    prices = [base_price]
    for _ in range(len(timestamps) - 1):
        random_shock = np.random.normal(0, 1)
        price_change = prices[-1] * (drift + volatility * random_shock)
        new_price = max(prices[-1] + price_change, base_price * 0.5)  # Floor at 50% of base
        prices.append(new_price)

    # Generate OHLCV from price series
    data = []
    for i, ts in enumerate(timestamps):
        price = prices[i]

        # Simulate intrabar movement
        high = price * (1 + np.random.uniform(0, 0.01))
        low = price * (1 - np.random.uniform(0, 0.01))
        open_price = price * (1 + np.random.uniform(-0.005, 0.005))
        close = price

        volume = np.random.uniform(100, 1000)

        data.append({
            'timestamp': ts,
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        })

    df = pd.DataFrame(data)

    logging.info(f"[DATA_LOADER] Simulated {len(df)} candles for {pair}")

    return df


def load_github_history(
    pairs: List[str],
    start_date: datetime,
    end_date: datetime
) -> Dict[str, pd.DataFrame]:
    """
    Load historical GitHub cross-moat signals

    Args:
        pairs: List of trading pairs
        start_date: Start date
        end_date: End date

    Returns:
        Dict mapping pair to DataFrame with cross-moat signals
        Columns: [timestamp, commits_24h, dependency_entropy, novelty_score, ...]
    """
    logging.info(
        f"[DATA_LOADER] Loading GitHub history | "
        f"{start_date} to {end_date}"
    )

    # Map pairs to relevant GitHub repos
    pair_to_repos = {
        "XXBTZUSD": ["bitcoin/bitcoin"],
        "XETHZUSD": ["ethereum/go-ethereum", "Uniswap/v3-core"],
        "XLTCZUSD": ["litecoin-project/litecoin"],
        "XXRPZUSD": ["ripple/rippled"]
    }

    data = {}

    for pair in pairs:
        repos = pair_to_repos.get(pair, [])

        if not repos:
            # No GitHub mapping, use simulated data
            data[pair] = simulate_github_data(pair, start_date, end_date)
            continue

        try:
            # In production, would query GitHub API for historical data
            # For now, simulate based on pair characteristics
            data[pair] = simulate_github_data(pair, start_date, end_date)

        except Exception as e:
            logging.error(f"[DATA_LOADER] Error loading GitHub data for {pair}: {e}")
            data[pair] = simulate_github_data(pair, start_date, end_date)

    return data


def simulate_github_data(
    pair: str,
    start_date: datetime,
    end_date: datetime
) -> pd.DataFrame:
    """
    Simulate GitHub cross-moat signals

    Args:
        pair: Trading pair
        start_date: Start date
        end_date: End date

    Returns:
        DataFrame with simulated cross-moat signals
    """
    logging.warning(f"[DATA_LOADER] Simulating GitHub data for {pair}")

    # Generate daily timestamps
    timestamps = []
    current = start_date
    while current <= end_date:
        timestamps.append(current)
        current += timedelta(hours=1)  # Hourly data

    # Simulate GitHub metrics
    np.random.seed(hash(pair) % 2**32)

    data = []
    for ts in timestamps:
        # Commits: 20-200 per day, with occasional spikes
        commits_24h = int(np.random.gamma(5, 10))  # Gamma distribution for occasional spikes

        # Contributors: 5-50
        contributors = int(np.random.uniform(5, 50))

        # Issues: 10-100
        open_issues = int(np.random.uniform(10, 100))

        # Dependency entropy: complex calculation
        import math
        if commits_24h > 0 and open_issues > 0:
            dependency_entropy = contributors * math.log(commits_24h + 1) / math.sqrt(open_issues)
        else:
            dependency_entropy = 0

        # Novelty score: commits per contributor
        novelty_score = (commits_24h / max(contributors, 1)) * 10

        data.append({
            'timestamp': ts,
            'commits_24h': commits_24h,
            'contributors': contributors,
            'open_issues': open_issues,
            'dependency_entropy': dependency_entropy,
            'novelty_score': novelty_score
        })

    df = pd.DataFrame(data)

    logging.info(f"[DATA_LOADER] Simulated {len(df)} GitHub records for {pair}")

    return df


def load_backtest_data(
    pairs: List[str],
    start_date: datetime,
    end_date: datetime,
    use_real_data: bool = True
) -> tuple[Dict[str, pd.DataFrame], Dict[str, pd.DataFrame]]:
    """
    Load all data required for backtesting

    Args:
        pairs: List of trading pairs
        start_date: Start date
        end_date: End date
        use_real_data: If True, attempt to load real Kraken data; otherwise simulate

    Returns:
        (market_data, cross_moat_data) tuple of dictionaries
    """
    logging.info(
        f"[DATA_LOADER] Loading backtest data | "
        f"Pairs: {pairs} | {start_date} to {end_date} | "
        f"Real data: {use_real_data}"
    )

    # Load market data
    if use_real_data:
        market_data = load_kraken_ohlcv_history(pairs, start_date, end_date)
    else:
        market_data = {
            pair: simulate_ohlcv_data(pair, start_date, end_date)
            for pair in pairs
        }

    # Load cross-moat data (currently always simulated)
    cross_moat_data = load_github_history(pairs, start_date, end_date)

    logging.info(
        f"[DATA_LOADER] Data loaded | "
        f"Market: {sum(len(df) for df in market_data.values())} candles | "
        f"GitHub: {sum(len(df) for df in cross_moat_data.values())} records"
    )

    return market_data, cross_moat_data
