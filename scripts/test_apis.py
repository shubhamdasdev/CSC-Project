#!/usr/bin/env python3
"""
API connectivity testing script.

This script tests the connectivity and configuration of all external APIs
used by the competitive intelligence system.
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
import aiohttp
from datetime import datetime
from typing import Dict, Any, Optional

from config.settings import get_settings, validate_api_keys
from src.utils.validators import URLValidator


class APITester:
    """Test connectivity to external APIs."""
    
    def __init__(self):
        """Initialize API tester with settings."""
        self.settings = get_settings()
        self.results = {}
    
    async def test_firecrawl_api(self) -> Dict[str, Any]:
        """
        Test Firecrawl API connectivity.
        
        Returns:
            dict: Test results
        """
        result = {
            'service': 'Firecrawl',
            'status': 'unknown',
            'message': '',
            'response_time': None,
            'error': None
        }
        
        try:
            start_time = datetime.now()
            
            # Test API key format (basic validation)
            api_key = self.settings.firecrawl_api_key
            if not api_key or api_key == "your_firecrawl_api_key_here":
                result.update({
                    'status': 'error',
                    'message': 'API key not configured',
                    'error': 'FIRECRAWL_API_KEY is missing or using placeholder value'
                })
                return result
            
            # Try to make a simple API call
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            # Test with a simple scrape request
            async with aiohttp.ClientSession() as session:
                test_data = {
                    'url': 'https://httpbin.org/html',
                    'formats': ['markdown']
                }
                
                async with session.post(
                    'https://api.firecrawl.dev/v0/scrape',
                    json=test_data,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    response_time = (datetime.now() - start_time).total_seconds()
                    result['response_time'] = response_time
                    
                    if response.status == 200:
                        data = await response.json()
                        if data.get('success'):
                            result.update({
                                'status': 'success',
                                'message': f'API working correctly (response time: {response_time:.2f}s)'
                            })
                        else:
                            result.update({
                                'status': 'error',
                                'message': 'API returned unsuccessful response',
                                'error': data.get('error', 'Unknown error')
                            })
                    elif response.status == 401:
                        result.update({
                            'status': 'error',
                            'message': 'Authentication failed',
                            'error': 'Invalid API key'
                        })
                    elif response.status == 429:
                        result.update({
                            'status': 'warning',
                            'message': 'Rate limit exceeded',
                            'error': 'Too many requests'
                        })
                    else:
                        result.update({
                            'status': 'error',
                            'message': f'HTTP {response.status}',
                            'error': await response.text()
                        })
        
        except aiohttp.ClientTimeout:
            result.update({
                'status': 'error',
                'message': 'Request timeout',
                'error': 'API request timed out after 30 seconds'
            })
        except aiohttp.ClientError as e:
            result.update({
                'status': 'error',
                'message': 'Connection error',
                'error': str(e)
            })
        except Exception as e:
            result.update({
                'status': 'error',
                'message': 'Unexpected error',
                'error': str(e)
            })
        
        return result
    
    async def test_claude_api(self) -> Dict[str, Any]:
        """
        Test Claude (Anthropic) API connectivity.
        
        Returns:
            dict: Test results
        """
        result = {
            'service': 'Claude (Anthropic)',
            'status': 'unknown',
            'message': '',
            'response_time': None,
            'error': None
        }
        
        try:
            start_time = datetime.now()
            
            # Test API key format
            api_key = self.settings.claude_api_key
            if not api_key or api_key == "your_anthropic_api_key_here":
                result.update({
                    'status': 'error',
                    'message': 'API key not configured',
                    'error': 'CLAUDE_API_KEY is missing or using placeholder value'
                })
                return result
            
            # Try to make a simple API call
            headers = {
                'x-api-key': api_key,
                'Content-Type': 'application/json',
                'anthropic-version': '2023-06-01'
            }
            
            async with aiohttp.ClientSession() as session:
                test_data = {
                    'model': 'claude-3-haiku-20240307',
                    'max_tokens': 100,
                    'messages': [
                        {
                            'role': 'user',
                            'content': 'Hello! Please respond with "API test successful" if you can read this.'
                        }
                    ]
                }
                
                async with session.post(
                    'https://api.anthropic.com/v1/messages',
                    json=test_data,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    response_time = (datetime.now() - start_time).total_seconds()
                    result['response_time'] = response_time
                    
                    if response.status == 200:
                        data = await response.json()
                        if data.get('content') and len(data['content']) > 0:
                            response_text = data['content'][0].get('text', '')
                            if 'API test successful' in response_text:
                                result.update({
                                    'status': 'success',
                                    'message': f'API working correctly (response time: {response_time:.2f}s)'
                                })
                            else:
                                result.update({
                                    'status': 'warning',
                                    'message': 'API responded but content unexpected',
                                    'error': f'Response: {response_text[:100]}'
                                })
                        else:
                            result.update({
                                'status': 'error',
                                'message': 'API returned empty response',
                                'error': 'No content in response'
                            })
                    elif response.status == 401:
                        result.update({
                            'status': 'error',
                            'message': 'Authentication failed',
                            'error': 'Invalid API key'
                        })
                    elif response.status == 429:
                        result.update({
                            'status': 'warning',
                            'message': 'Rate limit exceeded',
                            'error': 'Too many requests'
                        })
                    else:
                        error_text = await response.text()
                        result.update({
                            'status': 'error',
                            'message': f'HTTP {response.status}',
                            'error': error_text[:200]
                        })
        
        except aiohttp.ClientTimeout:
            result.update({
                'status': 'error',
                'message': 'Request timeout',
                'error': 'API request timed out after 30 seconds'
            })
        except aiohttp.ClientError as e:
            result.update({
                'status': 'error',
                'message': 'Connection error',
                'error': str(e)
            })
        except Exception as e:
            result.update({
                'status': 'error',
                'message': 'Unexpected error',
                'error': str(e)
            })
        
        return result
    
    async def test_supabase_connection(self) -> Dict[str, Any]:
        """
        Test Supabase database connectivity.
        
        Returns:
            dict: Test results
        """
        result = {
            'service': 'Supabase',
            'status': 'unknown',
            'message': '',
            'response_time': None,
            'error': None
        }
        
        try:
            start_time = datetime.now()
            
            # Test configuration
            url = self.settings.supabase_url
            key = self.settings.supabase_service_role_key
            
            if not url or url == "your_supabase_project_url":
                result.update({
                    'status': 'error',
                    'message': 'URL not configured',
                    'error': 'SUPABASE_URL is missing or using placeholder value'
                })
                return result
            
            if not key or key == "your_service_role_key":
                result.update({
                    'status': 'error',
                    'message': 'Service key not configured',
                    'error': 'SUPABASE_SERVICE_ROLE_KEY is missing or using placeholder value'
                })
                return result
            
            # Test basic connectivity with REST API
            headers = {
                'apikey': key,
                'Authorization': f'Bearer {key}',
                'Content-Type': 'application/json'
            }
            
            async with aiohttp.ClientSession() as session:
                # Try to access a simple endpoint (this will fail if tables don't exist, but shows connectivity)
                test_url = f"{url}/rest/v1/"
                
                async with session.get(
                    test_url,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    response_time = (datetime.now() - start_time).total_seconds()
                    result['response_time'] = response_time
                    
                    if response.status == 200:
                        result.update({
                            'status': 'success',
                            'message': f'Database connection successful (response time: {response_time:.2f}s)'
                        })
                    elif response.status == 401:
                        result.update({
                            'status': 'error',
                            'message': 'Authentication failed',
                            'error': 'Invalid service role key'
                        })
                    elif response.status == 404:
                        result.update({
                            'status': 'warning',
                            'message': 'Connected but no tables found',
                            'error': 'Database schema not yet created'
                        })
                    else:
                        result.update({
                            'status': 'error',
                            'message': f'HTTP {response.status}',
                            'error': await response.text()
                        })
        
        except aiohttp.ClientTimeout:
            result.update({
                'status': 'error',
                'message': 'Connection timeout',
                'error': 'Database connection timed out'
            })
        except aiohttp.ClientError as e:
            result.update({
                'status': 'error',
                'message': 'Connection error',
                'error': str(e)
            })
        except Exception as e:
            result.update({
                'status': 'error',
                'message': 'Unexpected error',
                'error': str(e)
            })
        
        return result
    
    def test_url_accessibility(self) -> Dict[str, Any]:
        """
        Test accessibility of competitor URLs from config.
        
        Returns:
            dict: Test results
        """
        result = {
            'service': 'Competitor URLs',
            'status': 'unknown',
            'message': '',
            'accessible_urls': 0,
            'total_urls': 0,
            'failed_urls': []
        }
        
        try:
            # Load competitor config
            from config.settings import load_competitor_config
            config_data = load_competitor_config()
            
            all_urls = []
            for competitor in config_data.get('competitors', []):
                all_urls.extend(competitor.get('new_urls', []))
                all_urls.extend(competitor.get('promo_urls', []))
            
            result['total_urls'] = len(all_urls)
            
            if not all_urls:
                result.update({
                    'status': 'warning',
                    'message': 'No URLs found in competitor configuration'
                })
                return result
            
            # Test each URL
            accessible_count = 0
            for url in all_urls:
                is_accessible, error = URLValidator.is_accessible(url, timeout=10)
                if is_accessible:
                    accessible_count += 1
                else:
                    result['failed_urls'].append({
                        'url': url,
                        'error': error
                    })
            
            result['accessible_urls'] = accessible_count
            success_rate = accessible_count / len(all_urls)
            
            if success_rate >= 0.9:
                result.update({
                    'status': 'success',
                    'message': f'{accessible_count}/{len(all_urls)} URLs accessible ({success_rate:.1%})'
                })
            elif success_rate >= 0.7:
                result.update({
                    'status': 'warning',
                    'message': f'{accessible_count}/{len(all_urls)} URLs accessible ({success_rate:.1%})'
                })
            else:
                result.update({
                    'status': 'error',
                    'message': f'Only {accessible_count}/{len(all_urls)} URLs accessible ({success_rate:.1%})'
                })
        
        except Exception as e:
            result.update({
                'status': 'error',
                'message': 'Failed to test URLs',
                'error': str(e)
            })
        
        return result
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """
        Run all API connectivity tests.
        
        Returns:
            dict: Complete test results
        """
        print("🔍 Testing API connectivity...\n")
        
        # Test settings validation first
        print("1. Validating configuration...")
        validation_errors = validate_api_keys(self.settings)
        
        if validation_errors:
            print("❌ Configuration validation failed:")
            for error in validation_errors:
                print(f"   - {error}")
            return {
                'status': 'failed',
                'message': 'Configuration validation failed',
                'errors': validation_errors
            }
        else:
            print("✅ Configuration validation passed\n")
        
        # Run API tests
        tests = [
            ("2. Testing Firecrawl API...", self.test_firecrawl_api()),
            ("3. Testing Claude API...", self.test_claude_api()),
            ("4. Testing Supabase connection...", self.test_supabase_connection()),
        ]
        
        results = {}
        
        for description, test_coro in tests:
            print(description)
            result = await test_coro
            results[result['service']] = result
            
            status_icon = {
                'success': '✅',
                'warning': '⚠️',
                'error': '❌',
                'unknown': '❓'
            }.get(result['status'], '❓')
            
            print(f"{status_icon} {result['message']}")
            if result.get('error'):
                print(f"   Error: {result['error']}")
            print()
        
        # Test URL accessibility
        print("5. Testing competitor URL accessibility...")
        url_result = self.test_url_accessibility()
        results['Competitor URLs'] = url_result
        
        status_icon = {
            'success': '✅',
            'warning': '⚠️',
            'error': '❌',
            'unknown': '❓'
        }.get(url_result['status'], '❓')
        
        print(f"{status_icon} {url_result['message']}")
        if url_result.get('failed_urls'):
            print(f"   Failed URLs: {len(url_result['failed_urls'])}")
            for failed in url_result['failed_urls'][:3]:  # Show first 3
                print(f"     - {failed['url']}: {failed['error']}")
            if len(url_result['failed_urls']) > 3:
                print(f"     ... and {len(url_result['failed_urls']) - 3} more")
        
        # Summary
        print("\n" + "="*50)
        print("📊 CONNECTIVITY TEST SUMMARY")
        print("="*50)
        
        success_count = sum(1 for r in results.values() if r['status'] == 'success')
        warning_count = sum(1 for r in results.values() if r['status'] == 'warning')
        error_count = sum(1 for r in results.values() if r['status'] == 'error')
        
        print(f"✅ Successful: {success_count}")
        print(f"⚠️  Warnings:   {warning_count}")
        print(f"❌ Errors:     {error_count}")
        
        overall_status = 'success' if error_count == 0 else ('warning' if success_count > 0 else 'error')
        
        return {
            'status': overall_status,
            'results': results,
            'summary': {
                'success': success_count,
                'warning': warning_count,
                'error': error_count
            }
        }


async def main():
    """Main function to run API tests."""
    try:
        tester = APITester()
        results = await tester.run_all_tests()
        
        # Exit with appropriate code
        if results['status'] == 'error':
            print("\n❌ Some critical tests failed. Please fix configuration issues before proceeding.")
            sys.exit(1)
        elif results['status'] == 'warning':
            print("\n⚠️  Some tests have warnings. Review issues but pipeline may still work.")
            sys.exit(0)
        else:
            print("\n✅ All tests passed! APIs are ready for use.")
            sys.exit(0)
    
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
