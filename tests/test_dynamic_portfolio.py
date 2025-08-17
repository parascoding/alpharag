#!/usr/bin/env python3
"""
Test script for dynamic portfolio analysis pipeline
"""

import sys
import os
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Fix relative imports for testing
sys.path.insert(0, str(Path(__file__).parent))

from src.dynamic_portfolio_analyzer import DynamicPortfolioAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_sample_upstox_portfolio():
    """Create a sample Upstox format portfolio for testing"""
    sample_data = '''Instrument,Qty.,Avg. cost,LTP,Invested,Cur. val,P&L,Net chg.,Day chg.,
RELIANCE,10,2450.00,2400,24500,24000,-500,-2.04,-1.5,
TCS,5,3680.00,3700,18400,18500,100,0.54,0.8,
INFY,8,1520.00,1500,12160,12000,-160,-1.32,-1.0,
SBIN,50,420.27,430,21013.5,21500,486.5,2.31,2.3,'''

    portfolio_file = Path(__file__).parent / 'data' / 'test_upstox_portfolio.csv'
    portfolio_file.parent.mkdir(exist_ok=True)

    with open(portfolio_file, 'w') as f:
        f.write(sample_data)

    logger.info(f"Created sample portfolio at: {portfolio_file}")
    return str(portfolio_file)

def test_dynamic_portfolio_analysis():
    """Test the complete dynamic portfolio analysis pipeline"""
    logger.info("=== Testing Dynamic Portfolio Analysis Pipeline ===")

    try:
        # Create sample portfolio
        portfolio_file = create_sample_upstox_portfolio()

        # RSS feeds for news analysis
        rss_feeds = [
            'https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms',
            'https://www.business-standard.com/rss/markets-106.rss'
        ]

        # Initialize analyzer
        logger.info("Initializing Dynamic Portfolio Analyzer...")
        analyzer = DynamicPortfolioAnalyzer(portfolio_file, rss_feeds)

        # Test 1: Validate pipeline components
        logger.info("\n=== Step 1: Validating Pipeline Components ===")
        validation_results = analyzer.validate_pipeline()

        print("\nValidation Results:")
        for component, status in validation_results.items():
            if component == 'errors':
                continue
            status_icon = "✅" if status else "❌"
            print(f"  {status_icon} {component}: {status}")

        if validation_results['errors']:
            print("\nErrors encountered:")
            for error in validation_results['errors']:
                print(f"  ⚠️ {error}")

        # Test 2: Run complete analysis
        logger.info("\n=== Step 2: Running Complete Analysis ===")
        analysis_result = analyzer.load_and_analyze_portfolio()

        # Display results
        print("\n=== Analysis Results ===")

        # Portfolio Summary
        portfolio_summary = analysis_result['portfolio_summary']
        print(f"\nPortfolio Summary:")
        print(f"  📊 Format: {portfolio_summary['detected_format']}")
        print(f"  🎯 Holdings: {portfolio_summary['total_holdings']}")
        print(f"  📈 Total Investment: ₹{portfolio_summary['total_investment']:,.2f}")
        print(f"  🏢 Symbols: {', '.join(portfolio_summary['symbols'])}")

        # Instrument Mapping
        instrument_mapping = analysis_result['instrument_mapping']
        print(f"\nInstrument Mapping:")
        mapped_count = len([k for k, v in instrument_mapping.items() if v])
        print(f"  🔗 Mapped: {mapped_count}/{len(instrument_mapping)} symbols")
        for symbol, instrument_key in instrument_mapping.items():
            if instrument_key:
                print(f"    ✅ {symbol} → {instrument_key}")
            else:
                print(f"    ❌ {symbol} → Not mapped")

        # Keyword Analysis
        keyword_analysis = analysis_result['keyword_analysis']
        print(f"\nKeyword Analysis:")
        print(f"  🔤 Total Keywords: {keyword_analysis['total_keywords']}")
        print(f"  📊 Average per Company: {keyword_analysis['average_keywords_per_company']}")
        print(f"  🔍 Most Common: {', '.join([word for word, count in keyword_analysis['most_common_keywords'][:5]])}")

        # News Sentiment
        news_sentiment = analysis_result['news_sentiment']
        print(f"\nNews Sentiment Analysis:")
        print(f"  📰 Total Articles: {news_sentiment.get('total_articles', 0)}")
        print(f"  🌡️ Overall Sentiment: {news_sentiment.get('overall_sentiment', {}).get('label', 'unknown')} ({news_sentiment.get('overall_sentiment', {}).get('score', 0):.3f})")

        individual_sentiment = news_sentiment.get('individual_sentiment', {})
        for symbol, sentiment_data in individual_sentiment.items():
            if sentiment_data:
                print(f"    📈 {symbol}: {sentiment_data.get('sentiment_label', 'unknown')} ({sentiment_data.get('sentiment_score', 0):.3f}) - {sentiment_data.get('article_count', 0)} articles")

        # Test 3: Symbol-specific details
        logger.info("\n=== Step 3: Testing Symbol-Specific Analysis ===")
        test_symbol = portfolio_summary['symbols'][0] if portfolio_summary['symbols'] else None

        if test_symbol:
            print(f"\nDetailed Analysis for {test_symbol}:")
            symbol_details = analyzer.get_symbol_details(test_symbol)

            if symbol_details['company_info']:
                company_info = symbol_details['company_info']
                print(f"  🏢 Company: {company_info.get('company_name', 'Unknown')}")
                print(f"  🎯 Trading Symbol: {company_info.get('trading_symbol', 'Unknown')}")
                print(f"  🏛️ Exchange: {company_info.get('exchange', 'Unknown')}")

            if symbol_details['keywords']:
                keywords = symbol_details['keywords']
                print(f"  🔍 Primary Keywords: {', '.join(keywords['primary'][:3])}")
                print(f"  🔍 Industry Keywords: {', '.join(keywords['industry'][:3])}")
                print(f"  🔤 Total Keywords: {len(keywords['all'])}")

        # Metadata
        metadata = analysis_result['analysis_metadata']
        print(f"\nAnalysis Metadata:")
        print(f"  📊 Portfolio Format: {metadata['portfolio_format']}")
        print(f"  🎯 Symbols Analyzed: {metadata['symbols_analyzed']}")
        print(f"  🔗 Instruments Mapped: {metadata['instruments_mapped']}")
        print(f"  🏢 Companies with Info: {metadata['companies_with_info']}")
        print(f"  🔤 Keywords Generated: {metadata['keywords_generated']}")
        print(f"  📰 News Articles: {metadata['news_articles_analyzed']}")

        logger.info("\n✅ Dynamic portfolio analysis test completed successfully!")

        return True

    except Exception as e:
        logger.error(f"❌ Error in dynamic portfolio analysis test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_specific_components():
    """Test individual components separately"""
    logger.info("\n=== Testing Individual Components ===")

    try:
        # Test 1: Portfolio Parser
        logger.info("Testing Portfolio Parser...")
        from src.dynamic_portfolio_parser import DynamicPortfolioParser

        portfolio_file = create_sample_upstox_portfolio()
        parser = DynamicPortfolioParser(portfolio_file)
        portfolio_data = parser.load_and_parse_portfolio()

        print(f"✅ Portfolio Parser: Loaded {len(portfolio_data)} holdings")
        print(f"   Detected format: {parser.detected_format}")
        print(f"   Symbols: {parser.get_symbols()}")

        # Test 2: Upstox Mapper
        logger.info("Testing Upstox Instrument Mapper...")
        from src.data_providers.upstox_instrument_mapper import upstox_mapper

        test_symbols = parser.get_symbols()[:2]  # Test first 2 symbols
        for symbol in test_symbols:
            instrument_key = upstox_mapper.get_instrument_key(symbol)
            company_info = upstox_mapper.get_company_info(symbol)

            print(f"✅ {symbol}:")
            print(f"   Instrument Key: {instrument_key}")
            if company_info:
                print(f"   Company: {company_info['company_name']}")
            else:
                print("   Company: No info found")

        # Test 3: Keyword Generator
        logger.info("Testing Keyword Generator...")
        from src.dynamic_news_keyword_generator import DynamicNewsKeywordGenerator

        generator = DynamicNewsKeywordGenerator()
        companies_info = upstox_mapper.bulk_get_company_info(test_symbols)
        keywords_map = generator.bulk_generate_keywords(companies_info)

        for symbol, keywords in keywords_map.items():
            print(f"✅ {symbol}: {len(keywords.all_keywords)} keywords")
            print(f"   Primary: {', '.join(keywords.primary_keywords[:3])}")

        logger.info("✅ All component tests completed!")

    except Exception as e:
        logger.error(f"❌ Error in component testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Starting Dynamic Portfolio Analysis Tests")

    # Run component tests
    test_specific_components()

    # Run full pipeline test
    success = test_dynamic_portfolio_analysis()

    if success:
        print("\n🎉 All tests passed! Dynamic portfolio analysis is working correctly.")
    else:
        print("\n❌ Tests failed. Please check the logs for details.")
        sys.exit(1)