"""
Simple Tesco scraper using requests + BeautifulSoup.
Sometimes simpler is better than complex browser automation.
"""

import re
import time
import random
from typing import List, Dict, Any, Optional
from urllib.parse import quote_plus, urljoin
import requests
from bs4 import BeautifulSoup
from langchain_core.tools import tool


class SimpleTescoScraper:
    """Simple HTTP-based scraper for Tesco.com."""
    
    def __init__(self):
        self.base_url = "https://www.tesco.com"
        self.session = requests.Session()
        
        # Mobile user agent works better
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-GB,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def search_products(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for products on Tesco.com."""
        print(f"🔍 Searching Tesco for: '{query}'")
        
        try:
            # Add delay to be respectful
            time.sleep(random.uniform(1, 3))
            
            search_url = f"{self.base_url}/groceries/en-GB/search?query={quote_plus(query)}"
            print(f"🌐 Fetching: {search_url}")
            
            response = self.session.get(search_url, timeout=10)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract products
            products = self._extract_products_from_html(soup, limit)
            
            print(f"✅ Found {len(products)} products")
            return products
            
        except Exception as e:
            print(f"❌ Error searching Tesco: {e}")
            return []
    
    def _extract_products_from_html(self, soup: BeautifulSoup, limit: int) -> List[Dict[str, Any]]:
        """Extract product data from HTML soup."""
        products = []
        
        # Look for script tags containing product data (common in SPAs)
        scripts = soup.find_all('script', type='application/json')
        
        for script in scripts:
            try:
                import json
                data = json.loads(script.string)
                
                # Look for products in the JSON data
                products_found = self._extract_from_json(data)
                if products_found:
                    products.extend(products_found)
                    if len(products) >= limit:
                        break
                        
            except (json.JSONDecodeError, AttributeError):
                continue
        
        # If no JSON data found, try HTML parsing
        if not products:
            print("🔄 No JSON data found, trying HTML parsing...")
            products = self._extract_from_html_elements(soup, limit)
        
        return products[:limit]
    
    def _extract_from_json(self, data, products=None) -> List[Dict[str, Any]]:
        """Recursively search JSON data for product information."""
        if products is None:
            products = []
        
        if isinstance(data, dict):
            # Look for product-like structures
            if all(key in data for key in ['id', 'name']) or \
               all(key in data for key in ['title', 'price']):
                
                product = {
                    'name': data.get('name') or data.get('title', 'Unknown Product'),
                    'price': self._extract_price(data),
                    'url': self._extract_url(data),
                    'image': data.get('image', ''),
                    'unit_price': data.get('unitPrice', ''),
                    'promotion': data.get('promotion', ''),
                    'availability': True
                }
                
                if product['name'] != 'Unknown Product':
                    products.append(product)
            
            # Recursively search nested objects
            for value in data.values():
                if isinstance(value, (dict, list)):
                    self._extract_from_json(value, products)
        
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, (dict, list)):
                    self._extract_from_json(item, products)
        
        return products
    
    def _extract_from_html_elements(self, soup: BeautifulSoup, limit: int) -> List[Dict[str, Any]]:
        """Extract products from HTML elements as fallback."""
        products = []
        
        # Try multiple selectors
        selectors = [
            '[data-auto*="product"]',
            '.product',
            'article',
            'li[data-auto]',
            'div[class*="product"]'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                print(f"🎯 Found {len(elements)} elements with selector: {selector}")
                
                for element in elements[:limit]:
                    product = self._extract_product_from_element(element)
                    if product and product.get('name'):
                        products.append(product)
                        if len(products) >= limit:
                            break
                break
        
        return products
    
    def _extract_product_from_element(self, element) -> Dict[str, Any]:
        """Extract product data from an HTML element."""
        product = {}
        
        # Extract name
        name_selectors = ['h3', 'h2', '[data-auto*="title"]', 'a[title]', '.title']
        name = ""
        for selector in name_selectors:
            elem = element.select_one(selector)
            if elem:
                name = elem.get_text(strip=True) or elem.get('title', '')
                if name:
                    break
        
        product['name'] = name or "Unknown Product"
        
        # Extract price
        price_selectors = ['[data-auto*="price"]', '.price', '[class*="price"]']
        price = ""
        for selector in price_selectors:
            elem = element.select_one(selector)
            if elem:
                price = elem.get_text(strip=True)
                if price and ('£' in price or any(c.isdigit() for c in price)):
                    break
        
        product['price'] = price or "Price not available"
        
        # Extract URL
        link = element.select_one('a[href]')
        if link:
            href = link.get('href', '')
            if href.startswith('/'):
                product['url'] = urljoin(self.base_url, href)
            else:
                product['url'] = href
        else:
            product['url'] = ""
        
        # Extract image
        img = element.select_one('img')
        if img:
            src = img.get('src') or img.get('data-src', '')
            product['image'] = urljoin(self.base_url, src) if src.startswith('/') else src
        else:
            product['image'] = ""
        
        product['unit_price'] = ""
        product['promotion'] = ""
        product['availability'] = True
        
        return product
    
    def _extract_price(self, data: dict) -> str:
        """Extract price from various data structures."""
        price_keys = ['price', 'currentPrice', 'displayPrice', 'cost']
        
        for key in price_keys:
            if key in data:
                price = data[key]
                if isinstance(price, (str, int, float)):
                    return str(price)
                elif isinstance(price, dict) and 'value' in price:
                    return str(price['value'])
        
        return "Price not available"
    
    def _extract_url(self, data: dict) -> str:
        """Extract URL from data."""
        url_keys = ['url', 'link', 'href', 'productUrl']
        
        for key in url_keys:
            if key in data:
                url = data[key]
                if isinstance(url, str):
                    if url.startswith('/'):
                        return urljoin(self.base_url, url)
                    return url
        
        return ""


@tool
def search_tesco_products_simple(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Search for products on Tesco.com using simple HTTP requests.
    This is more reliable than browser automation for basic scraping.
    
    Args:
        query: Search term (e.g., "chicken breast", "organic vegetables")
        limit: Maximum number of products to return (default: 5)
        
    Returns:
        List of products with name, price, URL, and basic info
    """
    try:
        scraper = SimpleTescoScraper()
        products = scraper.search_products(query, limit)
        
        if not products:
            return [{"error": f"No products found for '{query}'"}]
        
        return products
        
    except Exception as e:
        print(f"❌ Error in Tesco search: {e}")
        return [{"error": f"Search failed: {str(e)}"}]


if __name__ == "__main__":
    # Test the simple scraper
    print("🧪 Testing Simple Tesco Scraper...")
    
    scraper = SimpleTescoScraper()
    
    # Test search
    results = scraper.search_products("milk", 3)
    print(f"\nSearch Results ({len(results)} products):")
    
    for i, product in enumerate(results, 1):
        print(f"{i}. {product['name']}")
        print(f"   Price: {product['price']}")
        print(f"   URL: {product['url']}")
        print()