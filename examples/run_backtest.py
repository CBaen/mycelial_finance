#!/usr/bin/env python
# examples/run_backtest.py - PHASE 4.1: Backtest Runner Example
"""
Example script to run backtesting and validate the cross-moat hypothesis (Q10)

Usage:
    python examples/run_backtest.py

This script:
1. Loads historical market data (OHLCV) and cross-moat signals (GitHub)
2. Runs A/B test comparing:
   - TA-only strategy (baseline)
   - Cross-moat strategy (experimental)
3. Generates performance comparison report
4. Exports results to JSON
"""

import sys
import os
import logging
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.backtesting.backtest_engine import BacktestEngine, BacktestConfig
from src.backtesting.data_loader import load_backtest_data


def main():
    """Run backtesting example"""

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    print("\n" + "="*80)
    print("MYCELIAL FINANCE - CROSS-MOAT HYPOTHESIS BACKTEST")
    print("="*80)
    print("\nQ10: Does GitHub activity predict crypto volatility?")
    print("Testing hypothesis with A/B comparison:\n")
    print("  [BASELINE]     TA-Only Strategy - Technical Analysis alone")
    print("  [EXPERIMENTAL] Cross-Moat Strategy - TA + GitHub signals\n")
    print("="*80 + "\n")

    # ==========================================================================
    # CONFIGURATION
    # ==========================================================================

    # Backtest period: 3 months of historical data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)

    # Trading pairs to test
    pairs = ["XXBTZUSD", "XETHZUSD"]

    print(f"Configuration:")
    print(f"  Period:       {start_date.date()} to {end_date.date()}")
    print(f"  Pairs:        {', '.join(pairs)}")
    print(f"  Capital:      $10,000.00")
    print(f"  Trading fees: 0.72% round-trip\n")

    # Create backtest configuration
    config = BacktestConfig(
        start_date=start_date,
        end_date=end_date,
        pairs=pairs,
        initial_capital=10000.0
    )

    # ==========================================================================
    # LOAD DATA
    # ==========================================================================

    print("Loading historical data...")
    print("-" * 80)

    # Load market data and cross-moat signals
    # Note: Set use_real_data=True to attempt loading real Kraken data
    # Currently defaults to simulated data for demonstration
    market_data, cross_moat_data = load_backtest_data(
        pairs=pairs,
        start_date=start_date,
        end_date=end_date,
        use_real_data=False  # Set to True to use real Kraken API
    )

    # Print data summary
    for pair in pairs:
        market_candles = len(market_data[pair])
        github_records = len(cross_moat_data[pair])
        print(f"  {pair}: {market_candles} candles, {github_records} GitHub records")

    print()

    # ==========================================================================
    # RUN BACKTEST
    # ==========================================================================

    print("Running backtest...")
    print("-" * 80)

    # Initialize engine
    engine = BacktestEngine(config)

    # Run backtest
    results = engine.run(market_data, cross_moat_data)

    # ==========================================================================
    # EXPORT RESULTS
    # ==========================================================================

    output_file = "backtest_results.json"
    engine.export_results(output_file)

    print(f"\nResults exported to: {output_file}")

    # ==========================================================================
    # ANALYSIS
    # ==========================================================================

    from src.backtesting.backtest_engine import StrategyType

    ta_results = results[StrategyType.TA_ONLY]
    cm_results = results[StrategyType.CROSS_MOAT]

    print("\n" + "="*80)
    print("HYPOTHESIS TEST RESULTS")
    print("="*80)

    improvement = cm_results.total_pnl_pct - ta_results.total_pnl_pct

    if improvement > 0:
        print(f"\n✅ HYPOTHESIS VALIDATED")
        print(f"\nCross-moat signals provide a {improvement:+.2f}% improvement over TA-only.")
        print(f"This suggests GitHub activity DOES predict crypto volatility.")
        print(f"\nNext steps:")
        print(f"  1. Increase confidence with longer backtest period")
        print(f"  2. Test across more trading pairs")
        print(f"  3. Tune cross-moat signal weights")
        print(f"  4. Deploy to paper trading environment")

    elif improvement > -1.0:
        print(f"\n⚠️  HYPOTHESIS INCONCLUSIVE")
        print(f"\nCross-moat signals show {improvement:+.2f}% difference (not significant).")
        print(f"This suggests GitHub activity may have weak predictive power.")
        print(f"\nNext steps:")
        print(f"  1. Extend backtest period for more data")
        print(f"  2. Refine cross-moat signal calculation")
        print(f"  3. Test alternative cross-moat thresholds")
        print(f"  4. Investigate time lag between GitHub activity and price movement")

    else:
        print(f"\n❌ HYPOTHESIS NOT VALIDATED")
        print(f"\nCross-moat signals show {improvement:+.2f}% worse performance.")
        print(f"This suggests GitHub activity DOES NOT predict crypto volatility reliably.")
        print(f"\nPossible explanations:")
        print(f"  1. No causal relationship between GitHub commits and price")
        print(f"  2. Time lag not captured (commits → price movement delay)")
        print(f"  3. Wrong GitHub metrics (need different features)")
        print(f"  4. Overfitting to specific market conditions")
        print(f"\nNext steps:")
        print(f"  1. Test with different cross-moat features (issues, PRs, contributors)")
        print(f"  2. Introduce time lag analysis (e.g., 24h, 48h, 7d delays)")
        print(f"  3. Focus on high-activity periods only")
        print(f"  4. Consider alternative moats (Logistics, Government)")

    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    main()
