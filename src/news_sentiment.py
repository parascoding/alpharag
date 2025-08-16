import feedparser
import requests
import json
from pathlib import Path
from bs4 import BeautifulSoup
from textblob import TextBlob
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
import time
import re
import random

logger = logging.getLogger(__name__)

class NewsSentimentAnalyzer:
    def __init__(self, rss_feeds: List[str]):
        self.rss_feeds = rss_feeds
        self.cache = {}
        self.cache_timeout = 1800  # 30 minutes
        self.use_mock_data = False  # Default to real data

    def _load_mock_news_data(self) -> Dict:
        """
        Load mock news sentiment data from JSON file
        """
        try:
            mock_data_path = Path(__file__).parent.parent / 'mock_data' / 'news_sentiment.json'

            if not mock_data_path.exists():
                logger.warning(f"Mock news data file not found: {mock_data_path}")
                return self._get_fallback_news_data()

            with open(mock_data_path, 'r') as f:
                data = json.load(f)

            logger.error(f"Using MOCK news data from {mock_data_path} - RSS feeds not available")
            return data

        except Exception as e:
            logger.error(f"Error loading mock news data: {e}")
            return self._get_fallback_news_data()

    def _get_fallback_news_data(self) -> Dict:
        """
        Fallback news data if JSON file is not available
        """
        return {
            'news_articles': {
                'RELIANCE.NS': [{
                    'title': 'Reliance Industries reports strong Q3 results',
                    'summary': 'Company shows growth in petrochemicals and retail segments',
                    'sentiment_score': 0.25,
                    'sentiment_label': 'positive'
                }],
                'TCS.NS': [{
                    'title': 'TCS wins major digital transformation contract',
                    'summary': 'New deal expected to boost revenue growth significantly',
                    'sentiment_score': 0.35,
                    'sentiment_label': 'positive'
                }],
                'INFY.NS': [{
                    'title': 'Infosys raises FY24 revenue guidance',
                    'summary': 'Strong performance across all business segments',
                    'sentiment_score': 0.40,
                    'sentiment_label': 'positive'
                }]
            },
            'sentiment_summary': {
                'overall_sentiment': {'score': 0.156, 'label': 'positive'},
                'individual_stocks': {
                    'RELIANCE.NS': {'sentiment_score': 0.25, 'sentiment_label': 'positive', 'article_count': 1},
                    'TCS.NS': {'sentiment_score': 0.35, 'sentiment_label': 'positive', 'article_count': 1},
                    'INFY.NS': {'sentiment_score': 0.40, 'sentiment_label': 'positive', 'article_count': 1}
                }
            }
        }

    def collect_news(self, symbols: List[str], hours_back: int = 24) -> Dict[str, List[Dict]]:
        if self.use_mock_data:
            return self._collect_mock_news(symbols)

        # Real RSS feed collection (existing code)
        news_by_symbol = {symbol: [] for symbol in symbols}

        # Get company names for better news filtering
        company_keywords = self._get_company_keywords(symbols)

        for feed_url in self.rss_feeds:
            try:
                articles = self._fetch_rss_feed(feed_url, hours_back)

                for article in articles:
                    # Check which symbols this article is relevant to
                    relevant_symbols = self._find_relevant_symbols(article, symbols, company_keywords)

                    for symbol in relevant_symbols:
                        news_by_symbol[symbol].append(article)

                time.sleep(1)  # Rate limiting

            except Exception as e:
                logger.error(f"Error fetching from RSS feed {feed_url}: {e}")

        return news_by_symbol

    def _collect_mock_news(self, symbols: List[str]) -> Dict[str, List[Dict]]:
        """
        Collect mock news from JSON data
        """
        mock_data = self._load_mock_news_data()
        news_articles = mock_data.get('news_articles', {})

        news_by_symbol = {symbol: [] for symbol in symbols}

        # Add general market articles to all symbols
        general_articles = news_articles.get('general_market', [])
        for symbol in symbols:
            news_by_symbol[symbol].extend(general_articles)

        # Add symbol-specific articles
        for symbol in symbols:
            if symbol in news_articles:
                symbol_articles = news_articles[symbol]
                news_by_symbol[symbol].extend(symbol_articles)

        logger.error(f"Using MOCK news for {len(symbols)} symbols - RSS feeds failed")
        return news_by_symbol

    def get_news_summary(self, symbols: List[str], hours_back: int = 24) -> Dict:
        if self.use_mock_data:
            return self._get_mock_news_summary(symbols)

        # Real news analysis - fallback to existing RSS analysis
        return self._analyze_real_news(symbols, hours_back)

    def _get_mock_news_summary(self, symbols: List[str]) -> Dict:
        """
        Get mock news summary from JSON data with slight randomization
        """
        mock_data = self._load_mock_news_data()
        summary_data = mock_data.get('sentiment_summary', {})

        # Base summary structure
        summary = {
            'overall_sentiment': summary_data.get('overall_sentiment', {'score': 0.0, 'label': 'neutral'}),
            'individual_sentiment': {},
            'total_articles': 0,
            'articles_by_symbol': {},
            'timestamp': datetime.now().isoformat()
        }

        individual_stocks = summary_data.get('individual_stocks', {})
        total_articles = 0

        for symbol in symbols:
            if symbol in individual_stocks:
                stock_data = individual_stocks[symbol].copy()

                # Add slight randomization to scores (±10%)
                base_score = stock_data.get('sentiment_score', 0)
                variation = base_score * random.uniform(-0.1, 0.1)
                new_score = base_score + variation

                stock_data['sentiment_score'] = new_score
                stock_data['sentiment_label'] = self._score_to_label(new_score)

                # Add some mock articles
                news_articles = mock_data.get('news_articles', {})
                articles = []
                if symbol in news_articles:
                    articles = news_articles[symbol][:3]  # Top 3 articles

                stock_data['articles'] = articles
                summary['individual_sentiment'][symbol] = stock_data

                article_count = stock_data.get('article_count', 1)
                total_articles += article_count
                summary['articles_by_symbol'][symbol] = article_count
            else:
                # Fallback for symbols not in mock data
                summary['individual_sentiment'][symbol] = {
                    'sentiment_score': 0.0,
                    'sentiment_label': 'neutral',
                    'article_count': 0,
                    'positive_count': 0,
                    'negative_count': 0,
                    'articles': []
                }

        summary['total_articles'] = total_articles

        logger.error(
            f"Using MOCK analysis: {total_articles} articles. Overall sentiment: "
            f"{summary['overall_sentiment']['label']} "
            f"({summary['overall_sentiment']['score']:.3f}) - RSS feeds not working"
        )

        return summary

    def _analyze_real_news(self, symbols: List[str], hours_back: int = 24) -> Dict:
        """
        Analyze real news when not using mock data
        """
        news_data = self.collect_news(symbols, hours_back)

        summary = {
            'overall_sentiment': {'score': 0.0, 'label': 'neutral'},
            'individual_sentiment': {},
            'total_articles': 0,
            'articles_by_symbol': {},
            'timestamp': datetime.now().isoformat()
        }

        all_scores = []
        total_articles = 0

        for symbol, articles in news_data.items():
            if not articles:
                summary['individual_sentiment'][symbol] = {
                    'sentiment_score': 0.0,
                    'sentiment_label': 'neutral',
                    'article_count': 0,
                    'positive_count': 0,
                    'negative_count': 0,
                    'articles': []
                }
                continue

            symbol_scores = []
            processed_articles = []

            for article in articles:
                # Analyze sentiment
                sentiment_result = self._analyze_sentiment(article)
                article.update(sentiment_result)

                symbol_scores.append(sentiment_result['sentiment_score'])
                processed_articles.append(article)
                total_articles += 1

            # Calculate symbol-level sentiment
            avg_score = sum(symbol_scores) / len(symbol_scores) if symbol_scores else 0
            sentiment_label = self._score_to_label(avg_score)

            positive_count = sum(1 for score in symbol_scores if score > 0.1)
            negative_count = sum(1 for score in symbol_scores if score < -0.1)

            summary['individual_sentiment'][symbol] = {
                'sentiment_score': avg_score,
                'sentiment_label': sentiment_label,
                'article_count': len(articles),
                'positive_count': positive_count,
                'negative_count': negative_count,
                'articles': processed_articles[:5]  # Top 5 articles
            }

            all_scores.extend(symbol_scores)
            summary['articles_by_symbol'][symbol] = len(articles)

        # Calculate overall sentiment
        if all_scores:
            overall_score = sum(all_scores) / len(all_scores)
            summary['overall_sentiment'] = {
                'score': overall_score,
                'label': self._score_to_label(overall_score)
            }

        summary['total_articles'] = total_articles
        return summary

    def _get_company_keywords(self, symbols: List[str]) -> Dict[str, List[str]]:
        # Map NSE symbols to company names and keywords
        keyword_map = {
            'RELIANCE.NS': [
                'reliance', 'ril', 'reliance industries', 'mukesh ambani', 'ambani',
                'jamnagar', 'petrochemicals', 'refinery', 'retail', 'jio'
            ],
            'TCS.NS': [
                'tcs', 'tata consultancy', 'tata consultancy services', 'tata group',
                'it services', 'consulting', 'technology services', 'tata sons', 'tata'
            ],
            'INFY.NS': [
                'infosys', 'infy', 'it services', 'technology', 'consulting',
                'software services', 'bangalore', 'narayana murthy', 'nandan nilekani'
            ],
        }

        return {symbol: keyword_map.get(symbol, [symbol.replace('.NS', '').lower()])
                for symbol in symbols}

    def _fetch_rss_feed(self, feed_url: str, hours_back: int) -> List[Dict]:
        articles = []

        try:
            # Check cache first
            cache_key = f"rss_{feed_url}"
            if self._is_cached(cache_key):
                return self.cache[cache_key]['data']

            feed = feedparser.parse(feed_url)
            cutoff_time = datetime.now() - timedelta(hours=hours_back)

            for entry in feed.entries:
                try:
                    # Parse publication date
                    pub_date = None
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        pub_date = datetime(*entry.published_parsed[:6])
                    elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                        pub_date = datetime(*entry.updated_parsed[:6])

                    # Skip articles older than cutoff
                    if pub_date and pub_date < cutoff_time:
                        continue

                    article = {
                        'title': entry.title,
                        'link': entry.link,
                        'published': pub_date.isoformat() if pub_date else None,
                        'summary': getattr(entry, 'summary', ''),
                        'source': feed_url
                    }

                    articles.append(article)

                except Exception as e:
                    logger.error(f"Error processing RSS entry: {e}")
                    continue

            # Cache the results
            self.cache[cache_key] = {
                'data': articles,
                'timestamp': datetime.now()
            }

            logger.info(f"Fetched {len(articles)} articles from {feed_url}")

        except Exception as e:
            logger.error(f"Error fetching RSS feed {feed_url}: {e}")

        return articles

    def _find_relevant_symbols(self, article: Dict, symbols: List[str],
                              company_keywords: Dict[str, List[str]]) -> List[str]:
        relevant_symbols = []

        # Combine title and summary for keyword search
        text = f"{article.get('title', '')} {article.get('summary', '')}".lower()

        for symbol, keywords in company_keywords.items():
            for keyword in keywords:
                if keyword.lower() in text:
                    relevant_symbols.append(symbol)
                    break

        return relevant_symbols

    def _analyze_sentiment(self, article: Dict) -> Dict:
        # Combine title and summary for sentiment analysis
        text = f"{article.get('title', '')} {article.get('summary', '')}"

        if not text.strip():
            return {
                'sentiment_score': 0.0,
                'sentiment_label': 'neutral'
            }

        try:
            blob = TextBlob(text)
            sentiment_score = blob.sentiment.polarity

            # Convert to label
            sentiment_label = self._score_to_label(sentiment_score)

            return {
                'sentiment_score': sentiment_score,
                'sentiment_label': sentiment_label
            }

        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return {
                'sentiment_score': 0.0,
                'sentiment_label': 'neutral'
            }

    def _score_to_label(self, score: float) -> str:
        if score > 0.1:
            return 'positive'
        elif score < -0.1:
            return 'negative'
        else:
            return 'neutral'

    def _is_cached(self, key: str) -> bool:
        if key in self.cache:
            cached_time = self.cache[key]['timestamp']
            if (datetime.now() - cached_time).seconds < self.cache_timeout:
                return True
        return False