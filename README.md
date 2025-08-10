# 🎯 AlphaRAG - AI-Powered Portfolio Analysis System

AlphaRAG is an intelligent portfolio analysis system that combines market data, news sentiment analysis, and Claude AI to provide automated stock recommendations via email reports for Indian equity markets.

## ✨ Features

- 📊 **Portfolio Management**: Load and analyze portfolio from CSV file
- 📈 **Market Data Integration**: Fetch real-time stock prices and technical indicators
- 📰 **News Sentiment Analysis**: Analyze market sentiment from RSS feeds
- 🧠 **RAG-Powered AI Analysis**: Use Claude AI with contextual market data
- 📧 **Automated Email Reports**: Receive detailed analysis via email
- 🎯 **Stock Recommendations**: Get BUY/SELL/HOLD recommendations with confidence scores

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Gmail account with App Password enabled
- Anthropic Claude API key

### Installation

1. **Clone and setup**
```bash
cd alpharag
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure environment**
```bash
cp .env.template .env
# Edit .env file with your credentials
```

3. **Setup portfolio**
Edit `data/portfolio.csv` with your stock holdings:
```csv
symbol,quantity,buy_price,purchase_date
RELIANCE.NS,10,2450.00,2024-01-15
TCS.NS,5,3680.00,2024-02-01
INFY.NS,8,1520.00,2024-01-20
```

4. **Run analysis**
```bash
# Validate setup
python main.py --mode validate

# Test email
python main.py --mode test-email

# Run full analysis
python main.py
```

## 📁 Project Structure

```
alpharag/
├── src/                        # Core modules
│   ├── portfolio_manager.py    # Portfolio data management
│   ├── data_ingestion.py       # Market data fetching
│   ├── news_sentiment.py       # News sentiment analysis
│   ├── rag_engine.py           # RAG knowledge base
│   ├── prediction.py           # Claude AI predictions
│   └── email_service.py        # Email notifications
├── data/
│   └── portfolio.csv           # Your stock holdings
├── config/
│   └── settings.py            # Configuration management
├── main.py                    # Main orchestrator
├── requirements.txt           # Dependencies
├── .env.template             # Environment template
└── README.md                 # This file
```

## ⚙️ Configuration

### Environment Variables (.env file)

```bash
# Required - Claude AI API key
ANTHROPIC_API_KEY=your_claude_api_key_here

# Required - Email configuration
EMAIL_USER=your.email@gmail.com
EMAIL_PASS=your_gmail_app_password  # Not your regular password!
EMAIL_TO=recipient@gmail.com

# Optional - Email server settings (defaults to Gmail)
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587

# Optional - Alpha Vantage backup API
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
```

### Portfolio File Format

Your `data/portfolio.csv` should contain:
- `symbol`: NSE symbol (e.g., RELIANCE.NS, TCS.NS)
- `quantity`: Number of shares owned
- `buy_price`: Purchase price per share
- `purchase_date`: Date of purchase (YYYY-MM-DD)

## 🎯 Usage Examples

### Basic Analysis
```bash
python main.py
```
This runs the complete analysis pipeline and sends an email report.

### Validation Only
```bash
python main.py --mode validate
```
Checks if all configuration is correct.

### Email Test
```bash
python main.py --mode test-email
```
Sends a test email to verify email settings.

## 📊 Sample Output

The system generates comprehensive reports including:

### Email Report Content
- 📊 Portfolio performance summary
- 📈 Individual stock analysis
- 📰 Market sentiment analysis  
- 🎯 AI-powered recommendations
- ⚠️ Risk assessments

### Console Output
```
🎯 ALPHARAG ANALYSIS SUMMARY
============================================

📊 Portfolio Performance:
   Current Value: ₹55,940.20
   Total P&L: 🟢 ₹880.20 (+1.60%)

📰 Market Sentiment: 😐 Neutral
   Articles Analyzed: 12

🎯 AI Recommendations:
   🟢 RELIANCE.NS: BUY ⭐⭐⭐⭐⭐
   🟡 TCS.NS: HOLD ⭐⭐⭐
   🔴 INFY.NS: SELL ⭐⭐⭐⭐

📧 Detailed report sent to: your@email.com
============================================
```

## 🔧 Technical Architecture

### Data Flow
1. **Portfolio Loading** → Load holdings from CSV
2. **Market Data** → Fetch current prices and technical indicators  
3. **News Analysis** → Collect and analyze market sentiment
4. **RAG Context** → Build searchable knowledge base
5. **AI Analysis** → Generate predictions using Claude
6. **Email Report** → Send formatted analysis

### Key Components
- **Simple RAG Engine**: TF-IDF based document retrieval
- **Mock Data Support**: Works without external APIs for testing
- **Robust Error Handling**: Fallback mechanisms for API failures
- **Email Templates**: Rich formatted reports with emojis

## 🛠️ Development

### Testing Individual Components
```bash
# Test portfolio manager
python -c "from src.portfolio_manager import PortfolioManager; pm = PortfolioManager('data/portfolio.csv'); print(pm.get_portfolio_summary())"

# Test data ingestion  
python -c "from src.data_ingestion import MarketDataIngestion; di = MarketDataIngestion(); print(di.get_current_prices(['RELIANCE.NS']))"
```

### Adding New Stocks
1. Add stock symbols to `data/portfolio.csv`
2. Update mock prices in `src/data_ingestion.py` if needed
3. Run validation: `python main.py --mode validate`

## 📝 TODO / Future Enhancements

- [ ] Real yfinance integration (replace mock data)
- [ ] ChromaDB integration for better RAG performance
- [ ] Web dashboard interface
- [ ] Multiple portfolio support
- [ ] Advanced technical indicators
- [ ] Backtesting capabilities
- [ ] Slack/Discord notifications
- [ ] Database persistence

## ⚠️ Disclaimer

This system is for educational and informational purposes only. The AI-generated recommendations should not be considered as financial advice. Always consult with qualified financial advisors before making investment decisions. Past performance does not guarantee future results.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is open source. Feel free to modify and use for your own portfolio analysis needs.

---

Built with ❤️ using Claude AI and Python