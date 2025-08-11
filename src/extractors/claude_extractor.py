"""
Simple Claude AI extractor for product and promotion data.
Minimal implementation focused on core functionality.
"""

import json
import asyncio
from typing import Dict, Any, List, Optional
import aiohttp
from config.settings import get_settings


class ClaudeExtractor:
    """Simple Claude AI integration for data extraction."""
    
    def __init__(self):
        """Initialize extractor with settings."""
        self.settings = get_settings()
        self.api_key = self.settings.claude_api_key
        self.base_url = "https://api.anthropic.com/v1"
    
    async def extract_products(self, content: str, competitor: str) -> List[Dict[str, Any]]:
        """
        Extract product data from content.
        
        Args:
            content: Scraped content (markdown/html)
            competitor: Competitor name
            
        Returns:
            List of extracted products
        """
        prompt = f"""
Extract product information from this {competitor} webpage content.

Return ONLY a JSON array of products. Each product should have:
- product_name: string
- brand: string (or "{competitor}" if not specified)
- category: string (furniture, home_decor, bedding, etc.)
- price: number (extract numeric value only, no currency symbols)
- product_url: string (if found in content)
- image_url: string (if found)

Only extract products that are clearly listed with names and prices. Skip navigation, headers, footers.

Content:
{content[:3000]}

Return only valid JSON array:
"""
        
        try:
            response = await self._call_claude(prompt)
            if response:
                # Try to parse JSON from response
                json_start = response.find('[')
                json_end = response.rfind(']') + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_str = response[json_start:json_end]
                    products = json.loads(json_str)
                    
                    # Add competitor info
                    for product in products:
                        product['competitor'] = competitor
                        if not product.get('brand'):
                            product['brand'] = competitor
                    
                    print(f"  📦 Extracted {len(products)} products")
                    return products
                    
        except json.JSONDecodeError as e:
            print(f"  ❌ JSON parsing error: {e}")
        except Exception as e:
            print(f"  ❌ Product extraction error: {e}")
        
        return []
    
    async def extract_promotions(self, content: str, competitor: str) -> List[Dict[str, Any]]:
        """
        Extract promotion data from content.
        
        Args:
            content: Scraped content (markdown/html)
            competitor: Competitor name
            
        Returns:
            List of extracted promotions
        """
        prompt = f"""
Extract promotion information from this {competitor} webpage content.

Return ONLY a JSON array of promotions. Each promotion should have:
- promo_title: string
- promo_type: string (percentage_off, dollar_off, free_shipping, clearance, etc.)
- discount_value: number (percentage or dollar amount)
- promo_code: string (if any)
- promo_url: string (if found)
- description: string (brief description)

Only extract clear promotional offers, sales, discounts. Skip regular products.

Content:
{content[:3000]}

Return only valid JSON array:
"""
        
        try:
            response = await self._call_claude(prompt)
            if response:
                # Try to parse JSON from response
                json_start = response.find('[')
                json_end = response.rfind(']') + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_str = response[json_start:json_end]
                    promotions = json.loads(json_str)
                    
                    # Add competitor info
                    for promo in promotions:
                        promo['competitor'] = competitor
                    
                    print(f"  🎯 Extracted {len(promotions)} promotions")
                    return promotions
                    
        except json.JSONDecodeError as e:
            print(f"  ❌ JSON parsing error: {e}")
        except Exception as e:
            print(f"  ❌ Promotion extraction error: {e}")
        
        return []
    
    async def _call_claude(self, prompt: str) -> Optional[str]:
        """
        Make API call to Claude.
        
        Args:
            prompt: Prompt to send
            
        Returns:
            Response text or None if failed
        """
        headers = {
            'x-api-key': self.api_key,
            'Content-Type': 'application/json',
            'anthropic-version': '2023-06-01'
        }
        
        payload = {
            'model': 'claude-3-haiku-20240307',
            'max_tokens': 2000,
            'messages': [
                {
                    'role': 'user',
                    'content': prompt
                }
            ]
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/messages",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('content') and len(data['content']) > 0:
                            return data['content'][0].get('text', '')
                    else:
                        print(f"  ❌ Claude API error: HTTP {response.status}")
                        
        except Exception as e:
            print(f"  ❌ Claude API call error: {e}")
        
        return None


async def test_extractor():
    """Test the extractor with sample content."""
    extractor = ClaudeExtractor()
    
    sample_content = """
    # New Furniture Collection
    
    ## Modern Sofa - $899
    Contemporary 3-seat sofa in gray fabric
    
    ## Dining Table - $1,299  
    Oak dining table seats 6 people
    
    ## Sale: 20% Off All Chairs
    Use code CHAIR20 for 20% off dining chairs
    """
    
    products = await extractor.extract_products(sample_content, "Test Store")
    promotions = await extractor.extract_promotions(sample_content, "Test Store")
    
    print(f"✅ Test complete: {len(products)} products, {len(promotions)} promotions")
    return len(products) > 0 or len(promotions) > 0


if __name__ == "__main__":
    asyncio.run(test_extractor())
