#!/usr/bin/env python3
"""
Main pipeline runner for competitive intelligence system.
Streamlined version focused on core deliverables.
"""

import sys
import asyncio
from pathlib import Path
from datetime import datetime

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import load_competitor_config
from src.collectors.firecrawl_collector import FirecrawlCollector
from src.extractors.claude_extractor import ClaudeExtractor
from src.storage.csv_exporter import CSVExporter


class CompetitorMonitorPipeline:
    """Main pipeline for competitive intelligence."""
    
    def __init__(self):
        """Initialize pipeline components."""
        self.collector = FirecrawlCollector()
        self.extractor = ClaudeExtractor()
        self.exporter = CSVExporter()
        
        self.all_products = []
        self.all_promotions = []
    
    async def run_full_pipeline(self) -> bool:
        """
        Run the complete competitive intelligence pipeline.
        
        Returns:
            bool: True if successful
        """
        start_time = datetime.now()
        print("🚀 Starting Competitive Intelligence Pipeline")
        print(f"⏰ Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        try:
            # Load competitor configuration
            print("📋 Loading competitor configuration...")
            config = load_competitor_config()
            competitors = config.get('competitors', [])[:2]  # Limit to 2 for speed
            
            if not competitors:
                print("❌ No competitors found in configuration")
                return False
            
            print(f"🎯 Monitoring {len(competitors)} competitors")
            
            # Process each competitor
            for i, competitor in enumerate(competitors, 1):
                name = competitor.get('name', f'Competitor_{i}')
                print(f"\n📊 Processing {name} ({i}/{len(competitors)})")
                
                success = await self.process_competitor(competitor)
                if not success:
                    print(f"⚠️ Failed to process {name}, continuing...")
            
            # Export data
            print(f"\n💾 Exporting data...")
            await self.export_results()
            
            # Summary
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            print("\n" + "="*60)
            print("📊 PIPELINE SUMMARY")
            print("="*60)
            print(f"⏱️  Duration: {duration:.1f} seconds ({duration/60:.1f} minutes)")
            print(f"📦 Products extracted: {len(self.all_products)}")
            print(f"🎯 Promotions extracted: {len(self.all_promotions)}")
            print(f"✅ Pipeline completed successfully!")
            
            return True
            
        except Exception as e:
            print(f"\n💥 Pipeline failed: {e}")
            return False
    
    async def process_competitor(self, competitor_config: dict) -> bool:
        """
        Process a single competitor.
        
        Args:
            competitor_config: Competitor configuration
            
        Returns:
            bool: True if successful
        """
        name = competitor_config.get('name', 'Unknown')
        
        try:
            # Step 1: Scrape URLs
            scraped_data = await self.collector.scrape_competitor_urls(competitor_config)
            
            if not scraped_data:
                print(f"  ❌ No data scraped for {name}")
                return False
            
            # Step 2: Extract data from scraped content
            competitor_products = []
            competitor_promotions = []
            
            for page_data in scraped_data:
                if page_data.get('status') != 'success':
                    continue
                
                content = page_data.get('markdown', '') or page_data.get('html', '')
                if not content:
                    continue
                
                url_type = page_data.get('url_type', 'unknown')
                
                # Extract products from new product pages
                if url_type == 'new' or 'new' in page_data.get('url', '').lower():
                    print(f"    🔍 Extracting products from: {page_data.get('url', '')[:50]}...")
                    products = await self.extractor.extract_products(content, name)
                    competitor_products.extend(products)
                
                # Extract promotions from promo pages
                if url_type == 'promo' or any(term in page_data.get('url', '').lower() 
                                              for term in ['sale', 'promo', 'discount', 'clearance']):
                    print(f"    🔍 Extracting promotions from: {page_data.get('url', '')[:50]}...")
                    promotions = await self.extractor.extract_promotions(content, name)
                    competitor_promotions.extend(promotions)
            
            # Add to overall results
            self.all_products.extend(competitor_products)
            self.all_promotions.extend(competitor_promotions)
            
            print(f"  ✅ {name}: {len(competitor_products)} products, {len(competitor_promotions)} promotions")
            return True
            
        except Exception as e:
            print(f"  ❌ Error processing {name}: {e}")
            return False
    
    async def export_results(self) -> None:
        """Export all results to CSV files."""
        try:
            # Export products
            if self.all_products:
                product_file = self.exporter.export_products(self.all_products)
                validation = self.exporter.validate_csv_file(product_file)
                print(f"  📦 Products: {validation.get('row_count', 0)} rows → {product_file}")
            else:
                print("  📦 No products to export")
            
            # Export promotions
            if self.all_promotions:
                promo_file = self.exporter.export_promotions(self.all_promotions)
                validation = self.exporter.validate_csv_file(promo_file)
                print(f"  🎯 Promotions: {validation.get('row_count', 0)} rows → {promo_file}")
            else:
                print("  🎯 No promotions to export")
                
        except Exception as e:
            print(f"  ❌ Export error: {e}")


async def main():
    """Main function."""
    print("🎯 CSC Competitive Intelligence Pipeline")
    print("⚡ Streamlined version for rapid deployment")
    print()
    
    try:
        pipeline = CompetitorMonitorPipeline()
        success = await pipeline.run_full_pipeline()
        
        if success:
            print("\n🎉 SUCCESS: Pipeline completed successfully!")
            print("📁 Check data/exports/ for CSV files")
            sys.exit(0)
        else:
            print("\n❌ FAILED: Pipeline encountered errors")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
