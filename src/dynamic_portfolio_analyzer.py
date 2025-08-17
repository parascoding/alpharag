"""
Dynamic Portfolio Analyzer - Integrates all dynamic components for seamless portfolio analysis
"""

import logging
from typing import Dict, List, Optional
from pathlib import Path

try:
    from .dynamic_portfolio_parser import DynamicPortfolioParser
    from .data_providers.upstox_instrument_mapper import upstox_mapper
    from .dynamic_news_keyword_generator import DynamicNewsKeywordGenerator
    from .news_sentiment import NewsSentimentAnalyzer
except ImportError:
    # For standalone testing
    from dynamic_portfolio_parser import DynamicPortfolioParser
    from data_providers.upstox_instrument_mapper import upstox_mapper
    from dynamic_news_keyword_generator import DynamicNewsKeywordGenerator
    from news_sentiment import NewsSentimentAnalyzer

logger = logging.getLogger(__name__)

class DynamicPortfolioAnalyzer:
    """
    Main orchestrator for dynamic portfolio analysis without static mappings
    """

    def __init__(self, portfolio_file: str, rss_feeds: List[str]):
        self.portfolio_file = portfolio_file
        self.rss_feeds = rss_feeds

        # Initialize components
        self.portfolio_parser = DynamicPortfolioParser(portfolio_file)
        self.keyword_generator = DynamicNewsKeywordGenerator()
        self.news_analyzer = NewsSentimentAnalyzer(rss_feeds)

        # Data caches
        self.portfolio_data = None
        self.symbols = []
        self.company_info = {}
        self.keyword_mapping = {}

    def load_and_analyze_portfolio(self) -> Dict:
        """
        Complete pipeline: Load portfolio -> Map instruments -> Generate keywords -> Analyze news
        """
        try:
            logger.info("Starting dynamic portfolio analysis pipeline...")

            # Step 1: Load and parse portfolio
            self.portfolio_data = self.portfolio_parser.load_and_parse_portfolio()
            self.symbols = self.portfolio_parser.get_symbols()

            logger.info(f"Loaded {len(self.symbols)} symbols from {self.portfolio_parser.detected_format} format portfolio")

            # Step 2: Map symbols to Upstox instruments dynamically
            logger.info("Mapping symbols to Upstox instruments...")
            instrument_mapping = upstox_mapper.bulk_map_symbols(self.symbols)

            mapped_count = len([k for k, v in instrument_mapping.items() if v])
            logger.info(f"Successfully mapped {mapped_count}/{len(self.symbols)} symbols to Upstox instruments")

            # Step 3: Get company information for keyword generation
            logger.info("Fetching company information...")
            self.company_info = upstox_mapper.bulk_get_company_info(self.symbols)

            # Step 4: Generate dynamic news keywords
            logger.info("Generating dynamic news keywords...")
            self.keyword_mapping = self.keyword_generator.bulk_generate_keywords(self.company_info)

            keyword_stats = self.keyword_generator.get_keyword_summary(self.keyword_mapping)
            logger.info(f"Generated {keyword_stats['total_keywords']} keywords for {keyword_stats['total_companies']} companies")

            # Step 5: Analyze news sentiment using dynamic keywords
            logger.info("Analyzing news sentiment with dynamic keywords...")
            news_summary = self.news_analyzer.get_news_summary(self.symbols, hours_back=24)

            # Compile comprehensive analysis
            analysis_result = {
                'portfolio_summary': self.portfolio_parser.get_portfolio_summary(),
                'instrument_mapping': instrument_mapping,
                'company_information': self.company_info,
                'keyword_analysis': keyword_stats,
                'news_sentiment': news_summary,
                'analysis_metadata': {
                    'portfolio_format': self.portfolio_parser.detected_format,
                    'symbols_analyzed': len(self.symbols),
                    'instruments_mapped': mapped_count,
                    'companies_with_info': len(self.company_info),
                    'keywords_generated': keyword_stats['total_keywords'],
                    'news_articles_analyzed': news_summary.get('total_articles', 0)
                }
            }

            logger.info("Dynamic portfolio analysis completed successfully!")
            return analysis_result

        except Exception as e:
            logger.error(f"Error in dynamic portfolio analysis: {e}")
            raise

    def get_symbol_details(self, symbol: str) -> Dict:
        """
        Get detailed information for a specific symbol
        """
        details = {
            'symbol': symbol,
            'portfolio_holding': None,
            'instrument_key': None,
            'company_info': None,
            'keywords': None,
            'news_sentiment': None
        }

        try:
            # Portfolio holding information
            if self.portfolio_data is not None:
                holding = self.portfolio_data[self.portfolio_data['symbol'] == symbol]
                if not holding.empty:
                    details['portfolio_holding'] = holding.iloc[0].to_dict()

            # Instrument mapping
            details['instrument_key'] = upstox_mapper.get_instrument_key(symbol)

            # Company information
            details['company_info'] = self.company_info.get(symbol)

            # Keywords
            if symbol in self.keyword_mapping:
                details['keywords'] = {
                    'primary': self.keyword_mapping[symbol].primary_keywords,
                    'secondary': self.keyword_mapping[symbol].secondary_keywords,
                    'industry': self.keyword_mapping[symbol].industry_keywords,
                    'all': self.keyword_mapping[symbol].all_keywords
                }

            # News sentiment (get fresh data)
            try:
                news_data = self.news_analyzer.get_news_summary([symbol], hours_back=24)
                details['news_sentiment'] = news_data.get('individual_sentiment', {}).get(symbol)
            except Exception as e:
                logger.error(f"Error getting news sentiment for {symbol}: {e}")
                details['news_sentiment'] = None

        except Exception as e:
            logger.error(f"Error getting details for {symbol}: {e}")

        return details

    def validate_pipeline(self) -> Dict:
        """
        Validate that all pipeline components are working correctly
        """
        validation_results = {
            'portfolio_parser': False,
            'upstox_mapper': False,
            'keyword_generator': False,
            'news_analyzer': False,
            'overall_status': False,
            'errors': []
        }

        try:
            # Test portfolio parser
            portfolio_data = self.portfolio_parser.load_and_parse_portfolio()
            if portfolio_data is not None and not portfolio_data.empty:
                validation_results['portfolio_parser'] = True
                test_symbols = portfolio_data['symbol'].head(2).tolist()
            else:
                validation_results['errors'].append("Portfolio parser: No data loaded")
                test_symbols = ['RELIANCE.NS']  # Fallback

        except Exception as e:
            validation_results['errors'].append(f"Portfolio parser error: {e}")
            test_symbols = ['RELIANCE.NS']

        try:
            # Test Upstox mapper
            mapper_info = upstox_mapper.get_cache_info()
            test_key = upstox_mapper.get_instrument_key(test_symbols[0])
            if test_key:
                validation_results['upstox_mapper'] = True
            else:
                validation_results['errors'].append("Upstox mapper: Could not map test symbol")
        except Exception as e:
            validation_results['errors'].append(f"Upstox mapper error: {e}")

        try:
            # Test keyword generator
            test_company_info = {test_symbols[0]: {'symbol': test_symbols[0], 'company_name': 'Test Company', 'trading_symbol': 'TEST'}}
            keywords = self.keyword_generator.bulk_generate_keywords(test_company_info)
            if keywords and test_symbols[0] in keywords:
                validation_results['keyword_generator'] = True
            else:
                validation_results['errors'].append("Keyword generator: No keywords generated")
        except Exception as e:
            validation_results['errors'].append(f"Keyword generator error: {e}")

        try:
            # Test news analyzer (minimal test)
            news_summary = self.news_analyzer.get_news_summary(test_symbols[:1], hours_back=1)
            if news_summary and 'individual_sentiment' in news_summary:
                validation_results['news_analyzer'] = True
            else:
                validation_results['errors'].append("News analyzer: No sentiment data generated")
        except Exception as e:
            validation_results['errors'].append(f"News analyzer error: {e}")

        # Overall status
        validation_results['overall_status'] = all([
            validation_results['portfolio_parser'],
            validation_results['upstox_mapper'],
            validation_results['keyword_generator'],
            validation_results['news_analyzer']
        ])

        return validation_results

    def get_analysis_summary(self) -> Dict:
        """
        Get a summary of the current analysis state
        """
        return {
            'portfolio_loaded': self.portfolio_data is not None,
            'symbols_count': len(self.symbols),
            'companies_with_info': len(self.company_info),
            'keywords_generated': len(self.keyword_mapping),
            'portfolio_format': getattr(self.portfolio_parser, 'detected_format', 'unknown'),
            'symbols': self.symbols
        }