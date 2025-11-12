# src/agents/trading_agent.py - BIG ROCK 41 (Corrected): The Synthesis Gateway
import logging
from .base_agent import MycelialAgent
import time

# PHASE 2.1: Realistic trading costs (Kraken fees + market impact)
TRADING_FEE_PCT = 0.26  # 0.26% per trade (Kraken maker/taker average)
SLIPPAGE_PCT = 0.10     # 0.10% slippage (market impact)
TOTAL_COST_PCT = (TRADING_FEE_PCT + SLIPPAGE_PCT) / 100.0  # 0.0036 (0.36% per trade)

class TradingAgent(MycelialAgent):
    """
    BIG ROCK 41 (Corrected): The Synthesis Gateway - Signal Collision Detector

    This agent listens to BOTH:
    1. 'mycelial-trade-ideas' (Causal pattern discoveries from Swarm)
    2. 'baseline-trade-ideas' (Technical Analysis signals)

    It ONLY executes trades when both signals AGREE (Signal Collision) within a 5-second window.
    This creates the highest-conviction "Trifecta" signal.

    Three P&L streams are tracked:
    - Baseline P&L (if we traded every TA signal)
    - Mycelial P&L (if we traded every Swarm signal)
    - Synthesized P&L (when both agree - our primary product)
    """
    def __init__(self, model):
        super().__init__(model)
        self.name = f"Trader_{self.unique_id}"

        # BIG ROCK 41: Listen to both idea channels
        self.mycelial_channel = "mycelial-trade-ideas"
        self.baseline_channel = "baseline-trade-ideas"
        self.synthesized_channel = "synthesized-trade-log"
        self.confirmation_channel = "trade-confirmations"

        # BIG ROCK 41: Track recent ideas for collision detection
        self.recent_mycelial_ideas = {}  # {pair: {'direction': str, 'timestamp': float, 'data': dict}}
        self.recent_baseline_ideas = {}  # {pair: {'direction': str, 'timestamp': float, 'data': dict}}

        # BIG ROCK 41: Collision detection window (5 seconds)
        self.collision_window = 5.0

        # BIG ROCK 41: P&L Tracking for all three streams
        self.baseline_pnl = 0.0
        self.mycelial_pnl = 0.0
        self.synthesized_pnl = 0.0

        self.baseline_trades = 0
        self.mycelial_trades = 0
        self.synthesized_trades = 0

        # Track open positions for P&L calculation
        self.baseline_positions = {}  # {pair: {'entry_price': float, 'direction': str}}
        self.mycelial_positions = {}
        self.synthesized_positions = {}

        # Register listeners
        self._register_listener(self.mycelial_channel, self.handle_mycelial_idea)
        self._register_listener(self.baseline_channel, self.handle_baseline_idea)

        logging.info(f"[{self.name}] Synthesis Gateway initialized - listening for Signal Collisions")

    def step(self):
        """Purely reactive agent"""
        pass

    def handle_baseline_idea(self, message: dict):
        """
        BIG ROCK 41: Store baseline TA ideas and check for collisions
        """
        try:
            pair = message.get('pair')
            direction = message.get('direction')

            if not pair or not direction:
                return

            # Store the baseline idea
            self.recent_baseline_ideas[pair] = {
                'direction': direction,
                'timestamp': time.time(),
                'data': message
            }

            # Simulate P&L for baseline stream
            self._track_pnl_for_signal(pair, direction, message, 'baseline')

            # Check for Signal Collision
            self._check_for_collision(pair)

            logging.debug(f"[{self.name}] Baseline idea: {direction.upper()} {pair}")

        except Exception as e:
            logging.error(f"[{self.name}] Error handling baseline idea: {e}")

    def handle_mycelial_idea(self, message: dict):
        """
        BIG ROCK 41: Store Mycelial ideas and check for collisions
        """
        try:
            pair = message.get('pair')
            direction = message.get('direction')

            if not pair or not direction:
                return

            # Store the Mycelial idea
            self.recent_mycelial_ideas[pair] = {
                'direction': direction,
                'timestamp': time.time(),
                'data': message
            }

            # Simulate P&L for Mycelial stream
            self._track_pnl_for_signal(pair, direction, message, 'mycelial')

            # Check for Signal Collision
            self._check_for_collision(pair)

            logging.debug(f"[{self.name}] Mycelial idea: {direction.upper()} {pair}")

        except Exception as e:
            logging.error(f"[{self.name}] Error handling mycelial idea: {e}")

    def _check_for_collision(self, pair: str):
        """
        BIG ROCK 41: THE CORE LOGIC - Detect Signal Collisions

        A "collision" occurs when:
        1. Both Mycelial and Baseline have ideas for the same pair
        2. Both ideas have the SAME direction (buy/sell)
        3. Both ideas arrived within the collision window (5 seconds)

        This creates the highest-conviction "Synthesized Signal"
        """
        baseline_idea = self.recent_baseline_ideas.get(pair)
        mycelial_idea = self.recent_mycelial_ideas.get(pair)

        if not baseline_idea or not mycelial_idea:
            return  # No collision possible yet

        # Check time window
        time_diff = abs(baseline_idea['timestamp'] - mycelial_idea['timestamp'])
        if time_diff > self.collision_window:
            return  # Ideas are too far apart in time

        # Check direction agreement
        if baseline_idea['direction'] != mycelial_idea['direction']:
            logging.warning(
                f"[{self.name}] CONFLICT detected for {pair}: "
                f"Baseline={baseline_idea['direction']}, Mycelial={mycelial_idea['direction']}"
            )
            return  # Directions don't agree - no collision

        # ✓ SIGNAL COLLISION DETECTED! ✓
        direction = baseline_idea['direction']

        logging.info(
            f"[{self.name}] ✓✓✓ SIGNAL COLLISION ✓✓✓ {direction.upper()} {pair} | "
            f"Time diff: {time_diff:.2f}s | EXECUTING SYNTHESIZED TRADE"
        )

        # Execute the synthesized trade
        self._execute_synthesized_trade(pair, direction, baseline_idea['data'], mycelial_idea['data'])

        # Clear the collision so we don't execute it again
        self.recent_baseline_ideas.pop(pair, None)
        self.recent_mycelial_ideas.pop(pair, None)

    def _track_pnl_for_signal(self, pair: str, direction: str, message: dict, source: str):
        """
        BIG ROCK 41: Track simulated P&L for each signal stream independently
        """
        current_price = message.get('current_price', 0)
        if current_price == 0:
            return

        if source == 'baseline':
            positions = self.baseline_positions
            pnl_attr = 'baseline_pnl'
            trades_attr = 'baseline_trades'
        elif source == 'mycelial':
            positions = self.mycelial_positions
            pnl_attr = 'mycelial_pnl'
            trades_attr = 'mycelial_trades'
        else:
            return

        if direction == 'buy':
            # Open position
            positions[pair] = {
                'entry_price': current_price,
                'direction': 'long'
            }
            setattr(self, trades_attr, getattr(self, trades_attr) + 1)

        elif direction == 'sell' and pair in positions:
            # Close position and calculate P&L (PHASE 2.1: with fees + slippage)
            entry_price = positions[pair]['entry_price']

            # Calculate raw P&L
            raw_pnl_pct = ((current_price - entry_price) / entry_price) * 100

            # Apply trading costs: 0.36% per round trip (0.26% fee + 0.10% slippage)
            # Round trip = buy + sell = 2 trades
            total_cost_pct = TOTAL_COST_PCT * 2 * 100  # Convert to percentage

            # Net P&L after costs
            net_pnl_pct = raw_pnl_pct - total_cost_pct

            current_pnl = getattr(self, pnl_attr)
            setattr(self, pnl_attr, current_pnl + net_pnl_pct)

            positions.pop(pair)

    def _execute_synthesized_trade(self, pair: str, direction: str, baseline_data: dict, mycelial_data: dict):
        """
        BIG ROCK 41: Execute the highest-conviction Synthesized trade

        This is where the magic happens - when both systems agree, we have
        the strongest possible signal.
        """
        try:
            current_price = mycelial_data.get('current_price', 0)

            # Track P&L for synthesized stream
            if direction == 'buy':
                self.synthesized_positions[pair] = {
                    'entry_price': current_price,
                    'direction': 'long'
                }
                self.synthesized_trades += 1

            elif direction == 'sell' and pair in self.synthesized_positions:
                entry_price = self.synthesized_positions[pair]['entry_price']

                # Calculate raw P&L
                raw_pnl_pct = ((current_price - entry_price) / entry_price) * 100

                # PHASE 2.1: Apply trading costs (0.36% round trip)
                total_cost_pct = TOTAL_COST_PCT * 2 * 100

                # Net P&L after costs
                net_pnl_pct = raw_pnl_pct - total_cost_pct
                self.synthesized_pnl += net_pnl_pct
                self.synthesized_positions.pop(pair)

            # Execute via Kraken client
            result = self.kraken_client.place_order(
                pair=pair,
                order_type='market',
                direction=direction,
                amount=0.001,
                price=None
            )

            # Publish to synthesized-trade-log channel for dashboard
            log_message = {
                "source": self.name,
                "signal_type": "SYNTHESIZED",
                "pair": pair,
                "direction": direction,
                "current_price": current_price,
                "baseline_confidence": baseline_data.get('confidence', 0),
                "mycelial_total_pnl": mycelial_data.get('total_pnl', 0),
                "mycelial_win_rate": mycelial_data.get('win_rate', 0),
                "execution_result": result,
                "timestamp": time.time(),
                # BIG ROCK 41: Include all three P&L streams
                "baseline_pnl": self.baseline_pnl,
                "mycelial_pnl": self.mycelial_pnl,
                "synthesized_pnl": self.synthesized_pnl,
                "baseline_trades": self.baseline_trades,
                "mycelial_trades": self.mycelial_trades,
                "synthesized_trades": self.synthesized_trades
            }
            self.publish(self.synthesized_channel, log_message)

            # Also publish confirmation
            confirmation = {
                "source": self.name,
                "signal_type": "SYNTHESIZED",
                "baseline_idea": baseline_data,
                "mycelial_idea": mycelial_data,
                "execution_result": result
            }
            self.publish(self.confirmation_channel, confirmation)

        except Exception as e:
            logging.error(f"[{self.name}] Error executing synthesized trade: {e}")
