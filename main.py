#!/usr/bin/env python3
"""
AlphaRAG - AI-Powered Portfolio Analysis System
Main entry point for the application
"""

import sys
import logging
import argparse
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent))

from config.settings import settings
from src.portfolio_manager import PortfolioManager
from src.data_ingestion import MarketDataIngestion
from src.news_sentiment import NewsSentimentAnalyzer
from src.rag_engine import SimpleRAGEngine
from src.prediction import ClaudePredictionEngine
from src.email_service import EmailService
from src.financial_indicators import FinancialIndicatorsFetcher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('alpharag.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class AlphaRAGOrchestrator:
    def __init__(self):
        self.portfolio_manager = None
        self.data_ingestion = None
        self.news_analyzer = None
        self.rag_engine = None
        self.prediction_engine = None
        self.email_service = None
        self.financial_indicators = None
        
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize all system components"""
        try:
            logger.info("Initializing AlphaRAG components...")
            
            # Validate settings
            settings.validate()
            
            # Initialize portfolio manager
            self.portfolio_manager = PortfolioManager(settings.PORTFOLIO_FILE)
            logger.info("✅ Portfolio manager initialized")
            
            # Initialize data ingestion
            self.data_ingestion = MarketDataIngestion(settings.ALPHA_VANTAGE_API_KEY)
            logger.info("✅ Data ingestion initialized")
            
            # Initialize news sentiment analyzer
            self.news_analyzer = NewsSentimentAnalyzer(settings.RSS_FEEDS)
            logger.info("✅ News sentiment analyzer initialized")
            
            # Initialize RAG engine
            self.rag_engine = SimpleRAGEngine()
            logger.info("✅ RAG engine initialized")
            
            # Initialize Claude prediction engine
            self.prediction_engine = ClaudePredictionEngine(settings.ANTHROPIC_API_KEY)
            logger.info("✅ Claude prediction engine initialized")
            
            # Initialize email service
            self.email_service = EmailService(
                settings.EMAIL_SMTP_SERVER,
                settings.EMAIL_SMTP_PORT,
                settings.EMAIL_USER,
                settings.EMAIL_PASS
            )
            logger.info("✅ Email service initialized")
            
            # Initialize financial indicators
            self.financial_indicators = FinancialIndicatorsFetcher(
                settings.ALPHA_VANTAGE_API_KEY,
                settings.USE_REAL_FINANCIAL_APIS
            )
            mode = "real APIs" if settings.USE_REAL_FINANCIAL_APIS else "mock data"
            logger.info(f"✅ Financial indicators initialized ({mode})")
            
            logger.info("🚀 All components initialized successfully!")
            
        except Exception as e:
            logger.error(f"❌ Error initializing components: {e}")
            raise
    
    def run_full_analysis(self) -> bool:
        """Run the complete portfolio analysis pipeline"""
        try:
            logger.info("🔄 Starting full portfolio analysis...")
            
            # Step 1: Get portfolio data
            logger.info("📊 Loading portfolio data...")
            portfolio_summary = self.portfolio_manager.get_portfolio_summary()
            symbols = self.portfolio_manager.get_symbols()
            logger.info(f"Portfolio loaded: {len(symbols)} holdings, Total investment: ₹{portfolio_summary['total_investment']:,.2f}")
            
            # Step 2: Fetch market data
            logger.info("📈 Fetching market data...")
            current_prices = self.data_ingestion.get_current_prices(symbols)
            market_summary = self.data_ingestion.get_market_summary(symbols)
            portfolio_value = self.portfolio_manager.calculate_portfolio_value(current_prices)
            logger.info(f"Market data fetched for {len(current_prices)} symbols")
            
            # Step 3: Fetch financial indicators
            logger.info("💰 Fetching financial indicators...")
            financial_indicators = self.financial_indicators.get_financial_indicators(symbols)
            
            # Calculate financial health scores
            financial_data = {}
            for symbol, data in financial_indicators.items():
                health_score = self.financial_indicators.calculate_financial_health_score(data)
                data['health_score'] = health_score
                financial_data[symbol] = data
            
            logger.info(f"Financial indicators fetched for {len(financial_data)} symbols")
            
            # Step 4: Analyze news sentiment  
            logger.info("📰 Analyzing news sentiment...")
            sentiment_data = self.news_analyzer.get_news_summary(symbols, hours_back=24)
            logger.info(f"Sentiment analyzed from {sentiment_data['total_articles']} articles")
            
            # Step 5: Build RAG context
            logger.info("🧠 Building RAG context...")
            self.rag_engine.clear_documents()
            
            # Add portfolio data to RAG
            self.rag_engine.add_portfolio_data(portfolio_summary, portfolio_value)
            
            # Add market data to RAG
            for symbol in symbols:
                self.rag_engine.add_market_data(symbol, market_summary)
            
            # Add financial indicators to RAG
            for symbol in symbols:
                if symbol in financial_data:
                    self.rag_engine.add_financial_indicators(
                        symbol, 
                        financial_data[symbol], 
                        financial_data[symbol].get('health_score', {})
                    )
            
            # Add sentiment data to RAG
            for symbol in symbols:
                if symbol in sentiment_data['individual_sentiment']:
                    self.rag_engine.add_news_sentiment(symbol, sentiment_data['individual_sentiment'][symbol])
            
            # Build the search index
            self.rag_engine.build_index()
            
            # Get comprehensive context
            rag_context = self.rag_engine.get_all_context()
            logger.info("RAG context built successfully")
            
            # Step 6: Generate predictions using Claude
            logger.info("🤖 Generating AI predictions...")
            predictions = self.prediction_engine.generate_predictions(
                rag_context, portfolio_value, market_summary, sentiment_data, financial_data
            )
            logger.info("Predictions generated successfully")
            
            # Step 7: Send email report
            logger.info("📧 Sending email report...")
            email_success = self.email_service.send_portfolio_analysis(
                settings.EMAIL_TO, portfolio_value, market_summary, sentiment_data, predictions, financial_data
            )
            
            if email_success:
                logger.info("✅ Email report sent successfully!")
            else:
                logger.warning("⚠️  Email sending failed, but analysis completed")
            
            # Step 8: Display summary
            self._display_summary(portfolio_value, sentiment_data, predictions, financial_data)
            
            logger.info("🎉 Full analysis completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error during analysis: {e}")
            return False
    
    def _display_summary(self, portfolio_value: dict, sentiment_data: dict, predictions: dict, financial_data: dict = None):
        """Display a summary of the analysis results"""
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
        
        print(f"\n📧 Detailed report sent to: {settings.EMAIL_TO}")
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
            required_vars = ['ANTHROPIC_API_KEY', 'EMAIL_USER', 'EMAIL_PASS', 'EMAIL_TO']
            for var in required_vars:
                if not getattr(settings, var):
                    issues.append(f"Missing environment variable: {var}")
            
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

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="AlphaRAG - AI-Powered Portfolio Analysis System",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--mode', 
        choices=['analyze', 'test-email', 'validate'],
        default='analyze',
        help='Operation mode (default: analyze)'
    )
    
    args = parser.parse_args()
    
    print("🚀 AlphaRAG - AI-Powered Portfolio Analysis System")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)
    
    try:
        # Initialize orchestrator
        orchestrator = AlphaRAGOrchestrator()
        
        if args.mode == 'validate':
            success = orchestrator.validate_setup()
        elif args.mode == 'test-email':
            success = orchestrator.test_email()
        else:  # analyze mode
            success = orchestrator.run_full_analysis()
        
        if success:
            print("\n✅ Operation completed successfully!")
            return 0
        else:
            print("\n❌ Operation failed!")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
        return 1
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        print(f"\n❌ Fatal error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())