"""
Simple Firecrawl collector for web scraping.
Minimal implementation focused on core functionality.
"""

import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
from config.settings import get_settings


class FirecrawlCollector:
    """Simple Firecrawl integration for web scraping."""
    
    def __init__(self):
        """Initialize collector with settings."""
        self.settings = get_settings()
        self.api_key = self.settings.firecrawl_api_key
        self.base_url = "https://api.firecrawl.dev/v0"
    
    async def scrape_url(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Scrape a single URL using Firecrawl.
        
        Args:
            url: URL to scrape
            
        Returns:
            Dict with scraped content or None if failed
        """
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'url': url,
            'formats': ['markdown', 'html'],
            'onlyMainContent': True
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/scrape",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('success'):
                            return {
                                'url': url,
                                'markdown': data.get('data', {}).get('markdown', ''),
                                'html': data.get('data', {}).get('html', ''),
                                'title': data.get('data', {}).get('metadata', {}).get('title', ''),
                                'status': 'success'
                            }
                    
                    print(f"❌ Failed to scrape {url}: HTTP {response.status}")
                    return {'url': url, 'status': 'failed', 'error': f'HTTP {response.status}'}
                    
        except Exception as e:
            print(f"❌ Error scraping {url}: {e}")
            return {'url': url, 'status': 'failed', 'error': str(e)}
    
    async def scrape_competitor_urls(self, competitor_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Scrape all URLs for a competitor.
        
        Args:
            competitor_config: Competitor configuration
            
        Returns:
            List of scraped content
        """
        name = competitor_config.get('name', 'Unknown')
        print(f"🕷️ Scraping {name}...")
        
        # Get URLs (limit to 3-5 for speed)
        new_urls = competitor_config.get('new_urls', [])[:3]
        promo_urls = competitor_config.get('promo_urls', [])[:2]
        all_urls = new_urls + promo_urls
        
        results = []
        
        # Scrape URLs with basic rate limiting
        for url in all_urls:
            print(f"  📄 Scraping: {url}")
            result = await self.scrape_url(url)
            if result:
                result['competitor'] = name
                result['url_type'] = 'new' if url in new_urls else 'promo'
                results.append(result)
            
            # Simple rate limiting
            await asyncio.sleep(1)
        
        successful = len([r for r in results if r.get('status') == 'success'])
        print(f"  ✅ {successful}/{len(all_urls)} URLs scraped successfully")
        
        return results


async def test_collector():
    """Test the collector with a simple URL."""
    collector = FirecrawlCollector()
    
    # Test with a simple page
    result = await collector.scrape_url("https://httpbin.org/html")
    
    if result and result.get('status') == 'success':
        print("✅ Collector test successful!")
        print(f"Content length: {len(result.get('markdown', ''))}")
        return True
    else:
        print("❌ Collector test failed!")
        return False


if __name__ == "__main__":
    asyncio.run(test_collector())
