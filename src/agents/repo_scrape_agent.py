# src/agents/repo_scrape_agent.py - PHASE 3.2: Real GitHub API Integration
import logging
from .base_agent import MycelialAgent
import time
import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta

try:
    from github import Github, GithubException, RateLimitExceededException
    GITHUB_AVAILABLE = True
except ImportError:
    GITHUB_AVAILABLE = False
    logging.warning("[REPO_SCRAPE] PyGithub not installed. Install with: pip install PyGithub")

class RepoScrapeAgent(MycelialAgent):
    """
    PHASE 3.2: The Data Engineer for the Code Innovation Swarm

    Implements Q7: Real GitHub API integration to prove cross-moat concept.
    Tracks repository activity for smart contract platforms and calculates:
    - Commit frequency (development velocity)
    - Dependency entropy (ecosystem complexity)
    - Contributor activity (network effects)

    Cross-moat hypothesis: GitHub commits predict DeFi volatility 6hrs BEFORE price moves.
    """

    # Crypto projects to track by language/ecosystem
    CRYPTO_REPOS = {
        "Solidity": [
            "ethereum/go-ethereum",      # Ethereum core
            "Uniswap/v3-core",           # DeFi protocol
            "aave/aave-v3-core",         # Lending protocol
            "compound-finance/compound-protocol",
        ],
        "Rust": [
            "solana-labs/solana",        # Solana blockchain
            "paritytech/substrate",      # Polkadot framework
            "near/nearcore",             # NEAR protocol
        ],
        "Go": [
            "cosmos/cosmos-sdk",         # Cosmos ecosystem
            "tendermint/tendermint",     # Consensus engine
        ],
        "Python": [
            "ethereum/py-evm",           # Ethereum Python client
            "vyperlang/vyper",           # Smart contract language
        ]
    }

    def __init__(self, model, target_language: str = "Python", use_real_api: bool = True):
        super().__init__(model)
        self.target = target_language
        self.channel = f"code-data:{self.target}"
        self.name = f"RepoScraper_{self.unique_id}"
        self.use_real_api = use_real_api and GITHUB_AVAILABLE

        # GitHub API client
        self.github_client = None
        if self.use_real_api:
            github_token = os.getenv('GITHUB_TOKEN')
            if github_token:
                try:
                    self.github_client = Github(github_token)
                    # Test connection
                    rate_limit = self.github_client.get_rate_limit()
                    logging.info(
                        f"[{self.name}] GitHub API connected | "
                        f"Rate limit: {rate_limit.core.remaining}/{rate_limit.core.limit}"
                    )
                except Exception as e:
                    logging.error(f"[{self.name}] GitHub API initialization failed: {e}")
                    self.github_client = None
            else:
                logging.warning(
                    f"[{self.name}] GITHUB_TOKEN not found in .env | "
                    f"Falling back to simulated data"
                )

        # Get repos to track for this language
        self.tracked_repos = self.CRYPTO_REPOS.get(self.target, [])

        # Cache for avoiding excessive API calls
        self.last_fetch_time = 0
        self.fetch_interval = 300  # 5 minutes between fetches
        self.cached_data = {}

        logging.info(
            f"[{self.name}] Initialized | Language: {self.target} | "
            f"Tracking {len(self.tracked_repos)} repos | "
            f"Real API: {self.github_client is not None}"
        )

    def step(self):
        """
        PHASE 3.2: Fetches real GitHub activity data or falls back to simulation
        """
        try:
            current_time = time.time()

            # Rate limiting: only fetch every 5 minutes
            if current_time - self.last_fetch_time < self.fetch_interval:
                if self.cached_data:
                    self._publish_cached_data()
                return

            # Fetch real data if API available
            if self.github_client and self.tracked_repos:
                data = self._fetch_real_github_data()
            else:
                # Fallback to simulation
                data = self._generate_simulated_data()

            # Cache and publish
            if data:
                self.cached_data = data
                self.last_fetch_time = current_time
                self._publish_data(data)

        except RateLimitExceededException:
            logging.warning(f"[{self.name}] GitHub API rate limit exceeded. Using cached data.")
            if self.cached_data:
                self._publish_cached_data()
        except Exception as e:
            logging.error(f"[{self.name}] Error in step: {e}")
            # Fallback to simulation on error
            data = self._generate_simulated_data()
            self._publish_data(data)

    def _fetch_real_github_data(self) -> Optional[Dict]:
        """
        PHASE 3.2: Fetch real GitHub metrics using PyGithub
        """
        try:
            aggregate_metrics = {
                "total_commits_24h": 0,
                "total_contributors": 0,
                "total_open_issues": 0,
                "repos_analyzed": 0,
                "dependency_entropy": 0.0,
                "novelty_score": 0.0
            }

            # Sample one repo per call to avoid rate limits
            repo_name = self.tracked_repos[int(time.time()) % len(self.tracked_repos)]

            try:
                repo = self.github_client.get_repo(repo_name)

                # Commit frequency (last 24 hours)
                since = datetime.now() - timedelta(hours=24)
                commits_24h = repo.get_commits(since=since).totalCount

                # Contributor count
                contributors = repo.get_contributors().totalCount

                # Open issues (proxy for activity)
                open_issues = repo.open_issues_count

                # Calculate dependency entropy (normalized complexity metric)
                # Based on: contributors * log(commits) / sqrt(issues)
                import math
                if commits_24h > 0 and open_issues > 0:
                    dependency_entropy = (
                        contributors * math.log(commits_24h + 1) / math.sqrt(open_issues)
                    )
                else:
                    dependency_entropy = contributors * 0.5

                # Novelty score: commits per contributor (development velocity)
                novelty_score = (commits_24h / max(contributors, 1)) * 10
                novelty_score = min(max(novelty_score, 0.5), 9.5)  # Clamp to 0.5-9.5

                aggregate_metrics.update({
                    "total_commits_24h": commits_24h,
                    "total_contributors": contributors,
                    "total_open_issues": open_issues,
                    "repos_analyzed": 1,
                    "dependency_entropy": round(dependency_entropy, 2),
                    "novelty_score": round(novelty_score, 2),
                    "primary_repo": repo_name,
                    "primary_repo_url": repo.html_url
                })

                logging.info(
                    f"[{self.name}] Fetched {repo_name} | "
                    f"Commits(24h): {commits_24h} | "
                    f"Contributors: {contributors} | "
                    f"Novelty: {novelty_score:.2f} | "
                    f"Entropy: {dependency_entropy:.2f}"
                )

            except GithubException as e:
                logging.warning(f"[{self.name}] Error fetching {repo_name}: {e}")
                return None

            return aggregate_metrics

        except Exception as e:
            logging.error(f"[{self.name}] Error in _fetch_real_github_data: {e}")
            return None

    def _generate_simulated_data(self) -> Dict:
        """
        Fallback: Generate simulated data (original behavior)
        """
        import random

        novelty_score = random.uniform(0.5, 9.5)
        dependency_entropy = random.randint(1, 100)

        return {
            "total_commits_24h": random.randint(5, 150),
            "total_contributors": random.randint(10, 500),
            "total_open_issues": random.randint(20, 300),
            "repos_analyzed": len(self.tracked_repos),
            "dependency_entropy": dependency_entropy,
            "novelty_score": novelty_score,
            "primary_repo": "simulated/repo",
            "primary_repo_url": f"https://github.com/simulated/repo_{self.unique_id}"
        }

    def _publish_data(self, metrics: Dict):
        """
        PHASE 3.2: Publish enriched GitHub data to Redis channel
        """
        enriched_data = {
            "close": metrics["novelty_score"],  # For chart plotting compatibility
            "NoveltyScore": metrics["novelty_score"],
            "DependencyEntropy": metrics["dependency_entropy"],
            "Language": self.target,
            "Commits24h": metrics["total_commits_24h"],
            "Contributors": metrics["total_contributors"],
            "OpenIssues": metrics["total_open_issues"],
            "ReposAnalyzed": metrics["repos_analyzed"],
            "RepoUrl": metrics.get("primary_repo_url", "N/A")
        }

        message = {
            "source": self.name,
            "timestamp": time.time(),
            "features": enriched_data
        }

        self.publish(self.channel, message)

    def _publish_cached_data(self):
        """
        Republish cached data to maintain signal continuity
        """
        if self.cached_data:
            self._publish_data(self.cached_data)
