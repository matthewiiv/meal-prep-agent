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
from .nutrition_cache import get_cached_nutrition, cache_nutrition


class RealTescoScraper:
    """A scraper that actually extracts real product data from Tesco's GraphQL responses."""
    
    def __init__(self, extract_nutrition: bool = False):
        self.base_url = "https://www.tesco.com"
        self.extract_nutrition = extract_nutrition
        self.session = requests.Session()
        self._setup_session()
    
    def _setup_session(self):
        """Setup session with realistic browser characteristics."""
        # Use more realistic browser headers to avoid detection
        user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/120.0'
        ]
        
        import random
        selected_ua = random.choice(user_agents)
        
        self.session.headers.update({
            'User-Agent': selected_ua,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-GB,en;q=0.9,en-US;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'DNT': '1'
        })
        
        # Initialize session by visiting homepage first
        try:
            print("🌐 Initializing session with Tesco homepage...")
            homepage_response = self.session.get(self.base_url, timeout=15)
            if homepage_response.status_code == 200:
                print("✅ Session initialized successfully")
            else:
                print(f"⚠️ Homepage returned status: {homepage_response.status_code}")
        except Exception as e:
            print(f"⚠️ Failed to initialize session: {e}")
    
    def search_products(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for products on Tesco.com and extract real data."""
        print(f"🔍 Searching Tesco for: '{query}'")
        
        try:
            # Much longer delays to avoid pattern detection
            time.sleep(random.uniform(10, 20))
            
            search_url = f"{self.base_url}/groceries/en-GB/search?query={quote_plus(query)}"
            print(f"🌐 Fetching: {search_url}")
            
            # Add referrer and additional anti-detection measures
            headers = {
                'Referer': 'https://www.tesco.com/',
                'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"macOS"'
            }
            
            response = self.session.get(search_url, timeout=20, headers=headers)
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
                        nutrition = self._get_real_nutrition_with_name(product['url'], product['name'])
                        product['nutrition'] = nutrition
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
    
    def _get_real_nutrition_with_name(self, product_url: str, product_name: str) -> Dict[str, str]:
        """Get nutrition data with proper product name for caching."""
        
        # Check cache first
        cached_nutrition = get_cached_nutrition(product_url, product_name)
        if cached_nutrition:
            return cached_nutrition
        
        # Extract nutrition and cache with proper name
        nutrition_data = self._get_real_nutrition_raw(product_url)
        
        if nutrition_data:
            cache_nutrition(product_url, product_name, nutrition_data)
        
        return nutrition_data
    
    def _get_real_nutrition(self, product_url: str) -> Dict[str, str]:
        """Backward compatibility method."""
        return self._get_real_nutrition_with_name(product_url, "")
    
    def _get_real_nutrition_raw(self, product_url: str) -> Dict[str, str]:
        """Visit the actual product page and extract real nutrition data (no caching)."""
        
        try:
            print(f"🔍 Getting nutrition data from: {product_url}")
            
            # Much longer delay for nutrition pages
            time.sleep(random.uniform(15, 30))
            
            # Add referrer for product pages too
            headers = {
                'Referer': 'https://www.tesco.com/groceries/en-GB/search',
                'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"macOS"'
            }
            
            response = self.session.get(product_url, timeout=20, headers=headers)
            response.raise_for_status()
            
            # Check if we got blocked or minimal response
            if len(response.text) < 5000:
                print("⚠️ Got minimal response, might be blocked")
                return {}
            
            # Check for 403 Forbidden or other blocking indicators
            if "Access Denied" in response.text or "blocked" in response.text.lower():
                print("🚫 Access denied or blocked by Tesco")
                # Save a sample of the response for debugging
                with open("debug_blocked_response.html", "w") as f:
                    f.write(response.text[:5000])
                print("💾 Saved blocked response sample for debugging")
                return {}
            
            if response.status_code == 403:
                print("🚫 403 Forbidden - temporarily blocked by Tesco")
                return {}
            
            
            soup = BeautifulSoup(response.text, 'html.parser')
            nutrition_data = {}
            
            # Strategy 1: Extract serving size from specific HTML elements (more reliable than regex)
            # Primary method: Look for the Guideline Daily Amounts serving size display
            serving_size_element = soup.find('div', class_='ILAuM5ZwahtJKTg')
            if serving_size_element:
                serving_text = serving_size_element.get_text().strip()
                print(f"🎯 Found serving size element: '{serving_text}'")
                # Extract just the size part (e.g., "Per 125g" -> "125g")
                serving_match = re.search(r'(\d+g)', serving_text)
                if serving_match:
                    nutrition_data['serving_size'] = serving_match.group(1)
                    print(f"📏 Extracted serving size: {serving_match.group(1)}")
            
            # Strategy 2: Look for nutrition list with specific classes for nutrition values
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
                # Fallback: Extract serving size from table headers if not already found
                if not nutrition_data.get('serving_size'):
                    # Look for nutrition table with proper structure
                    nutrition_table = soup.find('table', class_=re.compile(r'product__info-table|RNEGJ486p9x6dl0', re.I))
                    if nutrition_table:
                        # Get the third column header (actual serving size, not 100g reference)
                        headers = nutrition_table.find('thead')
                        if headers:
                            th_elements = headers.find_all('th')
                            if len(th_elements) >= 3:
                                third_header = th_elements[2].get_text().strip()
                                print(f"🔍 Found table header: '{third_header}'")
                                serving_match = re.search(r'(\d+g)', third_header)
                                if serving_match:
                                    nutrition_data['serving_size'] = serving_match.group(1)
                                    print(f"📏 Extracted serving size from table header: {serving_match.group(1)}")
                    
                    # Final fallback if still no serving size found
                    if not nutrition_data.get('serving_size'):
                        nutrition_data['serving_size'] = "100g"
                        print(f"📏 No serving size found, defaulting to: 100g")
                
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
            
            # If we still don't have serving size but have nutrition data, default to 100g
            if nutrition_data and not nutrition_data.get('serving_size'):
                nutrition_data['serving_size'] = "100g"
                print(f"📏 Adding default serving size: 100g")
            
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