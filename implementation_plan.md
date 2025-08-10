# AlphaRAG MVP Implementation Plan
## Single-Client RAG Stock Market Prediction System for Indian Equity Market

### Phase 1: Project Setup & Foundation (30-45 minutes)

**1.1 Environment Setup**
- [ ] Initialize Python project with virtual environment
- [ ] Install core dependencies: `pandas`, `numpy`, `requests`, `python-dotenv`
- [ ] Install LLM dependencies: `anthropic`, `chromadb`, `sentence-transformers`
- [ ] Install additional libraries: `yfinance`, `beautifulsoup4`, `textblob`, `smtplib`
- [ ] Create simplified project structure:
  ```
  alpharag/
  ├── src/
  │   ├── data_ingestion.py
  │   ├── portfolio_manager.py
  │   ├── news_sentiment.py
  │   ├── rag_engine.py
  │   ├── prediction.py
  │   └── email_service.py
  ├── data/
  │   └── portfolio.csv
  ├── config/
  │   └── settings.py
  ├── main.py
  └── requirements.txt
  ```

**1.2 Configuration Management**
- [ ] Create `config/settings.py` for API keys (Claude, email, etc.)
- [ ] Set up environment variable handling (.env file) including `ANTHROPIC_API_KEY`
- [ ] Create sample `data/portfolio.csv` template

### Phase 2: Portfolio & Data Management (1 hour)

**2.1 Portfolio CSV Handler**
- [ ] Create `src/portfolio_manager.py` to read `data/portfolio.csv`
- [ ] Define CSV schema: `symbol,quantity,buy_price,purchase_date`
- [ ] Add basic validation for portfolio data
- [ ] Create portfolio summary functions

**2.2 Market Data Integration**
- [ ] Implement `src/data_ingestion.py` with yfinance for NSE data
- [ ] Add Alpha Vantage as backup (free tier: 25 requests/day)
- [ ] Create simple data fetching for current prices and historical data
- [ ] Add basic error handling and caching

### Phase 3: News & Sentiment Analysis (1.5 hours)

**3.1 Simple News Collection**
- [ ] Create `src/news_sentiment.py` with basic RSS feed parsing
- [ ] Use free sources like Economic Times RSS, Moneycontrol
- [ ] Filter news by portfolio stock symbols
- [ ] Implement basic TextBlob sentiment analysis
- [ ] Store sentiment scores with timestamps

### Phase 4: RAG Engine Implementation (2 hours)

**4.1 Simple Vector Storage**
- [ ] Create `src/rag_engine.py` with ChromaDB setup
- [ ] Implement basic embedding with sentence-transformers
- [ ] Store market data and news as documents
- [ ] Create simple retrieval function

**4.2 Claude API Integration**
- [ ] Set up Anthropic Claude API client
- [ ] Create structured prompt template for stock analysis with RAG context
- [ ] Implement RAG pipeline: retrieve relevant context + send to Claude for analysis
- [ ] Add proper error handling for API rate limits and failures

### Phase 5: Prediction Engine (1.5 hours)

**5.1 Claude-Powered Prediction Logic**
- [ ] Create `src/prediction.py` that sends structured data to Claude:
  - Portfolio holdings with current vs buy price
  - Recent price trends and technical indicators
  - News sentiment analysis results
  - Retrieved RAG context
- [ ] Let Claude analyze and provide Buy/Sell/Hold recommendations
- [ ] Extract structured predictions and rationale from Claude's response

### Phase 6: Email Communication (1 hour)

**6.1 Simple Email Service**
- [ ] Create `src/email_service.py` with SMTP (Gmail or similar)
- [ ] Create simple text email template
- [ ] Include portfolio analysis and recommendations
- [ ] Add basic error handling

### Phase 7: Main CLI Application (30 minutes)

**7.1 Main Orchestrator**
- [ ] Create `main.py` as single entry point
- [ ] Chain all modules: portfolio → data → news → RAG → prediction → email
- [ ] Add basic logging and error handling
- [ ] Create command line interface

### Phase 8: Testing & Documentation (30 minutes)

**8.1 MVP Testing**
- [ ] Create sample `data/portfolio.csv` with 2-3 Indian stocks
- [ ] Test end-to-end workflow
- [ ] Validate email delivery
- [ ] Update CLAUDE.md with run commands

## MVP Technical Architecture

### Simplified Components:
1. **Portfolio Layer**: CSV file reader (`data/portfolio.csv`)
2. **Data Layer**: yfinance for market data + RSS for news
3. **Intelligence Layer**: ChromaDB + Claude API for RAG-powered predictions
4. **Communication Layer**: SMTP email service
5. **Orchestration**: Single `main.py` CLI script

### Key MVP Design Decisions:
- Single user with CSV portfolio file
- CLI-only interface (no web UI)
- APIs: yfinance (free), RSS feeds (free), Claude API (Pro subscription), SMTP email
- Local ChromaDB for vector storage
- Claude API for sophisticated analysis and predictions
- Simple text email notifications
- Minimal dependencies for quick setup

## Estimated MVP Timeline: 8-10 hours total

### Critical Path for MVP:
1. Setup (45min) → Portfolio CSV (1h) → Data APIs (1h) → News (1.5h) → RAG (2h) → Prediction (1.5h) → Email (1h) → Integration (30min) → Testing (30min)

### MVP Success Criteria:
- Reads portfolio from CSV file
- Fetches current market data for portfolio stocks
- Collects and analyzes news sentiment
- Uses RAG to generate stock predictions with rationale
- Sends email with Buy/Sell/Hold recommendations
- Runs as single command: `python main.py`

### Sample Usage:
```bash
# Setup
pip install -r requirements.txt

# Configure APIs in .env
echo "ANTHROPIC_API_KEY=your_claude_api_key" >> .env
echo "EMAIL_USER=your@gmail.com" >> .env
echo "EMAIL_PASS=your_app_password" >> .env  
echo "EMAIL_TO=recipient@gmail.com" >> .env

# Run analysis
python main.py
```

### Sample Portfolio CSV (`data/portfolio.csv`):
```csv
symbol,quantity,buy_price,purchase_date
RELIANCE.NS,10,2450.00,2024-01-15
TCS.NS,5,3680.00,2024-02-01
INFY.NS,8,1520.00,2024-01-20
```

### Benefits of Using Claude API:
- **Superior Analysis**: Claude's advanced reasoning capabilities for complex financial analysis
- **Better RAG Integration**: Sophisticated context understanding and synthesis
- **Structured Output**: Can generate well-formatted recommendations and rationale
- **Financial Knowledge**: Pre-trained on financial data and market concepts
- **Reliability**: Consistent API performance with your Pro subscription

This MVP leverages Claude's advanced capabilities for sophisticated financial analysis while maintaining the simple, single-client architecture. It can be built in a single session and later scaled to support multiple users, web UI, and advanced features.