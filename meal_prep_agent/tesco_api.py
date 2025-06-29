"""
Real Tesco API integration using Apify's Tesco Grocery Scraper.
"""

import os
import json
import time
import requests
from typing import List, Dict, Any, Optional
from langchain_core.tools import tool


class TescoAPI:
    """Client for interacting with Tesco product data via Apify."""
    
    def __init__(self, api_token: Optional[str] = None):
        self.api_token = api_token or os.getenv("APIFY_API_TOKEN")
        if not self.api_token:
            raise ValueError("APIFY_API_TOKEN environment variable is required")
        
        self.base_url = "https://api.apify.com/v2"
        self.actor_id = "jupri~tesco-grocery"
    
    def search_products(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for products on Tesco using a query string.
        
        Args:
            query: Search term (e.g., "chicken breast", "organic vegetables")
            limit: Maximum number of products to return
            
        Returns:
            List of product dictionaries with details
        """
        # Construct search URL
        search_url = f"https://www.tesco.com/groceries/en-GB/search?query={query.replace(' ', '%20')}"
        
        # Input for the Apify actor
        input_data = {
            "query": [search_url],
            "limit": limit
        }
        
        return self._run_actor(input_data)
    
    def get_product_by_url(self, product_url: str) -> Dict[str, Any]:
        """
        Get detailed product information from a Tesco product URL.
        
        Args:
            product_url: Full Tesco product URL
            
        Returns:
            Product dictionary with detailed information
        """
        input_data = {
            "query": [product_url],
            "limit": 1
        }
        
        results = self._run_actor(input_data)
        return results[0] if results else {}
    
    def get_product_by_id(self, product_id: str) -> Dict[str, Any]:
        """
        Get product information using Tesco product ID.
        
        Args:
            product_id: Tesco product ID
            
        Returns:
            Product dictionary with detailed information
        """
        input_data = {
            "query": [product_id],
            "limit": 1
        }
        
        results = self._run_actor(input_data)
        return results[0] if results else {}
    
    def _run_actor(self, input_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Run the Apify actor and return results.
        
        Args:
            input_data: Input configuration for the actor
            
        Returns:
            List of product results
        """
        # Start the actor run  
        run_url = f"{self.base_url}/acts/{self.actor_id}/runs"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_token}"
        }
        
        params = {}
        
        print(f"🔄 Starting Tesco product search...")
        
        response = requests.post(
            run_url,
            json=input_data,
            headers=headers
        )
        
        if response.status_code != 201:
            raise Exception(f"Failed to start actor run: {response.text}")
        
        run_info = response.json()
        run_id = run_info["data"]["id"]
        
        # Wait for the run to complete
        dataset_id = self._wait_for_completion(run_id)
        
        # Get the results
        return self._get_dataset_items(dataset_id)
    
    def _wait_for_completion(self, run_id: str, max_wait: int = 120) -> str:
        """
        Wait for the actor run to complete and return the dataset ID.
        
        Args:
            run_id: The actor run ID
            max_wait: Maximum time to wait in seconds
            
        Returns:
            Dataset ID containing the results
        """
        run_url = f"{self.base_url}/acts/{self.actor_id}/runs/{run_id}"
        headers = {"Authorization": f"Bearer {self.api_token}"}
        
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            response = requests.get(run_url, headers=headers)
            
            if response.status_code != 200:
                raise Exception(f"Failed to get run status: {response.text}")
            
            run_data = response.json()["data"]
            status = run_data["status"]
            
            print(f"🔄 Run status: {status}")
            
            if status == "SUCCEEDED":
                return run_data["defaultDatasetId"]
            elif status == "FAILED":
                raise Exception(f"Actor run failed: {run_data.get('exitCode', 'Unknown error')}")
            
            time.sleep(3)  # Wait 3 seconds before checking again
        
        raise Exception(f"Actor run timed out after {max_wait} seconds")
    
    def _get_dataset_items(self, dataset_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve items from the dataset.
        
        Args:
            dataset_id: The dataset ID containing results
            
        Returns:
            List of product data
        """
        dataset_url = f"{self.base_url}/datasets/{dataset_id}/items"
        headers = {"Authorization": f"Bearer {self.api_token}"}
        
        response = requests.get(dataset_url, headers=headers)
        
        if response.status_code != 200:
            raise Exception(f"Failed to get dataset items: {response.text}")
        
        items = response.json()
        print(f"✅ Retrieved {len(items)} products from Tesco")
        
        return items


# LangChain tool wrapper
@tool
def search_tesco_products(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Search for products on Tesco using a query string.
    This tool provides real product data including prices, nutrition info, and availability.
    
    Args:
        query: Search term (e.g., "chicken breast", "organic vegetables", "protein powder")
        limit: Maximum number of products to return (default: 5)
        
    Returns:
        List of products with details like name, price, nutrition, images, etc.
    """
    try:
        api = TescoAPI()
        products = api.search_products(query, limit)
        
        # Clean up the product data to focus on key information
        cleaned_products = []
        for product in products:
            cleaned_product = {
                "name": product.get("title", "Unknown"),
                "price": product.get("price", "Price not available"),
                "url": product.get("url", ""),
                "image": product.get("image", ""),
                "brand": product.get("brand", ""),
                "description": product.get("description", ""),
                "nutrition": product.get("nutrition", {}),
                "unit_price": product.get("unitPrice", ""),
                "promotion": product.get("promotion", ""),
                "rating": product.get("rating", ""),
                "availability": product.get("inStock", True)
            }
            cleaned_products.append(cleaned_product)
        
        return cleaned_products
        
    except Exception as e:
        print(f"❌ Error searching Tesco products: {e}")
        return [{"error": f"Failed to search Tesco: {str(e)}"}]


@tool  
def get_tesco_product_details(product_url: str) -> Dict[str, Any]:
    """
    Get detailed information for a specific Tesco product using its URL.
    
    Args:
        product_url: Full Tesco product URL
        
    Returns:
        Detailed product information including nutrition facts, ingredients, etc.
    """
    try:
        api = TescoAPI()
        product = api.get_product_by_url(product_url)
        
        # Return cleaned product data
        return {
            "name": product.get("title", "Unknown"),
            "price": product.get("price", "Price not available"),
            "brand": product.get("brand", ""),
            "description": product.get("description", ""),
            "ingredients": product.get("ingredients", ""),
            "nutrition": product.get("nutrition", {}),
            "allergens": product.get("allergens", ""),
            "storage": product.get("storage", ""),
            "unit_price": product.get("unitPrice", ""),
            "pack_size": product.get("packSize", ""),
            "rating": product.get("rating", ""),
            "reviews_count": product.get("reviewsCount", 0),
            "image": product.get("image", ""),
            "availability": product.get("inStock", True)
        }
        
    except Exception as e:
        print(f"❌ Error getting Tesco product details: {e}")
        return {"error": f"Failed to get product details: {str(e)}"}


if __name__ == "__main__":
    # Test the API
    print("🧪 Testing Tesco API...")
    
    # Test search
    results = search_tesco_products("chicken breast", 3)
    print(f"Found {len(results)} products:")
    
    for i, product in enumerate(results, 1):
        print(f"{i}. {product['name']} - {product['price']}")
        if product.get('url'):
            # Test detailed product info
            details = get_tesco_product_details(product['url'])
            print(f"   Nutrition: {details.get('nutrition', 'N/A')}")
        print()