# src/connectors/market_data_aggregator.py - Multi-Source Market Data Aggregator
"""
Aggregates market data from multiple sources:
- CoinMarketCap: Market cap, rankings, social sentiment
- Twelve Data: Traditional market correlations, forex
- Free Crypto API: Additional price feeds, backup data source

Provides unified interface for enriched market intelligence.
"""

import logging
import requests
import time
from typing import Dict, Optional, List
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()


class CoinMarketCapClient:
    """
    CoinMarketCap API Client

    Free tier: 333 calls/day, 10K calls/month
    Provides: Market cap, rankings, volume, social sentiment
    """

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('CMC_API_KEY')
        self.base_url = 'https://pro-api.coinmarketcap.com/v1'
        self.headers = {
            'X-CMC_PRO_API_KEY': self.api_key,
            'Accept': 'application/json'
        }

        if not self.api_key:
            logging.warning("[CMC] No API key found. Set CMC_API_KEY in .env")
        else:
            logging.info("[CMC] CoinMarketCap client initialized")

    def get_market_overview(self, limit: int = 100) -> Optional[Dict]:
        """Get top cryptocurrencies by market cap"""
        try:
            response = requests.get(
                f'{self.base_url}/cryptocurrency/listings/latest',
                headers=self.headers,
                params={'limit': limit, 'convert': 'USD'}
            )

            if response.status_code == 200:
                data = response.json()

                # Simplify the data
                coins = []
                for coin in data['data']:
                    coins.append({
                        'symbol': coin['symbol'],
                        'name': coin['name'],
                        'rank': coin['cmc_rank'],
                        'price': coin['quote']['USD']['price'],
                        'market_cap': coin['quote']['USD']['market_cap'],
                        'volume_24h': coin['quote']['USD']['volume_24h'],
                        'percent_change_24h': coin['quote']['USD']['percent_change_24h'],
                        'percent_change_7d': coin['quote']['USD']['percent_change_7d']
                    })

                logging.info(f"[CMC] Retrieved {len(coins)} coins")
                return {'coins': coins, 'timestamp': datetime.now().isoformat()}

            else:
                logging.error(f"[CMC] API error: {response.status_code}")
                return None

        except Exception as e:
            logging.error(f"[CMC] Error: {e}")
            return None

    def get_coin_metadata(self, symbol: str) -> Optional[Dict]:
        """Get detailed metadata for a specific coin"""
        try:
            response = requests.get(
                f'{self.base_url}/cryptocurrency/info',
                headers=self.headers,
                params={'symbol': symbol}
            )

            if response.status_code == 200:
                data = response.json()
                if symbol in data['data']:
                    coin_data = data['data'][symbol]
                    return {
                        'name': coin_data['name'],
                        'symbol': coin_data['symbol'],
                        'category': coin_data.get('category', 'Unknown'),
                        'description': coin_data.get('description', ''),
                        'website': coin_data.get('urls', {}).get('website', []),
                        'twitter': coin_data.get('urls', {}).get('twitter', []),
                        'reddit': coin_data.get('urls', {}).get('reddit', [])
                    }

            return None

        except Exception as e:
            logging.error(f"[CMC] Metadata error: {e}")
            return None


class TwelveDataClient:
    """
    Twelve Data API Client

    Free tier: 8 calls/minute, 800 calls/day
    Provides: Stocks, Forex, Crypto, Technical indicators
    """

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('TWELVE_DATA_API_KEY')
        self.base_url = 'https://api.twelvedata.com'

        if not self.api_key:
            logging.warning("[TWELVE] No API key found. Set TWELVE_DATA_API_KEY in .env")
        else:
            logging.info("[TWELVE] Twelve Data client initialized")

    def get_crypto_price(self, symbol: str, interval: str = '1h') -> Optional[Dict]:
        """Get crypto price time series"""
        try:
            params = {
                'symbol': f'{symbol}/USD',
                'interval': interval,
                'apikey': self.api_key,
                'outputsize': 100
            }

            response = requests.get(f'{self.base_url}/time_series', params=params)

            if response.status_code == 200:
                data = response.json()

                if 'values' in data:
                    return {
                        'symbol': symbol,
                        'interval': interval,
                        'data': data['values'][:10],  # Last 10 periods
                        'timestamp': datetime.now().isoformat()
                    }

            return None

        except Exception as e:
            logging.error(f"[TWELVE] Price error: {e}")
            return None

    def get_forex_rate(self, pair: str = 'EUR/USD') -> Optional[Dict]:
        """Get forex rates for correlation analysis"""
        try:
            params = {
                'symbol': pair,
                'apikey': self.api_key
            }

            response = requests.get(f'{self.base_url}/quote', params=params)

            if response.status_code == 200:
                data = response.json()
                return {
                    'pair': pair,
                    'price': float(data.get('close', 0)),
                    'change_percent': float(data.get('percent_change', 0)),
                    'timestamp': data.get('timestamp', '')
                }

            return None

        except Exception as e:
            logging.error(f"[TWELVE] Forex error: {e}")
            return None


class FreeCryptoAPIClient:
    """
    Free Crypto API Client

    No API key required
    Provides: Basic price data, backup source
    """

    def __init__(self):
        self.base_url = 'https://api.coincap.io/v2'
        logging.info("[FREECRYPTO] Free Crypto API client initialized")

    def get_asset_price(self, symbol: str) -> Optional[Dict]:
        """Get current asset price"""
        try:
            # CoinCap uses full names, not symbols - try common mappings
            symbol_map = {
                'BTC': 'bitcoin',
                'ETH': 'ethereum',
                'LTC': 'litecoin',
                'XRP': 'ripple'
            }

            asset_id = symbol_map.get(symbol.upper(), symbol.lower())

            response = requests.get(f'{self.base_url}/assets/{asset_id}')

            if response.status_code == 200:
                data = response.json()['data']
                return {
                    'symbol': symbol,
                    'price': float(data['priceUsd']),
                    'market_cap': float(data['marketCapUsd']),
                    'volume_24h': float(data['volumeUsd24Hr']),
                    'change_24h': float(data['changePercent24Hr']),
                    'supply': float(data['supply']),
                    'timestamp': datetime.now().isoformat()
                }

            return None

        except Exception as e:
            logging.error(f"[FREECRYPTO] Error: {e}")
            return None

    def get_market_sentiment(self) -> Optional[Dict]:
        """Get overall market sentiment from top 10 coins"""
        try:
            response = requests.get(f'{self.base_url}/assets', params={'limit': 10})

            if response.status_code == 200:
                data = response.json()['data']

                # Calculate sentiment
                positive = sum(1 for coin in data if float(coin['changePercent24Hr']) > 0)
                negative = len(data) - positive

                avg_change = sum(float(coin['changePercent24Hr']) for coin in data) / len(data)

                return {
                    'positive_coins': positive,
                    'negative_coins': negative,
                    'avg_change_24h': avg_change,
                    'sentiment': 'BULLISH' if avg_change > 1 else ('BEARISH' if avg_change < -1 else 'NEUTRAL'),
                    'timestamp': datetime.now().isoformat()
                }

            return None

        except Exception as e:
            logging.error(f"[FREECRYPTO] Sentiment error: {e}")
            return None


class MarketDataAggregator:
    """
    Unified market data aggregator combining all sources

    Provides enriched market intelligence for decision making
    """

    def __init__(self):
        self.cmc = CoinMarketCapClient()
        self.twelve = TwelveDataClient()
        self.freecrypto = FreeCryptoAPIClient()

        logging.info("[AGGREGATOR] Market data aggregator initialized")

    def get_enriched_market_data(self, symbol: str) -> Dict:
        """
        Get comprehensive market data from all sources

        Returns unified view with:
        - Price and volume
        - Market cap and ranking
        - Sentiment indicators
        - Traditional market correlations
        """
        enriched_data = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'sources': {}
        }

        # CoinMarketCap data (if available)
        if self.cmc.api_key:
            cmc_meta = self.cmc.get_coin_metadata(symbol)
            if cmc_meta:
                enriched_data['sources']['coinmarketcap'] = cmc_meta
                enriched_data['name'] = cmc_meta['name']
                enriched_data['category'] = cmc_meta['category']

        # Twelve Data (if available)
        if self.twelve.api_key:
            twelve_price = self.twelve.get_crypto_price(symbol)
            if twelve_price:
                enriched_data['sources']['twelvedata'] = twelve_price

        # Free Crypto API (always available)
        free_data = self.freecrypto.get_asset_price(symbol)
        if free_data:
            enriched_data['sources']['freecrypto'] = free_data
            enriched_data['price'] = free_data['price']
            enriched_data['market_cap'] = free_data['market_cap']
            enriched_data['volume_24h'] = free_data['volume_24h']
            enriched_data['change_24h'] = free_data['change_24h']

        # Market sentiment
        sentiment = self.freecrypto.get_market_sentiment()
        if sentiment:
            enriched_data['market_sentiment'] = sentiment

        # Forex correlations (if available)
        if self.twelve.api_key:
            eurusd = self.twelve.get_forex_rate('EUR/USD')
            if eurusd:
                enriched_data['forex_correlations'] = {'EURUSD': eurusd}

        return enriched_data

    def get_market_story(self) -> Dict:
        """
        Generate a narrative summary of current market conditions

        Returns human-readable market story
        """
        sentiment = self.freecrypto.get_market_sentiment()

        if not sentiment:
            return {'story': 'Unable to read market conditions right now.'}

        # Build narrative
        sentiment_text = sentiment['sentiment']
        avg_change = sentiment['avg_change_24h']
        positive = sentiment['positive_coins']
        negative = sentiment['negative_coins']

        if sentiment_text == 'BULLISH':
            mood = "looking bright"
            action = "coins are climbing"
        elif sentiment_text == 'BEARISH':
            mood = "looking rough"
            action = "coins are dropping"
        else:
            mood = "pretty calm"
            action = "markets are sideways"

        story = f"""
Hey! Here's what's happening in crypto right now:

The market is {mood}. Out of the top 10 coins, {positive} are up and {negative} are down in the last 24 hours.

Overall, prices have moved {avg_change:.2f}% on average.

Right now the vibe is: **{sentiment_text}** 📊

{self._get_advice(sentiment_text, avg_change)}
"""

        return {
            'story': story.strip(),
            'sentiment': sentiment_text,
            'avg_change': avg_change,
            'timestamp': datetime.now().isoformat()
        }

    def _get_advice(self, sentiment: str, change: float) -> str:
        """Generate friendly advice based on market conditions"""
        if sentiment == 'BULLISH' and change > 3:
            return "🚀 Things are moving fast! Our agents are watching for opportunities."
        elif sentiment == 'BULLISH':
            return "📈 Steady upward movement. The bots are analyzing patterns."
        elif sentiment == 'BEARISH' and change < -3:
            return "⚠️ Big drops happening. Our risk management is active."
        elif sentiment == 'BEARISH':
            return "📉 Prices cooling off. Looking for bounce opportunities."
        else:
            return "😌 Quiet market. Good time for research and learning."


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    aggregator = MarketDataAggregator()

    # Get market story
    story = aggregator.get_market_story()
    print(story['story'])

    # Get enriched data for BTC
    btc_data = aggregator.get_enriched_market_data('BTC')
    print(f"\nBTC Price: ${btc_data.get('price', 'N/A')}")
