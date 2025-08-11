"""
Promotion data model for competitive intelligence system.

This module defines the Promotion model using Pydantic for data validation
and serialization of promotional information collected from competitor websites.
"""

from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, Field, validator, HttpUrl
from enum import Enum


class PromotionType(str, Enum):
    """Promotion type enumeration."""
    PERCENTAGE_OFF = "percentage_off"
    DOLLAR_OFF = "dollar_off"
    BOGO = "buy_one_get_one"
    FREE_SHIPPING = "free_shipping"
    FLASH_SALE = "flash_sale"
    CLEARANCE = "clearance"
    BUNDLE_DEAL = "bundle_deal"
    NEW_CUSTOMER = "new_customer"
    LOYALTY_PROGRAM = "loyalty_program"
    SEASONAL_SALE = "seasonal_sale"
    OTHER = "other"


class PromotionStatus(str, Enum):
    """Promotion status enumeration."""
    ACTIVE = "active"
    UPCOMING = "upcoming"
    EXPIRED = "expired"
    UNKNOWN = "unknown"


class Promotion(BaseModel):
    """
    Promotion data model for storing promotional information.
    
    This model validates and structures promotion data collected
    from competitor websites during the monitoring process.
    """
    
    # Required fields
    competitor: str = Field(
        ..., 
        description="Name of the competitor (e.g., 'West Elm', 'Crate & Barrel')",
        min_length=1,
        max_length=100
    )
    
    promo_title: str = Field(
        ...,
        description="Title or headline of the promotion",
        min_length=1,
        max_length=500
    )
    
    promo_url: HttpUrl = Field(
        ...,
        description="Direct URL to the promotion page"
    )
    
    # Promotion details
    promo_type: PromotionType = Field(
        ...,
        description="Type of promotion"
    )
    
    # Optional fields with validation
    promo_code: Optional[str] = Field(
        None,
        description="Promotional code if applicable",
        max_length=50
    )
    
    discount_value: Optional[float] = Field(
        None,
        description="Discount value (percentage for % off, dollar amount for $ off)",
        ge=0
    )
    
    minimum_purchase: Optional[float] = Field(
        None,
        description="Minimum purchase amount required",
        ge=0
    )
    
    start_date: Optional[date] = Field(
        None,
        description="Promotion start date"
    )
    
    end_date: Optional[date] = Field(
        None,
        description="Promotion end date"
    )
    
    status: PromotionStatus = Field(
        default=PromotionStatus.UNKNOWN,
        description="Current status of the promotion"
    )
    
    applicable_products: Optional[str] = Field(
        None,
        description="Description of applicable products or categories",
        max_length=1000
    )
    
    exclusions: Optional[str] = Field(
        None,
        description="Products or categories excluded from promotion",
        max_length=1000
    )
    
    image_url: Optional[HttpUrl] = Field(
        None,
        description="URL to the promotional image or banner"
    )
    
    description: Optional[str] = Field(
        None,
        description="Detailed promotion description",
        max_length=2000
    )
    
    terms_and_conditions: Optional[str] = Field(
        None,
        description="Terms and conditions text",
        max_length=3000
    )
    
    priority: Optional[int] = Field(
        None,
        description="Promotion priority (1=highest, 5=lowest)",
        ge=1,
        le=5
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
            date: lambda v: v.isoformat()
        }
    
    @validator('promo_title')
    def validate_promo_title(cls, v):
        """Clean and validate promotion title."""
        if v:
            # Remove excessive whitespace
            v = ' '.join(v.split())
            # Check for minimum meaningful length
            if len(v.strip()) < 2:
                raise ValueError("Promotion title too short")
        return v
    
    @validator('discount_value')
    def validate_discount_value(cls, v, values):
        """Validate discount value based on promotion type."""
        if v is not None:
            promo_type = values.get('promo_type')
            if promo_type == PromotionType.PERCENTAGE_OFF and v > 100:
                raise ValueError("Percentage discount cannot exceed 100%")
            if promo_type == PromotionType.DOLLAR_OFF and v > 10000:
                raise ValueError("Dollar discount seems unreasonably high")
        return v
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        """Validate that end date is after start date."""
        if v is not None and 'start_date' in values:
            start_date = values['start_date']
            if start_date is not None and v < start_date:
                raise ValueError("End date cannot be before start date")
        return v
    
    @validator('promo_code')
    def validate_promo_code(cls, v):
        """Clean and validate promotion code."""
        if v:
            v = v.strip().upper()
            # Remove common prefixes that might be extracted by mistake
            prefixes_to_remove = ['CODE:', 'PROMO:', 'USE:', 'COUPON:']
            for prefix in prefixes_to_remove:
                if v.startswith(prefix):
                    v = v[len(prefix):].strip()
        return v if v else None
    
    def is_currently_active(self) -> bool:
        """
        Check if promotion is currently active based on dates.
        
        Returns:
            bool: True if promotion is currently active
        """
        today = date.today()
        
        # If no dates provided, assume active
        if not self.start_date and not self.end_date:
            return self.status == PromotionStatus.ACTIVE
        
        # Check date range
        if self.start_date and today < self.start_date:
            return False
        
        if self.end_date and today > self.end_date:
            return False
        
        return True
    
    def get_days_remaining(self) -> Optional[int]:
        """
        Get number of days remaining for the promotion.
        
        Returns:
            Optional[int]: Days remaining, None if no end date
        """
        if not self.end_date:
            return None
        
        today = date.today()
        delta = self.end_date - today
        return max(0, delta.days)
    
    def to_csv_dict(self) -> dict:
        """
        Convert promotion to dictionary suitable for CSV export.
        
        Returns:
            dict: Flattened promotion data for CSV export
        """
        return {
            'competitor': self.competitor,
            'promo_title': self.promo_title,
            'promo_type': self.promo_type.value,
            'promo_code': self.promo_code,
            'discount_value': self.discount_value,
            'minimum_purchase': self.minimum_purchase,
            'start_date': self.start_date.strftime('%Y-%m-%d') if self.start_date else None,
            'end_date': self.end_date.strftime('%Y-%m-%d') if self.end_date else None,
            'status': self.status.value,
            'applicable_products': self.applicable_products,
            'exclusions': self.exclusions,
            'promo_url': str(self.promo_url),
            'image_url': str(self.image_url) if self.image_url else None,
            'description': self.description,
            'terms_and_conditions': self.terms_and_conditions,
            'priority': self.priority,
            'collected_at': self.collected_at.strftime('%Y-%m-%d %H:%M:%S'),
            'days_remaining': self.get_days_remaining(),
            'is_active': self.is_currently_active()
        }
    
    def is_valid_for_export(self) -> bool:
        """
        Check if promotion has minimum required fields for export.
        
        Returns:
            bool: True if promotion meets minimum export requirements
        """
        return (
            self.competitor and 
            self.promo_title and 
            self.promo_url and
            self.promo_type and
            len(self.promo_title.strip()) >= 2
        )
    
    def get_unique_key(self) -> str:
        """
        Generate unique key for deduplication.
        
        Returns:
            str: Unique identifier for the promotion
        """
        return f"{self.competitor}:{str(self.promo_url)}:{self.promo_title.lower()}"


class PromotionList(BaseModel):
    """Container for multiple promotions with metadata."""
    
    promotions: list[Promotion] = Field(default_factory=list)
    competitor: str
    collection_timestamp: datetime = Field(default_factory=datetime.utcnow)
    total_promotions: int = 0
    active_promotions: int = 0
    upcoming_promotions: int = 0
    expired_promotions: int = 0
    successful_extractions: int = 0
    failed_extractions: int = 0
    
    def add_promotion(self, promotion: Promotion) -> None:
        """Add a promotion to the list and update counters."""
        self.promotions.append(promotion)
        self.total_promotions = len(self.promotions)
        self._update_status_counts()
    
    def _update_status_counts(self) -> None:
        """Update promotion status counters."""
        self.active_promotions = sum(1 for p in self.promotions if p.is_currently_active())
        self.upcoming_promotions = sum(1 for p in self.promotions if p.status == PromotionStatus.UPCOMING)
        self.expired_promotions = sum(1 for p in self.promotions if p.status == PromotionStatus.EXPIRED)
    
    def get_valid_promotions(self) -> list[Promotion]:
        """Get only promotions that are valid for export."""
        return [p for p in self.promotions if p.is_valid_for_export()]
    
    def get_active_promotions(self) -> list[Promotion]:
        """Get only currently active promotions."""
        return [p for p in self.promotions if p.is_currently_active()]
    
    def get_success_rate(self) -> float:
        """Calculate extraction success rate."""
        total = self.successful_extractions + self.failed_extractions
        return self.successful_extractions / total if total > 0 else 0.0
