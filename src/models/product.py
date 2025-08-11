"""
Product data model for competitive intelligence system.

This module defines the Product model using Pydantic for data validation
and serialization of product information collected from competitor websites.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, validator, HttpUrl
from enum import Enum


class ProductCategory(str, Enum):
    """Product category enumeration."""
    FURNITURE = "furniture"
    HOME_DECOR = "home_decor"
    BEDDING = "bedding"
    LIGHTING = "lighting"
    RUGS = "rugs"
    KITCHEN = "kitchen"
    OUTDOOR = "outdoor"
    STORAGE = "storage"
    OFFICE = "office"
    KIDS = "kids"
    OTHER = "other"


class Product(BaseModel):
    """
    Product data model for storing product information.
    
    This model validates and structures product data collected
    from competitor websites during the monitoring process.
    """
    
    # Required fields
    competitor: str = Field(
        ..., 
        description="Name of the competitor (e.g., 'West Elm', 'Crate & Barrel')",
        min_length=1,
        max_length=100
    )
    
    product_name: str = Field(
        ...,
        description="Name of the product",
        min_length=1,
        max_length=500
    )
    
    product_url: HttpUrl = Field(
        ...,
        description="Direct URL to the product page"
    )
    
    # Optional fields with validation
    brand: Optional[str] = Field(
        None,
        description="Brand name if different from competitor",
        max_length=100
    )
    
    category: Optional[ProductCategory] = Field(
        None,
        description="Product category classification"
    )
    
    price: Optional[Decimal] = Field(
        None,
        description="Product price in USD",
        ge=0,
        decimal_places=2
    )
    
    original_price: Optional[Decimal] = Field(
        None,
        description="Original price before discounts",
        ge=0,
        decimal_places=2
    )
    
    launch_date: Optional[datetime] = Field(
        None,
        description="Product launch date if available"
    )
    
    image_url: Optional[HttpUrl] = Field(
        None,
        description="URL to the main product image"
    )
    
    description: Optional[str] = Field(
        None,
        description="Product description",
        max_length=2000
    )
    
    availability: Optional[str] = Field(
        None,
        description="Product availability status",
        max_length=50
    )
    
    rating: Optional[float] = Field(
        None,
        description="Product rating (0.0 to 5.0)",
        ge=0.0,
        le=5.0
    )
    
    review_count: Optional[int] = Field(
        None,
        description="Number of customer reviews",
        ge=0
    )
    
    sku: Optional[str] = Field(
        None,
        description="Product SKU or model number",
        max_length=100
    )
    
    # Metadata fields
    collected_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when data was collected"
    )
    
    extraction_confidence: Optional[float] = Field(
        None,
        description="Confidence score of AI extraction (0.0 to 1.0)",
        ge=0.0,
        le=1.0
    )
    
    source_html_snippet: Optional[str] = Field(
        None,
        description="HTML snippet used for extraction",
        max_length=5000
    )
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        validate_assignment = True
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v) if v is not None else None
        }
    
    @validator('price', 'original_price')
    def validate_price_range(cls, v):
        """Validate that prices are within reasonable range."""
        if v is not None:
            if v < 0:
                raise ValueError("Price cannot be negative")
            if v > 100000:
                raise ValueError("Price seems unreasonably high")
        return v
    
    @validator('product_name')
    def validate_product_name(cls, v):
        """Clean and validate product name."""
        if v:
            # Remove excessive whitespace
            v = ' '.join(v.split())
            # Check for minimum meaningful length
            if len(v.strip()) < 2:
                raise ValueError("Product name too short")
        return v
    
    @validator('category')
    def validate_category(cls, v):
        """Validate product category."""
        if v and isinstance(v, str):
            try:
                return ProductCategory(v.lower())
            except ValueError:
                return ProductCategory.OTHER
        return v
    
    def to_csv_dict(self) -> dict:
        """
        Convert product to dictionary suitable for CSV export.
        
        Returns:
            dict: Flattened product data for CSV export
        """
        return {
            'competitor': self.competitor,
            'product_name': self.product_name,
            'brand': self.brand,
            'category': self.category.value if self.category else None,
            'price': float(self.price) if self.price else None,
            'original_price': float(self.original_price) if self.original_price else None,
            'launch_date': self.launch_date.strftime('%Y-%m-%d') if self.launch_date else None,
            'product_url': str(self.product_url),
            'image_url': str(self.image_url) if self.image_url else None,
            'description': self.description,
            'availability': self.availability,
            'rating': self.rating,
            'review_count': self.review_count,
            'sku': self.sku,
            'collected_at': self.collected_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def is_valid_for_export(self) -> bool:
        """
        Check if product has minimum required fields for export.
        
        Returns:
            bool: True if product meets minimum export requirements
        """
        return (
            self.competitor and 
            self.product_name and 
            self.product_url and
            len(self.product_name.strip()) >= 2
        )
    
    def get_unique_key(self) -> str:
        """
        Generate unique key for deduplication.
        
        Returns:
            str: Unique identifier for the product
        """
        return f"{self.competitor}:{str(self.product_url)}"


class ProductList(BaseModel):
    """Container for multiple products with metadata."""
    
    products: list[Product] = Field(default_factory=list)
    competitor: str
    collection_timestamp: datetime = Field(default_factory=datetime.utcnow)
    total_products: int = 0
    successful_extractions: int = 0
    failed_extractions: int = 0
    
    def add_product(self, product: Product) -> None:
        """Add a product to the list."""
        self.products.append(product)
        self.total_products = len(self.products)
    
    def get_valid_products(self) -> list[Product]:
        """Get only products that are valid for export."""
        return [p for p in self.products if p.is_valid_for_export()]
    
    def get_success_rate(self) -> float:
        """Calculate extraction success rate."""
        total = self.successful_extractions + self.failed_extractions
        return self.successful_extractions / total if total > 0 else 0.0
