#!/usr/bin/env python3
"""
🎯 Intelligent Screenshot Capture System for Casino Review Publishing
===================================================================

Multi-tool screenshot capture system with smart selection based on site characteristics.
Integrates with existing Playwright Screenshot Engine and adds Firecrawl v2 support.

Features:
- Smart tool selection (Playwright, Firecrawl, Selenium, WebBase)
- Casino-specific optimizations and element targeting
- Anti-detection stealth capabilities
- LCEL-compatible for Universal RAG CMS integration
- Compliance validation and metadata enrichment
"""

import asyncio
import os
import time
from datetime import datetime
from urllib.parse import urlparse
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import logging

import requests
from langchain_core.runnables import Runnable, RunnablePassthrough, RunnableLambda
from langchain_core.runnables.router import RouterRunnable
from langchain_community.document_loaders import SeleniumURLLoader, WebBaseLoader

# Import existing Playwright Screenshot Engine
try:
    from src.integrations.playwright_screenshot_engine import (
        get_global_browser_pool,
        StealthScreenshotService,
        StealthConfig,
        StealthLevel,
        IntegratedScreenshotService
    )
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logging.warning("Playwright Screenshot Engine not available")
    
    # Mock StealthLevel for when Playwright is not available
    class StealthLevel:
        LEVEL_1_BASIC = "level_1_basic"
        LEVEL_2_ADVANCED = "level_2_advanced"
        LEVEL_3_FINGERPRINT = "level_3_fingerprint"
        LEVEL_4_PROFILE_ROTATION = "level_4_profile_rotation"

logger = logging.getLogger(__name__)

class CaptureMethod(Enum):
    """Screenshot capture methods"""
    PLAYWRIGHT_STEALTH_MAX = "playwright_stealth_level_4"
    PLAYWRIGHT_STEALTH_HIGH = "playwright_stealth_level_3"  
    PLAYWRIGHT_STEALTH_MED = "playwright_stealth_level_2"
    PLAYWRIGHT_BASIC = "playwright_basic"
    FIRECRAWL_V2 = "firecrawl_v2"
    SELENIUM_WEBDRIVER = "selenium"
    WEBBASE_LOADER = "webbase"

@dataclass
class ScreenshotRequest:
    """Screenshot capture request configuration"""
    url: str
    filename: Optional[str] = None
    alt_text: Optional[str] = None
    caption: Optional[str] = None
    target_elements: List[str] = None  # CSS selectors for specific elements
    quality: int = 85
    format: str = 'jpeg'
    timeout_ms: int = 30000
    full_page: bool = True
    stealth_required: bool = None  # Auto-detected if None

@dataclass 
class ScreenshotResponse:
    """Screenshot capture response"""
    success: bool
    image_data: Optional[bytes] = None
    image_url: Optional[str] = None  # For Firecrawl
    metadata: Dict[str, Any] = None
    method_used: Optional[str] = None
    error_message: Optional[str] = None
    compliance_status: str = "PENDING"  # PASS, FAIL, PENDING

class CasinoSiteIntelligence:
    """Intelligence about casino sites and their characteristics"""
    
    # High-security casino sites that aggressively block crawlers
    HIGH_SECURITY_DOMAINS = {
        'pokerstars.com', 'pokerstars.eu', 'pokerstars.net',
        'bet365.com', 'bet365.es', 'bet365.it',
        'unibet.com', 'unibet.co.uk', 'unibet.eu',
        'williamhill.com', 'williamhill.es', 'williamhill.it',
        'betway.com', 'betway.es', 'betway.de',
        '888casino.com', '888poker.com', '888sport.com',
        'bwin.com', 'bwin.es', 'bwin.it',
        'partypoker.com', 'partycasino.com'
    }
    
    # Crypto casinos (generally more permissive to crawlers)
    CRYPTO_CASINO_DOMAINS = {
        'stake.com', 'stake.us',
        'roobet.com',
        'bitcasino.io',
        'fortunejack.com',
        'cloudbet.com',
        'bitstarz.com',
        'mbitcasino.com',
        'betchain.com',
        'kingbitcasino.com'
    }
    
    # Sites known to have heavy JavaScript requirements
    JS_HEAVY_DOMAINS = {
        'evolution.com', 'ezugi.com', 'pragmaticplay.com',
        'netent.com', 'microgaming.com', 'playtech.com'
    }
    
    @classmethod
    def analyze_site(cls, url: str) -> Dict[str, Any]:
        """Analyze casino site characteristics"""
        domain = urlparse(url).netloc.lower()
        
        return {
            'domain': domain,
            'is_high_security': domain in cls.HIGH_SECURITY_DOMAINS,
            'is_crypto_casino': domain in cls.CRYPTO_CASINO_DOMAINS, 
            'requires_js': domain in cls.JS_HEAVY_DOMAINS,
            'stealth_level': cls._recommend_stealth_level(domain),
            'likely_blocks_crawlers': domain in cls.HIGH_SECURITY_DOMAINS
        }
    
    @classmethod
    def _recommend_stealth_level(cls, domain: str) -> StealthLevel:
        """Recommend stealth level based on domain"""
        if domain in cls.HIGH_SECURITY_DOMAINS:
            return StealthLevel.LEVEL_4_PROFILE_ROTATION
        elif domain in cls.CRYPTO_CASINO_DOMAINS:
            return StealthLevel.LEVEL_2_ADVANCED
        else:
            return StealthLevel.LEVEL_1_BASIC

class IntelligentScreenshotSelector:
    """Smart tool selection logic for screenshot capture"""
    
    def __init__(self):
        self.site_intelligence = CasinoSiteIntelligence()
    
    def select_method(self, request: ScreenshotRequest) -> CaptureMethod:
        """Select optimal capture method based on request and site analysis"""
        
        site_info = self.site_intelligence.analyze_site(request.url)
        
        # Override stealth requirement if not specified
        if request.stealth_required is None:
            request.stealth_required = site_info['likely_blocks_crawlers']
        
        # High-security sites always need maximum stealth
        if site_info['is_high_security'] or request.stealth_required:
            if PLAYWRIGHT_AVAILABLE:
                return CaptureMethod.PLAYWRIGHT_STEALTH_MAX
            else:
                logger.warning(f"High-security site {site_info['domain']} but Playwright not available")
                return CaptureMethod.SELENIUM_WEBDRIVER
        
        # Crypto casinos with moderate stealth
        if site_info['is_crypto_casino']:
            if PLAYWRIGHT_AVAILABLE:
                return CaptureMethod.PLAYWRIGHT_STEALTH_MED
            else:
                return CaptureMethod.SELENIUM_WEBDRIVER
        
        # JavaScript-heavy sites
        if site_info['requires_js'] or request.target_elements:
            if PLAYWRIGHT_AVAILABLE:
                return CaptureMethod.PLAYWRIGHT_BASIC
            else:
                return CaptureMethod.SELENIUM_WEBDRIVER
        
        # Simple screenshot requirements
        if request.full_page and not request.target_elements:
            return CaptureMethod.FIRECRAWL_V2
        
        # Default fallback
        return CaptureMethod.WEBBASE_LOADER

class FirecrawlV2Capturer:
    """Firecrawl v2 API screenshot capture"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('FIRECRAWL_API_KEY')
        if not self.api_key:
            logger.warning("Firecrawl API key not found")
    
    async def capture(self, request: ScreenshotRequest) -> ScreenshotResponse:
        """Capture screenshot using Firecrawl v2 API"""
        if not self.api_key:
            return ScreenshotResponse(
                success=False,
                error_message="Firecrawl API key not configured",
                method_used="firecrawl_v2"
            )
        
        try:
            # Correct Firecrawl v2 format based on documentation
            payload = {
                "url": request.url,
                "formats": ["screenshot"]
            }
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                'https://api.firecrawl.dev/v2/scrape',
                headers=headers,
                json=payload,
                timeout=request.timeout_ms / 1000
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('data', {}).get('screenshot'):
                    return ScreenshotResponse(
                        success=True,
                        image_url=data['data']['screenshot'],
                        metadata={
                            'source_url': request.url,
                            'capture_method': 'firecrawl_v2',
                            'capture_timestamp': datetime.now().isoformat(),
                            'firecrawl_metadata': data.get('data', {}).get('metadata', {})
                        },
                        method_used="firecrawl_v2"
                    )
            
            return ScreenshotResponse(
                success=False,
                error_message=f"Firecrawl API error: {response.status_code} - {response.text}",
                method_used="firecrawl_v2"
            )
            
        except Exception as e:
            logger.error(f"Firecrawl capture failed: {str(e)}")
            return ScreenshotResponse(
                success=False,
                error_message=f"Firecrawl exception: {str(e)}",
                method_used="firecrawl_v2"
            )

class PlaywrightCapturer:
    """Playwright-based screenshot capture with stealth"""
    
    def __init__(self):
        self.browser_pool = None
        self.stealth_service = None
    
    async def initialize(self):
        """Initialize Playwright services"""
        if not PLAYWRIGHT_AVAILABLE:
            raise RuntimeError("Playwright Screenshot Engine not available")
        
        try:
            self.browser_pool = await get_global_browser_pool()
            await self.browser_pool.initialize()
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Playwright browser pool: {str(e)}")
    
    async def capture(self, request: ScreenshotRequest, stealth_level: StealthLevel = None) -> ScreenshotResponse:
        """Capture screenshot using Playwright with optional stealth"""
        if not self.browser_pool:
            await self.initialize()
        
        try:
            if stealth_level and stealth_level != StealthLevel.LEVEL_1_BASIC:
                # Use stealth service
                stealth_config = StealthConfig(
                    level=stealth_level,
                    escalate_on_block=True,
                    max_retries_per_level=3
                )
                
                stealth_service = StealthScreenshotService(self.browser_pool, stealth_config)
                
                result = await stealth_service.capture_stealth_screenshot(
                    url=request.url,
                    capture_type="full_page" if request.full_page else "viewport",
                    max_escalation_attempts=3
                )
                
                if result.get('success'):
                    return ScreenshotResponse(
                        success=True,
                        image_data=result.get('screenshot_data'),
                        metadata={
                            'source_url': request.url,
                            'capture_method': f'playwright_stealth_{stealth_level.value}',
                            'stealth_level_used': result.get('level_used', stealth_level.value),
                            'capture_timestamp': datetime.now().isoformat()
                        },
                        method_used=f"playwright_stealth_{stealth_level.value}"
                    )
            else:
                # Use basic Playwright service
                if not PLAYWRIGHT_AVAILABLE:
                    return ScreenshotResponse(
                        success=False,
                        error_message="Playwright Screenshot Engine not available for basic capture",
                        method_used="playwright_basic"
                    )
                    
                from src.integrations.playwright_screenshot_engine import ScreenshotService
                
                service = ScreenshotService(self.browser_pool)
                result = await service.capture_full_page_screenshot(request.url)
                
                if result.success:
                    return ScreenshotResponse(
                        success=True,
                        image_data=result.screenshot_data,
                        metadata={
                            'source_url': request.url,
                            'capture_method': 'playwright_basic',
                            'capture_timestamp': datetime.now().isoformat(),
                            'file_size': result.file_size,
                            'viewport': result.viewport_size
                        },
                        method_used="playwright_basic"
                    )
            
            return ScreenshotResponse(
                success=False,
                error_message="Playwright capture failed - no error details available",
                method_used="playwright"
            )
            
        except Exception as e:
            logger.error(f"Playwright capture failed: {str(e)}")
            return ScreenshotResponse(
                success=False,
                error_message=f"Playwright exception: {str(e)}",
                method_used="playwright"
            )
    
    async def cleanup(self):
        """Cleanup Playwright resources"""
        if self.browser_pool:
            await self.browser_pool.cleanup()

class SeleniumCapturer:
    """Selenium-based screenshot capture"""
    
    async def capture(self, request: ScreenshotRequest) -> ScreenshotResponse:
        """Capture using Selenium WebDriver"""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            
            # Configure Chrome options for stealth
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            driver = webdriver.Chrome(options=chrome_options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            try:
                driver.get(request.url)
                time.sleep(3)  # Wait for page load
                
                screenshot_data = driver.get_screenshot_as_png()
                
                return ScreenshotResponse(
                    success=True,
                    image_data=screenshot_data,
                    metadata={
                        'source_url': request.url,
                        'capture_method': 'selenium',
                        'capture_timestamp': datetime.now().isoformat()
                    },
                    method_used="selenium"
                )
                
            finally:
                driver.quit()
                
        except Exception as e:
            logger.error(f"Selenium capture failed: {str(e)}")
            return ScreenshotResponse(
                success=False,
                error_message=f"Selenium exception: {str(e)}",
                method_used="selenium"
            )

class IntelligentScreenshotCapturer:
    """Main screenshot capture orchestrator"""
    
    def __init__(self):
        self.selector = IntelligentScreenshotSelector()
        self.firecrawl = FirecrawlV2Capturer()
        self.playwright = PlaywrightCapturer() if PLAYWRIGHT_AVAILABLE else None
        self.selenium = SeleniumCapturer()
        
    async def capture(self, request: ScreenshotRequest) -> ScreenshotResponse:
        """Capture screenshot using the most appropriate method"""
        
        # Select optimal method
        method = self.selector.select_method(request)
        logger.info(f"Selected capture method: {method.value} for {request.url}")
        
        # Execute capture based on selected method
        try:
            if method in [CaptureMethod.PLAYWRIGHT_STEALTH_MAX, 
                         CaptureMethod.PLAYWRIGHT_STEALTH_HIGH,
                         CaptureMethod.PLAYWRIGHT_STEALTH_MED]:
                if self.playwright:
                    site_info = self.selector.site_intelligence.analyze_site(request.url)
                    stealth_level = site_info['stealth_level']
                    return await self.playwright.capture(request, stealth_level)
                else:
                    # Fallback to Selenium
                    logger.warning("Playwright not available, falling back to Selenium")
                    return await self.selenium.capture(request)
                    
            elif method == CaptureMethod.PLAYWRIGHT_BASIC:
                if self.playwright:
                    return await self.playwright.capture(request, StealthLevel.LEVEL_1_BASIC)
                else:
                    return await self.selenium.capture(request)
                    
            elif method == CaptureMethod.FIRECRAWL_V2:
                return await self.firecrawl.capture(request)
                
            elif method == CaptureMethod.SELENIUM_WEBDRIVER:
                return await self.selenium.capture(request)
                
            else:  # WEBBASE_LOADER
                # For simple text extraction, WebBase is sufficient
                logger.info("Using WebBaseLoader for simple content extraction")
                return ScreenshotResponse(
                    success=False,
                    error_message="WebBaseLoader doesn't support screenshots - use for content only",
                    method_used="webbase"
                )
                
        except Exception as e:
            logger.error(f"Capture failed with method {method.value}: {str(e)}")
            return ScreenshotResponse(
                success=False,
                error_message=f"Method {method.value} failed: {str(e)}",
                method_used=method.value
            )
    
    async def cleanup(self):
        """Cleanup all resources"""
        if self.playwright:
            await self.playwright.cleanup()

# LCEL Integration Functions
def select_screenshot_tool(data: Dict[str, Any]) -> str:
    """LCEL-compatible tool selection function"""
    request = ScreenshotRequest(
        url=data['url'],
        **data.get('capture_options', {})
    )
    
    selector = IntelligentScreenshotSelector()
    method = selector.select_method(request)
    
    return method.value

async def capture_screenshot_with_method(data: Dict[str, Any]) -> Dict[str, Any]:
    """LCEL-compatible screenshot capture function"""
    capturer = IntelligentScreenshotCapturer()
    
    try:
        request = ScreenshotRequest(
            url=data['url'],
            **data.get('capture_options', {})
        )
        
        response = await capturer.capture(request)
        
        return {
            'success': response.success,
            'image_data': response.image_data,
            'image_url': response.image_url,
            'metadata': response.metadata or {},
            'method_used': response.method_used,
            'error_message': response.error_message,
            'compliance_status': response.compliance_status
        }
        
    finally:
        await capturer.cleanup()

def image_compliance_guard(data: Dict[str, Any]) -> Dict[str, Any]:
    """Compliance validation for captured images"""
    
    # Basic compliance checks
    compliance_issues = []
    
    if not data.get('success'):
        data['compliance_status'] = 'FAIL'
        data['compliance_issues'] = ['Capture failed']
        return data
    
    # Check image size/quality
    if data.get('image_data'):
        image_size = len(data['image_data'])
        if image_size < 1000:  # Too small
            compliance_issues.append('Image too small')
        if image_size > 10_000_000:  # Too large
            compliance_issues.append('Image too large')
    
    # Check metadata completeness
    metadata = data.get('metadata', {})
    required_fields = ['source_url', 'capture_method', 'capture_timestamp']
    
    for field in required_fields:
        if not metadata.get(field):
            compliance_issues.append(f'Missing metadata field: {field}')
    
    # Set compliance status
    if compliance_issues:
        data['compliance_status'] = 'FAIL'
        data['compliance_issues'] = compliance_issues
    else:
        data['compliance_status'] = 'PASS'
    
    return data

async def supabase_upload_image(data: Dict[str, Any]) -> Dict[str, Any]:
    """Upload image to Supabase storage (placeholder)"""
    
    if data.get('compliance_status') != 'PASS':
        logger.warning("Skipping upload - compliance check failed")
        return data
    
    # TODO: Implement actual Supabase upload
    # This would integrate with existing Supabase storage system
    
    logger.info("Image upload to Supabase - TODO: implement")
    data['storage_result'] = {
        'uploaded': False,
        'message': 'Supabase integration pending'
    }
    
    return data

# LCEL Screenshot Chain
def create_screenshot_chain() -> Runnable:
    """Create the complete LCEL screenshot processing chain"""
    
    def route_and_capture(data: Dict[str, Any]) -> Dict[str, Any]:
        """Combined routing and capture function"""
        # Select the method
        method = select_screenshot_tool(data)
        
        # Add method to data for capture function
        data_with_method = {**data, 'selected_method': method}
        
        # Capture screenshot
        return asyncio.run(capture_screenshot_with_method(data_with_method))
    
    return (
        RunnablePassthrough()
        | RunnableLambda(route_and_capture)
        | RunnableLambda(image_compliance_guard)
        | RunnableLambda(supabase_upload_image)
    )

# Usage Example
async def main():
    """Example usage of intelligent screenshot capture"""
    
    capturer = IntelligentScreenshotCapturer()
    
    try:
        # Test with different casino types
        test_urls = [
            "https://stake.com/",  # Crypto casino
            "https://bet365.com/", # High-security
            "https://example.com/" # Basic site
        ]
        
        for url in test_urls:
            request = ScreenshotRequest(
                url=url,
                filename=f"screenshot_{urlparse(url).netloc}.jpg",
                alt_text=f"Screenshot of {urlparse(url).netloc}",
                caption=f"Website screenshot captured for {urlparse(url).netloc}"
            )
            
            response = await capturer.capture(request)
            
            if response.success:
                print(f"✅ {url} - Method: {response.method_used}")
                if response.image_data:
                    print(f"   📸 Image size: {len(response.image_data)} bytes")
                elif response.image_url:
                    print(f"   🔗 Image URL: {response.image_url}")
            else:
                print(f"❌ {url} - Error: {response.error_message}")
                
    finally:
        await capturer.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
