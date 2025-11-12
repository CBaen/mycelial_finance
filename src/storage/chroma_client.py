# src/storage/chroma_client.py - PHASE 4.4: ChromaDB Integration
"""
PHASE 4.4: ChromaDB Vector Database Client

Replaces Redis-based pattern storage with true vector similarity search.
Enables Federated Reinforcement Learning (FRL) through pattern clustering.

Features:
- Vector embeddings for trading patterns
- Similarity search for pattern matching
- Persistent storage across restarts
- Efficient clustering for FRL
- Pattern metadata and performance tracking
"""

import logging
import numpy as np
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import json


try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    logging.warning("[CHROMADB] ChromaDB not installed. Install with: pip install chromadb")


class ChromaDBClient:
    """
    PHASE 4.4: ChromaDB client for pattern storage and similarity search

    Manages trading pattern vectors for Federated Reinforcement Learning.

    Collections:
    - trading_patterns: Successful trading patterns with performance metrics
    - failed_patterns: Failed patterns for negative learning
    - agent_knowledge: Per-agent learned knowledge representations
    """

    def __init__(self, persist_directory: str = "./chroma_db", client_type: str = "persistent"):
        """
        Initialize ChromaDB client

        Args:
            persist_directory: Directory for persistent storage
            client_type: "persistent" or "memory" (default: persistent)
        """
        if not CHROMADB_AVAILABLE:
            raise ImportError("ChromaDB not installed. Install with: pip install chromadb")

        self.persist_directory = persist_directory

        # Initialize ChromaDB client (new API)
        if client_type == "persistent":
            self.client = chromadb.PersistentClient(path=persist_directory)
            logging.info(f"[CHROMADB] Persistent client initialized at {persist_directory}")
        else:
            self.client = chromadb.Client()
            logging.info("[CHROMADB] In-memory client initialized")

        # Create/get collections
        self.trading_patterns = self._get_or_create_collection(
            "trading_patterns",
            metadata={"description": "Successful trading patterns"}
        )

        self.failed_patterns = self._get_or_create_collection(
            "failed_patterns",
            metadata={"description": "Failed patterns for negative learning"}
        )

        self.agent_knowledge = self._get_or_create_collection(
            "agent_knowledge",
            metadata={"description": "Per-agent learned knowledge"}
        )

        logging.info("[CHROMADB] Collections initialized")

    def _get_or_create_collection(self, name: str, metadata: Dict = None):
        """Get existing collection or create new one"""
        try:
            collection = self.client.get_collection(name)
            logging.info(f"[CHROMADB] Collection '{name}' loaded ({collection.count()} items)")
        except Exception:
            collection = self.client.create_collection(name, metadata=metadata or {})
            logging.info(f"[CHROMADB] Collection '{name}' created")

        return collection

    def store_pattern(self, pattern_id: str, embedding: List[float],
                     metadata: Dict, success: bool = True):
        """
        Store a trading pattern with its vector embedding

        Args:
            pattern_id: Unique pattern identifier
            embedding: Vector representation of the pattern
            metadata: Pattern metadata (pair, timestamp, signals, performance, etc.)
            success: True for successful patterns, False for failed patterns
        """
        collection = self.trading_patterns if success else self.failed_patterns

        # Add timestamp if not present
        if 'timestamp' not in metadata:
            metadata['timestamp'] = datetime.now().isoformat()

        # Store pattern
        collection.add(
            ids=[pattern_id],
            embeddings=[embedding],
            metadatas=[metadata]
        )

        logging.debug(
            f"[CHROMADB] Pattern stored | ID: {pattern_id} | "
            f"Success: {success} | Pair: {metadata.get('pair', 'unknown')}"
        )

    def find_similar_patterns(self, query_embedding: List[float],
                             n_results: int = 10,
                             success_only: bool = True,
                             filter_metadata: Dict = None) -> List[Dict]:
        """
        Find similar patterns using vector similarity search

        Args:
            query_embedding: Query vector
            n_results: Number of similar patterns to return
            success_only: Only search successful patterns
            filter_metadata: Optional metadata filters (e.g., {'pair': 'XXBTZUSD'})

        Returns:
            List of similar patterns with distances and metadata
        """
        collection = self.trading_patterns if success_only else self.failed_patterns

        # Query collection
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=filter_metadata
        )

        # Format results
        similar_patterns = []
        if results['ids'] and len(results['ids'][0]) > 0:
            for i in range(len(results['ids'][0])):
                pattern = {
                    'id': results['ids'][0][i],
                    'distance': results['distances'][0][i],
                    'metadata': results['metadatas'][0][i]
                }
                similar_patterns.append(pattern)

        logging.debug(
            f"[CHROMADB] Similarity search | "
            f"Query: {len(query_embedding)}D | "
            f"Found: {len(similar_patterns)} patterns"
        )

        return similar_patterns

    def get_pattern_clusters(self, n_clusters: int = 5, success_only: bool = True) -> List[List[str]]:
        """
        Get pattern clusters for Federated Reinforcement Learning

        Args:
            n_clusters: Number of clusters to create
            success_only: Only cluster successful patterns

        Returns:
            List of clusters (each cluster is a list of pattern IDs)
        """
        collection = self.trading_patterns if success_only else self.failed_patterns

        # Get all patterns
        all_patterns = collection.get(include=['embeddings', 'metadatas'])

        if not all_patterns['ids']:
            logging.warning("[CHROMADB] No patterns available for clustering")
            return []

        embeddings = np.array(all_patterns['embeddings'])
        pattern_ids = all_patterns['ids']

        # Simple k-means clustering
        from sklearn.cluster import KMeans

        try:
            kmeans = KMeans(n_clusters=min(n_clusters, len(pattern_ids)), random_state=42)
            cluster_labels = kmeans.fit_predict(embeddings)

            # Group patterns by cluster
            clusters = [[] for _ in range(n_clusters)]
            for pattern_id, label in zip(pattern_ids, cluster_labels):
                clusters[label].append(pattern_id)

            logging.info(
                f"[CHROMADB] Clustering complete | "
                f"Patterns: {len(pattern_ids)} | "
                f"Clusters: {len([c for c in clusters if c])}"
            )

            return [c for c in clusters if c]  # Remove empty clusters

        except Exception as e:
            logging.error(f"[CHROMADB] Clustering failed: {e}")
            return [[p] for p in pattern_ids]  # Fallback: each pattern in own cluster

    def store_agent_knowledge(self, agent_id: str, knowledge_vector: List[float],
                             metadata: Dict):
        """
        Store agent's learned knowledge for FRL

        Args:
            agent_id: Unique agent identifier
            knowledge_vector: Vector representation of agent's knowledge
            metadata: Agent metadata (type, pair, performance, etc.)
        """
        metadata['agent_id'] = agent_id
        metadata['timestamp'] = datetime.now().isoformat()

        self.agent_knowledge.upsert(
            ids=[agent_id],
            embeddings=[knowledge_vector],
            metadatas=[metadata]
        )

        logging.debug(f"[CHROMADB] Agent knowledge stored | Agent: {agent_id}")

    def find_similar_agents(self, agent_id: str, n_results: int = 5) -> List[Dict]:
        """
        Find agents with similar knowledge for peer learning

        Args:
            agent_id: Query agent ID
            n_results: Number of similar agents to return

        Returns:
            List of similar agents
        """
        # Get query agent's knowledge vector
        agent = self.agent_knowledge.get(ids=[agent_id], include=['embeddings'])

        if not agent['embeddings']:
            logging.warning(f"[CHROMADB] Agent {agent_id} not found")
            return []

        query_embedding = agent['embeddings'][0]

        # Find similar agents
        results = self.agent_knowledge.query(
            query_embeddings=[query_embedding],
            n_results=n_results + 1  # +1 to exclude self
        )

        # Format and filter results
        similar_agents = []
        if results['ids'] and len(results['ids'][0]) > 0:
            for i in range(len(results['ids'][0])):
                if results['ids'][0][i] != agent_id:  # Exclude self
                    agent_info = {
                        'agent_id': results['ids'][0][i],
                        'distance': results['distances'][0][i],
                        'metadata': results['metadatas'][0][i]
                    }
                    similar_agents.append(agent_info)

        logging.debug(
            f"[CHROMADB] Agent similarity search | "
            f"Agent: {agent_id} | "
            f"Found: {len(similar_agents)} similar agents"
        )

        return similar_agents[:n_results]

    def get_top_performing_patterns(self, pair: str = None, n_results: int = 10) -> List[Dict]:
        """
        Get top performing patterns for a given pair

        Args:
            pair: Trading pair filter (optional)
            n_results: Number of patterns to return

        Returns:
            List of top patterns sorted by performance
        """
        filter_dict = {'pair': pair} if pair else None

        # Get all successful patterns
        patterns = self.trading_patterns.get(
            where=filter_dict,
            include=['embeddings', 'metadatas']
        )

        if not patterns['ids']:
            return []

        # Sort by performance (assume metadata contains 'pnl_pct')
        pattern_list = []
        for i in range(len(patterns['ids'])):
            pattern_list.append({
                'id': patterns['ids'][i],
                'embedding': patterns['embeddings'][i],
                'metadata': patterns['metadatas'][i],
                'pnl_pct': float(patterns['metadatas'][i].get('pnl_pct', 0))
            })

        # Sort by P&L
        pattern_list.sort(key=lambda x: x['pnl_pct'], reverse=True)

        logging.info(
            f"[CHROMADB] Top patterns retrieved | "
            f"Pair: {pair or 'all'} | "
            f"Count: {min(n_results, len(pattern_list))}"
        )

        return pattern_list[:n_results]

    def delete_old_patterns(self, days_old: int = 90):
        """
        Delete patterns older than specified days

        Args:
            days_old: Delete patterns older than this many days
        """
        from datetime import timedelta

        cutoff_date = datetime.now() - timedelta(days=days_old)
        cutoff_iso = cutoff_date.isoformat()

        for collection in [self.trading_patterns, self.failed_patterns]:
            # Get all patterns
            all_patterns = collection.get(include=['metadatas'])

            # Find old pattern IDs
            old_ids = [
                pattern_id for pattern_id, metadata in zip(all_patterns['ids'], all_patterns['metadatas'])
                if metadata.get('timestamp', '') < cutoff_iso
            ]

            if old_ids:
                collection.delete(ids=old_ids)
                logging.info(f"[CHROMADB] Deleted {len(old_ids)} old patterns from {collection.name}")

    def get_collection_stats(self) -> Dict[str, int]:
        """Get statistics about stored patterns"""
        return {
            'trading_patterns': self.trading_patterns.count(),
            'failed_patterns': self.failed_patterns.count(),
            'agent_knowledge': self.agent_knowledge.count(),
            'total': (
                self.trading_patterns.count() +
                self.failed_patterns.count() +
                self.agent_knowledge.count()
            )
        }

    def persist(self):
        """Persist all collections to disk"""
        if hasattr(self.client, 'persist'):
            self.client.persist()
            logging.info("[CHROMADB] Collections persisted to disk")


# =============================================================================
# PATTERN EMBEDDING UTILITIES
# =============================================================================

def create_pattern_embedding(pattern_data: Dict) -> List[float]:
    """
    Create vector embedding from trading pattern data

    Args:
        pattern_data: Dictionary containing pattern features
            {
                'rsi': 45.2,
                'macd': 0.5,
                'volume': 1000000,
                'price_change_pct': 2.5,
                'cross_moat_score': 2,
                ...
            }

    Returns:
        Vector embedding (list of floats)
    """
    # Extract numerical features
    features = []

    # Technical indicators
    features.append(pattern_data.get('rsi', 50.0) / 100.0)  # Normalize 0-1
    features.append((pattern_data.get('macd', 0.0) + 10) / 20.0)  # Normalize roughly -10 to 10
    features.append(np.log1p(pattern_data.get('volume', 0.0)) / 20.0)  # Log normalize volume

    # Price movements
    features.append((pattern_data.get('price_change_pct', 0.0) + 10) / 20.0)  # Normalize -10% to +10%

    # Cross-moat signals
    features.append(pattern_data.get('cross_moat_score', 0) / 2.0)  # 0-2 scale

    # Time features (hour of day, day of week)
    timestamp = pattern_data.get('timestamp', datetime.now())
    if isinstance(timestamp, str):
        timestamp = datetime.fromisoformat(timestamp)

    features.append(timestamp.hour / 24.0)
    features.append(timestamp.weekday() / 7.0)

    # Performance features (if available)
    features.append((pattern_data.get('pnl_pct', 0.0) + 20) / 40.0)  # Normalize -20% to +20%

    return features


# =============================================================================
# MAIN - Example Usage
# =============================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Initialize client
    client = ChromaDBClient(persist_directory="./test_chroma_db", client_type="memory")

    # Example: Store a pattern
    pattern_data = {
        'rsi': 65.0,
        'macd': 1.2,
        'volume': 5000000,
        'price_change_pct': 3.5,
        'cross_moat_score': 2,
        'pnl_pct': 2.8,
        'pair': 'XXBTZUSD',
        'direction': 'BUY'
    }

    embedding = create_pattern_embedding(pattern_data)

    client.store_pattern(
        pattern_id="pattern_001",
        embedding=embedding,
        metadata=pattern_data,
        success=True
    )

    # Example: Find similar patterns
    similar = client.find_similar_patterns(
        query_embedding=embedding,
        n_results=5,
        filter_metadata={'pair': 'XXBTZUSD'}
    )

    print(f"\nFound {len(similar)} similar patterns")

    # Example: Get statistics
    stats = client.get_collection_stats()
    print(f"\nCollection stats: {stats}")
