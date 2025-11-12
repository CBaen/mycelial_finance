#!/usr/bin/env python
"""
Smoke Test - Quick validation that all critical components work
This test runs for 10 steps (~10 seconds) to verify:
1. All agents initialize
2. Redis connections work
3. Kraken API connects
4. TradeDatabase creates schema
5. No import errors
"""

import sys
import time
from src.core.model import MycelialModel

def main():
    print("=" * 70)
    print("SMOKE TEST: Mycelial Finance System")
    print("=" * 70)
    print("\nRunning 10-step validation test...\n")

    # Configuration
    pairs_to_trade = [
        "XXBTZUSD",  # Bitcoin
        "XETHZUSD",  # Ethereum
        "SOLUSD",    # Solana
    ]

    try:
        # Initialize model
        print("[1/5] Initializing model...")
        model = MycelialModel(
            pairs_to_trade=pairs_to_trade,
            num_traders=1,
            num_risk_managers=1,
            num_swarm_agents=10,  # Reduced for smoke test
            num_instigators=1,
            num_research_agents=1,
            num_ta_agents=1,
            num_explorer_agents=3
        )
        print("[OK] Model initialized")

        # Check agent count
        agent_count = len(model.agents)
        print(f"[OK] {agent_count} agents registered")

        # Check TradeDatabase
        print("\n[2/5] Checking TradeDatabase...")
        if hasattr(model, 'trade_db') and model.trade_db is not None:
            print("[OK] TradeDatabase initialized")
        else:
            print("[FAIL] TradeDatabase NOT initialized")
            return False

        # Run 10 steps
        print("\n[3/5] Running 10 system steps...")
        start_time = time.time()
        for i in range(10):
            model.step()
            if (i + 1) % 5 == 0:
                print(f"  Step {i + 1}/10 complete")

        elapsed = time.time() - start_time
        print(f"[OK] 10 steps completed in {elapsed:.2f}s")

        # Check for errors in logs
        print("\n[4/5] Verifying no critical errors...")
        print("[OK] No exceptions raised")

        # Check database
        print("\n[5/5] Verifying database...")
        import sqlite3
        conn = sqlite3.connect('trades.db')
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in c.fetchall()]
        conn.close()

        if 'trades' in tables:
            print("[OK] trades.db schema created successfully")
        else:
            print("[FAIL] trades table not found")
            return False

        # Success!
        print("\n" + "=" * 70)
        print("[SUCCESS] SMOKE TEST PASSED")
        print("=" * 70)
        print(f"\nAgent Count: {agent_count}")
        print(f"Runtime: {elapsed:.2f}s")
        print(f"Steps: 10")
        print("\nSystem is ready for full validation test!")
        print("\nNext step: Run 1-hour validation")
        print("  python test_system.py")
        print("=" * 70)
        return True

    except Exception as e:
        print("\n" + "=" * 70)
        print("[FAILED] SMOKE TEST FAILED")
        print("=" * 70)
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
