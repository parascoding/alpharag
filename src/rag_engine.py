import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import logging
import json
import hashlib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

class SimpleRAGEngine:
    def __init__(self):
        self.documents = []
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        self.document_vectors = None
        self.is_fitted = False
    
    def add_document(self, doc_id: str, content: str, metadata: Dict[str, Any]) -> None:
        document = {
            'id': doc_id,
            'content': content,
            'metadata': metadata,
            'timestamp': datetime.now().isoformat()
        }
        
        # Check if document already exists
        existing_doc = next((doc for doc in self.documents if doc['id'] == doc_id), None)
        if existing_doc:
            # Update existing document
            existing_doc.update(document)
            logger.info(f"Updated document: {doc_id}")
        else:
            # Add new document
            self.documents.append(document)
            logger.info(f"Added document: {doc_id}")
        
        # Mark as not fitted since we added/updated documents
        self.is_fitted = False
    
    def add_market_data(self, symbol: str, market_data: Dict, historical_data: Optional[Any] = None) -> None:
        doc_id = f"market_data_{symbol}"
        
        content_parts = [
            f"Stock symbol: {symbol}",
            f"Current price: {market_data.get('prices', {}).get(symbol, 0)}",
            f"Market status: {market_data.get('market_status', 'unknown')}"
        ]
        
        # Add technical analysis if available
        tech_key = f"{symbol}_technical"
        if tech_key in market_data:
            tech_data = market_data[tech_key]
            content_parts.extend([
                f"SMA 5: {tech_data.get('sma_5')}",
                f"SMA 20: {tech_data.get('sma_20')}",
                f"RSI: {tech_data.get('rsi')}",
                f"Volume: {tech_data.get('volume')}",
                f"52-week high: {tech_data.get('high_52w')}",
                f"52-week low: {tech_data.get('low_52w')}"
            ])
        
        content = " ".join(content_parts)
        
        metadata = {
            'type': 'market_data',
            'symbol': symbol,
            'data': market_data
        }
        
        self.add_document(doc_id, content, metadata)
    
    def add_news_sentiment(self, symbol: str, sentiment_data: Dict) -> None:
        doc_id = f"news_sentiment_{symbol}"
        
        content_parts = [
            f"Stock symbol: {symbol}",
            f"Sentiment score: {sentiment_data.get('sentiment_score', 0)}",
            f"Sentiment label: {sentiment_data.get('sentiment_label', 'neutral')}",
            f"Article count: {sentiment_data.get('article_count', 0)}",
            f"Positive articles: {sentiment_data.get('positive_count', 0)}",
            f"Negative articles: {sentiment_data.get('negative_count', 0)}"
        ]
        
        # Add article titles and summaries
        articles = sentiment_data.get('articles', [])
        for i, article in enumerate(articles[:3]):  # Top 3 articles
            content_parts.append(f"Article {i+1}: {article.get('title', '')}")
            content_parts.append(f"Summary {i+1}: {article.get('summary', '')}")
        
        content = " ".join(content_parts)
        
        metadata = {
            'type': 'news_sentiment',
            'symbol': symbol,
            'data': sentiment_data
        }
        
        self.add_document(doc_id, content, metadata)
    
    def add_portfolio_data(self, portfolio_summary: Dict, portfolio_value: Dict) -> None:
        doc_id = "portfolio_overview"
        
        content_parts = [
            f"Total holdings: {portfolio_summary.get('total_holdings', 0)}",
            f"Total investment: {portfolio_summary.get('total_investment', 0)}",
            f"Current portfolio value: {portfolio_value['summary'].get('total_current_value', 0)}",
            f"Total P&L: {portfolio_value['summary'].get('total_pnl', 0)}",
            f"P&L percentage: {portfolio_value['summary'].get('total_pnl_percent', 0)}%"
        ]
        
        # Add individual holding performance
        for holding in portfolio_value.get('holdings', []):
            symbol = holding['symbol']
            content_parts.extend([
                f"{symbol} holding: {holding['quantity']} shares",
                f"{symbol} buy price: {holding['buy_price']}",
                f"{symbol} current price: {holding['current_price']}",
                f"{symbol} P&L: {holding['pnl']} ({holding['pnl_percent']}%)"
            ])
        
        content = " ".join(content_parts)
        
        metadata = {
            'type': 'portfolio_data',
            'data': {
                'summary': portfolio_summary,
                'value': portfolio_value
            }
        }
        
        self.add_document(doc_id, content, metadata)
    
    def build_index(self) -> None:
        if not self.documents:
            logger.warning("No documents to index")
            return
        
        # Extract content for vectorization
        contents = [doc['content'] for doc in self.documents]
        
        # Fit and transform the documents
        self.document_vectors = self.vectorizer.fit_transform(contents)
        self.is_fitted = True
        
        logger.info(f"Built index for {len(self.documents)} documents")
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        if not self.is_fitted or not self.documents:
            logger.warning("Index not built or no documents available")
            return []
        
        # Vectorize the query
        query_vector = self.vectorizer.transform([query])
        
        # Calculate similarities
        similarities = cosine_similarity(query_vector, self.document_vectors).flatten()
        
        # Get top k results
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            if similarities[idx] > 0:  # Only return documents with some similarity
                results.append({
                    'document': self.documents[idx],
                    'similarity_score': float(similarities[idx])
                })
        
        logger.info(f"Found {len(results)} relevant documents for query: {query[:50]}...")
        return results
    
    def get_context_for_symbol(self, symbol: str, include_portfolio: bool = True) -> str:
        context_parts = []
        
        for doc in self.documents:
            if doc['metadata'].get('symbol') == symbol or \
               (include_portfolio and doc['metadata'].get('type') == 'portfolio_data'):
                context_parts.append(f"[{doc['metadata']['type']}] {doc['content']}")
        
        return "\n".join(context_parts)
    
    def get_all_context(self) -> str:
        context_parts = []
        
        for doc in self.documents:
            doc_type = doc['metadata'].get('type', 'unknown')
            context_parts.append(f"[{doc_type}] {doc['content']}")
        
        return "\n".join(context_parts)
    
    def clear_documents(self) -> None:
        self.documents = []
        self.document_vectors = None
        self.is_fitted = False
        logger.info("Cleared all documents from RAG engine")