"""
Competitor configuration model for competitive intelligence system.

This module defines the Competitor model using Pydantic for data validation
and configuration management of competitor monitoring settings.
"""

from typing import Optional, List
from pydantic import BaseModel, Field, validator, HttpUrl


class CrawlSettings(BaseModel):
    """Crawling configuration for a competitor."""
    
    depth: int = Field(
        default=2,
        description="Maximum crawl depth",
        ge=1,
        le=5
    )
    
    limit: int = Field(
        default=50,
        description="Maximum number of pages to crawl per URL",
        ge=1,
        le=1000
    )
    
    delay: float = Field(
        default=1.0,
        description="Delay between requests in seconds",
        ge=0.1,
        le=10.0
    )
    
    timeout: int = Field(
        default=30,
        description="Request timeout in seconds",
        ge=5,
        le=300
    )
    
    retries: int = Field(
        default=3,
        description="Number of retry attempts",
        ge=0,
        le=10
    )


class Competitor(BaseModel):
    """
    Competitor configuration model.
    
    This model defines the configuration for monitoring a specific competitor,
    including URLs to crawl and crawling parameters.
    """
    
    name: str = Field(
        ...,
        description="Competitor name (e.g., 'West Elm', 'Crate & Barrel')",
        min_length=1,
        max_length=100
    )
    
    new_urls: List[HttpUrl] = Field(
        ...,
        description="URLs for new product pages",
        min_items=1
    )
    
    promo_urls: List[HttpUrl] = Field(
        ...,
        description="URLs for promotion pages",
        min_items=1
    )
    
    crawl: CrawlSettings = Field(
        default_factory=CrawlSettings,
        description="Crawling configuration"
    )
    
    # Optional fields
    description: Optional[str] = Field(
        None,
        description="Description of the competitor",
        max_length=500
    )
    
    website: Optional[HttpUrl] = Field(
        None,
        description="Main website URL"
    )
    
    priority: int = Field(
        default=1,
        description="Competitor priority (1=highest, 5=lowest)",
        ge=1,
        le=5
    )
    
    enabled: bool = Field(
        default=True,
        description="Whether this competitor is enabled for monitoring"
    )
    
    tags: List[str] = Field(
        default_factory=list,
        description="Tags for categorizing competitors"
    )
    
    # Advanced settings
    custom_headers: dict = Field(
        default_factory=dict,
        description="Custom HTTP headers for requests"
    )
    
    user_agent: Optional[str] = Field(
        None,
        description="Custom user agent string"
    )
    
    exclude_patterns: List[str] = Field(
        default_factory=list,
        description="URL patterns to exclude from crawling"
    )
    
    class Config:
        """Pydantic configuration."""
        validate_assignment = True
        arbitrary_types_allowed = True
    
    @validator('name')
    def validate_name(cls, v):
        """Clean and validate competitor name."""
        if v:
            v = v.strip()
            if len(v) < 1:
                raise ValueError("Competitor name cannot be empty")
        return v
    
    @validator('new_urls', 'promo_urls')
    def validate_url_lists(cls, v):
        """Validate URL lists are not empty."""
        if not v:
            raise ValueError("URL list cannot be empty")
        return v
    
    @validator('tags')
    def validate_tags(cls, v):
        """Clean and validate tags."""
        if v:
            # Remove duplicates and clean whitespace
            cleaned_tags = []
            for tag in v:
                tag = tag.strip().lower()
                if tag and tag not in cleaned_tags:
                    cleaned_tags.append(tag)
            return cleaned_tags
        return v
    
    def get_all_urls(self) -> List[HttpUrl]:
        """
        Get all URLs for this competitor.
        
        Returns:
            List[HttpUrl]: Combined list of new product and promotion URLs
        """
        return list(self.new_urls) + list(self.promo_urls)
    
    def get_total_url_count(self) -> int:
        """
        Get total number of URLs to monitor.
        
        Returns:
            int: Total count of URLs
        """
        return len(self.new_urls) + len(self.promo_urls)
    
    def get_estimated_pages(self) -> int:
        """
        Estimate total pages to be crawled based on configuration.
        
        Returns:
            int: Estimated number of pages
        """
        base_pages = self.get_total_url_count()
        # Estimate additional pages based on depth and limit
        estimated_additional = base_pages * min(self.crawl.depth - 1, self.crawl.limit // 10)
        return base_pages + estimated_additional
    
    def get_estimated_time_minutes(self) -> float:
        """
        Estimate crawling time in minutes.
        
        Returns:
            float: Estimated time in minutes
        """
        estimated_requests = self.get_estimated_pages()
        total_delay = estimated_requests * self.crawl.delay
        # Add processing time estimate (0.5 seconds per page)
        processing_time = estimated_requests * 0.5
        return (total_delay + processing_time) / 60
    
    def is_url_excluded(self, url: str) -> bool:
        """
        Check if URL matches exclusion patterns.
        
        Args:
            url: URL to check
            
        Returns:
            bool: True if URL should be excluded
        """
        for pattern in self.exclude_patterns:
            if pattern in url:
                return True
        return False


class GlobalSettings(BaseModel):
    """Global crawling settings that apply to all competitors."""
    
    user_agent: str = Field(
        default="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        description="Default user agent string"
    )
    
    max_retries: int = Field(
        default=3,
        description="Default maximum retries",
        ge=0,
        le=10
    )
    
    timeout: int = Field(
        default=30,
        description="Default timeout in seconds",
        ge=5,
        le=300
    )
    
    respect_robots_txt: bool = Field(
        default=True,
        description="Whether to respect robots.txt"
    )
    
    concurrent_requests: int = Field(
        default=5,
        description="Number of concurrent requests",
        ge=1,
        le=20
    )
    
    rate_limit_per_minute: int = Field(
        default=60,
        description="Rate limit per minute",
        ge=1,
        le=1000
    )


class CompetitorConfig(BaseModel):
    """Complete competitor configuration including all competitors and global settings."""
    
    competitors: List[Competitor] = Field(
        ...,
        description="List of competitors to monitor",
        min_items=1
    )
    
    global_settings: GlobalSettings = Field(
        default_factory=GlobalSettings,
        description="Global crawling settings"
    )
    
    def get_enabled_competitors(self) -> List[Competitor]:
        """Get only enabled competitors."""
        return [c for c in self.competitors if c.enabled]
    
    def get_competitor_by_name(self, name: str) -> Optional[Competitor]:
        """Get competitor by name."""
        for competitor in self.competitors:
            if competitor.name.lower() == name.lower():
                return competitor
        return None
    
    def get_total_estimated_time(self) -> float:
        """Get total estimated crawling time for all enabled competitors."""
        return sum(c.get_estimated_time_minutes() for c in self.get_enabled_competitors())
    
    def get_total_estimated_pages(self) -> int:
        """Get total estimated pages for all enabled competitors."""
        return sum(c.get_estimated_pages() for c in self.get_enabled_competitors())
    
    def validate_time_constraint(self, max_minutes: int = 80) -> tuple[bool, str]:
        """
        Validate that estimated time is within constraint.
        
        Args:
            max_minutes: Maximum allowed time in minutes
            
        Returns:
            tuple: (is_valid, message)
        """
        estimated_time = self.get_total_estimated_time()
        
        if estimated_time > max_minutes:
            return False, f"Estimated time ({estimated_time:.1f}min) exceeds limit ({max_minutes}min)"
        
        return True, f"Estimated time ({estimated_time:.1f}min) within limit"
