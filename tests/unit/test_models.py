"""
Unit tests for data models.

This module contains comprehensive tests for the Product, Promotion,
and Competitor data models to ensure proper validation and functionality.
"""

import pytest
from datetime import datetime, date
from decimal import Decimal
from pydantic import ValidationError

from src.models.product import Product, ProductCategory, ProductList
from src.models.promotion import Promotion, PromotionType, PromotionStatus, PromotionList
from src.models.competitor import Competitor, CrawlSettings, CompetitorConfig, GlobalSettings


class TestProduct:
    """Test cases for Product model."""
    
    def test_create_valid_product(self):
        """Test creating a valid product."""
        product = Product(
            competitor="West Elm",
            product_name="Modern Sofa",
            product_url="https://www.westelm.com/products/modern-sofa/",
            category=ProductCategory.FURNITURE,
            price=Decimal("899.99")
        )
        
        assert product.competitor == "West Elm"
        assert product.product_name == "Modern Sofa"
        assert product.category == ProductCategory.FURNITURE
        assert product.price == Decimal("899.99")
        assert product.is_valid_for_export()
    
    def test_product_name_validation(self):
        """Test product name validation."""
        # Test empty name
        with pytest.raises(ValidationError):
            Product(
                competitor="Test",
                product_name="",
                product_url="https://example.com"
            )
        
        # Test name too short
        with pytest.raises(ValidationError):
            Product(
                competitor="Test",
                product_name="A",
                product_url="https://example.com"
            )
    
    def test_price_validation(self):
        """Test price validation."""
        # Test negative price
        with pytest.raises(ValidationError):
            Product(
                competitor="Test",
                product_name="Test Product",
                product_url="https://example.com",
                price=Decimal("-10.00")
            )
        
        # Test extremely high price
        with pytest.raises(ValidationError):
            Product(
                competitor="Test",
                product_name="Test Product",
                product_url="https://example.com",
                price=Decimal("999999.99")
            )
    
    def test_csv_export(self):
        """Test CSV export functionality."""
        product = Product(
            competitor="Test Store",
            product_name="Test Product",
            product_url="https://example.com/product",
            category=ProductCategory.FURNITURE,
            price=Decimal("99.99"),
            brand="Test Brand"
        )
        
        csv_dict = product.to_csv_dict()
        
        assert csv_dict['competitor'] == "Test Store"
        assert csv_dict['product_name'] == "Test Product"
        assert csv_dict['category'] == "furniture"
        assert csv_dict['price'] == 99.99
        assert csv_dict['brand'] == "Test Brand"
    
    def test_unique_key_generation(self):
        """Test unique key generation for deduplication."""
        product = Product(
            competitor="Test Store",
            product_name="Test Product",
            product_url="https://example.com/product"
        )
        
        expected_key = "Test Store:https://example.com/product"
        assert product.get_unique_key() == expected_key


class TestPromotion:
    """Test cases for Promotion model."""
    
    def test_create_valid_promotion(self):
        """Test creating a valid promotion."""
        promotion = Promotion(
            competitor="Crate & Barrel",
            promo_title="20% Off Furniture",
            promo_url="https://www.crateandbarrel.com/sale/",
            promo_type=PromotionType.PERCENTAGE_OFF,
            discount_value=20.0,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
        
        assert promotion.competitor == "Crate & Barrel"
        assert promotion.promo_title == "20% Off Furniture"
        assert promotion.promo_type == PromotionType.PERCENTAGE_OFF
        assert promotion.discount_value == 20.0
        assert promotion.is_valid_for_export()
    
    def test_date_validation(self):
        """Test date range validation."""
        # Test end date before start date
        with pytest.raises(ValidationError):
            Promotion(
                competitor="Test",
                promo_title="Test Sale",
                promo_url="https://example.com/sale",
                promo_type=PromotionType.PERCENTAGE_OFF,
                start_date=date(2024, 1, 31),
                end_date=date(2024, 1, 1)
            )
    
    def test_discount_validation(self):
        """Test discount value validation."""
        # Test percentage over 100%
        with pytest.raises(ValidationError):
            Promotion(
                competitor="Test",
                promo_title="Test Sale",
                promo_url="https://example.com/sale",
                promo_type=PromotionType.PERCENTAGE_OFF,
                discount_value=150.0
            )
    
    def test_promo_code_cleaning(self):
        """Test promotion code cleaning."""
        promotion = Promotion(
            competitor="Test",
            promo_title="Test Sale",
            promo_url="https://example.com/sale",
            promo_type=PromotionType.PERCENTAGE_OFF,
            promo_code="CODE: SAVE20"
        )
        
        assert promotion.promo_code == "SAVE20"
    
    def test_days_remaining(self):
        """Test days remaining calculation."""
        future_date = date.today().replace(year=date.today().year + 1)
        
        promotion = Promotion(
            competitor="Test",
            promo_title="Test Sale",
            promo_url="https://example.com/sale",
            promo_type=PromotionType.PERCENTAGE_OFF,
            end_date=future_date
        )
        
        days_remaining = promotion.get_days_remaining()
        assert days_remaining is not None
        assert days_remaining > 0
    
    def test_is_currently_active(self):
        """Test active status checking."""
        # Test active promotion (no dates)
        promotion = Promotion(
            competitor="Test",
            promo_title="Test Sale",
            promo_url="https://example.com/sale",
            promo_type=PromotionType.PERCENTAGE_OFF,
            status=PromotionStatus.ACTIVE
        )
        
        assert promotion.is_currently_active()


class TestCompetitor:
    """Test cases for Competitor model."""
    
    def test_create_valid_competitor(self):
        """Test creating a valid competitor."""
        competitor = Competitor(
            name="West Elm",
            new_urls=["https://www.westelm.com/shop/new/"],
            promo_urls=["https://www.westelm.com/shop/sale/"],
            crawl=CrawlSettings(depth=2, limit=50)
        )
        
        assert competitor.name == "West Elm"
        assert len(competitor.new_urls) == 1
        assert len(competitor.promo_urls) == 1
        assert competitor.crawl.depth == 2
        assert competitor.crawl.limit == 50
    
    def test_empty_url_lists(self):
        """Test validation of empty URL lists."""
        # Test empty new_urls
        with pytest.raises(ValidationError):
            Competitor(
                name="Test",
                new_urls=[],
                promo_urls=["https://example.com/sale/"]
            )
        
        # Test empty promo_urls
        with pytest.raises(ValidationError):
            Competitor(
                name="Test",
                new_urls=["https://example.com/new/"],
                promo_urls=[]
            )
    
    def test_get_all_urls(self):
        """Test getting all URLs."""
        competitor = Competitor(
            name="Test",
            new_urls=["https://example.com/new1/", "https://example.com/new2/"],
            promo_urls=["https://example.com/sale1/"]
        )
        
        all_urls = competitor.get_all_urls()
        assert len(all_urls) == 3
    
    def test_estimated_time_calculation(self):
        """Test estimated crawling time calculation."""
        competitor = Competitor(
            name="Test",
            new_urls=["https://example.com/new/"],
            promo_urls=["https://example.com/sale/"],
            crawl=CrawlSettings(depth=1, limit=10, delay=1.0)
        )
        
        estimated_time = competitor.get_estimated_time_minutes()
        assert estimated_time > 0
        assert isinstance(estimated_time, float)
    
    def test_url_exclusion(self):
        """Test URL exclusion patterns."""
        competitor = Competitor(
            name="Test",
            new_urls=["https://example.com/new/"],
            promo_urls=["https://example.com/sale/"],
            exclude_patterns=["/account/", "/cart/"]
        )
        
        assert competitor.is_url_excluded("https://example.com/account/login")
        assert competitor.is_url_excluded("https://example.com/cart/view")
        assert not competitor.is_url_excluded("https://example.com/products/")


class TestCrawlSettings:
    """Test cases for CrawlSettings model."""
    
    def test_valid_settings(self):
        """Test valid crawl settings."""
        settings = CrawlSettings(
            depth=3,
            limit=100,
            delay=1.5,
            timeout=45,
            retries=2
        )
        
        assert settings.depth == 3
        assert settings.limit == 100
        assert settings.delay == 1.5
        assert settings.timeout == 45
        assert settings.retries == 2
    
    def test_settings_validation(self):
        """Test crawl settings validation."""
        # Test depth too high
        with pytest.raises(ValidationError):
            CrawlSettings(depth=10)
        
        # Test negative delay
        with pytest.raises(ValidationError):
            CrawlSettings(delay=-1.0)
        
        # Test limit too high
        with pytest.raises(ValidationError):
            CrawlSettings(limit=5000)


class TestCompetitorConfig:
    """Test cases for CompetitorConfig model."""
    
    def test_create_config(self):
        """Test creating competitor configuration."""
        competitor = Competitor(
            name="Test",
            new_urls=["https://example.com/new/"],
            promo_urls=["https://example.com/sale/"]
        )
        
        config = CompetitorConfig(
            competitors=[competitor],
            global_settings=GlobalSettings()
        )
        
        assert len(config.competitors) == 1
        assert config.global_settings.concurrent_requests == 5
    
    def test_get_enabled_competitors(self):
        """Test getting enabled competitors."""
        competitor1 = Competitor(
            name="Enabled",
            new_urls=["https://example.com/new/"],
            promo_urls=["https://example.com/sale/"],
            enabled=True
        )
        
        competitor2 = Competitor(
            name="Disabled",
            new_urls=["https://example.com/new/"],
            promo_urls=["https://example.com/sale/"],
            enabled=False
        )
        
        config = CompetitorConfig(competitors=[competitor1, competitor2])
        enabled = config.get_enabled_competitors()
        
        assert len(enabled) == 1
        assert enabled[0].name == "Enabled"
    
    def test_time_constraint_validation(self):
        """Test time constraint validation."""
        # Create competitor with very fast settings
        competitor = Competitor(
            name="Fast",
            new_urls=["https://example.com/new/"],
            promo_urls=["https://example.com/sale/"],
            crawl=CrawlSettings(depth=1, limit=1, delay=0.1)
        )
        
        config = CompetitorConfig(competitors=[competitor])
        is_valid, message = config.validate_time_constraint(max_minutes=80)
        
        assert is_valid
        assert "within limit" in message


class TestProductList:
    """Test cases for ProductList model."""
    
    def test_add_product(self):
        """Test adding products to list."""
        product_list = ProductList(competitor="Test Store")
        
        product = Product(
            competitor="Test Store",
            product_name="Test Product",
            product_url="https://example.com/product"
        )
        
        product_list.add_product(product)
        
        assert len(product_list.products) == 1
        assert product_list.total_products == 1
    
    def test_get_valid_products(self):
        """Test getting valid products only."""
        product_list = ProductList(competitor="Test Store")
        
        # Valid product
        valid_product = Product(
            competitor="Test Store",
            product_name="Valid Product",
            product_url="https://example.com/valid"
        )
        
        # Invalid product (empty name)
        try:
            invalid_product = Product(
                competitor="Test Store",
                product_name="",
                product_url="https://example.com/invalid"
            )
            product_list.add_product(invalid_product)
        except ValidationError:
            pass  # Expected to fail validation
        
        product_list.add_product(valid_product)
        valid_products = product_list.get_valid_products()
        
        assert len(valid_products) == 1


class TestPromotionList:
    """Test cases for PromotionList model."""
    
    def test_add_promotion(self):
        """Test adding promotions to list."""
        promo_list = PromotionList(competitor="Test Store")
        
        promotion = Promotion(
            competitor="Test Store",
            promo_title="Test Sale",
            promo_url="https://example.com/sale",
            promo_type=PromotionType.PERCENTAGE_OFF
        )
        
        promo_list.add_promotion(promotion)
        
        assert len(promo_list.promotions) == 1
        assert promo_list.total_promotions == 1
    
    def test_success_rate_calculation(self):
        """Test success rate calculation."""
        promo_list = PromotionList(
            competitor="Test Store",
            successful_extractions=8,
            failed_extractions=2
        )
        
        success_rate = promo_list.get_success_rate()
        assert success_rate == 0.8  # 8/10 = 0.8
