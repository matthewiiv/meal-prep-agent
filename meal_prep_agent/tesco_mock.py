"""
Mock Tesco data for testing the agent while scraper connectivity is being fixed.
"""

from typing import List, Dict, Any
from langchain_core.tools import tool


# Mock product database
MOCK_PRODUCTS = {
    "chicken": [
        {
            "name": "Tesco British Chicken Breast Fillets 640G",
            "price": "£4.50",
            "url": "https://www.tesco.com/groceries/en-GB/products/254892116",
            "image": "https://digitalcontent.api.tesco.com/v2/media/ghs/snapshotimagehandler_1896091563.jpeg",
            "unit_price": "£0.70/100g",
            "promotion": "",
            "availability": True,
            "brand": "Tesco",
            "nutrition": {
                "energy": "106",
                "protein": "23.1", 
                "carbs": "0",
                "fat": "1.9",
                "salt": "0.22"
            }
        },
        {
            "name": "Tesco Organic Chicken Breast Fillets 450G",
            "price": "£6.00",
            "url": "https://www.tesco.com/groceries/en-GB/products/254892117",
            "image": "https://digitalcontent.api.tesco.com/v2/media/ghs/snapshotimagehandler_1896091564.jpeg",
            "unit_price": "£1.33/100g",
            "promotion": "",
            "availability": True,
            "brand": "Tesco Organic",
            "nutrition": {
                "energy": "106",
                "protein": "23.1",
                "carbs": "0", 
                "fat": "1.9",
                "salt": "0.22"
            }
        }
    ],
    "broccoli": [
        {
            "name": "Tesco Broccoli Each",
            "price": "£1.10",
            "url": "https://www.tesco.com/groceries/en-GB/products/254892118",
            "image": "https://digitalcontent.api.tesco.com/v2/media/ghs/snapshotimagehandler_1896091565.jpeg",
            "unit_price": "£1.10/each",
            "promotion": "",
            "availability": True,
            "brand": "Tesco",
            "nutrition": {
                "energy": "25",
                "protein": "3.0",
                "carbs": "2.0",
                "fat": "0.4",
                "salt": "0.01"
            }
        }
    ],
    "rice": [
        {
            "name": "Tesco Basmati Rice 1Kg",
            "price": "£2.50", 
            "url": "https://www.tesco.com/groceries/en-GB/products/254892119",
            "image": "https://digitalcontent.api.tesco.com/v2/media/ghs/snapshotimagehandler_1896091566.jpeg",
            "unit_price": "£0.25/100g",
            "promotion": "Clubcard Price £2.00",
            "availability": True,
            "brand": "Tesco",
            "nutrition": {
                "energy": "349",
                "protein": "7.9",
                "carbs": "77.8",
                "fat": "0.6",
                "salt": "0.01"
            }
        }
    ],
    "yogurt": [
        {
            "name": "Tesco Greek Style Natural Yogurt 500G",
            "price": "£1.75",
            "url": "https://www.tesco.com/groceries/en-GB/products/254892120",
            "image": "https://digitalcontent.api.tesco.com/v2/media/ghs/snapshotimagehandler_1896091567.jpeg",
            "unit_price": "£0.35/100g",
            "promotion": "",
            "availability": True,
            "brand": "Tesco",
            "nutrition": {
                "energy": "115",
                "protein": "9.0",
                "carbs": "4.5",
                "fat": "6.4",
                "salt": "0.13"
            }
        }
    ]
}


def find_products(query: str) -> List[Dict[str, Any]]:
    """Find mock products matching the query."""
    query_lower = query.lower()
    results = []
    
    for category, products in MOCK_PRODUCTS.items():
        if category in query_lower or any(word in query_lower for word in category.split()):
            results.extend(products)
        else:
            # Check if query words match product names
            for product in products:
                if any(word in product["name"].lower() for word in query_lower.split()):
                    results.append(product)
    
    return results


@tool
def search_tesco_products_mock(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Mock version of Tesco product search for testing.
    Returns realistic product data without needing actual scraping.
    
    Args:
        query: Search term (e.g., "chicken breast", "broccoli")
        limit: Maximum number of products to return
        
    Returns:
        List of mock products matching the query
    """
    print(f"🎭 MOCK: Searching for '{query}'")
    
    products = find_products(query)
    
    if not products:
        # Return generic results for unknown queries
        products = [
            {
                "name": f"Mock Product for '{query}'",
                "price": "£3.50",
                "url": "https://www.tesco.com/groceries/mock",
                "image": "",
                "unit_price": "£0.50/100g",
                "promotion": "",
                "availability": True,
                "brand": "Mock Brand",
                "nutrition": {
                    "energy": "150",
                    "protein": "10.0",
                    "carbs": "15.0", 
                    "fat": "5.0",
                    "salt": "0.5"
                }
            }
        ]
    
    return products[:limit]


@tool
def get_tesco_product_details_mock(product_url: str) -> Dict[str, Any]:
    """
    Mock version of detailed product info.
    
    Args:
        product_url: Product URL (ignored in mock)
        
    Returns:
        Mock detailed product information
    """
    print(f"🎭 MOCK: Getting details for {product_url}")
    
    return {
        "name": "Mock Detailed Product",
        "price": "£4.50",
        "brand": "Mock Brand",
        "description": "High-quality mock product perfect for meal prep.",
        "ingredients": "Mock ingredients, natural flavoring",
        "nutrition": {
            "energy": "120",
            "protein": "15.0",
            "carbs": "10.0",
            "fat": "3.0",
            "salt": "0.3"
        },
        "allergens": "May contain traces of mock allergens",
        "storage": "Store in a cool, dry place",
        "unit_price": "£0.60/100g", 
        "pack_size": "750g",
        "image": "https://example.com/mock-image.jpg",
        "availability": True,
        "url": product_url
    }


if __name__ == "__main__":
    # Test the mock functions
    print("🧪 Testing Mock Tesco Functions...")
    
    queries = ["chicken breast", "broccoli", "unknown item"]
    
    for query in queries:
        results = search_tesco_products_mock.invoke({"query": query, "limit": 3})
        print(f"\nQuery: '{query}' - Found {len(results)} products:")
        for product in results:
            print(f"  - {product['name']} - {product['price']}")
    
    # Test detailed info
    details = get_tesco_product_details_mock.invoke({"product_url": "https://example.com"})
    print(f"\nDetailed info: {details['name']} - {details['nutrition']}")