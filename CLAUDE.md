# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**AlphaRAG** is an AI-powered portfolio analysis system designed for Indian equity markets. The system combines financial fundamentals analysis, news sentiment analysis, and AI-driven investment recommendations using a RAG (Retrieval Augmented Generation) architecture.

### Key Features
- **Portfolio Management**: CSV-based portfolio tracking with P&L calculations
- **Financial Analysis**: 20+ financial ratios per stock with health scoring (0-10 scale)
- **News Sentiment**: Real-time RSS feed analysis with TextBlob sentiment scoring
- **AI Recommendations**: Claude AI integration for investment strategy and analysis
- **Email Reports**: Automated portfolio analysis reports with financial scorecards
- **Multi-Provider Data System**: Pluggable data providers with intelligent fallback (Yahoo Finance, Alpha Vantage, Mock)
- **Real Market Data**: Support for live Indian stock market data with automatic fallback to mock data

## Development Setup

### Prerequisites
- Python 3.8+
- Virtual environment (venv)
- Required API keys: Anthropic (Claude), Gmail App Password
- Optional API keys: Alpha Vantage (for real market data)

### Installation
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Environment Configuration
```bash
# Copy template and configure
cp .env.template .env
# Edit .env with your API keys and credentials
```

### Email Recipients
The system supports sending reports to multiple email addresses:
```bash
# Single recipient
EMAIL_TO=user@example.com

# Multiple recipients (comma-separated)
EMAIL_TO=user1@example.com,user2@example.com,admin@company.com
```

### Data Provider Configuration
The system supports multiple data sources with automatic fallback:
```bash
# Alpha Vantage API (for real market data)
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key_here

# Data Provider Selection
PRIMARY_DATA_PROVIDER=alpha_vantage  # or 'yahoo', 'mock'
FALLBACK_DATA_PROVIDERS=mock        # comma-separated fallback list
```

## Architecture

### Core Components

1. **Portfolio Manager** (`src/portfolio_manager.py`)
   - Loads portfolio from CSV file (`data/portfolio.csv`)
   - Calculates P&L, returns, and portfolio valuation

2. **Financial Indicators** (`src/financial_indicators.py`)
   - JSON-based mock data with 20+ financial ratios per stock
   - Alpha Vantage API integration for real data (optional)
   - Financial health scoring algorithm with sector-specific benchmarks

3. **Market Data Ingestion** (`src/data_ingestion_v2.py`)
   - Multi-provider data system with intelligent fallback
   - Real market data from Yahoo Finance and Alpha Vantage
   - Enhanced caching and rate limiting
   - Technical indicators and market analysis

4. **News Sentiment Analysis** (`src/news_sentiment.py`)
   - RSS feed parsing for Indian market news
   - TextBlob sentiment analysis with keyword matching
   - JSON-based mock news data with realistic articles

5. **RAG Engine** (`src/rag_engine.py`)
   - TF-IDF vectorization for document similarity
   - Contextual retrieval of portfolio, market, and news data
   - Structured context building for AI analysis

6. **AI Prediction Engine** (`src/prediction.py`)
   - Claude AI integration for investment recommendations
   - Enhanced fallback predictions using financial health scores
   - BUY/SELL/HOLD recommendations with confidence levels

7. **Email Service** (`src/email_service.py`)
   - SMTP-based portfolio analysis reports
   - Financial health scorecards with risk assessment
   - Professional formatting with emojis and structured layout

### Data Provider System

The system uses a **pluggable data provider architecture** with automatic fallback:

- **`src/data_providers/base_provider.py`**: Abstract interface for all data providers
- **`src/data_providers/yahoo_provider.py`**: Yahoo Finance integration via direct HTTP requests
- **`src/data_providers/alpha_vantage_provider.py`**: Alpha Vantage API with rate limiting and currency conversion
- **`src/data_providers/mock_provider.py`**: Enhanced mock data with realistic randomization
- **`src/data_providers/provider_factory.py`**: Factory pattern with intelligent fallback chains

**Current Configuration:** Alpha Vantage (Primary) → Mock Data (Fallback)
**Alternative Fallback Chain:** Yahoo Finance → Alpha Vantage → Mock Data

**Key Benefits:**
- Automatic provider switching when APIs fail or hit rate limits
- Zero-downtime operation with mock data fallback
- Easy provider addition/removal via configuration
- **Real-time portfolio calculation**: Live market data with accurate P&L tracking (₹28,847 portfolio value vs mock ₹59,868)

### Mock Data System

The system uses a **JSON-based mock data architecture** for development and testing:

- **`mock_data/financial_indicators.json`**: Comprehensive financial ratios for Indian stocks (IT Services vs Oil & Gas sectors)
- **`mock_data/market_data.json`**: Real-time market prices, technical indicators, and market status
- **`mock_data/news_sentiment.json`**: Realistic news articles with sentiment analysis

**Key Benefits:**
- Easy data modification without code changes
- Realistic randomization (±2-10%) for simulation
- Clean separation between data and business logic
- Seamless transition to real APIs via environment flags

## Common Commands

### Development
- **Build**: Not applicable (Python project)
- **Test**: `python main.py --mode validate`
- **Lint**: Use your preferred Python linter (ruff, flake8, etc.)
- **Start development server**: `python main.py --mode analyze`

### Testing
- **Run full analysis**: `python main.py --mode analyze`
- **Test email configuration**: `python main.py --mode test-email`
- **Validate setup**: `python main.py --mode validate`
- **Test Alpha Vantage API**: `python test_alpha_vantage_direct.py`
- **Test real portfolio analysis**: `python test_real_portfolio.py`

### Environment Flags
- **Data Providers**: Set `PRIMARY_DATA_PROVIDER=upstox` for real Indian market data (requires access token)
- **Financial APIs**: Set `USE_REAL_FINANCIAL_APIS=true` to use Alpha Vantage for financial indicators
- **News Analysis**: Uses RSS feeds by default, falls back to JSON mock data if feeds fail

### Real Market Data Status (Current: August 2025)
- **✅ Upstox Integration**: Fully operational with real-time prices and historical data from NSE/BSE
- **✅ Real Portfolio Analysis**: Live data showing -26.57% P&L (₹40,431.10 current value)
- **✅ Historical Data**: 20+ days of OHLCV data with technical indicators (RSI, SMA)
- **✅ Multi-Provider Fallback**: Upstox → Alpha Vantage → Mock data ensures 100% uptime
- **⚠️ Alpha Vantage**: Rate limited (25 calls/day) but working for financial fundamentals
- **❌ Yahoo Finance**: Limited due to authentication requirements and Python 3.8 compatibility

## Data Sources & API Usage

### Current Data Architecture (Configurable: 100% Mock to 100% Real)

**What We Compute:**
- Portfolio P&L calculations and performance metrics
- 20+ financial ratios (P/E, ROE, debt ratios, etc.)
- Financial health scoring algorithm (4-component system)
- News sentiment analysis using TextBlob
- TF-IDF document vectorization and similarity search

**What AI (Claude) Does:**
- Investment strategy and recommendation generation
- Complex market analysis and pattern recognition
- Natural language insights and reasoning
- Portfolio-level strategic advice

**External Dependencies:**
- **Claude AI API**: Investment analysis and recommendations
- **Email SMTP**: Portfolio report delivery
- **RSS Feeds**: Real-time Indian market news (with JSON fallback)
- **Upstox API**: Real-time Indian stock prices and historical data (primary provider)
- **Alpha Vantage API**: Financial fundamentals and historical data (fallback)
- **Yahoo Finance API**: Real-time stock prices and company data (fallback)

### API Migration Path
The system supports seamless migration from mock to real data:
1. **Mock Data**: Default configuration, always available as fallback
2. **Upstox**: Set `UPSTOX_ACCESS_TOKEN` for real Indian market data (₹499 one-time subscription)
3. **Alpha Vantage**: Set `ALPHA_VANTAGE_API_KEY` for real financial data (500 calls/day free)
4. **Yahoo Finance**: Implemented via direct HTTP requests (authentication may be required)
5. **Multi-Provider**: Use provider factory for automatic fallback chains

### Provider Status & Issues
- **✅ Upstox**: Fully working with real-time prices and historical data (primary provider)
- **⚠️ Alpha Vantage**: Rate limited (25 calls/day free tier) but very reliable for financial ratios
- **❌ Yahoo Finance API**: May require authentication for reliable access
- **❌ yfinance library**: Incompatible with Python 3.8 due to typing syntax in dependencies
- **✅ Solution**: Multi-provider architecture ensures system always works via fallback chains

## Portfolio Configuration

Edit `data/portfolio.csv` to customize your portfolio:
```csv
symbol,quantity,buy_price
RELIANCE.NS,10,2500.00
TCS.NS,5,3600.00
INFY.NS,15,1400.00
```

## Key Files & Locations

- **Portfolio Data**: `data/portfolio.csv`
- **Mock Data**: `mock_data/*.json`
- **Environment Config**: `.env` (copy from `.env.template`)
- **Main Entry Point**: `main.py`
- **Logs**: `alpharag.log`

## Important Implementation Notes

### Mock Data Randomization
- **Financial Indicators**: ±5% variation on base values
- **Market Prices**: ±2% variation for realistic price movements  
- **News Sentiment**: ±10% variation on sentiment scores
- **Technical Indicators**: ±1% variation on RSI, SMA values

### Financial Health Scoring
- **Valuation Score**: Based on P/E, P/B ratios vs sector benchmarks
- **Profitability Score**: ROE and profit margin analysis
- **Financial Health Score**: Debt ratios and liquidity assessment
- **Growth Score**: Revenue and earnings growth trends
- **Overall Score**: Weighted average (35% profitability, 25% valuation, 25% health, 15% growth)

### Error Handling & Fallbacks
- **Data Provider Failures**: Automatic fallback from Alpha Vantage → Mock data
- **Rate Limiting**: 12-second delays between Alpha Vantage API calls for free tier compliance
- **Currency Conversion**: Intelligent USD to INR conversion for Indian stocks (₹1,373.75 RELIANCE.NS)
- **JSON file missing**: Falls back to hard-coded mock data
- **Claude API fails**: Uses enhanced rule-based predictions with financial scores
- **Email fails**: Analysis continues, logs warning
- **RSS feeds fail**: Uses JSON mock news data

This system provides a robust, maintainable foundation for portfolio analysis with realistic mock data and clear migration paths to production APIs.