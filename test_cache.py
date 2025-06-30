#!/usr/bin/env python3
"""
Test the nutrition cache system.
"""

from meal_prep_agent.tesco_real import RealTescoScraper
from meal_prep_agent.nutrition_cache import get_cache_stats
import time

def test_cache_system():
    """Test the nutrition cache with real Tesco searches."""
    
    print("🧪 Testing Nutrition Cache System")
    print("="*50)
    
    # Create scraper with nutrition extraction enabled
    scraper = RealTescoScraper(extract_nutrition=True)
    
    print("📊 Initial cache stats:")
    stats = get_cache_stats()
    print(f"   Cached products: {stats['total_cached_products']}")
    print(f"   Cache hits: {stats['total_cache_hits']}")
    
    print(f"\n🔍 First search (will cache nutrition data):")
    start_time = time.time()
    products = scraper.search_products("chicken breast", limit=2)
    first_duration = time.time() - start_time
    
    print(f"⏱️ First search took: {first_duration:.2f} seconds")
    print(f"🍗 Found {len(products)} products")
    
    # Show nutrition data for first product
    if products and products[0].get('nutrition'):
        print(f"📊 Sample nutrition: {products[0]['nutrition']}")
    
    print(f"\n📊 Cache stats after first search:")
    stats = get_cache_stats()
    print(f"   Cached products: {stats['total_cached_products']}")
    print(f"   Cache hits: {stats['total_cache_hits']}")
    
    print(f"\n🔍 Second search (should use cached data):")
    start_time = time.time()
    products2 = scraper.search_products("chicken breast", limit=2)
    second_duration = time.time() - start_time
    
    print(f"⏱️ Second search took: {second_duration:.2f} seconds")
    print(f"🍗 Found {len(products2)} products")
    
    print(f"\n📊 Final cache stats:")
    stats = get_cache_stats()
    print(f"   Cached products: {stats['total_cached_products']}")
    print(f"   Cache hits: {stats['total_cache_hits']}")
    
    # Calculate speedup
    if second_duration > 0:
        speedup = first_duration / second_duration
        print(f"\n🚀 Cache speedup: {speedup:.1f}x faster!")
    
    # Show most popular products
    if stats['most_popular_products']:
        print(f"\n🏆 Most accessed products:")
        for product in stats['most_popular_products'][:3]:
            print(f"   • {product['name']} ({product['hits']} hits)")
    
    print(f"\n💡 Benefits:")
    print(f"   • Reduced API calls: {stats['total_cache_hits']} requests saved")
    print(f"   • Faster response times for repeated searches")
    print(f"   • Persistent nutrition data storage")
    print(f"   • CSV export available for analysis")

def test_cache_without_api():
    """Test cache functionality without making API calls."""
    
    print("🧪 Testing Cache Functions (No API Calls)")
    print("="*50)
    
    from meal_prep_agent.nutrition_cache import cache_nutrition, get_cached_nutrition
    
    # Test data
    test_url = "https://www.tesco.com/groceries/en-GB/products/123456"
    test_name = "Test Product - Chicken Breast"
    test_nutrition = {
        "serving_size": "100g",
        "energy": "115kcal",
        "protein": "21.5g",
        "carbs": "0g", 
        "fat": "3.3g",
        "salt": "0.18g"
    }
    
    print(f"💾 Caching test data...")
    cache_nutrition(test_url, test_name, test_nutrition)
    
    print(f"🔍 Retrieving cached data...")
    cached = get_cached_nutrition(test_url, test_name)
    
    if cached == test_nutrition:
        print(f"✅ Cache test passed!")
        print(f"📊 Retrieved: {cached}")
    else:
        print(f"❌ Cache test failed!")
        print(f"Expected: {test_nutrition}")
        print(f"Got: {cached}")
    
    # Show stats
    stats = get_cache_stats()
    print(f"\n📊 Cache contains {stats['total_cached_products']} products")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--no-api":
        test_cache_without_api()
    else:
        print("ℹ️ This test will make real API calls to Tesco")
        print("Use --no-api flag to test cache without API calls")
        confirm = input("Continue with API test? (y/N): ")
        if confirm.lower() == 'y':
            test_cache_system()
        else:
            test_cache_without_api()