"""
Test script for the Tesco API integration.
Run this to test if the Tesco product search is working.
"""

import os
from dotenv import load_dotenv
from meal_prep_agent.tesco_api import search_tesco_products

# Load environment variables
load_dotenv()

def test_tesco_search():
    """Test the Tesco product search functionality."""
    
    # Check if API token is set
    if not os.getenv("APIFY_API_TOKEN"):
        print("❌ APIFY_API_TOKEN not found in environment variables!")
        print("Please set your Apify API token in a .env file")
        print("1. Sign up at https://apify.com/")
        print("2. Get your API token from the Apify console")
        print("3. Add APIFY_API_TOKEN=your_token_here to your .env file")
        return
    
    print("🧪 Testing Tesco Product Search...")
    print("=" * 50)
    
    # Test search queries
    test_queries = [
        "chicken breast",
        "organic broccoli", 
        "greek yogurt",
    ]
    
    for query in test_queries:
        print(f"\n🔍 Searching for: '{query}'")
        print("-" * 30)
        
        try:
            # Use the LangChain tool function
            results = search_tesco_products.invoke({"query": query, "limit": 3})
            
            if results and not results[0].get("error"):
                print(f"✅ Found {len(results)} products:")
                
                for i, product in enumerate(results, 1):
                    print(f"{i}. {product['name']}")
                    print(f"   Price: {product['price']}")
                    print(f"   Brand: {product.get('brand', 'N/A')}")
                    print(f"   Available: {product.get('availability', 'Unknown')}")
                    
                    if product.get('nutrition'):
                        print(f"   Nutrition: {product['nutrition']}")
                    print()
            else:
                error_msg = results[0].get("error", "Unknown error") if results else "No results"
                print(f"❌ Error: {error_msg}")
                
        except Exception as e:
            print(f"❌ Exception occurred: {e}")
    
    print("\n🏁 Test completed!")


if __name__ == "__main__":
    test_tesco_search()