# src/agents/memory_agent.py - Memory-Driven Agent Intelligence
"""
Memory Agent: Agents with Long-Term Memory

This module gives agents the ability to:
1. Store successful/failed patterns in ChromaDB
2. Search for similar historical situations
3. Learn from past experiences
4. Make informed decisions based on memory

Integration with market data APIs for enriched context.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import numpy as np

from src.storage.chroma_client import ChromaDBClient, create_pattern_embedding
from src.connectors.market_data_aggregator import MarketDataAggregator


class MemoryAgent:
    """
    Agent with long-term memory capabilities

    Uses ChromaDB to store and retrieve trading patterns,
    enabling learning from historical experiences.
    """

    def __init__(self, agent_id: str, pair: str, chroma_client: ChromaDBClient = None):
        """
        Initialize memory agent

        Args:
            agent_id: Unique agent identifier
            pair: Trading pair this agent focuses on
            chroma_client: Optional ChromaDB client (creates new if None)
        """
        self.agent_id = agent_id
        self.pair = pair

        # Initialize memory storage
        if chroma_client:
            self.chroma = chroma_client
        else:
            self.chroma = ChromaDBClient(persist_directory="./chroma_db")

        # Initialize market data aggregator
        self.market_data = MarketDataAggregator()

        # Agent learning stats
        self.patterns_stored = 0
        self.successful_patterns = 0
        self.failed_patterns = 0

        logging.info(f"[MEMORY-AGENT] {agent_id} initialized for {pair}")

    def analyze_current_situation(self, market_state: Dict) -> Dict:
        """
        Analyze current market state with enriched data and memory

        Args:
            market_state: Current market indicators (RSI, MACD, volume, etc.)

        Returns:
            Analysis with recommendations based on memory
        """
        # Extract symbol from pair (e.g., XXBTZUSD -> BTC)
        symbol = self._extract_symbol(self.pair)

        # Get enriched market data
        enriched_data = self.market_data.get_enriched_market_data(symbol)

        # Create pattern embedding from current state
        pattern_data = {
            'rsi': market_state.get('rsi', 50.0),
            'macd': market_state.get('macd', 0.0),
            'volume': market_state.get('volume', 0.0),
            'price_change_pct': enriched_data.get('change_24h', 0.0) if enriched_data else 0.0,
            'cross_moat_score': market_state.get('cross_moat_score', 0),
            'timestamp': datetime.now()
        }

        current_embedding = create_pattern_embedding(pattern_data)

        # Search memory for similar patterns
        similar_patterns = self.chroma.find_similar_patterns(
            query_embedding=current_embedding,
            n_results=10,
            success_only=True,
            filter_metadata={'pair': self.pair}
        )

        # Analyze similar patterns
        analysis = self._analyze_similar_patterns(similar_patterns, pattern_data, enriched_data)

        return analysis

    def _analyze_similar_patterns(self, similar_patterns: List[Dict],
                                  current_data: Dict, enriched_data: Optional[Dict]) -> Dict:
        """
        Analyze similar patterns and generate recommendations

        Args:
            similar_patterns: List of similar historical patterns
            current_data: Current market state
            enriched_data: Enriched market data from APIs

        Returns:
            Analysis with confidence, recommendation, and reasoning
        """
        if not similar_patterns:
            return {
                'confidence': 'low',
                'recommendation': 'OBSERVE',
                'reasoning': 'No similar historical patterns found. Not enough data to make confident decision.',
                'similar_count': 0
            }

        # Calculate statistics from similar patterns
        profits = [p['metadata'].get('pnl_pct', 0) for p in similar_patterns]
        avg_profit = np.mean(profits)
        success_rate = sum(1 for p in profits if p > 0) / len(profits)

        # Get market sentiment
        market_sentiment = 'NEUTRAL'
        if enriched_data and 'market_sentiment' in enriched_data:
            market_sentiment = enriched_data['market_sentiment'].get('sentiment', 'NEUTRAL')

        # Decision logic
        confidence = 'low'
        recommendation = 'OBSERVE'
        reasoning = ''

        if len(similar_patterns) >= 5 and success_rate > 0.6 and avg_profit > 1.0:
            confidence = 'high'
            recommendation = 'BUY'
            reasoning = (
                f"Found {len(similar_patterns)} similar patterns. "
                f"Success rate: {success_rate*100:.1f}%. "
                f"Average profit: {avg_profit:.2f}%. "
                f"Market sentiment: {market_sentiment}. "
                f"Historical data suggests this is a good opportunity."
            )
        elif len(similar_patterns) >= 3 and success_rate > 0.5:
            confidence = 'medium'
            recommendation = 'BUY_SMALL'
            reasoning = (
                f"Found {len(similar_patterns)} similar patterns with moderate success. "
                f"Success rate: {success_rate*100:.1f}%. "
                f"Average profit: {avg_profit:.2f}%. "
                f"Recommend small position to test this pattern."
            )
        elif avg_profit < -1.0 or success_rate < 0.4:
            confidence = 'medium'
            recommendation = 'AVOID'
            reasoning = (
                f"Found {len(similar_patterns)} similar patterns with poor outcomes. "
                f"Success rate: {success_rate*100:.1f}%. "
                f"Average profit: {avg_profit:.2f}%. "
                f"Historical data suggests avoiding this trade."
            )
        else:
            confidence = 'low'
            recommendation = 'OBSERVE'
            reasoning = (
                f"Found {len(similar_patterns)} similar patterns, but results are mixed. "
                f"Success rate: {success_rate*100:.1f}%. "
                f"Not enough confidence to make a move."
            )

        return {
            'confidence': confidence,
            'recommendation': recommendation,
            'reasoning': reasoning,
            'similar_count': len(similar_patterns),
            'success_rate': success_rate,
            'avg_profit': avg_profit,
            'market_sentiment': market_sentiment,
            'top_similar_patterns': similar_patterns[:3]  # Top 3 most similar
        }

    def store_trade_outcome(self, trade_data: Dict, pnl_pct: float):
        """
        Store trade outcome in memory for future learning

        Args:
            trade_data: Trade details (entry signals, market state, etc.)
            pnl_pct: Profit/loss percentage
        """
        pattern_id = f"{self.agent_id}_{self.pair}_{datetime.now().isoformat()}"

        # Create pattern data
        pattern_data = {
            'pair': self.pair,
            'agent_id': self.agent_id,
            'direction': trade_data.get('direction', 'BUY'),
            'entry_price': trade_data.get('entry_price', 0.0),
            'exit_price': trade_data.get('exit_price', 0.0),
            'pnl_pct': pnl_pct,
            'rsi': trade_data.get('rsi', 50.0),
            'macd': trade_data.get('macd', 0.0),
            'volume': trade_data.get('volume', 0.0),
            'cross_moat_score': trade_data.get('cross_moat_score', 0),
            'timestamp': datetime.now()
        }

        # Create embedding
        embedding = create_pattern_embedding(pattern_data)

        # Determine success
        success = pnl_pct > 0

        # Store in ChromaDB
        self.chroma.store_pattern(
            pattern_id=pattern_id,
            embedding=embedding,
            metadata=pattern_data,
            success=success
        )

        # Update stats
        self.patterns_stored += 1
        if success:
            self.successful_patterns += 1
        else:
            self.failed_patterns += 1

        logging.info(
            f"[MEMORY-AGENT] {self.agent_id} stored pattern | "
            f"P&L: {pnl_pct:+.2f}% | Success: {success} | "
            f"Total patterns: {self.patterns_stored}"
        )

    def get_learning_stats(self) -> Dict:
        """Get agent's learning statistics"""
        success_rate = 0
        if self.patterns_stored > 0:
            success_rate = self.successful_patterns / self.patterns_stored

        return {
            'agent_id': self.agent_id,
            'pair': self.pair,
            'patterns_stored': self.patterns_stored,
            'successful_patterns': self.successful_patterns,
            'failed_patterns': self.failed_patterns,
            'success_rate': success_rate,
            'total_knowledge': self.chroma.get_collection_stats()
        }

    def find_peer_agents(self, n_peers: int = 3) -> List[Dict]:
        """
        Find similar agents for peer learning (Federated RL)

        Args:
            n_peers: Number of peer agents to find

        Returns:
            List of similar agents
        """
        similar_agents = self.chroma.find_similar_agents(
            agent_id=self.agent_id,
            n_results=n_peers
        )

        logging.info(
            f"[MEMORY-AGENT] {self.agent_id} found {len(similar_agents)} peer agents"
        )

        return similar_agents

    def get_market_story(self) -> str:
        """
        Get friendly market story for this pair

        Returns:
            Human-readable market narrative
        """
        story_data = self.market_data.get_market_story()

        if story_data and 'story' in story_data:
            return story_data['story']
        else:
            return "Unable to read market conditions right now."

    def _extract_symbol(self, pair: str) -> str:
        """Extract symbol from trading pair (e.g., XXBTZUSD -> BTC)"""
        if 'BTC' in pair:
            return 'BTC'
        elif 'ETH' in pair:
            return 'ETH'
        elif 'LTC' in pair:
            return 'LTC'
        elif 'XRP' in pair:
            return 'XRP'
        else:
            return pair[:3]  # Fallback


# =============================================================================
# MEMORY-DRIVEN AGENT SWARM
# =============================================================================

class MemoryAgentSwarm:
    """
    Manages a swarm of memory-driven agents

    Coordinates multiple agents across different pairs,
    enabling collective learning and knowledge sharing.
    """

    def __init__(self, pairs: List[str], chroma_dir: str = "./chroma_db"):
        """
        Initialize agent swarm

        Args:
            pairs: List of trading pairs
            chroma_dir: ChromaDB directory
        """
        self.chroma = ChromaDBClient(persist_directory=chroma_dir)
        self.agents: Dict[str, MemoryAgent] = {}

        # Create agents for each pair
        for pair in pairs:
            agent_id = f"memory_agent_{pair}"
            self.agents[pair] = MemoryAgent(
                agent_id=agent_id,
                pair=pair,
                chroma_client=self.chroma
            )

        logging.info(f"[SWARM] Initialized {len(self.agents)} memory agents")

    def analyze_all_pairs(self, market_states: Dict[str, Dict]) -> Dict[str, Dict]:
        """
        Analyze all pairs with memory-driven intelligence

        Args:
            market_states: Dict mapping pair -> market state

        Returns:
            Dict mapping pair -> analysis
        """
        analyses = {}

        for pair, market_state in market_states.items():
            if pair in self.agents:
                analysis = self.agents[pair].analyze_current_situation(market_state)
                analyses[pair] = analysis

        return analyses

    def get_swarm_stats(self) -> Dict:
        """Get overall swarm learning statistics"""
        total_patterns = 0
        total_successful = 0
        total_failed = 0

        agent_stats = []

        for pair, agent in self.agents.items():
            stats = agent.get_learning_stats()
            agent_stats.append(stats)

            total_patterns += stats['patterns_stored']
            total_successful += stats['successful_patterns']
            total_failed += stats['failed_patterns']

        overall_success_rate = 0
        if total_patterns > 0:
            overall_success_rate = total_successful / total_patterns

        return {
            'total_agents': len(self.agents),
            'total_patterns': total_patterns,
            'total_successful': total_successful,
            'total_failed': total_failed,
            'overall_success_rate': overall_success_rate,
            'agent_stats': agent_stats,
            'memory_bank': self.chroma.get_collection_stats()
        }


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Create memory agent
    agent = MemoryAgent(
        agent_id="test_agent_001",
        pair="XXBTZUSD"
    )

    # Simulate current market state
    market_state = {
        'rsi': 65.0,
        'macd': 1.2,
        'volume': 5000000,
        'cross_moat_score': 2
    }

    # Analyze with memory
    analysis = agent.analyze_current_situation(market_state)

    print("\n" + "="*80)
    print("MEMORY-DRIVEN ANALYSIS")
    print("="*80)
    print(f"Confidence: {analysis['confidence']}")
    print(f"Recommendation: {analysis['recommendation']}")
    print(f"Reasoning: {analysis['reasoning']}")
    print(f"Similar patterns found: {analysis['similar_count']}")
    if analysis['similar_count'] > 0:
        print(f"Success rate: {analysis['success_rate']*100:.1f}%")
        print(f"Avg profit: {analysis['avg_profit']:.2f}%")
    print("="*80)

    # Get market story
    print("\nMARKET STORY:")
    print(agent.get_market_story())
    print("="*80)
