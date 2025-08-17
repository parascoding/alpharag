"""
AlphaRAG Orchestrator - Main application coordinator
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional

from config.settings import settings
from src.portfolio_manager import PortfolioManager
from src.data_ingestion_v2 import MarketDataIngestionV2
from src.news_sentiment import NewsSentimentAnalyzer
from src.rag_engine import SimpleRAGEngine
from src.llm_providers.llm_factory import LLMFactory
from src.email_service import EmailService
from src.financial_indicators import FinancialIndicatorsFetcher

logger = logging.getLogger(__name__)


class AlphaRAGOrchestrator:
    """Main orchestrator for the AlphaRAG system"""
    
    def __init__(self):
        self.portfolio_manager: Optional[PortfolioManager] = None
        self.data_ingestion: Optional[MarketDataIngestionV2] = None
        self.news_analyzer: Optional[NewsSentimentAnalyzer] = None
        self.rag_engine: Optional[SimpleRAGEngine] = None
        self.llm_factory: Optional[LLMFactory] = None
        self.email_service: Optional[EmailService] = None
        self.financial_indicators: Optional[FinancialIndicatorsFetcher] = None

        self._initialize_components()

    def _initialize_components(self):
        """Initialize all system components"""
        try:
            logger.info("Initializing AlphaRAG components...")
            settings.validate()

            self._init_portfolio_manager()
            self._init_data_ingestion()
            self._init_news_analyzer()
            self._init_rag_engine()
            self._init_llm_factory()
            self._init_email_service()
            
            logger.info("🚀 All components initialized successfully!")

        except Exception as e:
            logger.error(f"❌ Error initializing components: {e}")
            raise

    def _init_portfolio_manager(self):
        """Initialize portfolio manager"""
        self.portfolio_manager = PortfolioManager(settings.PORTFOLIO_FILE)
        logger.info("✅ Portfolio manager initialized")

    def _init_data_ingestion(self):
        """Initialize data ingestion with multi-provider support"""
        provider_kwargs = {}
        if settings.ALPHA_VANTAGE_API_KEY:
            provider_kwargs['api_key'] = settings.ALPHA_VANTAGE_API_KEY
        if settings.UPSTOX_ACCESS_TOKEN:
            provider_kwargs['access_token'] = settings.UPSTOX_ACCESS_TOKEN

        self.data_ingestion = MarketDataIngestionV2(
            primary_provider=settings.PRIMARY_DATA_PROVIDER,
            fallback_providers=settings.FALLBACK_DATA_PROVIDERS,
            **provider_kwargs
        )
        logger.info(f"✅ Data ingestion initialized with provider: {self.data_ingestion.provider.name}")

    def _init_news_analyzer(self):
        """Initialize news sentiment analyzer"""
        self.news_analyzer = NewsSentimentAnalyzer(settings.RSS_FEEDS)
        logger.info("✅ News sentiment analyzer initialized")

    def _init_rag_engine(self):
        """Initialize RAG engine"""
        self.rag_engine = SimpleRAGEngine()
        logger.info("✅ RAG engine initialized")

    def _init_llm_factory(self):
        """Initialize LLM Factory with fallback chain"""
        llm_api_keys = settings.get_available_llm_api_keys()
        self.llm_factory = LLMFactory(
            primary_provider=settings.PRIMARY_LLM_PROVIDER,
            fallback_providers=settings.FALLBACK_LLM_PROVIDERS,
            **llm_api_keys
        )

        provider_status = self.llm_factory.get_provider_status()
        healthy_providers = provider_status['healthy_providers']
        total_providers = provider_status['total_providers']
        available_providers = self.llm_factory.get_available_providers()

        if available_providers:
            logger.info(f"✅ LLM Factory initialized: {healthy_providers}/{total_providers} providers healthy")
            logger.info(f"🤖 Available LLMs: {' → '.join(available_providers)}")
        else:
            logger.warning("⚠️ No LLM providers available - will use emergency fallback")

    def _init_email_service(self):
        """Initialize email service"""
        self.email_service = EmailService(
            settings.EMAIL_SMTP_SERVER,
            settings.EMAIL_SMTP_PORT,
            settings.EMAIL_USER,
            settings.EMAIL_PASS
        )
        logger.info("✅ Email service initialized")

    def run_full_analysis(self) -> bool:
        """Run the complete portfolio analysis pipeline"""
        try:
            logger.info("🔄 Starting full portfolio analysis...")

            # Get portfolio and market data
            portfolio_data = self._get_portfolio_data()
            market_data = self._get_market_data(portfolio_data['symbols'])
            
            # Analyze sentiment
            sentiment_data = self._analyze_sentiment(portfolio_data['symbols'])
            
            # Build RAG context
            rag_context = self._build_rag_context(portfolio_data, market_data, sentiment_data)
            
            # Generate predictions
            predictions = self._generate_predictions(rag_context, market_data, sentiment_data)
            
            # Send email report
            self._send_email_report(market_data, sentiment_data, predictions)
            
            # Display summary
            self._display_summary(market_data, sentiment_data, predictions)

            logger.info("🎉 Full analysis completed successfully!")
            return True

        except Exception as e:
            logger.error(f"❌ Error during analysis: {e}")
            return False

    def _get_portfolio_data(self) -> Dict[str, Any]:
        """Get portfolio data"""
        logger.info("📊 Loading portfolio data...")
        portfolio_summary = self.portfolio_manager.get_portfolio_summary()
        symbols = self.portfolio_manager.get_symbols()
        logger.info(f"Portfolio loaded: {len(symbols)} holdings, Total investment: ₹{portfolio_summary['total_investment']:,.2f}")
        
        return {
            'summary': portfolio_summary,
            'symbols': symbols
        }

    def _get_market_data(self, symbols: list) -> Dict[str, Any]:
        """Get market data"""
        logger.info("📈 Fetching market data...")
        current_prices = self.data_ingestion.get_current_prices(symbols)
        market_summary = self.data_ingestion.get_market_summary(symbols)
        portfolio_value = self.portfolio_manager.calculate_portfolio_value(current_prices)
        
        # Identify liquid funds and available cash
        liquid_funds = self.portfolio_manager.identify_liquid_funds(current_prices)
        available_cash = liquid_funds['total_available_cash']
        
        logger.info(f"Market data fetched for {len(current_prices)} symbols")
        logger.info(f"💰 Available cash identified: ₹{available_cash:,.2f} from {liquid_funds['count']} liquid holdings")
        
        return {
            'current_prices': current_prices,
            'market_summary': market_summary,
            'portfolio_value': portfolio_value,
            'liquid_funds': liquid_funds,
            'available_cash': available_cash
        }

    def _analyze_sentiment(self, symbols: list) -> Dict[str, Any]:
        """Analyze news sentiment"""
        logger.info("📰 Analyzing news sentiment...")
        sentiment_data = self.news_analyzer.get_news_summary(symbols, hours_back=24)
        logger.info(f"Sentiment analyzed from {sentiment_data['total_articles']} articles")
        return sentiment_data

    def _build_rag_context(self, portfolio_data: Dict, market_data: Dict, sentiment_data: Dict) -> Dict[str, Any]:
        """Build RAG context"""
        logger.info("🧠 Building RAG context...")
        self.rag_engine.clear_documents()

        # Add portfolio data to RAG
        self.rag_engine.add_portfolio_data(portfolio_data['summary'], market_data['portfolio_value'])

        # Add market data to RAG
        for symbol in portfolio_data['symbols']:
            self.rag_engine.add_market_data(symbol, market_data['market_summary'])

        # Add sentiment data to RAG
        for symbol in portfolio_data['symbols']:
            if symbol in sentiment_data['individual_sentiment']:
                self.rag_engine.add_news_sentiment(symbol, sentiment_data['individual_sentiment'][symbol])

        # Add market investment context for new stock recommendations
        available_cash = market_data.get('available_cash', 0)
        if available_cash > 0:
            self.rag_engine.add_market_investment_context(available_cash)

        # Build the search index
        self.rag_engine.build_index()
        rag_context = self.rag_engine.get_all_context()
        logger.info("RAG context built successfully")
        
        return rag_context

    def _generate_predictions(self, rag_context: Dict, market_data: Dict, sentiment_data: Dict) -> Dict[str, Any]:
        """Generate AI predictions"""
        logger.info("🤖 Generating AI predictions...")
        available_cash = market_data.get('available_cash', 0)
        predictions = self.llm_factory.generate_predictions(
            rag_context, market_data['portfolio_value'], market_data['market_summary'], sentiment_data, {}, available_cash
        )

        provider_used = predictions.get('provider_used', 'unknown')
        if predictions.get('emergency_fallback', False):
            logger.warning("🚨 Used emergency fallback for predictions")
        elif predictions.get('fallback_mode', False):
            logger.warning(f"⚠️ Used fallback mode with {provider_used}")
        else:
            logger.info(f"✅ Predictions generated successfully using {provider_used.upper()}")
        
        return predictions

    def _send_email_report(self, market_data: Dict, sentiment_data: Dict, predictions: Dict):
        """Send email report"""
        logger.info("📧 Sending email report...")
        email_success = self.email_service.send_portfolio_analysis(
            settings.EMAIL_TO, market_data['portfolio_value'], market_data['market_summary'], 
            sentiment_data, predictions, {}
        )

        if email_success:
            logger.info("✅ Email report sent successfully!")
        else:
            logger.warning("⚠️  Email sending failed, but analysis completed")

    def _display_summary(self, market_data: Dict, sentiment_data: Dict, predictions: Dict, financial_data: Dict = None):
        """Display a summary of the analysis results"""
        portfolio_value = market_data['portfolio_value']
        
        print("\n" + "="*60)
        print("🎯 ALPHARAG ANALYSIS SUMMARY")
        print("="*60)

        # Portfolio summary
        summary = portfolio_value['summary']
        pnl_symbol = "🟢" if summary['total_pnl'] > 0 else "🔴"
        print(f"\n📊 Portfolio Performance:")
        print(f"   Current Value: ₹{summary['total_current_value']:,.2f}")
        print(f"   Total P&L: {pnl_symbol} ₹{summary['total_pnl']:,.2f} ({summary['total_pnl_percent']:+.2f}%)")

        # Sentiment summary
        overall_sentiment = sentiment_data['overall_sentiment']
        sentiment_emoji = {'positive': '😊', 'negative': '😟', 'neutral': '😐'}.get(overall_sentiment['label'], '❓')
        print(f"\n📰 Market Sentiment: {sentiment_emoji} {overall_sentiment['label'].title()}")
        print(f"   Articles Analyzed: {sentiment_data['total_articles']}")

        # Financial health summary
        if financial_data:
            print(f"\n💰 Financial Health Scores:")
            for symbol, data in financial_data.items():
                health_score = data.get('health_score', {})
                score = health_score.get('overall_score', 0)
                rating = health_score.get('rating', 'Unknown')
                rating_emoji = health_score.get('rating_emoji', '❓')
                print(f"   {rating_emoji} {symbol}: {score:.1f}/10 ({rating})")

        # Recommendations
        print(f"\n🎯 AI Recommendations:")
        recommendations = predictions.get('individual_recommendations', {})
        for symbol, rec in recommendations.items():
            rec_emoji = {'BUY': '🟢', 'SELL': '🔴', 'HOLD': '🟡'}.get(rec['recommendation'], '❓')
            confidence_stars = '⭐' * min(rec.get('confidence', 5), 5)
            print(f"   {rec_emoji} {symbol}: {rec['recommendation']} {confidence_stars}")

        # Display email recipients
        recipients = ', '.join(settings.EMAIL_TO) if isinstance(settings.EMAIL_TO, list) else str(settings.EMAIL_TO)
        print(f"\n📧 Detailed report sent to: {recipients}")
        print("="*60)

    def test_email(self) -> bool:
        """Test email configuration"""
        try:
            logger.info("📧 Testing email configuration...")
            success = self.email_service.send_test_email(settings.EMAIL_TO)

            if success:
                logger.info("✅ Test email sent successfully!")
                print(f"✅ Test email sent to {settings.EMAIL_TO}")
            else:
                logger.error("❌ Test email failed!")
                print("❌ Test email failed! Check your email settings.")

            return success

        except Exception as e:
            logger.error(f"❌ Error testing email: {e}")
            print(f"❌ Email test error: {e}")
            return False

    def validate_setup(self) -> bool:
        """Validate that all components are properly configured"""
        try:
            logger.info("🔍 Validating system setup...")

            issues = []

            # Check portfolio file
            if not Path(settings.PORTFOLIO_FILE).exists():
                issues.append(f"Portfolio file not found: {settings.PORTFOLIO_FILE}")

            # Check required environment variables
            required_vars = ['ANTHROPIC_API_KEY', 'EMAIL_USER', 'EMAIL_PASS']
            for var in required_vars:
                if not getattr(settings, var):
                    issues.append(f"Missing environment variable: {var}")

            # Check EMAIL_TO specifically (it's a list)
            if not settings.EMAIL_TO:
                issues.append("Missing environment variable: EMAIL_TO (or invalid format)")

            if issues:
                logger.error("❌ Setup validation failed:")
                for issue in issues:
                    logger.error(f"   • {issue}")
                    print(f"❌ {issue}")
                return False

            logger.info("✅ Setup validation passed!")
            print("✅ All setup requirements satisfied!")
            return True

        except Exception as e:
            logger.error(f"❌ Error validating setup: {e}")
            print(f"❌ Setup validation error: {e}")
            return False