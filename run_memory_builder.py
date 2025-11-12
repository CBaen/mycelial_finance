#!/usr/bin/env python3
# run_memory_builder.py - Build Agent Memory Through Backtesting
"""
Memory Builder: Generate Historical Data for Agent Intelligence

This script runs comprehensive backtests to:
1. Generate trading patterns from historical data
2. Store successful and failed patterns in ChromaDB
3. Build enriched market intelligence using multiple APIs
4. Create a knowledge base that agents can reference

The goal: Give our AI agents a rich memory to learn from.
"""

import logging
import sys
from datetime import datetime, timedelta
from typing import Dict, List
import pandas as pd
import json

# Add src to path
sys.path.insert(0, './src')

from backtesting.backtest_engine import BacktestEngine, BacktestConfig, StrategyType
from backtesting.data_loader import load_backtest_data
from storage.chroma_client import ChromaDBClient, create_pattern_embedding
from connectors.market_data_aggregator import MarketDataAggregator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('memory_builder.log'),
        logging.StreamHandler(sys.stdout)
    ]
)


class MemoryBuilder:
    """
    Builds agent memory through backtesting and enriched data collection
    """

    def __init__(self, chroma_dir: str = "./chroma_db"):
        """
        Initialize memory builder

        Args:
            chroma_dir: Directory for ChromaDB storage
        """
        self.chroma = ChromaDBClient(persist_directory=chroma_dir)
        self.aggregator = MarketDataAggregator()
        self.engine = BacktestEngine()

        logging.info("[MEMORY] Memory builder initialized")

    def run_backtest_and_store(self, pairs: List[str], days_back: int = 90,
                               initial_capital: float = 10000.0):
        """
        Run backtests and store all patterns in agent memory

        Args:
            pairs: List of trading pairs to backtest
            days_back: How many days of history to test
            initial_capital: Starting capital for backtest
        """
        logging.info(f"[MEMORY] Starting backtest for {len(pairs)} pairs, {days_back} days back")

        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        # Create backtest config
        config = BacktestConfig(
            start_date=start_date,
            end_date=end_date,
            pairs=pairs,
            initial_capital=initial_capital,
            trading_fee_pct=0.36,
            slippage_pct=0.1
        )

        # Load data
        logging.info("[MEMORY] Loading historical data...")
        market_data, cross_moat_data = load_backtest_data(
            pairs=pairs,
            start_date=start_date,
            end_date=end_date,
            use_real_data=False  # Set to True if you have real API access
        )

        # Run backtest
        logging.info("[MEMORY] Running backtest with both strategies...")
        results = self.engine.run(market_data, cross_moat_data)

        # Store patterns from both strategies
        self._store_strategy_patterns(results, StrategyType.TA_ONLY, "TA-Only Strategy")
        self._store_strategy_patterns(results, StrategyType.CROSS_MOAT, "Cross-Moat Strategy")

        # Print summary
        self._print_memory_summary(results)

        return results

    def _store_strategy_patterns(self, results: Dict, strategy: StrategyType, strategy_name: str):
        """
        Extract and store patterns from a strategy's backtest results

        Args:
            results: Backtest results
            strategy: Strategy type
            strategy_name: Human-readable strategy name
        """
        logging.info(f"[MEMORY] Storing patterns from {strategy_name}...")

        result = results[strategy]

        # Store each closed position as a pattern
        for position in result.closed_positions:
            pattern_id = f"{strategy.value}_{position['pair']}_{position['entry_time'].isoformat()}"

            # Create pattern data
            pattern_data = {
                'pair': position['pair'],
                'direction': position['direction'],
                'entry_price': position['entry_price'],
                'exit_price': position['exit_price'],
                'pnl_pct': position['pnl_pct'],
                'rsi': position.get('entry_rsi', 50.0),
                'macd': position.get('entry_macd', 0.0),
                'volume': position.get('entry_volume', 0.0),
                'cross_moat_score': position.get('cross_moat_score', 0),
                'timestamp': position['entry_time'],
                'strategy': strategy.value
            }

            # Create embedding
            embedding = create_pattern_embedding(pattern_data)

            # Determine success (profitable = success)
            success = position['pnl_pct'] > 0

            # Store in ChromaDB
            self.chroma.store_pattern(
                pattern_id=pattern_id,
                embedding=embedding,
                metadata=pattern_data,
                success=success
            )

        logging.info(
            f"[MEMORY] Stored {len(result.closed_positions)} patterns from {strategy_name} "
            f"(Success rate: {result.win_rate*100:.1f}%)"
        )

    def enrich_with_current_data(self, pairs: List[str]):
        """
        Enrich memory with current market data from APIs

        Args:
            pairs: List of pairs to fetch current data for
        """
        logging.info("[MEMORY] Enriching memory with current market data...")

        for pair in pairs:
            # Extract symbol (e.g., 'XXBTZUSD' -> 'BTC')
            if 'BTC' in pair:
                symbol = 'BTC'
            elif 'ETH' in pair:
                symbol = 'ETH'
            elif 'LTC' in pair:
                symbol = 'LTC'
            elif 'XRP' in pair:
                symbol = 'XRP'
            else:
                continue

            logging.info(f"[MEMORY] Fetching enriched data for {symbol}...")

            # Get enriched market data
            enriched_data = self.aggregator.get_enriched_market_data(symbol)

            if enriched_data and 'price' in enriched_data:
                # Create a "current state" pattern
                pattern_id = f"current_{symbol}_{datetime.now().isoformat()}"

                pattern_data = {
                    'pair': pair,
                    'price': enriched_data['price'],
                    'market_cap': enriched_data.get('market_cap', 0),
                    'volume_24h': enriched_data.get('volume_24h', 0),
                    'change_24h': enriched_data.get('change_24h', 0),
                    'timestamp': datetime.now(),
                    'source': 'market_data_api'
                }

                # Add RSI/MACD placeholders (will be calculated by agents)
                pattern_data['rsi'] = 50.0
                pattern_data['macd'] = 0.0
                pattern_data['cross_moat_score'] = 0

                # Create embedding
                embedding = create_pattern_embedding(pattern_data)

                # Store as neutral pattern (not success or failure)
                self.chroma.store_pattern(
                    pattern_id=pattern_id,
                    embedding=embedding,
                    metadata=pattern_data,
                    success=True  # Store in trading_patterns for reference
                )

                logging.info(f"[MEMORY] Stored current market state for {symbol}")

        # Get overall market sentiment
        market_story = self.aggregator.get_market_story()
        if market_story:
            logging.info(f"[MEMORY] Market sentiment: {market_story.get('sentiment', 'UNKNOWN')}")

    def _print_memory_summary(self, results: Dict):
        """Print summary of what was stored in memory"""
        logging.info("\n" + "="*80)
        logging.info("MEMORY BANK SUMMARY")
        logging.info("="*80)

        # Backtest results
        for strategy, result in results.items():
            logging.info(f"\n{strategy.value} Results:")
            logging.info(f"  Total P&L: {result.total_pnl_pct:+.2f}%")
            logging.info(f"  Trades: {result.total_trades}")
            logging.info(f"  Win Rate: {result.win_rate*100:.1f}%")
            logging.info(f"  Sharpe Ratio: {result.sharpe_ratio:.3f}")
            logging.info(f"  Max Drawdown: {result.max_drawdown:.2f}%")

        # ChromaDB stats
        stats = self.chroma.get_collection_stats()
        logging.info(f"\nMemory Bank Stats:")
        logging.info(f"  Total Patterns: {stats['total']}")
        logging.info(f"  Successful: {stats['trading_patterns']}")
        logging.info(f"  Failed: {stats['failed_patterns']}")
        logging.info(f"  Agent Knowledge: {stats['agent_knowledge']}")

        logging.info("\n" + "="*80)

    def export_memory_summary(self, output_file: str = "memory_summary.json"):
        """
        Export a summary of stored memories to JSON

        Args:
            output_file: Output filename
        """
        stats = self.chroma.get_collection_stats()

        # Get top patterns
        top_patterns = self.chroma.get_top_performing_patterns(n_results=20)

        summary = {
            'timestamp': datetime.now().isoformat(),
            'stats': stats,
            'top_patterns': [
                {
                    'id': p['id'],
                    'pnl_pct': p['pnl_pct'],
                    'metadata': p['metadata']
                }
                for p in top_patterns
            ]
        }

        with open(output_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)

        logging.info(f"[MEMORY] Summary exported to {output_file}")


def main():
    """
    Main execution: Build agent memory through backtesting
    """
    logging.info("="*80)
    logging.info("MEMORY BUILDER - Building Agent Intelligence")
    logging.info("="*80)

    # Initialize builder
    builder = MemoryBuilder()

    # Define trading pairs
    pairs = ["XXBTZUSD", "XETHZUSD", "XLTCZUSD", "XXRPZUSD"]

    # Step 1: Run backtests and store patterns
    logging.info("\n[STEP 1] Running backtests to generate historical patterns...")
    results = builder.run_backtest_and_store(
        pairs=pairs,
        days_back=90,  # 3 months of history
        initial_capital=10000.0
    )

    # Step 2: Enrich with current market data
    logging.info("\n[STEP 2] Enriching memory with current market data...")
    builder.enrich_with_current_data(pairs)

    # Step 3: Export summary
    logging.info("\n[STEP 3] Exporting memory summary...")
    builder.export_memory_summary("memory_summary.json")

    # Final stats
    logging.info("\n" + "="*80)
    logging.info("MEMORY BUILDING COMPLETE!")
    logging.info("="*80)
    logging.info("\nYour AI agents now have a rich memory to learn from.")
    logging.info("They can:")
    logging.info("  ✓ Find similar historical patterns")
    logging.info("  ✓ Learn from past successes and failures")
    logging.info("  ✓ Reference current market conditions")
    logging.info("  ✓ Make more informed trading decisions")
    logging.info("\nNext step: Run the storytelling dashboard to see what they learned!")
    logging.info("  python dashboard_storytelling.py")
    logging.info("="*80)


if __name__ == "__main__":
    main()
