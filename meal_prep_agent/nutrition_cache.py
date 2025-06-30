#!/usr/bin/env python3
"""
Nutrition data cache for Tesco products to avoid redundant API calls.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

class NutritionCache:
    """Cache for storing Tesco product nutrition data locally."""
    
    def __init__(self, cache_file: str = "tesco_nutrition_cache.json"):
        """Initialize the nutrition cache."""
        self.cache_file = Path(cache_file)
        self.cache_data = self._load_cache()
    
    def _load_cache(self) -> Dict[str, Any]:
        """Load existing cache data from file."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"📁 Loaded nutrition cache with {len(data.get('products', {}))} products")
                    return data
            except (json.JSONDecodeError, IOError) as e:
                print(f"⚠️ Error loading cache: {e}, starting fresh")
        
        # Return empty cache structure
        return {
            "cache_version": "1.0",
            "last_updated": datetime.now().isoformat(),
            "products": {}
        }
    
    def _save_cache(self) -> None:
        """Save cache data to file."""
        try:
            self.cache_data["last_updated"] = datetime.now().isoformat()
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache_data, f, indent=2, ensure_ascii=False)
            print(f"💾 Saved nutrition cache with {len(self.cache_data['products'])} products")
        except IOError as e:
            print(f"❌ Error saving cache: {e}")
    
    def _get_product_key(self, product_url: str) -> str:
        """Generate a cache key from product URL."""
        # Extract product ID from URL
        if '/products/' in product_url:
            product_id = product_url.split('/products/')[-1]
            return product_id
        return product_url
    
    def get_nutrition(self, product_url: str, product_name: str = "") -> Optional[Dict[str, Any]]:
        """Get nutrition data from cache if available."""
        key = self._get_product_key(product_url)
        
        if key in self.cache_data["products"]:
            cached_product = self.cache_data["products"][key]
            print(f"🎯 Cache HIT for {product_name or key}")
            return cached_product.get("nutrition", {})
        
        print(f"🔍 Cache MISS for {product_name or key}")
        return None
    
    def set_nutrition(self, product_url: str, product_name: str, nutrition_data: Dict[str, Any]) -> None:
        """Store nutrition data in cache."""
        key = self._get_product_key(product_url)
        
        self.cache_data["products"][key] = {
            "product_name": product_name,
            "product_url": product_url,
            "nutrition": nutrition_data,
            "cached_at": datetime.now().isoformat(),
            "cache_hits": self.cache_data["products"].get(key, {}).get("cache_hits", 0)
        }
        
        print(f"💾 Cached nutrition for {product_name}")
        self._save_cache()
    
    def increment_hit_count(self, product_url: str) -> None:
        """Increment cache hit counter for analytics."""
        key = self._get_product_key(product_url)
        if key in self.cache_data["products"]:
            self.cache_data["products"][key]["cache_hits"] = (
                self.cache_data["products"][key].get("cache_hits", 0) + 1
            )
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        products = self.cache_data["products"]
        total_products = len(products)
        total_hits = sum(p.get("cache_hits", 0) for p in products.values())
        
        # Find most popular products
        popular_products = sorted(
            products.items(),
            key=lambda x: x[1].get("cache_hits", 0),
            reverse=True
        )[:5]
        
        return {
            "total_cached_products": total_products,
            "total_cache_hits": total_hits,
            "cache_file_size_kb": self.cache_file.stat().st_size // 1024 if self.cache_file.exists() else 0,
            "last_updated": self.cache_data.get("last_updated"),
            "most_popular_products": [
                {
                    "name": item[1].get("product_name", "Unknown"),
                    "hits": item[1].get("cache_hits", 0)
                }
                for item in popular_products
            ]
        }
    
    def clear_cache(self) -> None:
        """Clear all cached data."""
        self.cache_data = {
            "cache_version": "1.0",
            "last_updated": datetime.now().isoformat(),
            "products": {}
        }
        self._save_cache()
        print("🗑️ Cache cleared")
    
    def export_to_csv(self, output_file: str = "tesco_nutrition_export.csv") -> None:
        """Export cached nutrition data to CSV for analysis."""
        import csv
        
        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Write header
                writer.writerow([
                    'Product ID', 'Product Name', 'Product URL', 
                    'Serving Size', 'Energy', 'Protein', 'Carbs', 'Fat', 'Salt',
                    'Cache Hits', 'Cached At'
                ])
                
                # Write data
                for product_id, data in self.cache_data["products"].items():
                    nutrition = data.get("nutrition", {})
                    writer.writerow([
                        product_id,
                        data.get("product_name", ""),
                        data.get("product_url", ""),
                        nutrition.get("serving_size", ""),
                        nutrition.get("energy", ""),
                        nutrition.get("protein", ""),
                        nutrition.get("carbs", ""),
                        nutrition.get("fat", ""),
                        nutrition.get("salt", ""),
                        data.get("cache_hits", 0),
                        data.get("cached_at", "")
                    ])
            
            print(f"📊 Exported {len(self.cache_data['products'])} products to {output_file}")
            
        except IOError as e:
            print(f"❌ Error exporting to CSV: {e}")

# Global cache instance
_nutrition_cache = NutritionCache()

def get_cached_nutrition(product_url: str, product_name: str = "") -> Optional[Dict[str, Any]]:
    """Get nutrition data from cache."""
    nutrition = _nutrition_cache.get_nutrition(product_url, product_name)
    if nutrition:
        _nutrition_cache.increment_hit_count(product_url)
    return nutrition

def cache_nutrition(product_url: str, product_name: str, nutrition_data: Dict[str, Any]) -> None:
    """Cache nutrition data."""
    _nutrition_cache.set_nutrition(product_url, product_name, nutrition_data)

def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics."""
    return _nutrition_cache.get_cache_stats()

def clear_nutrition_cache() -> None:
    """Clear the nutrition cache."""
    _nutrition_cache.clear_cache()

def export_cache_to_csv(output_file: str = "tesco_nutrition_export.csv") -> None:
    """Export cache to CSV."""
    _nutrition_cache.export_to_csv(output_file)

if __name__ == "__main__":
    # Test the cache
    print("🧪 Testing Nutrition Cache")
    print("="*40)
    
    # Show current stats
    stats = get_cache_stats()
    print(f"Cache stats: {stats}")
    
    # Test caching
    test_url = "https://www.tesco.com/groceries/en-GB/products/294007923"
    test_nutrition = {
        "serving_size": "100g",
        "energy": "115kcal",
        "protein": "21.5g",
        "carbs": "0g",
        "fat": "3.3g",
        "salt": "0.18g"
    }
    
    # Cache some data
    cache_nutrition(test_url, "Tesco British Chicken Breast", test_nutrition)
    
    # Retrieve it
    cached = get_cached_nutrition(test_url, "Tesco British Chicken Breast")
    print(f"Retrieved: {cached}")
    
    # Show updated stats
    stats = get_cache_stats()
    print(f"Updated stats: {stats}")