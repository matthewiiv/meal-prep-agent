"""
Simple Tesco product search using basic product information extraction.
"""

import re
import time
import random
from typing import List, Dict, Any
from urllib.parse import quote_plus
import requests
from bs4 import BeautifulSoup
from langchain_core.tools import tool
from .nutrition_cache import get_cached_nutrition, cache_nutrition


class SimpleTescoScraper:
    """Simple scraper focusing on basic product extraction."""
    
    def __init__(self, extract_nutrition: bool = False):
        self.base_url = "https://www.tesco.com"
        self.extract_nutrition = extract_nutrition
        self.session = requests.Session()
        self._setup_session()
    
    def _setup_session(self):
        """Setup session with realistic headers."""
        # Real browser user agents
        user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1.2 Safari/605.1.15'
        ]
        
        selected_ua = random.choice(user_agents)
        
        self.session.headers.update({
            'User-Agent': selected_ua,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-GB,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def search_products(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for products with long delays."""
        print(f"🔍 Simple search for: '{query}'")
        
        try:
            # Very long delay to appear human-like
            delay = random.uniform(30, 60)
            print(f"⏱️ Waiting {delay:.1f} seconds to appear human-like...")
            time.sleep(delay)
            
            search_url = f"{self.base_url}/groceries/en-GB/search?query={quote_plus(query)}"
            print(f"🌐 Fetching: {search_url}")
            
            response = self.session.get(search_url, timeout=30)
            response.raise_for_status()
            
            print(f"✅ Got response: {response.status_code} ({len(response.text)} chars)")
            
            if len(response.text) < 10000:
                print("⚠️ Minimal response - likely blocked")
                return []
            
            # Extract products using multiple strategies
            products = self._extract_products_robust(response.text, query)
            
            if products:
                print(f"✅ Extracted {len(products)} products")
                
                # Add nutrition data if requested (very cautiously)
                if self.extract_nutrition:
                    products = self._add_nutrition_cautiously(products)
                
                return products[:limit]
            else:
                print("❌ No products extracted")
                return []
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return []
    
    def _extract_products_robust(self, html_content: str, query: str) -> List[Dict[str, Any]]:
        """Extract products using multiple robust strategies."""
        products = []
        
        # Strategy 1: Look for embedded JSON with product data
        products.extend(self._extract_from_json_patterns(html_content))
        
        # Strategy 2: Extract from HTML structure
        if not products:
            products.extend(self._extract_from_html_patterns(html_content))
        
        # Strategy 3: Simple text pattern matching
        if not products:
            products.extend(self._extract_from_text_patterns(html_content, query))
        
        return products
    
    def _extract_from_json_patterns(self, html_content: str) -> List[Dict[str, Any]]:
        """Extract from various JSON patterns in the HTML."""
        products = []
        
        # Common patterns where Tesco embeds product data
        patterns = [
            # Look for any JSON array that might contain products
            r'"title":\s*"([^"]+)"[^}]*"tpnc":\s*"([^"]+)"',
            r'"productName":\s*"([^"]+)"[^}]*"id":\s*"([^"]+)"',
            r'"name":\s*"([^"]+)"[^}]*"productId":\s*"([^"]+)"',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            for match in matches:
                if len(match) >= 2:
                    title, product_id = match[0], match[1]
                    if len(title) > 3 and len(product_id) > 3:
                        products.append(self._create_product_dict(title, product_id))
        
        return products
    
    def _extract_from_html_patterns(self, html_content: str) -> List[Dict[str, Any]]:
        """Extract from HTML structure patterns."""
        products = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Look for links that go to product pages
            product_links = soup.find_all('a', href=re.compile(r'/products/\d+'))
            
            for link in product_links[:20]:  # Limit to prevent issues
                href = link.get('href', '')
                title = link.get_text(strip=True)
                
                # Extract product ID from URL
                product_id_match = re.search(r'/products/(\d+)', href)
                if product_id_match and title and len(title) > 3:
                    product_id = product_id_match.group(1)
                    products.append(self._create_product_dict(title, product_id))
            
        except Exception as e:
            print(f"❌ HTML parsing error: {e}")
        
        return products
    
    def _extract_from_text_patterns(self, html_content: str, query: str) -> List[Dict[str, Any]]:
        """Extract using simple text patterns as last resort."""
        products = []
        
        # Look for Tesco product names in the text
        tesco_patterns = [
            rf'Tesco[^<>"]*{query}[^<>"]*',
            rf'{query.title()}[^<>"]*\d+[gG]\b',
            rf'[A-Z][^<>"]*{query}[^<>"]*[0-9]+[gGkK]',
        ]
        
        for pattern in tesco_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            for i, match in enumerate(matches[:10]):  # Limit matches
                if len(match) > 10:  # Reasonable product name length
                    # Generate a fake but consistent product ID
                    product_id = str(hash(match) % 1000000000)
                    products.append(self._create_product_dict(match.strip(), product_id))
        
        return products
    
    def _create_product_dict(self, title: str, product_id: str) -> Dict[str, Any]:
        """Create a standardized product dictionary."""
        return {
            'name': title,
            'price': 'Price not available',
            'url': f"{self.base_url}/groceries/en-GB/products/{product_id}",
            'image': '',
            'unit_price': '',
            'promotion': '',
            'availability': True,
            'brand': self._extract_brand_from_title(title),
            'nutrition': {},
            'product_id': product_id,
            'tpnc': product_id
        }
    
    def _extract_brand_from_title(self, title: str) -> str:
        """Extract brand from product title."""
        title_lower = title.lower()
        
        if title.startswith('Tesco'):
            if 'finest' in title_lower:
                return 'Tesco Finest'
            elif 'organic' in title_lower:
                return 'Tesco Organic'
            elif 'free range' in title_lower:
                return 'Tesco Free Range'
            else:
                return 'Tesco'
        
        # Extract first word as potential brand
        words = title.split()
        if words:
            return words[0]
        
        return 'Unknown'
    
    def _add_nutrition_cautiously(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Add nutrition data very cautiously to avoid detection."""
        print("🔬 Attempting cautious nutrition extraction...")
        
        # Only try nutrition for a maximum of 2 products to minimize detection risk
        max_nutrition_requests = 2
        nutrition_count = 0
        
        for product in products:
            if nutrition_count >= max_nutrition_requests:
                print(f"⏹️ Stopping nutrition extraction at {max_nutrition_requests} products to avoid detection")
                break
            
            product_url = product.get('url', '')
            product_name = product.get('name', '')
            
            if not product_url or not product_name:
                continue
            
            # Check cache first
            cached_nutrition = get_cached_nutrition(product_url, product_name)
            if cached_nutrition:
                product['nutrition'] = cached_nutrition
                print(f"🎯 Used cached nutrition for: {product_name}")
                continue
            
            # Very cautiously try to get nutrition data
            nutrition = self._get_nutrition_ultra_cautious(product_url, product_name)
            if nutrition:
                product['nutrition'] = nutrition
                nutrition_count += 1
                print(f"✅ Got nutrition for: {product_name}")
                
                # Much longer delay after successful nutrition extraction
                if nutrition_count < max_nutrition_requests:
                    delay = random.uniform(120, 300)  # 2-5 minutes!
                    print(f"⏱️ Extra long delay: {delay:.1f} seconds...")
                    time.sleep(delay)
            else:
                print(f"❌ Failed to get nutrition for: {product_name}")
                # If we fail, stop trying more to avoid escalating detection
                break
        
        return products
    
    def _get_nutrition_ultra_cautious(self, product_url: str, product_name: str) -> Dict[str, str]:
        """Ultra-cautious nutrition extraction with maximum delays."""
        try:
            print(f"🔍 Getting nutrition for: {product_name}")
            
            # Extremely long delay before attempting
            delay = random.uniform(180, 360)  # 3-6 minutes
            print(f"⏱️ Ultra-cautious delay: {delay:.1f} seconds...")
            time.sleep(delay)
            
            # Try to get the product page
            response = self.session.get(product_url, timeout=30)
            
            if response.status_code == 403:
                print("🚫 403 Forbidden - stopping nutrition extraction")
                return {}
            
            if response.status_code != 200:
                print(f"⚠️ Unexpected status: {response.status_code}")
                return {}
            
            if len(response.text) < 10000:
                print("⚠️ Minimal response - likely soft blocked")
                return {}
            
            # Extract nutrition using the same logic as the working scraper
            nutrition_data = self._extract_nutrition_from_html(response.text)
            
            # Cache successful extractions
            if nutrition_data:
                cache_nutrition(product_url, product_name, nutrition_data)
            
            return nutrition_data
            
        except Exception as e:
            print(f"❌ Nutrition extraction error: {e}")
            return {}
    
    def _extract_nutrition_from_html(self, html_content: str) -> Dict[str, str]:
        """Extract nutrition data from product page HTML."""
        nutrition_data = {}
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Look for serving size first using the working approach
            serving_size_element = soup.find('div', class_='ILAuM5ZwahtJKTg')
            if serving_size_element:
                serving_text = serving_size_element.get_text().strip()
                serving_match = re.search(r'(\d+g)', serving_text)
                if serving_match:
                    nutrition_data['serving_size'] = serving_match.group(1)
            
            # Look for nutrition list
            nutrition_list = soup.find('dl', class_=re.compile(r'nutritional-info-list', re.I))
            if nutrition_list:
                nutrition_text = nutrition_list.get_text()
                
                # Extract nutrition values
                energy_match = re.search(r'(\d+\.?\d*)\s*kcal', nutrition_text, re.I)
                if energy_match:
                    nutrition_data['energy'] = f"{energy_match.group(1)}kcal"
                
                fat_match = re.search(r'Fat\s+(\d+\.?\d*)\s*g', nutrition_text, re.I)
                if fat_match:
                    nutrition_data['fat'] = f"{fat_match.group(1)}g"
                
                salt_match = re.search(r'Salt\s+(\d+\.?\d*)\s*g', nutrition_text, re.I)
                if salt_match:
                    nutrition_data['salt'] = f"{salt_match.group(1)}g"
            
            # Look for table data for protein and carbs
            tables = soup.find_all('table')
            for table in tables:
                if 'nutrition' in table.get_text().lower() or 'protein' in table.get_text().lower():
                    table_text = table.get_text()
                    
                    protein_match = re.search(r'Protein\s*(\d+\.?\d*)\s*g', table_text, re.I)
                    if protein_match:
                        nutrition_data['protein'] = f"{protein_match.group(1)}g"
                    
                    carb_match = re.search(r'Carbohydrate\s*(\d+\.?\d*)\s*g', table_text, re.I)
                    if carb_match:
                        nutrition_data['carbs'] = f"{carb_match.group(1)}g"
                    break
            
            # Default serving size if not found
            if nutrition_data and not nutrition_data.get('serving_size'):
                nutrition_data['serving_size'] = "100g"
            
            return nutrition_data
            
        except Exception as e:
            print(f"❌ HTML nutrition parsing error: {e}")
            return {}


@tool
def search_tesco_products_simple(query: str, limit: int = 5, extract_nutrition: bool = False) -> List[Dict[str, Any]]:
    """
    Simple Tesco product search with optional nutrition extraction.
    
    Args:
        query: Search term (e.g., "chicken breast", "rice")
        limit: Maximum number of products to return (default: 5)
        extract_nutrition: Whether to extract nutrition data (default: False, very slow if True)
        
    Returns:
        List of products with basic information and optional nutrition data
    """
    try:
        scraper = SimpleTescoScraper(extract_nutrition=extract_nutrition)
        products = scraper.search_products(query, limit)
        
        if not products:
            return [{"message": f"No products found for '{query}' - search may be temporarily limited"}]
        
        return products
        
    except Exception as e:
        print(f"❌ Error in simple Tesco search: {e}")
        return [{"error": f"Search failed: {str(e)}"}]


if __name__ == "__main__":
    # Test the simple scraper
    print("🧪 Testing Simple Tesco Scraper...")
    
    scraper = SimpleTescoScraper()
    results = scraper.search_products("chicken", 5)
    
    print(f"\\nFound {len(results)} products:")
    for i, product in enumerate(results, 1):
        print(f"{i}. {product['name']}")
        print(f"   Brand: {product['brand']}")
        print(f"   URL: {product['url']}")
        print()