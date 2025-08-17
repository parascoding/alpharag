"""
Application constants and configuration values
"""

# Email configuration
DEFAULT_SMTP_SERVER = "smtp.gmail.com"
DEFAULT_SMTP_PORT = 587

# Data provider names
PROVIDER_UPSTOX = "upstox"
PROVIDER_ALPHA_VANTAGE = "alpha_vantage"
PROVIDER_YAHOO = "yahoo"
PROVIDER_MOCK = "mock"

# LLM provider names
LLM_CLAUDE = "claude"
LLM_GPT = "gpt"
LLM_GEMINI = "gemini"

# File paths
DEFAULT_PORTFOLIO_FILE = "data/portfolio.csv"
DEFAULT_LOG_FILE = "alpharag.log"

# RSS Feed URLs for Indian financial news
DEFAULT_RSS_FEEDS = [
    "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "https://www.livemint.com/rss/markets",
    "https://economictimes.indiatimes.com/news/economy/rssfeeds/1373380680.cms"
]

# Financial health scoring weights
FINANCIAL_HEALTH_WEIGHTS = {
    'profitability': 0.35,
    'valuation': 0.25,
    'financial_health': 0.25,
    'growth': 0.15
}

# Risk assessment thresholds
RISK_THRESHOLDS = {
    'low': 7.0,
    'medium': 5.0,
    'high': 3.0
}

# Sentiment analysis settings
SENTIMENT_HOURS_BACK = 24
SENTIMENT_KEYWORDS = [
    'buy', 'sell', 'hold', 'target', 'upgrade', 'downgrade',
    'bullish', 'bearish', 'positive', 'negative', 'growth', 'decline'
]

# Market data settings
CACHE_DURATION_MINUTES = 5
RATE_LIMIT_DELAY_SECONDS = 12