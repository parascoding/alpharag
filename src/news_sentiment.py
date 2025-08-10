import feedparser
import requests
from bs4 import BeautifulSoup
from textblob import TextBlob
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
import time
import re

logger = logging.getLogger(__name__)

class NewsSentimentAnalyzer:
    def __init__(self, rss_feeds: List[str]):
        self.rss_feeds = rss_feeds
        self.cache = {}
        self.cache_timeout = 1800  # 30 minutes
    
    def collect_news(self, symbols: List[str], hours_back: int = 24) -> Dict[str, List[Dict]]:
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
    
    def _get_company_keywords(self, symbols: List[str]) -> Dict[str, List[str]]:
        # Map NSE symbols to company names and keywords
        keyword_map = {
            'RELIANCE.NS': ['reliance', 'ril', 'reliance industries', 'mukesh ambani'],
            'TCS.NS': ['tcs', 'tata consultancy', 'tata consultancy services'],
            'INFY.NS': ['infosys', 'infy', 'wipro', 'it services'],
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
                    
                    # Skip old articles
                    if pub_date and pub_date < cutoff_time:
                        continue
                    
                    article = {
                        'title': entry.get('title', ''),
                        'summary': entry.get('summary', ''),
                        'link': entry.get('link', ''),
                        'published': pub_date.isoformat() if pub_date else datetime.now().isoformat(),
                        'source': feed.feed.get('title', 'Unknown')
                    }
                    
                    articles.append(article)
                    
                except Exception as e:
                    logger.warning(f"Error parsing RSS entry: {e}")
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
    
    def _find_relevant_symbols(self, article: Dict, symbols: List[str], keywords: Dict[str, List[str]]) -> List[str]:
        relevant = []
        text = (article['title'] + ' ' + article['summary']).lower()
        
        for symbol in symbols:
            symbol_keywords = keywords.get(symbol, [])
            
            for keyword in symbol_keywords:
                if keyword.lower() in text:
                    relevant.append(symbol)
                    break
        
        return relevant
    
    def analyze_sentiment(self, news_by_symbol: Dict[str, List[Dict]]) -> Dict[str, Dict]:
        sentiment_results = {}
        
        for symbol, articles in news_by_symbol.items():
            if not articles:
                sentiment_results[symbol] = {
                    'sentiment_score': 0.0,
                    'sentiment_label': 'neutral',
                    'article_count': 0,
                    'positive_count': 0,
                    'negative_count': 0,
                    'neutral_count': 0
                }
                continue
            
            sentiments = []
            positive_count = 0
            negative_count = 0
            neutral_count = 0
            
            for article in articles:
                text = article['title'] + ' ' + article['summary']
                
                try:
                    blob = TextBlob(text)
                    polarity = blob.sentiment.polarity
                    sentiments.append(polarity)
                    
                    if polarity > 0.1:
                        positive_count += 1
                    elif polarity < -0.1:
                        negative_count += 1
                    else:
                        neutral_count += 1
                        
                except Exception as e:
                    logger.warning(f"Error analyzing sentiment: {e}")
                    neutral_count += 1
            
            # Calculate overall sentiment
            avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0.0
            
            if avg_sentiment > 0.1:
                sentiment_label = 'positive'
            elif avg_sentiment < -0.1:
                sentiment_label = 'negative'
            else:
                sentiment_label = 'neutral'
            
            sentiment_results[symbol] = {
                'sentiment_score': round(avg_sentiment, 3),
                'sentiment_label': sentiment_label,
                'article_count': len(articles),
                'positive_count': positive_count,
                'negative_count': negative_count,
                'neutral_count': neutral_count,
                'articles': articles[:5]  # Keep top 5 articles for context
            }
        
        return sentiment_results
    
    def get_news_summary(self, symbols: List[str], hours_back: int = 24) -> Dict:
        news_by_symbol = self.collect_news(symbols, hours_back)
        sentiment_analysis = self.analyze_sentiment(news_by_symbol)
        
        # Overall market sentiment
        all_scores = [result['sentiment_score'] for result in sentiment_analysis.values() 
                     if result['article_count'] > 0]
        
        overall_sentiment = sum(all_scores) / len(all_scores) if all_scores else 0.0
        
        return {
            'individual_sentiment': sentiment_analysis,
            'overall_sentiment': {
                'score': round(overall_sentiment, 3),
                'label': self._get_sentiment_label(overall_sentiment)
            },
            'timestamp': datetime.now().isoformat(),
            'total_articles': sum(result['article_count'] for result in sentiment_analysis.values())
        }
    
    def _get_sentiment_label(self, score: float) -> str:
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