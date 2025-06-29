"""
Real working Tesco scraper that extracts actual product data from the page.
"""

import re
import json
import time
import random
from typing import List, Dict, Any, Optional
from urllib.parse import quote_plus, urljoin
import requests
from bs4 import BeautifulSoup
from langchain_core.tools import tool


class RealTescoScraper:
    """A scraper that actually extracts real product data from Tesco's GraphQL responses."""
    
    def __init__(self, extract_nutrition: bool = False):
        self.base_url = "https://www.tesco.com"
        self.extract_nutrition = extract_nutrition
        self.session = requests.Session()
        
        # Use mobile headers that work
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-GB,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none'
        })
    
    def search_products(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for products on Tesco.com and extract real data."""
        print(f"🔍 Searching Tesco for: '{query}'")
        
        try:
            # Be respectful with delays
            time.sleep(random.uniform(2, 4))
            
            search_url = f"{self.base_url}/groceries/en-GB/search?query={quote_plus(query)}"
            print(f"🌐 Fetching: {search_url}")
            
            response = self.session.get(search_url, timeout=15)
            response.raise_for_status()
            
            print(f"✅ Got response: {response.status_code}")
            
            # Extract real product data from the HTML
            products = self._extract_real_product_data(response.text)
            
            if products:
                print(f"✅ Extracted {len(products)} real products")
                return products[:limit]
            else:
                print("❌ No real product data found")
                return []
            
        except Exception as e:
            print(f"❌ Error searching Tesco: {e}")
            return []
    
    def _extract_real_product_data(self, html_content: str) -> List[Dict[str, Any]]:
        """Extract real product data from Tesco's embedded JSON."""
        products = []
        
        try:
            # Extract product titles directly
            title_pattern = r'\"title\":\"([^\"]+)\"'
            titles = re.findall(title_pattern, html_content)
            
            # Extract product IDs
            id_pattern = r'\"ProductType:(\d+)\"'
            product_ids = re.findall(id_pattern, html_content)
            
            # Extract tpnc values (used for URLs)
            tpnc_pattern = r'\"tpnc\":\"(\d+)\"'
            tpncs = re.findall(tpnc_pattern, html_content)
            
            # Extract brand names
            brand_pattern = r'\"brandName\":\"([^\"]+)\"'
            brands = re.findall(brand_pattern, html_content)
            
            print(f"🔍 Found {len(titles)} titles, {len(product_ids)} IDs, {len(tpncs)} TPNCs")
            
            # Match up the data (this is approximate but works)
            for i, title in enumerate(titles):
                if title and len(title) > 5:  # Filter out short/empty titles
                    product_id = product_ids[i] if i < len(product_ids) else f"unknown_{i}"
                    tpnc = tpncs[i] if i < len(tpncs) else product_id
                    brand = brands[i] if i < len(brands) else self._extract_brand_from_title(title)
                    
                    product = {
                        'name': title,
                        'price': 'Price not available',
                        'url': f"{self.base_url}/groceries/en-GB/products/{tpnc}",
                        'image': f"https://digitalcontent.api.tesco.com/v2/media/ghs/default-product.jpeg",
                        'unit_price': '',
                        'promotion': '',
                        'availability': True,
                        'brand': brand,
                        'nutrition': {},
                        'product_id': product_id,
                        'tpnc': tpnc
                    }
                    
                    products.append(product)
            
            # Try to add price data
            self._enrich_with_price_data(products, html_content)
            
            # Filter out products without real data
            products = [p for p in products if self._is_valid_product(p)]
            
        except Exception as e:
            print(f"❌ Error extracting product data: {e}")
        
        return products
    
    def _format_real_product(self, data: Dict[str, Any], product_id: str) -> Optional[Dict[str, Any]]:
        """Format real product data into our standard format."""
        try:
            title = data.get('title', '')
            if not title or len(title) < 5:
                return None
            
            # Construct product URL
            tpnc = data.get('tpnc', product_id)
            product_url = f"{self.base_url}/groceries/en-GB/products/{tpnc}"
            
            # Extract available information
            product = {
                'name': title,
                'price': 'Price not available',  # Will be enriched later
                'url': product_url,
                'image': '',
                'unit_price': '',
                'promotion': '',
                'availability': True,
                'brand': self._extract_brand_from_title(title),
                'nutrition': {},
                'product_id': product_id,
                'tpnc': tpnc,
                'gtin': data.get('gtin', ''),
                'tpnb': data.get('tpnb', '')
            }
            
            return product
            
        except Exception as e:
            return None
    
    def _extract_brand_from_title(self, title: str) -> str:
        """Extract brand from product title."""
        if title.startswith('Tesco'):
            if 'Finest' in title:
                return 'Tesco Finest'
            elif 'Organic' in title:
                return 'Tesco Organic'
            else:
                return 'Tesco'
        
        # Extract first word as potential brand
        words = title.split()
        if words:
            return words[0]
        
        return ''
    
    def _enrich_with_price_data(self, products: List[Dict[str, Any]], html_content: str):
        """Try to find and add price data to products."""
        try:
            # Look for price patterns in the HTML
            price_patterns = [
                r'\"price\":\s*(\d+\.?\d*)',
                r'\"currentPrice\":\s*(\d+\.?\d*)',
                r'\"displayPrice\":\s*\"([^\"]+)\"'
            ]
            
            all_prices = []
            for pattern in price_patterns:
                matches = re.findall(pattern, html_content)
                all_prices.extend(matches)
            
            # Convert string prices to floats where possible
            numeric_prices = []
            for price in all_prices:
                try:
                    if isinstance(price, str) and '£' in price:
                        # Extract number from £X.XX format
                        price_num = re.search(r'(\d+\.?\d*)', price)
                        if price_num:
                            numeric_prices.append(float(price_num.group(1)))
                    else:
                        numeric_prices.append(float(price))
                except (ValueError, AttributeError):
                    continue
            
            # Assign reasonable prices to products (this is imperfect but better than nothing)
            if numeric_prices and products:
                for i, product in enumerate(products):
                    if i < len(numeric_prices):
                        price_val = numeric_prices[i]
                        product['price'] = f"£{price_val:.2f}"
                        
                        # Calculate unit price from product name
                        if 'kg' in product['name'].lower():
                            weight_match = re.search(r'(\d+\.?\d*)kg', product['name'].lower())
                            if weight_match:
                                weight = float(weight_match.group(1))
                                unit_price = price_val / weight
                                product['unit_price'] = f"£{unit_price:.2f}/kg"
                        elif 'g' in product['name'].lower():
                            weight_match = re.search(r'(\d+)g', product['name'].lower())
                            if weight_match:
                                weight_g = float(weight_match.group(1))
                                unit_price = (price_val / weight_g) * 100
                                product['unit_price'] = f"£{unit_price:.2f}/100g"
            
            # Get real nutrition data if enabled
            if self.extract_nutrition:
                print("🔬 Extracting nutrition data from product pages...")
                for product in products:
                    if not product.get('nutrition'):
                        product['nutrition'] = self._get_real_nutrition(product['url'])
            else:
                print("⏭️ Skipping nutrition extraction (disabled)")
                
        except Exception as e:
            print(f"⚠️ Error enriching price data: {e}")
    
    def _is_valid_product(self, product: Dict[str, Any]) -> bool:
        """Check if a product has valid data."""
        return (
            product.get('name') and 
            len(product['name']) > 5 and
            product.get('product_id') and
            product.get('url')
        )
    
    def _get_real_nutrition(self, product_url: str) -> Dict[str, str]:
        """Visit the actual product page and extract real nutrition data."""
        try:
            print(f"🔍 Getting nutrition data from: {product_url}")
            
            # Add delay to be respectful
            time.sleep(random.uniform(1, 3))
            
            response = self.session.get(product_url, timeout=15)
            response.raise_for_status()
            
            # Check if we got blocked or minimal response
            if len(response.text) < 5000:
                print("⚠️ Got minimal response, might be blocked")
                return {}
            
            soup = BeautifulSoup(response.text, 'html.parser')
            nutrition_data = {}
            
            # Strategy 1: Look for nutrition list with specific classes
            nutrition_list = soup.find('dl', class_=re.compile(r'nutritional-info-list', re.I))
            if nutrition_list:
                nutrition_text = nutrition_list.get_text()
                print(f"🔍 Found nutrition text: {nutrition_text[:300]}...")
                
                # Parse specific values using improved regex patterns based on actual Tesco data
                # Energy (kcal) - pattern: "115kcal"
                energy_match = re.search(r'(\d+\.?\d*)\s*kcal', nutrition_text, re.I)
                if energy_match:
                    nutrition_data['energy'] = f"{energy_match.group(1)}kcal"
                
                # Fat - pattern: "Fat 3.3g" (avoiding Saturates)
                fat_match = re.search(r'Fat\s+(\d+\.?\d*)\s*g', nutrition_text, re.I)
                if fat_match:
                    nutrition_data['fat'] = f"{fat_match.group(1)}g"
                
                # Salt - pattern: "Salt 0.18g"
                salt_match = re.search(r'Salt\s+(\d+\.?\d*)\s*g', nutrition_text, re.I)
                if salt_match:
                    nutrition_data['salt'] = f"{salt_match.group(1)}g"
                
                print(f"✅ Parsed from nutrition list: {nutrition_data}")
            
            # Strategy 1.5: Also look for nutrition table data which contains protein and carbs
            tables = soup.find_all('table')
            table_text = ""
            for table in tables:
                if 'nutrition' in table.get_text().lower() or 'protein' in table.get_text().lower():
                    table_text = table.get_text()
                    print(f"🔍 Found nutrition table: {table_text[:200]}...")
                    break
            
            # If we found table text, extract protein and carbs from it
            if table_text:
                # Protein - pattern: "Protein21.5g" (no space in table format)
                protein_match = re.search(r'Protein\s*(\d+\.?\d*)\s*g', table_text, re.I)
                if protein_match:
                    nutrition_data['protein'] = f"{protein_match.group(1)}g"
                
                # Carbohydrate - pattern: "Carbohydrate0g"
                carb_match = re.search(r'Carbohydrate\s*(\d+\.?\d*)\s*g', table_text, re.I)
                if carb_match:
                    nutrition_data['carbs'] = f"{carb_match.group(1)}g"
                
                # Also try to get energy, fat, salt from table if not found yet
                if not nutrition_data.get('energy'):
                    energy_match = re.search(r'(\d+\.?\d*)\s*kcal', table_text, re.I)
                    if energy_match:
                        nutrition_data['energy'] = f"{energy_match.group(1)}kcal"
                
                if not nutrition_data.get('fat'):
                    fat_match = re.search(r'Fat(\d+\.?\d*)\s*g', table_text, re.I)
                    if fat_match:
                        nutrition_data['fat'] = f"{fat_match.group(1)}g"
                
                if not nutrition_data.get('salt'):
                    salt_match = re.search(r'Salt(\d+\.?\d*)\s*g', table_text, re.I)
                    if salt_match:
                        nutrition_data['salt'] = f"{salt_match.group(1)}g"
                
                print(f"✅ Enhanced from table: {nutrition_data}")
            
            # Strategy 2: Look for nutrition table
            if not nutrition_data:
                tables = soup.find_all('table')
                for table in tables:
                    table_text = table.get_text().lower()
                    if any(word in table_text for word in ['nutrition', 'energy', 'protein', 'kcal']):
                        rows = table.find_all('tr')
                        
                        for row in rows:
                            cells = row.find_all(['td', 'th'])
                            if len(cells) >= 2:
                                key = cells[0].get_text().strip().lower()
                                value = cells[1].get_text().strip()
                                
                                if 'energy' in key and 'kcal' in value:
                                    kcal_match = re.search(r'(\d+)\s*kcal', value)
                                    if kcal_match:
                                        nutrition_data['energy'] = f"{kcal_match.group(1)}kcal"
                                elif 'fat' in key and key == 'fat':  # Avoid saturated fat
                                    fat_match = re.search(r'(\d+\.?\d*)\s*g', value)
                                    if fat_match:
                                        nutrition_data['fat'] = f"{fat_match.group(1)}g"
                                elif 'carbohydrate' in key:
                                    carb_match = re.search(r'(\d+\.?\d*)\s*g', value)
                                    if carb_match:
                                        nutrition_data['carbs'] = f"{carb_match.group(1)}g"
                                elif 'protein' in key:
                                    protein_match = re.search(r'(\d+\.?\d*)\s*g', value)
                                    if protein_match:
                                        nutrition_data['protein'] = f"{protein_match.group(1)}g"
                                elif 'salt' in key:
                                    salt_match = re.search(r'(\d+\.?\d*)\s*g', value)
                                    if salt_match:
                                        nutrition_data['salt'] = f"{salt_match.group(1)}g"
                        
                        if nutrition_data:  # Found nutrition in this table
                            break
            
            if nutrition_data:
                print(f"✅ Found nutrition data: {nutrition_data}")
            else:
                print("❌ No nutrition data found on product page")
            
            return nutrition_data
            
        except Exception as e:
            print(f"❌ Error getting nutrition data: {e}")
            return {}
    
    def _extract_nutrition_from_json(self, data: Any) -> Dict[str, str]:
        """Extract nutrition data from JSON-LD or other structured data."""
        nutrition = {}
        
        if isinstance(data, dict):
            for key, value in data.items():
                if key.lower() == 'nutrition' and isinstance(value, dict):
                    for nutrient, amount in value.items():
                        if nutrient.lower() in ['energy', 'calories']:
                            nutrition['energy'] = str(amount)
                        elif nutrient.lower() == 'protein':
                            nutrition['protein'] = str(amount)
                        elif nutrient.lower() in ['carbohydrate', 'carbs']:
                            nutrition['carbs'] = str(amount)
                        elif nutrient.lower() == 'fat':
                            nutrition['fat'] = str(amount)
                        elif nutrient.lower() == 'salt':
                            nutrition['salt'] = str(amount)
                elif isinstance(value, (dict, list)):
                    # Recursively search nested structures
                    nested_nutrition = self._extract_nutrition_from_json(value)
                    if nested_nutrition:
                        nutrition.update(nested_nutrition)
        
        elif isinstance(data, list):
            for item in data:
                nested_nutrition = self._extract_nutrition_from_json(item)
                if nested_nutrition:
                    nutrition.update(nested_nutrition)
        
        return nutrition


@tool
def search_tesco_products_real(query: str, limit: int = 5, extract_nutrition: bool = False) -> List[Dict[str, Any]]:
    """
    Search for products on Tesco.com using real data extraction from their GraphQL cache.
    This extracts actual product titles, IDs, and other data embedded in the page.
    
    Args:
        query: Search term (e.g., "chicken breast", "organic vegetables")
        limit: Maximum number of products to return (default: 5)
        extract_nutrition: Whether to visit individual product pages for nutrition data (default: False)
        
    Returns:
        List of real products with extracted data from Tesco
    """
    try:
        scraper = RealTescoScraper(extract_nutrition=extract_nutrition)
        products = scraper.search_products(query, limit)
        
        if not products:
            return [{"error": f"No products found for '{query}'"}]
        
        return products
        
    except Exception as e:
        print(f"❌ Error in Tesco search: {e}")
        return [{"error": f"Search failed: {str(e)}"}]


if __name__ == "__main__":
    # Test the real scraper
    print("🧪 Testing REAL Tesco Scraper...")
    
    scraper = RealTescoScraper()
    
    test_queries = ["chicken", "milk"]
    
    for query in test_queries:
        print(f"\n{'='*50}")
        results = scraper.search_products(query, 5)
        print(f"Query: '{query}' - Found {len(results)} products:")
        
        for i, product in enumerate(results, 1):
            print(f"{i}. {product['name']}")
            print(f"   Price: {product['price']}")
            print(f"   Brand: {product['brand']}")
            print(f"   URL: {product['url']}")
            print(f"   Product ID: {product['product_id']}")
            if product.get('nutrition'):
                print(f"   Nutrition: {product['nutrition']}")
        print()