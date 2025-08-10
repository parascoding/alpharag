import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
    
    EMAIL_USER = os.getenv('EMAIL_USER')
    EMAIL_PASS = os.getenv('EMAIL_PASS') 
    EMAIL_TO = os.getenv('EMAIL_TO')
    EMAIL_SMTP_SERVER = os.getenv('EMAIL_SMTP_SERVER', 'smtp.gmail.com')
    EMAIL_SMTP_PORT = int(os.getenv('EMAIL_SMTP_PORT', '587'))
    
    PORTFOLIO_FILE = 'data/portfolio.csv'
    
    ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')
    
    RSS_FEEDS = [
        'https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms',
        'https://www.moneycontrol.com/rss/business.xml'
    ]
    
    @staticmethod
    def validate():
        required_vars = ['ANTHROPIC_API_KEY', 'EMAIL_USER', 'EMAIL_PASS', 'EMAIL_TO']
        missing = [var for var in required_vars if not getattr(Settings, var)]
        if missing:
            raise ValueError(f"Missing required environment variables: {missing}")
        return True

settings = Settings()