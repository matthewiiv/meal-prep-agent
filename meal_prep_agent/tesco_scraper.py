"""
Advanced Tesco web scraper using Playwright.
Handles JavaScript-heavy sites much better than Beautiful Soup.
"""

import re
import json
import time
import random
from typing import List, Dict, Any, Optional
from urllib.parse import quote_plus, urljoin
from playwright.sync_api import sync_playwright, Page, Browser
from langchain_core.tools import tool


class TescoScraper:
    """Advanced scraper for Tesco.com using Playwright."""
    
    def __init__(self, headless: bool = True):
        self.base_url = "https://www.tesco.com"
        self.headless = headless
    
    def search_products(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for products on Tesco.com.
        
        Args:
            query: Search term (e.g., "chicken breast")
            limit: Maximum number of products to return
            
        Returns:
            List of product dictionaries
        """
        print(f"🔍 Searching Tesco for: '{query}'")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=self.headless,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-extensions'
                ]
            )
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080},
                extra_http_headers={
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-GB,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                }
            )
            
            # Add stealth settings
            context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
            """)
            
            try:
                page = context.new_page()
                
                # Navigate to Tesco search
                search_url = f"{self.base_url}/groceries/en-GB/search?query={quote_plus(query)}"
                print(f"🌐 Navigating to: {search_url}")
                
                page.goto(search_url, wait_until='domcontentloaded', timeout=15000)
                
                # Wait for products to load
                print("⏳ Waiting for products to load...")
                try:
                    page.wait_for_selector('[data-auto="product-tile"]', timeout=5000)
                except:
                    # Try alternative selectors
                    try:
                        page.wait_for_selector('.product-tile', timeout=5000)
                    except:
                        try:
                            page.wait_for_selector('[data-testid="product-tile"]', timeout=5000)
                        except:
                            print("⚠️ Could not find standard product selectors, proceeding anyway...")
                
                # Extract products
                products = self._extract_search_results(page, limit)
                
                print(f"✅ Found {len(products)} products")
                return products
                
            except Exception as e:
                print(f"❌ Error searching Tesco: {e}")
                return []
            finally:
                browser.close()
    
    def get_product_details(self, product_url: str) -> Dict[str, Any]:
        """
        Get detailed information for a specific product.
        
        Args:
            product_url: Tesco product URL
            
        Returns:
            Detailed product information
        """
        print(f"🔍 Getting details for: {product_url}")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            )
            
            try:
                page = context.new_page()
                page.goto(product_url, wait_until='domcontentloaded', timeout=15000)
                
                # Wait for product details to load
                page.wait_for_selector('h1', timeout=10000)
                
                return self._extract_product_details(page, product_url)
                
            except Exception as e:
                print(f"❌ Error getting product details: {e}")
                return {"error": str(e)}
            finally:
                browser.close()
    
    def _extract_search_results(self, page: Page, limit: int) -> List[Dict[str, Any]]:
        """Extract product information from search results page."""
        products = []
        
        # Look for product tiles - updated selectors for modern Tesco
        product_selectors = [
            '[data-auto="product-tile"]',
            '.product-tile',
            '[data-testid="product-tile"]', 
            '.product-list-item',
            '.product-details-tile',
            '[data-testid="product-tile-wrapper"]',
            '.product-item',
            'li[data-auto]',
            'article',
            'div[class*="product"]'
        ]
        
        product_elements = None
        for selector in product_selectors:
            try:
                product_elements = page.locator(selector).all()
                if product_elements:
                    print(f"🎯 Found {len(product_elements)} products using selector: {selector}")
                    break
            except:
                continue
        
        if not product_elements:
            print("❌ No product elements found")
            # Debug: print page content to understand structure
            try:
                page_content = page.content()
                print("🔍 Debugging: Looking for any divs with 'product' in class...")
                # Look for any element that might contain products
                all_product_divs = page.locator('div').all()
                found_count = 0
                for div in all_product_divs[:10]:  # Check first 10 divs
                    try:
                        class_attr = div.get_attribute('class') or ""
                        if 'product' in class_attr.lower():
                            print(f"   Found div with class: {class_attr}")
                            found_count += 1
                    except:
                        pass
                
                if found_count == 0:
                    print("   No divs with 'product' in class found")
                    
            except Exception as debug_e:
                print(f"Debug error: {debug_e}")
            
            return []
        
        for i, element in enumerate(product_elements[:limit]):
            try:
                product = self._extract_product_from_element(element, page)
                if product and product.get('name'):
                    products.append(product)
            except Exception as e:
                print(f"⚠️ Error extracting product {i}: {e}")
                continue
        
        return products
    
    def _extract_product_from_element(self, element, page: Page) -> Dict[str, Any]:
        """Extract product data from a single product element."""
        product = {}
        
        try:
            # Extract product name
            name_selectors = [
                '[data-auto="product-tile-title"]',
                'h3',
                'h2',
                '.product-title',
                'a[data-auto="product-tile-title"]'
            ]
            
            name = ""
            for selector in name_selectors:
                try:
                    name_elem = element.locator(selector).first
                    if name_elem.is_visible():
                        name = name_elem.inner_text().strip()
                        if name:
                            break
                except:
                    continue
            
            product['name'] = name or "Unknown Product"
            
            # Extract price
            price_selectors = [
                '[data-auto="price-current-value"]',
                '.price-current-value',
                '.price',
                '.current-price'
            ]
            
            price = ""
            for selector in price_selectors:
                try:
                    price_elem = element.locator(selector).first
                    if price_elem.is_visible():
                        price = price_elem.inner_text().strip()
                        if price:
                            break
                except:
                    continue
            
            product['price'] = price or "Price not available"
            
            # Extract product URL
            try:
                link_elem = element.locator('a').first
                if link_elem:
                    href = link_elem.get_attribute('href')
                    if href:
                        if href.startswith('/'):
                            product['url'] = urljoin(self.base_url, href)
                        else:
                            product['url'] = href
                    else:
                        product['url'] = ""
                else:
                    product['url'] = ""
            except:
                product['url'] = ""
            
            # Extract image
            try:
                img_elem = element.locator('img').first
                if img_elem:
                    img_src = img_elem.get_attribute('src') or img_elem.get_attribute('data-src')
                    if img_src:
                        product['image'] = urljoin(self.base_url, img_src) if img_src.startswith('/') else img_src
                    else:
                        product['image'] = ""
                else:
                    product['image'] = ""
            except:
                product['image'] = ""
            
            # Extract unit price
            unit_price_selectors = [
                '.price-per-unit',
                '[data-auto="price-per-unit"]',
                '.unit-price'
            ]
            
            unit_price = ""
            for selector in unit_price_selectors:
                try:
                    unit_elem = element.locator(selector).first
                    if unit_elem.is_visible():
                        unit_price = unit_elem.inner_text().strip()
                        if unit_price:
                            break
                except:
                    continue
            
            product['unit_price'] = unit_price
            
            # Extract promotional info
            promo_selectors = [
                '.promotion',
                '.offer',
                '.badge',
                '[data-auto="promotion-badge"]'
            ]
            
            promotion = ""
            for selector in promo_selectors:
                try:
                    promo_elem = element.locator(selector).first
                    if promo_elem.is_visible():
                        promotion = promo_elem.inner_text().strip()
                        if promotion:
                            break
                except:
                    continue
            
            product['promotion'] = promotion
            product['availability'] = True  # Assume available unless indicated otherwise
            
            return product
            
        except Exception as e:
            print(f"Error extracting product data: {e}")
            return {}
    
    def _extract_product_details(self, page: Page, url: str) -> Dict[str, Any]:
        """Extract detailed product information from product page."""
        product = {
            'url': url,
            'name': '',
            'price': '',
            'brand': '',
            'description': '',
            'ingredients': '',
            'nutrition': {},
            'allergens': '',
            'storage': '',
            'unit_price': '',
            'pack_size': '',
            'image': '',
            'availability': True
        }
        
        try:
            # Extract product name
            name_selectors = ['h1', '[data-auto="pdp-product-title"]', '.product-title']
            for selector in name_selectors:
                try:
                    elem = page.locator(selector).first
                    if elem.is_visible():
                        product['name'] = elem.inner_text().strip()
                        break
                except:
                    continue
            
            # Extract price
            price_selectors = [
                '[data-auto="price-current-value"]',
                '.price-current-value',
                '.price',
                '.current-price'
            ]
            for selector in price_selectors:
                try:
                    elem = page.locator(selector).first
                    if elem.is_visible():
                        product['price'] = elem.inner_text().strip()
                        break
                except:
                    continue
            
            # Extract brand
            brand_selectors = ['.brand', '[data-auto="brand"]', '.product-brand']
            for selector in brand_selectors:
                try:
                    elem = page.locator(selector).first
                    if elem.is_visible():
                        product['brand'] = elem.inner_text().strip()
                        break
                except:
                    continue
            
            # Extract description
            desc_selectors = [
                '.product-description',
                '[data-auto="product-description"]',
                '.product-marketing-text'
            ]
            for selector in desc_selectors:
                try:
                    elem = page.locator(selector).first
                    if elem.is_visible():
                        product['description'] = elem.inner_text().strip()
                        break
                except:
                    continue
            
            # Extract nutrition information
            nutrition = self._extract_nutrition_info(page)
            product['nutrition'] = nutrition
            
            # Extract ingredients
            ingredients_selectors = [
                '.ingredients',
                '[data-auto="ingredients"]',
                '.product-ingredients'
            ]
            for selector in ingredients_selectors:
                try:
                    elem = page.locator(selector).first
                    if elem.is_visible():
                        product['ingredients'] = elem.inner_text().strip()
                        break
                except:
                    continue
            
            # Extract main product image
            try:
                img_elem = page.locator('img[data-auto="pdp-product-image"]').first
                if not img_elem.is_visible():
                    img_elem = page.locator('.product-image img').first
                
                if img_elem.is_visible():
                    img_src = img_elem.get_attribute('src') or img_elem.get_attribute('data-src')
                    if img_src:
                        product['image'] = urljoin(self.base_url, img_src) if img_src.startswith('/') else img_src
            except:
                pass
            
        except Exception as e:
            print(f"Error extracting product details: {e}")
        
        return product
    
    def _extract_nutrition_info(self, page: Page) -> Dict[str, Any]:
        """Extract nutritional information from product page."""
        nutrition = {}
        
        try:
            # Look for nutrition table or section
            nutrition_selectors = [
                '[data-auto="nutrition-table"]',
                '.nutrition-table',
                '.nutrition-info',
                '.nutritional-information'
            ]
            
            nutrition_section = None
            for selector in nutrition_selectors:
                try:
                    elem = page.locator(selector).first
                    if elem.is_visible():
                        nutrition_section = elem
                        break
                except:
                    continue
            
            if nutrition_section:
                # Extract nutrition text and parse it
                nutrition_text = nutrition_section.inner_text()
                
                # Common nutrition patterns
                patterns = {
                    'energy': r'energy[:\s]*(\d+(?:\.\d+)?)\s*(?:kcal|kj)',
                    'protein': r'protein[:\s]*(\d+(?:\.\d+)?)\s*g',
                    'carbs': r'carbohydrate[s]?[:\s]*(\d+(?:\.\d+)?)\s*g',
                    'fat': r'fat[:\s]*(\d+(?:\.\d+)?)\s*g',
                    'sugar': r'sugar[s]?[:\s]*(\d+(?:\.\d+)?)\s*g',
                    'salt': r'salt[:\s]*(\d+(?:\.\d+)?)\s*(?:g|mg)',
                    'fibre': r'fibre[:\s]*(\d+(?:\.\d+)?)\s*g'
                }
                
                for key, pattern in patterns.items():
                    match = re.search(pattern, nutrition_text, re.IGNORECASE)
                    if match:
                        nutrition[key] = match.group(1)
            
        except Exception as e:
            print(f"Error extracting nutrition info: {e}")
        
        return nutrition


# LangChain tool wrappers
@tool
def search_tesco_products_free(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Search for products on Tesco.com using free web scraping with Playwright.
    This tool provides real product data without API costs and handles JavaScript properly.
    
    Args:
        query: Search term (e.g., "chicken breast", "organic vegetables")
        limit: Maximum number of products to return (default: 5)
        
    Returns:
        List of products with name, price, URL, and basic info
    """
    try:
        scraper = TescoScraper()
        products = scraper.search_products(query, limit)
        
        if not products:
            return [{"error": f"No products found for '{query}'"}]
        
        return products
        
    except Exception as e:
        print(f"❌ Error in Tesco search: {e}")
        return [{"error": f"Search failed: {str(e)}"}]


@tool
def get_tesco_product_details_free(product_url: str) -> Dict[str, Any]:
    """
    Get detailed product information from a Tesco product URL using free Playwright scraping.
    
    Args:
        product_url: Full Tesco product URL
        
    Returns:
        Detailed product info including nutrition, ingredients, etc.
    """
    try:
        scraper = TescoScraper()
        details = scraper.get_product_details(product_url)
        
        return details
        
    except Exception as e:
        print(f"❌ Error getting product details: {e}")
        return {"error": f"Failed to get details: {str(e)}"}


if __name__ == "__main__":
    # Test the scraper
    print("🧪 Testing Playwright Tesco Scraper...")
    
    scraper = TescoScraper(headless=False)  # Set to False to see browser
    
    # Test search
    results = scraper.search_products("chicken breast", 3)
    print(f"\nSearch Results ({len(results)} products):")
    
    for i, product in enumerate(results, 1):
        print(f"{i}. {product['name']}")
        print(f"   Price: {product['price']}")
        print(f"   URL: {product['url']}")
        
        # Test detailed product info for first result
        if i == 1 and product.get('url'):
            print("\n🔍 Getting detailed info for first product...")
            details = scraper.get_product_details(product['url'])
            print(f"   Brand: {details.get('brand', 'N/A')}")
            print(f"   Description: {details.get('description', 'N/A')[:100]}...")
            print(f"   Nutrition: {details.get('nutrition', {})}")
        print()