"""
Data validation utilities for the competitive intelligence system.

This module provides utility functions for validating URLs, data quality,
and other validation tasks throughout the pipeline.
"""

import re
import validators
from typing import Optional, List, Tuple
from urllib.parse import urlparse
import requests
from datetime import datetime


class URLValidator:
    """URL validation utilities."""
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """
        Check if URL is valid.
        
        Args:
            url: URL to validate
            
        Returns:
            bool: True if URL is valid
        """
        try:
            return bool(validators.url(url))
        except Exception:
            return False
    
    @staticmethod
    def is_accessible(url: str, timeout: int = 10) -> Tuple[bool, Optional[str]]:
        """
        Check if URL is accessible.
        
        Args:
            url: URL to check
            timeout: Request timeout in seconds
            
        Returns:
            tuple: (is_accessible, error_message)
        """
        try:
            response = requests.head(
                url,
                timeout=timeout,
                allow_redirects=True,
                headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
            )
            if response.status_code == 405:  # Method not allowed, try GET
                response = requests.get(url, timeout=timeout, stream=True)
                # Close the connection immediately to avoid downloading content
                response.close()
            
            return response.status_code < 400, None
            
        except requests.exceptions.Timeout:
            return False, "Request timeout"
        except requests.exceptions.ConnectionError:
            return False, "Connection error"
        except requests.exceptions.RequestException as e:
            return False, f"Request error: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
    
    @staticmethod
    def normalize_url(url: str) -> str:
        """
        Normalize URL for consistent comparison.
        
        Args:
            url: URL to normalize
            
        Returns:
            str: Normalized URL
        """
        if not url:
            return url
        
        # Ensure URL has scheme
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Parse and reconstruct
        parsed = urlparse(url)
        
        # Remove default ports
        port = parsed.port
        if port and ((parsed.scheme == 'http' and port == 80) or 
                    (parsed.scheme == 'https' and port == 443)):
            netloc = parsed.hostname
        else:
            netloc = parsed.netloc
        
        # Remove trailing slash from path (except for root)
        path = parsed.path.rstrip('/') if parsed.path != '/' else parsed.path
        
        # Reconstruct URL
        normalized = f"{parsed.scheme}://{netloc}{path}"
        if parsed.query:
            normalized += f"?{parsed.query}"
        if parsed.fragment:
            normalized += f"#{parsed.fragment}"
        
        return normalized
    
    @staticmethod
    def get_domain(url: str) -> Optional[str]:
        """
        Extract domain from URL.
        
        Args:
            url: URL to extract domain from
            
        Returns:
            Optional[str]: Domain name or None if invalid URL
        """
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower()
        except Exception:
            return None


class PriceValidator:
    """Price validation utilities."""
    
    @staticmethod
    def extract_price(text: str) -> Optional[float]:
        """
        Extract price from text string.
        
        Args:
            text: Text containing price information
            
        Returns:
            Optional[float]: Extracted price or None if not found
        """
        if not text:
            return None
        
        # Common price patterns
        price_patterns = [
            r'\$\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',  # $1,234.56
            r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*\$',  # 1234.56$
            r'USD\s*(\d+(?:,\d{3})*(?:\.\d{2})?)', # USD 1234.56
            r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*USD', # 1234.56 USD
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                price_str = match.group(1).replace(',', '')
                try:
                    return float(price_str)
                except ValueError:
                    continue
        
        return None
    
    @staticmethod
    def is_reasonable_price(price: float, min_price: float = 0.01, max_price: float = 100000.0) -> bool:
        """
        Check if price is within reasonable range.
        
        Args:
            price: Price to validate
            min_price: Minimum acceptable price
            max_price: Maximum acceptable price
            
        Returns:
            bool: True if price is reasonable
        """
        return min_price <= price <= max_price


class DateValidator:
    """Date validation utilities."""
    
    @staticmethod
    def parse_date(date_str: str) -> Optional[datetime]:
        """
        Parse date string in various formats.
        
        Args:
            date_str: Date string to parse
            
        Returns:
            Optional[datetime]: Parsed date or None if parsing fails
        """
        if not date_str:
            return None
        
        # Common date formats
        formats = [
            "%Y-%m-%d",           # 2024-01-15
            "%m/%d/%Y",           # 01/15/2024
            "%d/%m/%Y",           # 15/01/2024
            "%B %d, %Y",          # January 15, 2024
            "%b %d, %Y",          # Jan 15, 2024
            "%d %B %Y",           # 15 January 2024
            "%d %b %Y",           # 15 Jan 2024
            "%Y-%m-%d %H:%M:%S",  # 2024-01-15 10:30:45
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue
        
        return None


class TextValidator:
    """Text validation utilities."""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """
        Clean and normalize text.
        
        Args:
            text: Text to clean
            
        Returns:
            str: Cleaned text
        """
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove control characters
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
        
        return text
    
    @staticmethod
    def is_meaningful_text(text: str, min_length: int = 2) -> bool:
        """
        Check if text is meaningful (not just whitespace or special characters).
        
        Args:
            text: Text to validate
            min_length: Minimum meaningful length
            
        Returns:
            bool: True if text is meaningful
        """
        if not text:
            return False
        
        cleaned = TextValidator.clean_text(text)
        if len(cleaned) < min_length:
            return False
        
        # Check if text contains at least some alphanumeric characters
        return bool(re.search(r'[a-zA-Z0-9]', cleaned))
    
    @staticmethod
    def extract_text_from_html(html: str) -> str:
        """
        Extract text content from HTML.
        
        Args:
            html: HTML content
            
        Returns:
            str: Extracted text
        """
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text and clean it
            text = soup.get_text()
            return TextValidator.clean_text(text)
            
        except Exception:
            return ""


class DataQualityValidator:
    """Data quality validation utilities."""
    
    @staticmethod
    def validate_product_data(product_data: dict) -> List[str]:
        """
        Validate product data quality.
        
        Args:
            product_data: Product data dictionary
            
        Returns:
            List[str]: List of validation errors
        """
        errors = []
        
        # Check required fields
        required_fields = ['competitor', 'product_name', 'product_url']
        for field in required_fields:
            if not product_data.get(field):
                errors.append(f"Missing required field: {field}")
        
        # Validate URL
        if product_data.get('product_url'):
            if not URLValidator.is_valid_url(product_data['product_url']):
                errors.append("Invalid product URL")
        
        # Validate price
        if product_data.get('price'):
            try:
                price = float(product_data['price'])
                if not PriceValidator.is_reasonable_price(price):
                    errors.append("Price outside reasonable range")
            except (ValueError, TypeError):
                errors.append("Invalid price format")
        
        # Validate text fields
        if product_data.get('product_name'):
            if not TextValidator.is_meaningful_text(product_data['product_name']):
                errors.append("Product name is not meaningful")
        
        return errors
    
    @staticmethod
    def validate_promotion_data(promotion_data: dict) -> List[str]:
        """
        Validate promotion data quality.
        
        Args:
            promotion_data: Promotion data dictionary
            
        Returns:
            List[str]: List of validation errors
        """
        errors = []
        
        # Check required fields
        required_fields = ['competitor', 'promo_title', 'promo_url', 'promo_type']
        for field in required_fields:
            if not promotion_data.get(field):
                errors.append(f"Missing required field: {field}")
        
        # Validate URL
        if promotion_data.get('promo_url'):
            if not URLValidator.is_valid_url(promotion_data['promo_url']):
                errors.append("Invalid promotion URL")
        
        # Validate discount value
        if promotion_data.get('discount_value'):
            try:
                discount = float(promotion_data['discount_value'])
                promo_type = promotion_data.get('promo_type', '').lower()
                
                if 'percentage' in promo_type and discount > 100:
                    errors.append("Percentage discount cannot exceed 100%")
                elif discount < 0:
                    errors.append("Discount value cannot be negative")
                elif discount > 10000:
                    errors.append("Discount value seems unreasonably high")
                    
            except (ValueError, TypeError):
                errors.append("Invalid discount value format")
        
        # Validate text fields
        if promotion_data.get('promo_title'):
            if not TextValidator.is_meaningful_text(promotion_data['promo_title']):
                errors.append("Promotion title is not meaningful")
        
        return errors
    
    @staticmethod
    def calculate_quality_score(data: dict, data_type: str) -> float:
        """
        Calculate data quality score (0.0 to 1.0).
        
        Args:
            data: Data dictionary to score
            data_type: Type of data ('product' or 'promotion')
            
        Returns:
            float: Quality score between 0.0 and 1.0
        """
        if data_type == 'product':
            errors = DataQualityValidator.validate_product_data(data)
            total_checks = 8  # Approximate number of validation checks
        elif data_type == 'promotion':
            errors = DataQualityValidator.validate_promotion_data(data)
            total_checks = 7  # Approximate number of validation checks
        else:
            return 0.0
        
        # Calculate score based on number of errors
        error_count = len(errors)
        score = max(0.0, (total_checks - error_count) / total_checks)
        
        return score
