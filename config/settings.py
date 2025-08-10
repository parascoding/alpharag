import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

class Settings:
    def __init__(self):
        # Core API keys
        self.ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
        
        # Email settings
        self.EMAIL_SMTP_SERVER = os.getenv('EMAIL_SMTP_SERVER', 'smtp.gmail.com')
        self.EMAIL_SMTP_PORT = int(os.getenv('EMAIL_SMTP_PORT', '587'))
        self.EMAIL_USER = os.getenv('EMAIL_USER')
        self.EMAIL_PASS = os.getenv('EMAIL_PASS')
        
        # Parse EMAIL_TO as comma-separated list
        email_to_raw = os.getenv('EMAIL_TO', '')
        if email_to_raw:
            self.EMAIL_TO = [email.strip() for email in email_to_raw.split(',') if email.strip()]
        else:
            self.EMAIL_TO = []
        
        # Portfolio configuration
        self.PORTFOLIO_FILE = 'data/portfolio.csv'
        
        # Optional API keys
        self.ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')
        
        # Financial Indicators Configuration
        self.USE_REAL_FINANCIAL_APIS = os.getenv('USE_REAL_FINANCIAL_APIS', 'false').lower() == 'true'
        
        # RSS Feeds for news sentiment
        self.RSS_FEEDS = [
            'https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms',
            'https://www.moneycontrol.com/rss/business.xml'
        ]
    
    def validate(self):
        """Validate required environment variables"""
        issues = []
        
        # Check required environment variables
        required_vars = ['ANTHROPIC_API_KEY', 'EMAIL_USER', 'EMAIL_PASS']
        for var in required_vars:
            if not getattr(self, var):
                issues.append(f"Missing environment variable: {var}")
        
        # Check EMAIL_TO specifically (it's a list)
        if not self.EMAIL_TO:
            issues.append("Missing environment variable: EMAIL_TO (or invalid format)")
        
        if issues:
            raise ValueError(f"Missing required environment variables: {issues}")
        
        return True

# Create global settings instance
settings = Settings()