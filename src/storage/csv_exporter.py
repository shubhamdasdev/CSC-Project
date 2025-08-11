"""
Simple CSV export functionality.
Minimal implementation for core deliverables.
"""

import csv
import os
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime


class CSVExporter:
    """Simple CSV export functionality."""
    
    def __init__(self, exports_dir: str = "data/exports"):
        """Initialize exporter with export directory."""
        self.exports_dir = Path(exports_dir)
        self.exports_dir.mkdir(parents=True, exist_ok=True)
    
    def export_products(self, products: List[Dict[str, Any]]) -> str:
        """
        Export products to CSV.
        
        Args:
            products: List of product dictionaries
            
        Returns:
            Path to exported CSV file
        """
        filename = "new_products.csv"
        filepath = self.exports_dir / filename
        
        # Define CSV columns
        columns = [
            'competitor',
            'product_name',
            'brand',
            'category',
            'price',
            'product_url',
            'image_url',
            'collected_at'
        ]
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=columns)
            writer.writeheader()
            
            for product in products:
                # Clean and prepare data
                row = {}
                for col in columns:
                    value = product.get(col, '')
                    
                    # Clean the value
                    if value is None:
                        value = ''
                    elif isinstance(value, (int, float)):
                        value = str(value)
                    else:
                        value = str(value).strip()
                    
                    row[col] = value
                
                # Add timestamp if not present
                if not row.get('collected_at'):
                    row['collected_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                writer.writerow(row)
        
        print(f"✅ Exported {len(products)} products to {filepath}")
        return str(filepath)
    
    def export_promotions(self, promotions: List[Dict[str, Any]]) -> str:
        """
        Export promotions to CSV.
        
        Args:
            promotions: List of promotion dictionaries
            
        Returns:
            Path to exported CSV file
        """
        filename = "current_promotions.csv"
        filepath = self.exports_dir / filename
        
        # Define CSV columns
        columns = [
            'competitor',
            'promo_title',
            'promo_type',
            'discount_value',
            'promo_code',
            'promo_url',
            'description',
            'collected_at'
        ]
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=columns)
            writer.writeheader()
            
            for promotion in promotions:
                # Clean and prepare data
                row = {}
                for col in columns:
                    value = promotion.get(col, '')
                    
                    # Clean the value
                    if value is None:
                        value = ''
                    elif isinstance(value, (int, float)):
                        value = str(value)
                    else:
                        value = str(value).strip()
                    
                    row[col] = value
                
                # Add timestamp if not present
                if not row.get('collected_at'):
                    row['collected_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                writer.writerow(row)
        
        print(f"✅ Exported {len(promotions)} promotions to {filepath}")
        return str(filepath)
    
    def validate_csv_file(self, filepath: str) -> Dict[str, Any]:
        """
        Validate exported CSV file.
        
        Args:
            filepath: Path to CSV file
            
        Returns:
            Validation results
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                rows = list(reader)
                
                if len(rows) < 2:  # Header + at least one data row
                    return {
                        'valid': False,
                        'error': 'No data rows found',
                        'row_count': len(rows) - 1 if rows else 0
                    }
                
                return {
                    'valid': True,
                    'row_count': len(rows) - 1,  # Exclude header
                    'column_count': len(rows[0]) if rows else 0,
                    'file_size': os.path.getsize(filepath)
                }
                
        except Exception as e:
            return {
                'valid': False,
                'error': str(e),
                'row_count': 0
            }


def test_csv_exporter():
    """Test CSV exporter with sample data."""
    exporter = CSVExporter()
    
    # Sample products
    products = [
        {
            'competitor': 'Test Store',
            'product_name': 'Modern Sofa',
            'brand': 'Test Brand',
            'category': 'furniture',
            'price': 899.99,
            'product_url': 'https://example.com/sofa',
            'image_url': 'https://example.com/sofa.jpg'
        },
        {
            'competitor': 'Test Store',
            'product_name': 'Dining Table',
            'brand': 'Test Brand', 
            'category': 'furniture',
            'price': 1299.99,
            'product_url': 'https://example.com/table'
        }
    ]
    
    # Sample promotions
    promotions = [
        {
            'competitor': 'Test Store',
            'promo_title': '20% Off Chairs',
            'promo_type': 'percentage_off',
            'discount_value': 20,
            'promo_code': 'CHAIR20',
            'description': '20% off all dining chairs'
        }
    ]
    
    # Export and validate
    product_file = exporter.export_products(products)
    promo_file = exporter.export_promotions(promotions)
    
    # Validate
    product_validation = exporter.validate_csv_file(product_file)
    promo_validation = exporter.validate_csv_file(promo_file)
    
    print(f"Products CSV: {product_validation}")
    print(f"Promotions CSV: {promo_validation}")
    
    return product_validation['valid'] and promo_validation['valid']


if __name__ == "__main__":
    success = test_csv_exporter()
    print(f"✅ CSV exporter test: {'PASSED' if success else 'FAILED'}")
