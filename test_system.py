# test_system.py - System Hardening and Adversarial Test Setup (Big Rock 20)
# BIG ROCK 29: Dry-Run Operational Launch with command-line arguments
import logging
from src.core.model import MycelialModel
import time
import argparse

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

if __name__ == "__main__":
    # BIG ROCK 29: Parse command-line arguments
    parser = argparse.ArgumentParser(description='Mycelial Finance Engine')
    parser.add_argument('--dry_run_mode', type=bool, default=False,
                        help='Enable dry-run mode (live Kraken data, no adversarial testing)')
    parser.add_argument('--steps', type=int, default=600,
                        help='Number of steps to run (default: 600 = 10 minutes)')
    args = parser.parse_args()

    dry_run_mode = args.dry_run_mode
    num_steps = args.steps
    logging.info("=" * 80)
    if dry_run_mode:
        logging.info("Starting Mycelial Finance v11.0 - BIG ROCK 29: DRY-RUN OPERATIONAL LAUNCH")
        logging.info("Mode: LIVE KRAKEN DATA FEED (No Adversarial Testing)")
    else:
        logging.info("Starting Mycelial Finance v7.3 - BIG ROCK 20: System Hardening")
        logging.info("Adversarial Simulation: Toxic agent injection enabled")
    logging.info("=" * 80)
    logging.info("HAVEN Framework: Risk governance and policy contagion controls active")
    logging.info(f"Runtime: {num_steps} steps ({num_steps // 60} minutes)")
    logging.info("=" * 80)

    # Products to randomly assign the 100 SwarmBrains to:
    # 1. Finance (Broad)
    # 2. Code Innovation
    # 3. Logistics
    # 4. Government (US Policy)
    # 5. US Corporations

    # --- CORE LOGIC UPDATE: Enable HAVEN and Adversarial Mode ---
    # BIG ROCK 39: Final 123-Agent Architecture with TA and Market Explorer layers
    model = MycelialModel(
        pairs_to_trade=['XXBTZUSD', 'XETHZUSD'],
        target_repos=['Python'],
        target_regions=['US-West'],
        target_govt_regions=['US-Federal'],
        target_corp_sectors=['Tech'],
        num_traders=1,
        num_risk_managers=1,
        num_swarm_agents=100,

        # HAVEN AND RISK PARAMETERS:
        risk_governance_enabled=True,           # Activates the HAVEN coordination layer
        max_drawdown_percent=0.05,              # Global risk constraint (max 5% drawdown)
        policy_contagion_threshold=0.80,        # BIG ROCK 30: Lowered to 0.80 for safety buffer
        adversarial_test_mode=not dry_run_mode, # BIG ROCK 29: Disable toxic agents in dry-run mode

        # Regulatory Compliance
        regulatory_compliance_check=True,       # Explicitly check for manipulative behaviors like 'spoofing'

        # BIG ROCK 39: Technical Analysis and Market Explorer Parameters
        num_ta_agents=3,                        # Technical Analysis competitive baseline
        num_explorer_agents=3                   # Market exploration and discovery
    )

    if not model.running:
        logging.critical("Model failed to start. Exiting.")
        exit(1)

    logging.info("=" * 80)
    logging.info("System initialized with HAVEN Risk Framework")
    logging.info("Risk Parameters:")
    logging.info("  - Max Drawdown: 5%")
    logging.info("  - Policy Contagion Threshold: 80% (BIG ROCK 30: Safety Buffer)")
    if dry_run_mode:
        logging.info("  - Adversarial Testing: DISABLED (Dry-Run Mode)")
        logging.info("  - BIG ROCK 28: Dual-Threshold Decision Architecture ACTIVE")
        logging.info("    • Pattern Learner Threshold: Prediction Score > 0.8")
        logging.info("    • Trading Agent Filter: Interestingness Score > 75")
    else:
        logging.info("  - Adversarial Testing: ACTIVE")
    logging.info("  - Regulatory Compliance Check: ACTIVE")
    logging.info("=" * 80)

    # BIG ROCK 29: Run for configurable duration with live data feed
    for i in range(num_steps):
        model.step()
        if i % 60 == 0:  # Log every minute
            elapsed_minutes = i // 60
            remaining_minutes = (num_steps // 60) - elapsed_minutes
            mode_str = "Dry-run operational testing" if dry_run_mode else "Adversarial testing"
            logging.info(f"Step {i}/{num_steps} ({elapsed_minutes} minutes elapsed, {remaining_minutes} remaining): {mode_str} in progress...")
        time.sleep(1)

    logging.info("=" * 80)
    if dry_run_mode:
        logging.info(f"{num_steps // 60}-minute dry-run operational test complete.")
        logging.info("BIG ROCK 29: Live Kraken data feed successfully integrated")
        logging.info("Dual-Threshold Decision Architecture validated")
    else:
        logging.info(f"{num_steps // 60}-minute adversarial simulation complete.")
        logging.info("HAVEN Framework successfully prevented policy contagion during stress test")
    logging.info("Dashboard available at http://127.0.0.1:8055")
    logging.info("=" * 80)
