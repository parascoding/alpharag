import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

class Settings:
    def __init__(self):
        # LLM API keys (multiple providers)
        self.GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
        self.GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')  # Alternative name for Gemini
        self.OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
        self.GPT_API_KEY = os.getenv('GPT_API_KEY')  # Alternative name for OpenAI
        self.OPENAI_ORG_ID = os.getenv('OPENAI_ORG_ID')  # Optional OpenAI organization
        self.ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
        self.CLAUDE_API_KEY = os.getenv('CLAUDE_API_KEY')  # Alternative name for Claude

        # LLM Provider Configuration
        self.PRIMARY_LLM_PROVIDER = os.getenv('PRIMARY_LLM_PROVIDER', 'gemini')
        fallback_llm_providers_raw = os.getenv('FALLBACK_LLM_PROVIDERS', 'gpt,claude')
        self.FALLBACK_LLM_PROVIDERS = [provider.strip() for provider in fallback_llm_providers_raw.split(',') if provider.strip()]

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

        # Optional API keys for data providers
        self.ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')
        self.UPSTOX_ACCESS_TOKEN = os.getenv('UPSTOX_ACCESS_TOKEN')

        # Data Provider Configuration
        self.PRIMARY_DATA_PROVIDER = os.getenv('PRIMARY_DATA_PROVIDER', 'mock')
        fallback_providers_raw = os.getenv('FALLBACK_DATA_PROVIDERS', 'mock')
        self.FALLBACK_DATA_PROVIDERS = [provider.strip() for provider in fallback_providers_raw.split(',') if provider.strip()]

        # Financial Indicators Configuration
        self.USE_REAL_FINANCIAL_APIS = os.getenv('USE_REAL_FINANCIAL_APIS', 'false').lower() == 'true'

        # RSS Feeds for news sentiment
        self.RSS_FEEDS = [
            'https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms',
            'https://www.moneycontrol.com/rss/business.xml'
        ]

    def get_available_llm_api_keys(self):
        """Get dictionary of available LLM API keys"""
        return {
            'GEMINI_API_KEY': self.GEMINI_API_KEY or self.GOOGLE_API_KEY,
            'GOOGLE_API_KEY': self.GEMINI_API_KEY or self.GOOGLE_API_KEY,
            'OPENAI_API_KEY': self.OPENAI_API_KEY or self.GPT_API_KEY,
            'GPT_API_KEY': self.OPENAI_API_KEY or self.GPT_API_KEY,
            'OPENAI_ORG_ID': self.OPENAI_ORG_ID,
            'ANTHROPIC_API_KEY': self.ANTHROPIC_API_KEY or self.CLAUDE_API_KEY,
            'CLAUDE_API_KEY': self.ANTHROPIC_API_KEY or self.CLAUDE_API_KEY
        }

    def validate(self):
        """Validate required environment variables"""
        issues = []

        # Check email settings (still required)
        email_vars = ['EMAIL_USER', 'EMAIL_PASS']
        for var in email_vars:
            if not getattr(self, var):
                issues.append(f"Missing environment variable: {var}")

        # Check EMAIL_TO specifically (it's a list)
        if not self.EMAIL_TO:
            issues.append("Missing environment variable: EMAIL_TO (or invalid format)")

        # Check that at least one LLM API key is available
        llm_keys = self.get_available_llm_api_keys()
        available_llm_keys = [k for k, v in llm_keys.items() if v]

        if not available_llm_keys:
            issues.append("Missing LLM API keys: At least one of GEMINI_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY is required")

        # Validate LLM provider configuration
        all_llm_providers = [self.PRIMARY_LLM_PROVIDER] + self.FALLBACK_LLM_PROVIDERS
        valid_providers = ['gemini', 'gpt', 'claude']

        for provider in all_llm_providers:
            if provider not in valid_providers:
                issues.append(f"Invalid LLM provider: {provider}. Valid options: {valid_providers}")

        if issues:
            raise ValueError(f"Configuration issues: {issues}")

        return True

# Create global settings instance
settings = Settings()