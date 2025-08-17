#!/usr/bin/env python3
"""
Test script for the real Upstox portfolio data
"""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))
sys.path.insert(0, str(Path(__file__).parent))

from src.dynamic_portfolio_analyzer import DynamicPortfolioAnalyzer
from src.portfolio_manager import PortfolioManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_real_portfolio():
    """Test the real Upstox portfolio from data/portfolio.csv"""
    logger.info("=== Testing Real Upstox Portfolio ===")

    try:
        # Path to real portfolio
        portfolio_file = str(Path(__file__).parent / 'data' / 'portfolio.csv')

        # RSS feeds for news analysis
        rss_feeds = [
            'https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms',
            'https://www.business-standard.com/rss/markets-106.rss'
        ]

        # Test 1: Basic Portfolio Loading
        logger.info("\n=== Step 1: Testing Portfolio Loading ===")
        portfolio_manager = PortfolioManager(portfolio_file)

        print(f"✅ Portfolio Format: {portfolio_manager.detected_format}")
        print(f"✅ Holdings Count: {len(portfolio_manager.portfolio_df)}")
        print(f"✅ Symbols: {portfolio_manager.get_symbols()}")
        print(f"✅ Columns: {list(portfolio_manager.portfolio_df.columns)}")

        # Show sample data
        print("\n📊 Portfolio Data Sample:")
        for idx, row in portfolio_manager.portfolio_df.iterrows():
            print(f"  {row['symbol']}: {row['quantity']} shares @ ₹{row['buy_price']:.2f}")
            if 'current_price' in row and row['current_price'] > 0:
                print(f"    Current: ₹{row['current_price']:.2f}")

        # Test 2: Dynamic Analysis Pipeline
        logger.info("\n=== Step 2: Testing Dynamic Analysis Pipeline ===")
        analyzer = DynamicPortfolioAnalyzer(portfolio_file, rss_feeds)

        # Run validation
        validation_results = analyzer.validate_pipeline()
        print(f"\n🔍 Pipeline Validation:")
        for component, status in validation_results.items():
            if component == 'errors':
                continue
            status_icon = "✅" if status else "❌"
            print(f"  {status_icon} {component}: {status}")

        if validation_results['errors']:
            print("\n⚠️ Validation Errors:")
            for error in validation_results['errors']:
                print(f"  • {error}")

        # Test 3: Full Analysis
        if validation_results['overall_status']:
            logger.info("\n=== Step 3: Running Full Analysis ===")

            try:
                analysis_result = analyzer.load_and_analyze_portfolio()

                # Display results
                print(f"\n=== 📈 Analysis Results ===")

                # Portfolio Summary
                portfolio_summary = analysis_result['portfolio_summary']
                print(f"\n💼 Portfolio Summary:")
                print(f"  📊 Format: {portfolio_summary['detected_format']}")
                print(f"  🎯 Holdings: {portfolio_summary['total_holdings']}")
                print(f"  💰 Total Investment: ₹{portfolio_summary['total_investment']:,.2f}")
                print(f"  🏢 Symbols: {', '.join(portfolio_summary['symbols'])}")

                # Instrument Mapping Results
                instrument_mapping = analysis_result['instrument_mapping']
                mapped_count = len([k for k, v in instrument_mapping.items() if v])
                print(f"\n🔗 Instrument Mapping ({mapped_count}/{len(instrument_mapping)} mapped):")
                for symbol, instrument_key in instrument_mapping.items():
                    if instrument_key:
                        print(f"  ✅ {symbol} → {instrument_key}")
                    else:
                        print(f"  ❌ {symbol} → Not found")

                # Company Information
                company_info = analysis_result['company_information']
                print(f"\n🏢 Company Information ({len(company_info)} companies):")
                for symbol, info in company_info.items():
                    if info:
                        print(f"  📋 {symbol}: {info['company_name']}")
                        print(f"     Trading Symbol: {info['trading_symbol']}")
                        print(f"     Exchange: {info['exchange']}")
                    else:
                        print(f"  ❌ {symbol}: No company info found")

                # Keyword Analysis
                keyword_analysis = analysis_result['keyword_analysis']
                print(f"\n🔤 Keyword Analysis:")
                print(f"  📊 Total Keywords: {keyword_analysis['total_keywords']}")
                print(f"  📈 Average per Company: {keyword_analysis['average_keywords_per_company']:.1f}")
                if keyword_analysis['most_common_keywords']:
                    top_keywords = [word for word, count in keyword_analysis['most_common_keywords'][:5]]
                    print(f"  🔍 Top Keywords: {', '.join(top_keywords)}")

                # News Sentiment
                news_sentiment = analysis_result['news_sentiment']
                print(f"\n📰 News Sentiment Analysis:")
                print(f"  📊 Total Articles: {news_sentiment.get('total_articles', 0)}")
                print(f"  🌡️ Overall Sentiment: {news_sentiment.get('overall_sentiment', {}).get('label', 'unknown')} "
                      f"({news_sentiment.get('overall_sentiment', {}).get('score', 0):.3f})")

                individual_sentiment = news_sentiment.get('individual_sentiment', {})
                for symbol, sentiment_data in individual_sentiment.items():
                    if sentiment_data and sentiment_data.get('article_count', 0) > 0:
                        print(f"    📈 {symbol}: {sentiment_data.get('sentiment_label', 'unknown')} "
                              f"({sentiment_data.get('sentiment_score', 0):.3f}) - "
                              f"{sentiment_data.get('article_count', 0)} articles")
                    else:
                        print(f"    📈 {symbol}: No news articles found")

                # Analysis Metadata
                metadata = analysis_result['analysis_metadata']
                print(f"\n📊 Analysis Metadata:")
                print(f"  🎯 Symbols Analyzed: {metadata['symbols_analyzed']}")
                print(f"  🔗 Instruments Mapped: {metadata['instruments_mapped']}")
                print(f"  🏢 Companies with Info: {metadata['companies_with_info']}")
                print(f"  🔤 Keywords Generated: {metadata['keywords_generated']}")
                print(f"  📰 News Articles: {metadata['news_articles_analyzed']}")

                logger.info("✅ Full analysis completed successfully!")

            except Exception as e:
                logger.error(f"❌ Error in full analysis: {e}")
                import traceback
                traceback.print_exc()
        else:
            logger.warning("⚠️ Skipping full analysis due to validation failures")

        # Test 4: Individual Symbol Analysis
        logger.info("\n=== Step 4: Testing Individual Symbol Analysis ===")
        symbols = portfolio_manager.get_symbols()

        if symbols:
            test_symbol = symbols[0]
            print(f"\n🔍 Detailed Analysis for {test_symbol}:")

            try:
                symbol_details = analyzer.get_symbol_details(test_symbol)

                if symbol_details['company_info']:
                    info = symbol_details['company_info']
                    print(f"  🏢 Company: {info.get('company_name', 'Unknown')}")
                    print(f"  🎯 Trading Symbol: {info.get('trading_symbol', 'Unknown')}")
                    print(f"  🏛️ Exchange: {info.get('exchange', 'Unknown')}")
                    print(f"  🔑 Instrument Key: {info.get('instrument_key', 'Unknown')}")

                if symbol_details['keywords']:
                    keywords = symbol_details['keywords']
                    print(f"  🔍 Primary Keywords: {', '.join(keywords['primary'][:5])}")
                    print(f"  🏭 Industry Keywords: {', '.join(keywords['industry'][:3])}")
                    print(f"  📊 Total Keywords: {len(keywords['all'])}")

                if symbol_details['portfolio_holding']:
                    holding = symbol_details['portfolio_holding']
                    print(f"  💼 Holding: {holding.get('quantity', 0)} shares @ ₹{holding.get('buy_price', 0):.2f}")

            except Exception as e:
                logger.error(f"❌ Error in symbol analysis: {e}")

        return True

    except Exception as e:
        logger.error(f"❌ Error in real portfolio test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Testing Real Upstox Portfolio Analysis")

    success = test_real_portfolio()

    if success:
        print("\n🎉 Real portfolio analysis test completed!")
    else:
        print("\n❌ Real portfolio analysis test failed!")
        sys.exit(1)