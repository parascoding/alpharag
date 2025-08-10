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
- **Mock-First Design**: JSON-based mock data with easy migration to real APIs

## Development Setup

### Prerequisites
- Python 3.8+
- Virtual environment (venv)
- Required API keys: Anthropic (Claude), Gmail App Password

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

## Architecture

### Core Components

1. **Portfolio Manager** (`src/portfolio_manager.py`)
   - Loads portfolio from CSV file (`data/portfolio.csv`)
   - Calculates P&L, returns, and portfolio valuation

2. **Financial Indicators** (`src/financial_indicators.py`)
   - JSON-based mock data with 20+ financial ratios per stock
   - Alpha Vantage API integration for real data (optional)
   - Financial health scoring algorithm with sector-specific benchmarks

3. **Market Data Ingestion** (`src/data_ingestion.py`)
   - JSON-based mock market data with technical indicators
   - Real-time price simulation with randomization
   - Market status and technical analysis

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

### Environment Flags
- **Financial APIs**: Set `USE_REAL_FINANCIAL_APIS=true` to use Alpha Vantage instead of mock data
- **News Analysis**: Uses RSS feeds by default, falls back to JSON mock data if feeds fail

## Data Sources & API Usage

### Current Data Architecture (85% Mock, 15% Real)

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

### API Migration Path
The system is designed for easy migration from mock to real data:
1. **Alpha Vantage**: Set `USE_REAL_FINANCIAL_APIS=true` for real financial data
2. **yfinance**: Can be integrated for real-time stock prices (Python 3.9+ required)
3. **News APIs**: Can replace RSS feeds for more comprehensive news coverage

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
- JSON file missing → Falls back to hard-coded mock data
- Claude API fails → Uses enhanced rule-based predictions with financial scores
- Email fails → Analysis continues, logs warning
- RSS feeds fail → Uses JSON mock news data

This system provides a robust, maintainable foundation for portfolio analysis with realistic mock data and clear migration paths to production APIs.