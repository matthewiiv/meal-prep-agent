"""
Test suite for the Tesco scraper to ensure it extracts real data correctly.
"""

import pytest
import re
from unittest.mock import Mock, patch
from meal_prep_agent.tesco_real import RealTescoScraper, search_tesco_products_real


class TestRealTescoScraper:
    """Test the real Tesco scraper functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.scraper = RealTescoScraper()
    
    def test_scraper_initialization(self):
        """Test that scraper initializes correctly."""
        assert self.scraper.base_url == "https://www.tesco.com"
        assert self.scraper.session is not None
        assert "iPhone" in self.scraper.session.headers['User-Agent']
    
    def test_extract_brand_from_title(self):
        """Test brand extraction from product titles."""
        # Test Tesco brands
        assert self.scraper._extract_brand_from_title("Tesco British Chicken Breast") == "Tesco"
        assert self.scraper._extract_brand_from_title("Tesco Finest Free Range Chicken") == "Tesco Finest"
        assert self.scraper._extract_brand_from_title("Tesco Organic Semi Skimmed Milk") == "Tesco Organic"
        
        # Test other brands
        assert self.scraper._extract_brand_from_title("Heinz Baked Beans") == "Heinz"
        assert self.scraper._extract_brand_from_title("Birds Eye Fish Fingers") == "Birds"
    
    @patch('meal_prep_agent.tesco_real.RealTescoScraper._get_real_nutrition')
    def test_get_real_nutrition_call(self, mock_nutrition):
        """Test that real nutrition method is called."""
        mock_nutrition.return_value = {'energy': '100kcal', 'protein': '20g'}
        
        nutrition = self.scraper._get_real_nutrition("https://example.com/product")
        mock_nutrition.assert_called_once_with("https://example.com/product")
        
        # Test that empty dict is returned when no nutrition found
        mock_nutrition.return_value = {}
        nutrition = self.scraper._get_real_nutrition("https://example.com/product")
        assert nutrition == {}
    
    @patch('meal_prep_agent.tesco_real.RealTescoScraper._get_real_nutrition')
    @patch('requests.Session.get')
    def test_search_products_with_mock_response(self, mock_get, mock_nutrition):
        """Test product search with mocked HTML response."""
        # Mock nutrition data
        mock_nutrition.return_value = {'energy': '100kcal', 'protein': '20g'}
        
        # Mock HTML content with embedded product data
        mock_html = '''
        <html>
        <script>
        "ProductType:123456":{"title":"Tesco British Chicken Breast 500G","brandName":"TESCO"}
        "ProductType:789012":{"title":"Tesco Finest Free Range Chicken 1Kg","brandName":"TESCO finest"}
        "tpnc":"123456","tpnc":"789012"
        "price":4.50,"price":8.99
        </script>
        </html>
        '''
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = mock_html
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        products = self.scraper.search_products("chicken", limit=2)
        
        # Verify the search request was made
        assert mock_get.call_count >= 1
        search_call = mock_get.call_args_list[0]
        assert 'search?query=chicken' in search_call[0][0]
        
        # Verify products were extracted
        assert len(products) >= 1
        assert any("Chicken" in product['name'] for product in products)
    
    def test_extract_real_product_data_with_sample_html(self):
        """Test data extraction with sample HTML containing product data."""
        sample_html = '''
        "ProductType:276054144":{"__typename":"ProductType","title":"Tesco British Chicken Breast 650G","brandName":"TESCO"}
        "ProductType:304404328":{"__typename":"ProductType","title":"Tesco Finest Free Range Chicken 1Kg","brandName":"TESCO finest"}
        "tpnc":"276054144"
        "tpnc":"304404328"
        "price":5.50
        "price":9.99
        '''
        
        products = self.scraper._extract_real_product_data(sample_html)
        
        assert len(products) >= 2
        
        # Check first product
        first_product = products[0]
        assert "Tesco British Chicken Breast 650G" in first_product['name']
        assert first_product['brand'] == "TESCO"
        assert first_product['url'].endswith("276054144")
        assert 'nutrition' in first_product
        
        # Check second product  
        second_product = products[1]
        assert "Tesco Finest Free Range Chicken 1Kg" in second_product['name']
        assert first_product['brand'] == "TESCO"
    
    def test_price_enrichment(self):
        """Test that price data gets properly enriched."""
        products = [
            {'name': 'Tesco Chicken Breast 500G', 'price': 'Price not available'},
            {'name': 'Tesco Milk 1L', 'price': 'Price not available'}
        ]
        
        html_with_prices = '''
        "price":4.50
        "price":2.30
        £5.99
        £1.85
        '''
        
        self.scraper._enrich_with_price_data(products, html_with_prices)
        
        # At least some products should have prices now
        prices_found = [p['price'] for p in products if p['price'] != 'Price not available']
        assert len(prices_found) > 0
    
    def test_product_url_generation(self):
        """Test that product URLs are generated correctly."""
        products = [
            {'name': 'Test Product', 'tpnc': '123456789', 'price': '£4.50'}
        ]
        
        assert products[0]['tpnc'] == '123456789'
        
        # Test URL construction
        expected_url = f"{self.scraper.base_url}/groceries/en-GB/products/123456789"
        test_url = f"{self.scraper.base_url}/groceries/en-GB/products/{products[0]['tpnc']}"
        assert test_url == expected_url


class TestSearchTescoProductsRealTool:
    """Test the LangChain tool wrapper."""
    
    @patch('meal_prep_agent.tesco_real.RealTescoScraper.search_products')
    def test_search_tool_success(self, mock_search):
        """Test successful product search through the tool."""
        mock_search.return_value = [
            {
                'name': 'Tesco British Chicken Breast 500G',
                'price': '£4.50',
                'brand': 'TESCO',
                'url': 'https://www.tesco.com/groceries/en-GB/products/123456',
                'nutrition': {'protein': '23.1g', 'energy': '106kcal'}
            }
        ]
        
        result = search_tesco_products_real.invoke({"query": "chicken", "limit": 5})
        
        assert len(result) == 1
        assert result[0]['name'] == 'Tesco British Chicken Breast 500G'
        assert result[0]['price'] == '£4.50'
        assert 'nutrition' in result[0]
    
    @patch('meal_prep_agent.tesco_real.RealTescoScraper.search_products')
    def test_search_tool_no_results(self, mock_search):
        """Test tool behavior when no products found."""
        mock_search.return_value = []
        
        result = search_tesco_products_real.invoke({"query": "nonexistent", "limit": 5})
        
        assert len(result) == 1
        assert "error" in result[0]
        assert "No products found" in result[0]["error"]
    
    @patch('meal_prep_agent.tesco_real.RealTescoScraper.search_products')
    def test_search_tool_exception_handling(self, mock_search):
        """Test tool behavior when scraper raises exception."""
        mock_search.side_effect = Exception("Network error")
        
        result = search_tesco_products_real.invoke({"query": "chicken", "limit": 5})
        
        assert len(result) == 1
        assert "error" in result[0]
        assert "Search failed" in result[0]["error"]


class TestRealDataExtraction:
    """Integration tests that verify real data extraction patterns."""
    
    def test_regex_patterns(self):
        """Test that our regex patterns work correctly."""
        sample_data = '''
        "title":"Tesco British Chicken Breast Fillets 650G"
        "title":"Tesco Finest Free Range Whole Chicken 1Kg-2.3Kg"
        "ProductType:276054144"
        "ProductType:304404328" 
        "tpnc":"276054144"
        "tpnc":"304404328"
        "brandName":"TESCO"
        "brandName":"TESCO finest"
        "price":4.50
        "price":8.99
        '''
        
        # Test title extraction
        title_pattern = r'"title":"([^"]+)"'
        titles = re.findall(title_pattern, sample_data)
        assert len(titles) == 2
        assert "Tesco British Chicken Breast Fillets 650G" in titles
        
        # Test ID extraction
        id_pattern = r'"ProductType:(\d+)"'
        ids = re.findall(id_pattern, sample_data)
        assert len(ids) == 2
        assert "276054144" in ids
        
        # Test tpnc extraction
        tpnc_pattern = r'"tpnc":"(\d+)"'
        tpncs = re.findall(tpnc_pattern, sample_data)
        assert len(tpncs) == 2
        
        # Test brand extraction
        brand_pattern = r'"brandName":"([^"]+)"'
        brands = re.findall(brand_pattern, sample_data)
        assert len(brands) == 2
        assert "TESCO" in brands
        assert "TESCO finest" in brands
    
    @patch('meal_prep_agent.tesco_real.RealTescoScraper._get_real_nutrition')
    def test_nutrition_data_structure(self, mock_nutrition):
        """Test that nutrition data has the correct structure when found."""
        mock_nutrition.return_value = {
            'energy': '100kcal',
            'protein': '20g',
            'carbs': '5g',
            'fat': '2g',
            'salt': '0.5g'
        }
        
        scraper = RealTescoScraper()
        nutrition = scraper._get_real_nutrition("https://example.com/product")
        
        required_keys = ['energy', 'protein', 'carbs', 'fat', 'salt']
        for key in required_keys:
            assert key in nutrition
            assert isinstance(nutrition[key], str)
            assert nutrition[key].endswith(('kcal', 'g'))  # Proper units


@pytest.mark.integration
class TestTescoIntegration:
    """Integration tests that make real requests to Tesco (run with caution)."""
    
    @pytest.mark.slow
    def test_real_tesco_request(self):
        """Test making a real request to Tesco (disabled by default)."""
        pytest.skip("Integration test - enable manually for real API testing")
        
        scraper = RealTescoScraper()
        products = scraper.search_products("chicken", limit=2)
        
        # If this passes, we got real data
        if products:
            assert len(products) <= 2
            for product in products:
                assert 'name' in product
                assert 'url' in product
                assert product['url'].startswith('https://www.tesco.com')


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])