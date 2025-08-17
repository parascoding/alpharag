#!/usr/bin/env python3
"""
Script to show all news articles fetched from RSS feeds
"""
import sys
sys.path.append('.')

from src.news_sentiment import NewsSentimentAnalyzer
from config.settings import settings
from datetime import datetime

def main():
    print('📰 DETAILED NEWS ARTICLES REPORT')
    print('=' * 60)

    analyzer = NewsSentimentAnalyzer(settings.RSS_FEEDS)

    print(f'🕐 Report generated at: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print(f'📡 RSS Feeds configured: {len(settings.RSS_FEEDS)}')

    for i, feed_url in enumerate(settings.RSS_FEEDS, 1):
        print(f'  {i}. {feed_url}')

    print('\n' + '='*60)

    total_articles = 0
    portfolio_matches = 0

    # Fetch articles from each RSS feed
    for i, feed_url in enumerate(settings.RSS_FEEDS, 1):
        print(f'\n📡 FEED #{i}')
        print(f'URL: {feed_url}')
        print('-' * 80)

        try:
            articles = analyzer._fetch_rss_feed(feed_url, 24)
            total_articles += len(articles)
            print(f'✅ Successfully fetched {len(articles)} articles')

            if articles:
                print('\n📄 ARTICLES:')
                for j, article in enumerate(articles, 1):
                    title = article.get('title', 'No title')
                    summary = article.get('summary', '')
                    link = article.get('link', 'No link')
                    published = article.get('published', 'Unknown date')
                    source = article.get('source', 'Unknown source')

                    print(f'\n[{j:2d}] {title}')
                    print(f'     📅 {published}')
                    print(f'     🏢 {source}')
                    print(f'     🔗 {link[:80]}...' if len(link) > 80 else f'     🔗 {link}')

                    if summary and len(summary.strip()) > 0:
                        if len(summary) > 200:
                            summary_display = summary[:200] + '...'
                        else:
                            summary_display = summary
                        print(f'     📝 {summary_display}')

                    # Check portfolio matches
                    text_to_check = (title + ' ' + summary).lower()
                    matches = []

                    # Check for Reliance keywords
                    reliance_keywords = ['reliance', 'ril', 'ambani', 'jio', 'mukesh ambani']
                    if any(keyword in text_to_check for keyword in reliance_keywords):
                        matches.append('RELIANCE.NS')

                    # Check for TCS/Tata keywords
                    tcs_keywords = ['tcs', 'tata consultancy', 'tata group', 'tata']
                    if any(keyword in text_to_check for keyword in tcs_keywords):
                        matches.append('TCS.NS')

                    # Check for Infosys keywords
                    infosys_keywords = ['infosys', 'infy', 'narayana murthy']
                    if any(keyword in text_to_check for keyword in infosys_keywords):
                        matches.append('INFY.NS')

                    if matches:
                        print(f'     🎯 PORTFOLIO MATCHES: {", ".join(matches)}')
                        portfolio_matches += 1
                    else:
                        print(f'     ⚪ No portfolio matches')
            else:
                print('❌ No articles found from this feed')

        except Exception as e:
            print(f'❌ ERROR fetching from feed: {str(e)}')

    print('\n' + '='*60)
    print('📊 SUMMARY')
    print('='*60)
    print(f'📰 Total articles fetched: {total_articles}')
    print(f'🎯 Portfolio-relevant articles: {portfolio_matches}')
    if total_articles > 0:
        relevance_rate = (portfolio_matches/total_articles*100)
        print(f'📈 Relevance rate: {relevance_rate:.1f}%')
    else:
        print(f'📈 Relevance rate: N/A')

    print('\n✅ Complete articles report generated!')

if __name__ == "__main__":
    main()