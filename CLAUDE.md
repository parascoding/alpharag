# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AlphaRAG is an AI-powered portfolio analysis system for Indian equity markets. It combines market data, news sentiment analysis, and Claude AI to provide intelligent stock recommendations via email reports.

## Development Setup

### Prerequisites
- Python 3.8+
- pip package manager
- Gmail account with App Password for email notifications
- Anthropic Claude API key

### Installation
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment file
cp .env.template .env
# Edit .env with your API keys and email settings
```

## Configuration

Create a `.env` file with the following variables:
```
ANTHROPIC_API_KEY=your_claude_api_key_here
EMAIL_USER=your.email@gmail.com  
EMAIL_PASS=your_gmail_app_password
EMAIL_TO=recipient@gmail.com
```

## Common Commands

### Development
- Run full analysis: `python main.py`
- Test email setup: `python main.py --mode test-email`
- Validate configuration: `python main.py --mode validate`

### Testing
- Test portfolio manager: `python -c "from src.portfolio_manager import PortfolioManager; pm = PortfolioManager('data/portfolio.csv'); print(pm.get_portfolio_summary())"`
- Test data ingestion: `python -c "from src.data_ingestion import MarketDataIngestion; di = MarketDataIngestion(); print(di.get_current_prices(['RELIANCE.NS']))"`

## Architecture

The system consists of 6 main components:

1. **Portfolio Manager** (`src/portfolio_manager.py`): Loads and manages portfolio data from CSV
2. **Data Ingestion** (`src/data_ingestion.py`): Fetches market data and calculates technical indicators  
3. **News Sentiment** (`src/news_sentiment.py`): Analyzes news sentiment from RSS feeds
4. **RAG Engine** (`src/rag_engine.py`): Creates searchable knowledge base from all data
5. **Prediction Engine** (`src/prediction.py`): Uses Claude API for AI-powered analysis
6. **Email Service** (`src/email_service.py`): Sends formatted analysis reports

### Data Flow
Portfolio CSV → Market Data → News Analysis → RAG Context → Claude Analysis → Email Report

## File Structure
```
alpharag/
├── src/                    # Core modules
├── data/portfolio.csv      # Portfolio holdings
├── config/settings.py      # Configuration management  
├── main.py                # Main orchestrator
├── requirements.txt       # Python dependencies
└── .env                   # Environment variables (not in git)
```