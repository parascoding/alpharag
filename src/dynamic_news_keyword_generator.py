"""
Dynamic News Keyword Generator for creating intelligent news search keywords
from company information without static mappings
"""

import re
import logging
from typing import Dict, List, Set, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class CompanyKeywords:
    """Container for company-specific keywords"""
    symbol: str
    primary_keywords: List[str]
    secondary_keywords: List[str]
    industry_keywords: List[str]
    all_keywords: List[str]

class DynamicNewsKeywordGenerator:
    """
    Generates intelligent news search keywords from company information
    """

    def __init__(self):
        # Common business terms to filter out
        self.stop_words = {
            'limited', 'ltd', 'pvt', 'private', 'public', 'company', 'corp',
            'corporation', 'inc', 'incorporated', 'enterprises', 'group',
            'holdings', 'international', 'india', 'indian', 'co', 'and',
            'the', 'of', 'for', 'in', 'at', 'to', 'a', 'an'
        }

        # Industry-specific keyword mappings
        self.industry_keywords = {
            'bank': ['banking', 'financial services', 'loans', 'deposits', 'credit', 'finance'],
            'finance': ['banking', 'financial services', 'loans', 'credit', 'investment'],
            'tech': ['technology', 'software', 'it services', 'digital', 'tech'],
            'pharma': ['pharmaceutical', 'drugs', 'medicine', 'healthcare', 'biotech'],
            'auto': ['automotive', 'automobile', 'vehicles', 'cars', 'mobility'],
            'oil': ['petroleum', 'energy', 'gas', 'fuel', 'refinery'],
            'steel': ['metals', 'iron', 'manufacturing', 'industrial'],
            'cement': ['construction', 'building materials', 'infrastructure'],
            'telecom': ['telecommunications', 'mobile', 'network', 'communication'],
            'fmcg': ['consumer goods', 'retail', 'brands', 'products']
        }

        # Common abbreviation patterns
        self.abbreviation_patterns = {
            'BANK': ['BNK', 'BANKING'],
            'FINANCE': ['FIN', 'FINANCIAL'],
            'TECH': ['TECHNOLOGY', 'IT'],
            'AUTO': ['AUTOMOBILE', 'AUTOMOTIVE'],
            'PHARMA': ['PHARMACEUTICAL'],
            'INFRA': ['INFRASTRUCTURE'],
            'POWER': ['ENERGY', 'ELECTRICITY'],
            'STEEL': ['METALS', 'IRON']
        }

    def generate_keywords_from_company_info(self, company_info: Dict) -> CompanyKeywords:
        """
        Generate comprehensive keywords from company information
        """
        symbol = company_info.get('symbol', '')
        trading_symbol = company_info.get('trading_symbol', '')
        company_name = company_info.get('company_name', '')

        # Extract different types of keywords
        primary_keywords = self._extract_primary_keywords(symbol, trading_symbol, company_name)
        secondary_keywords = self._extract_secondary_keywords(company_name)
        industry_keywords = self._extract_industry_keywords(company_name, trading_symbol)

        # Combine all keywords and remove duplicates
        all_keywords = list(dict.fromkeys(primary_keywords + secondary_keywords + industry_keywords))

        return CompanyKeywords(
            symbol=symbol,
            primary_keywords=primary_keywords,
            secondary_keywords=secondary_keywords,
            industry_keywords=industry_keywords,
            all_keywords=all_keywords
        )

    def _extract_primary_keywords(self, symbol: str, trading_symbol: str, company_name: str) -> List[str]:
        """
        Extract primary keywords (symbol variations and main company identifiers)
        """
        keywords = []

        # Add symbol variations
        base_symbol = symbol.replace('.NS', '').replace('.BO', '')
        keywords.append(base_symbol.lower())

        if trading_symbol and trading_symbol != base_symbol:
            keywords.append(trading_symbol.lower())

        # Extract main company identifier (first significant word)
        if company_name:
            # Remove common prefixes/suffixes and split
            clean_name = self._clean_company_name(company_name)
            words = clean_name.split()

            if words:
                # Add first significant word as primary keyword
                first_word = words[0].lower()
                if len(first_word) > 2 and first_word not in self.stop_words:
                    keywords.append(first_word)

                # If company has multiple words, try combinations
                if len(words) > 1:
                    # Add first two words combined
                    two_word_combo = f"{words[0]} {words[1]}".lower()
                    keywords.append(two_word_combo)

        return keywords

    def _extract_secondary_keywords(self, company_name: str) -> List[str]:
        """
        Extract secondary keywords from company name analysis
        """
        keywords = []

        if not company_name:
            return keywords

        # Clean and split company name
        clean_name = self._clean_company_name(company_name)
        words = [word.lower() for word in clean_name.split() if len(word) > 2 and word.lower() not in self.stop_words]

        # Add significant words from company name
        for word in words:
            if len(word) >= 3:
                keywords.append(word)

        # Add abbreviations and variations
        for word in words:
            if word.upper() in self.abbreviation_patterns:
                keywords.extend([abbr.lower() for abbr in self.abbreviation_patterns[word.upper()]])

        # Look for compound words and split them
        for word in words:
            if len(word) > 6:
                # Try to split CamelCase or compound words
                split_words = re.findall(r'[A-Z][a-z]+|[a-z]+', word)
                if len(split_words) > 1:
                    keywords.extend([sw.lower() for sw in split_words if len(sw) > 2])

        return keywords

    def _extract_industry_keywords(self, company_name: str, trading_symbol: str) -> List[str]:
        """
        Extract industry-specific keywords
        """
        keywords = []

        # Combine name and symbol for analysis
        text_to_analyze = f"{company_name} {trading_symbol}".lower()

        # Match against industry patterns
        for industry_key, related_keywords in self.industry_keywords.items():
            if industry_key in text_to_analyze:
                keywords.extend(related_keywords)

        # Special patterns for Indian companies
        indian_patterns = {
            'bank': ['banking', 'financial services', 'loans', 'deposits'],
            'finance': ['financial services', 'loans', 'credit', 'investment'],
            'technologies': ['tech', 'software', 'it services'],
            'systems': ['tech', 'software', 'systems'],
            'solutions': ['tech', 'software', 'solutions'],
            'services': ['services', 'consulting'],
            'industries': ['manufacturing', 'industrial'],
            'motors': ['automotive', 'automobile', 'vehicles'],
            'power': ['energy', 'electricity', 'power'],
            'steel': ['metals', 'steel', 'manufacturing'],
            'cement': ['construction', 'building materials'],
            'pharma': ['pharmaceutical', 'healthcare', 'medicines'],
            'chemicals': ['chemical', 'petrochemical'],
            'textiles': ['textile', 'fabric', 'clothing']
        }

        for pattern, related_keywords in indian_patterns.items():
            if pattern in text_to_analyze:
                keywords.extend(related_keywords)

        return keywords

    def _clean_company_name(self, company_name: str) -> str:
        """
        Clean company name by removing common suffixes and formatting
        """
        if not company_name:
            return ""

        # Remove common company suffixes
        suffixes = [
            ' limited', ' ltd', ' pvt ltd', ' private limited',
            ' corporation', ' corp', ' inc', ' incorporated',
            ' company', ' co', ' enterprises', ' group',
            ' holdings', ' international', ' india'
        ]

        clean_name = company_name.lower()
        for suffix in suffixes:
            if clean_name.endswith(suffix):
                clean_name = clean_name[:-len(suffix)]

        # Remove special characters and extra spaces
        clean_name = re.sub(r'[^\w\s]', ' ', clean_name)
        clean_name = re.sub(r'\s+', ' ', clean_name).strip()

        return clean_name.title()

    def bulk_generate_keywords(self, companies_info: Dict[str, Dict]) -> Dict[str, CompanyKeywords]:
        """
        Generate keywords for multiple companies
        """
        keywords_map = {}

        for symbol, company_info in companies_info.items():
            try:
                keywords = self.generate_keywords_from_company_info(company_info)
                keywords_map[symbol] = keywords
                logger.debug(f"Generated {len(keywords.all_keywords)} keywords for {symbol}")
            except Exception as e:
                logger.error(f"Error generating keywords for {symbol}: {e}")
                # Create fallback keywords
                keywords_map[symbol] = CompanyKeywords(
                    symbol=symbol,
                    primary_keywords=[symbol.replace('.NS', '').replace('.BO', '').lower()],
                    secondary_keywords=[],
                    industry_keywords=[],
                    all_keywords=[symbol.replace('.NS', '').replace('.BO', '').lower()]
                )

        return keywords_map

    def get_keyword_summary(self, keywords_map: Dict[str, CompanyKeywords]) -> Dict:
        """
        Get summary statistics of generated keywords
        """
        total_companies = len(keywords_map)
        total_keywords = sum(len(kw.all_keywords) for kw in keywords_map.values())
        avg_keywords = total_keywords / total_companies if total_companies > 0 else 0

        # Get most common keywords
        all_keywords_flat = []
        for kw in keywords_map.values():
            all_keywords_flat.extend(kw.all_keywords)

        from collections import Counter
        most_common = Counter(all_keywords_flat).most_common(10)

        return {
            'total_companies': total_companies,
            'total_keywords': total_keywords,
            'average_keywords_per_company': round(avg_keywords, 2),
            'most_common_keywords': most_common,
            'companies_processed': list(keywords_map.keys())
        }