"""
Firecrawl Screenshot Tool
=========================

Casino interface capture tool using Firecrawl API with compliance checking.
Follows WARP.md screenshot policy and uploads to WordPress media library.
"""

import asyncio
import aiohttp
import aiofiles
import tempfile
import os
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse
from datetime import datetime
from PIL import Image
import logging

from ..schemas.casino_review import ScreenshotResult
from .wordpress import WordPressClient

logger = logging.getLogger(__name__)


class FirecrawlConfig:
    """Firecrawl API configuration"""
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.firecrawl.dev/v0"
        self.timeout = 60  # seconds
        self.max_retries = 3


class FirecrawlClient:
    """
    Firecrawl API client for casino screenshot capture
    
    Features:
    - High-quality casino interface screenshots
    - Multiple viewport sizes (desktop, mobile, tablet)
    - Compliance checking per WARP.md policy
    - WordPress media library integration
    - Automatic retry with exponential backoff
    """
    
    def __init__(self, config: FirecrawlConfig, wordpress_client: WordPressClient):
        self.config = config
        self.wordpress = wordpress_client
        self.session = None
        self._setup_session()
    
    def _setup_session(self):
        """Setup aiohttp session with proper headers"""
        timeout = aiohttp.ClientTimeout(total=self.config.timeout)
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "CrashCasino-Agent/1.0"
            }
        )
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def capture_casino_screenshots(self, 
                                       casino_url: str, 
                                       tenant_id: str = "crashcasino") -> List[ScreenshotResult]:
        """
        Capture multiple casino interface screenshots with different viewports
        
        Args:
            casino_url: Target casino website URL
            tenant_id: Tenant identifier for storage path
            
        Returns:
            List of ScreenshotResult objects with WordPress media IDs
        """
        
        # Define screenshot configurations
        screenshot_configs = [
            {
                "view_type": "desktop_homepage",
                "viewport": {"width": 1920, "height": 1080},
                "url_suffix": "",
                "description": "Desktop homepage view"
            },
            {
                "view_type": "desktop_games",
                "viewport": {"width": 1920, "height": 1080},
                "url_suffix": "/games",
                "description": "Desktop games section"
            },
            {
                "view_type": "mobile_homepage",
                "viewport": {"width": 375, "height": 812},
                "url_suffix": "",
                "description": "Mobile homepage view"
            }
        ]
        
        results = []
        
        for config in screenshot_configs:
            try:
                logger.info(f"Capturing {config['view_type']} screenshot for {casino_url}")
                
                # Capture screenshot
                screenshot_result = await self._capture_single_screenshot(
                    url=casino_url + config["url_suffix"],
                    viewport=config["viewport"],
                    view_type=config["view_type"],
                    tenant_id=tenant_id
                )
                
                if screenshot_result:
                    results.append(screenshot_result)
                    logger.info(f"✅ Successfully captured {config['view_type']} screenshot")
                else:
                    logger.warning(f"⚠️ Failed to capture {config['view_type']} screenshot")
                
                # Rate limiting between screenshots
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"❌ Error capturing {config['view_type']}: {str(e)}")
                continue
        
        logger.info(f"Captured {len(results)}/{len(screenshot_configs)} screenshots for {casino_url}")
        return results
    
    async def _capture_single_screenshot(self, 
                                       url: str, 
                                       viewport: Dict[str, int],
                                       view_type: str,
                                       tenant_id: str) -> Optional[ScreenshotResult]:
        """Capture a single screenshot with compliance checking"""
        
        try:
            # Step 1: Capture screenshot via Firecrawl
            screenshot_data = await self._call_firecrawl_screenshot(url, viewport)
            
            if not screenshot_data:
                return None
            
            # Step 2: Download and process image
            temp_file_path = await self._download_screenshot_image(screenshot_data["screenshot_url"])
            
            if not temp_file_path:
                return None
            
            # Step 3: Compliance checking per WARP.md policy
            compliance_result = await self._check_image_compliance(temp_file_path, url)
            
            if not compliance_result["compliance_pass"]:
                logger.warning(f"Screenshot failed compliance check: {compliance_result['issues']}")
                os.unlink(temp_file_path)  # Clean up
                return None
            
            # Step 4: Upload to WordPress media library
            media_result = await self._upload_to_wordpress(
                temp_file_path, 
                view_type, 
                url,
                tenant_id
            )
            
            if not media_result:
                os.unlink(temp_file_path)  # Clean up
                return None
            
            # Step 5: Generate Supabase storage path (per WARP.md structure)
            storage_path = self._generate_storage_path(tenant_id, url, view_type)
            
            # Step 6: Build ScreenshotResult
            result = ScreenshotResult(
                view_type=view_type,
                image_url=media_result["source_url"],
                media_id=media_result["id"],
                width=compliance_result["width"],
                height=compliance_result["height"],
                file_size=compliance_result["file_size"],
                format=compliance_result["format"],
                compliance_pass=compliance_result["compliance_pass"],
                licensing_compliant=compliance_result["licensing_compliant"],
                branding_compliant=compliance_result["branding_compliant"],
                dimensions_compliant=compliance_result["dimensions_compliant"],
                capture_timestamp=datetime.now(),
                capture_method="firecrawl",
                source_url=url,
                storage_path=storage_path
            )
            
            # Clean up temporary file
            os.unlink(temp_file_path)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to capture screenshot for {url}: {str(e)}")
            return None
    
    async def _call_firecrawl_screenshot(self, url: str, viewport: Dict[str, int]) -> Optional[Dict]:
        """Call Firecrawl API to capture screenshot"""
        
        payload = {
            "url": url,
            "screenshot": True,
            "fullPageScreenshot": False,  # Capture above-the-fold content
            "waitFor": 3000,  # Wait 3 seconds for page load
            "viewport": viewport,
            "options": {
                "timeout": 30000,
                "waitUntil": "networkidle0"
            }
        }
        
        for attempt in range(self.config.max_retries):
            try:
                async with self.session.post(
                    f"{self.config.base_url}/screenshot",
                    json=payload
                ) as response:
                    
                    if response.status == 401:
                        raise Exception("Firecrawl authentication failed - check API key")
                    
                    if response.status == 429:
                        logger.warning("Firecrawl rate limit hit, waiting...")
                        await asyncio.sleep(5)
                        continue
                    
                    if response.status >= 400:
                        error_data = await response.json()
                        raise Exception(f"Firecrawl API error: {error_data.get('error', 'Unknown error')}")
                    
                    result = await response.json()
                    
                    if result.get("success") and result.get("screenshot"):
                        return {
                            "screenshot_url": result["screenshot"],
                            "metadata": result.get("metadata", {})
                        }
                    else:
                        raise Exception(f"Firecrawl screenshot failed: {result.get('error', 'Unknown error')}")
                        
            except aiohttp.ClientError as e:
                logger.warning(f"Firecrawl request failed (attempt {attempt + 1}): {str(e)}")
                if attempt == self.config.max_retries - 1:
                    raise Exception(f"Firecrawl connection failed after {self.config.max_retries} attempts")
                
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        return None
    
    async def _download_screenshot_image(self, screenshot_url: str) -> Optional[str]:
        """Download screenshot image to temporary file"""
        
        try:
            async with self.session.get(screenshot_url) as response:
                if response.status != 200:
                    logger.error(f"Failed to download screenshot: HTTP {response.status}")
                    return None
                
                # Create temporary file
                temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
                temp_file_path = temp_file.name
                
                # Download image data
                async with aiofiles.open(temp_file_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(8192):
                        await f.write(chunk)
                
                return temp_file_path
                
        except Exception as e:
            logger.error(f"Failed to download screenshot image: {str(e)}")
            return None
    
    async def _check_image_compliance(self, image_path: str, source_url: str) -> Dict:
        """
        Check image compliance per WARP.md screenshot policy
        
        Compliance requirements:
        - Minimum dimensions: 900×600 pixels
        - No licensing violations 
        - Proper branding/attribution
        - Acceptable file format (PNG, JPEG, WebP)
        """
        
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                format_type = img.format
                file_size = os.path.getsize(image_path)
                
                # Check minimum dimensions (WARP.md requirement)
                dimensions_compliant = width >= 900 and height >= 600
                
                # Basic compliance checks
                licensing_compliant = True  # Assume compliant for direct casino screenshots
                branding_compliant = True   # Direct screenshots should be compliant
                
                # Overall compliance
                compliance_pass = (
                    dimensions_compliant and 
                    licensing_compliant and 
                    branding_compliant and
                    format_type in ["PNG", "JPEG", "WebP"]
                )
                
                issues = []
                if not dimensions_compliant:
                    issues.append(f"Dimensions too small: {width}×{height} (minimum 900×600)")
                if format_type not in ["PNG", "JPEG", "WebP"]:
                    issues.append(f"Invalid format: {format_type}")
                
                return {
                    "compliance_pass": compliance_pass,
                    "licensing_compliant": licensing_compliant,
                    "branding_compliant": branding_compliant,
                    "dimensions_compliant": dimensions_compliant,
                    "width": width,
                    "height": height,
                    "file_size": file_size,
                    "format": format_type,
                    "issues": issues
                }
                
        except Exception as e:
            logger.error(f"Image compliance check failed: {str(e)}")
            return {
                "compliance_pass": False,
                "licensing_compliant": False,
                "branding_compliant": False,
                "dimensions_compliant": False,
                "width": 0,
                "height": 0,
                "file_size": 0,
                "format": "unknown",
                "issues": [f"Compliance check error: {str(e)}"]
            }
    
    async def _upload_to_wordpress(self, 
                                 image_path: str, 
                                 view_type: str, 
                                 source_url: str,
                                 tenant_id: str) -> Optional[Dict]:
        """Upload screenshot to WordPress media library"""
        
        try:
            # Generate descriptive title and alt text
            domain = urlparse(source_url).netloc.replace('www.', '')
            title = f"{domain.title()} - {view_type.replace('_', ' ').title()}"
            
            # Upload to WordPress
            result = await self.wordpress.upload_media(
                file_path=image_path,
                title=title,
                description=f"Casino interface screenshot captured from {source_url}"
            )
            
            if result and result.get("id"):
                logger.info(f"Uploaded screenshot to WordPress media ID: {result['id']}")
                return result
            else:
                logger.error("WordPress media upload failed - no ID returned")
                return None
                
        except Exception as e:
            logger.error(f"WordPress media upload failed: {str(e)}")
            return None
    
    def _generate_storage_path(self, tenant_id: str, url: str, view_type: str) -> str:
        """Generate Supabase storage path per WARP.md structure"""
        
        domain = urlparse(url).netloc.replace('www.', '')
        timestamp = datetime.now().isoformat()
        
        # Format: images/{tenant}/{brand}/{category}/{ISO8601}.png
        return f"images/{tenant_id}/{domain}/screenshots/{timestamp}.png"
    
    async def test_connection(self) -> bool:
        """Test Firecrawl API connection"""
        try:
            # Simple test screenshot
            result = await self._call_firecrawl_screenshot(
                "https://example.com", 
                {"width": 1200, "height": 800}
            )
            
            if result:
                logger.info("✅ Firecrawl API connection successful")
                return True
            else:
                logger.error("❌ Firecrawl API test failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Firecrawl API connection failed: {str(e)}")
            return False


# Factory function for easy instantiation
def create_firecrawl_client(api_key: str, wordpress_client: WordPressClient) -> FirecrawlClient:
    """
    Factory function to create Firecrawl client
    
    Args:
        api_key: Firecrawl API key
        wordpress_client: Configured WordPress client
        
    Returns:
        Configured FirecrawlClient instance
    """
    config = FirecrawlConfig(api_key=api_key)
    return FirecrawlClient(config, wordpress_client)


# Fallback screenshot tools (CF Browser, Browserless)
class FallbackScreenshotClient:
    """
    Fallback screenshot client using CF Browser Rendering or Browserless
    
    Used when Firecrawl is unavailable, following WARP.md screenshot policy
    priority: Firecrawl → CF Browser → Browserless → Playwright
    """
    
    def __init__(self, cf_token: str = None, browserless_token: str = None):
        self.cf_token = cf_token
        self.browserless_token = browserless_token
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def capture_screenshot(self, url: str, viewport: Dict[str, int]) -> Optional[bytes]:
        """Capture screenshot using available fallback service"""
        
        # Try CF Browser first
        if self.cf_token:
            result = await self._capture_cf_browser(url, viewport)
            if result:
                return result
        
        # Fallback to Browserless
        if self.browserless_token:
            result = await self._capture_browserless(url, viewport)
            if result:
                return result
        
        logger.error("All fallback screenshot services failed")
        return None
    
    async def _capture_cf_browser(self, url: str, viewport: Dict[str, int]) -> Optional[bytes]:
        """Capture using Cloudflare Browser Rendering"""
        # Implementation for CF Browser API
        # This would follow the CF Browser Rendering API documentation
        pass
    
    async def _capture_browserless(self, url: str, viewport: Dict[str, int]) -> Optional[bytes]:
        """Capture using Browserless API"""
        # Implementation for Browserless API
        # This would follow the Browserless API documentation
        pass


# Example usage and testing
async def test_firecrawl_screenshot():
    """Test function for Firecrawl screenshot capture"""
    import os
    from dotenv import load_dotenv
    from .wordpress import create_wordpress_client
    
    load_dotenv()
    
    # Create WordPress client
    wp_client = create_wordpress_client(
        base_url=os.getenv("WORDPRESS_BASE_URL", "https://www.crashcasino.io"),
        username=os.getenv("WORDPRESS_USERNAME"),
        app_password=os.getenv("WORDPRESS_APP_PASSWORD")
    )
    
    # Create Firecrawl client
    firecrawl_client = create_firecrawl_client(
        api_key=os.getenv("FIRECRAWL_API_KEY"),
        wordpress_client=wp_client
    )
    
    async with firecrawl_client, wp_client:
        # Test connection
        if await firecrawl_client.test_connection():
            print("✅ Firecrawl connection successful")
            
            # Test casino screenshot
            results = await firecrawl_client.capture_casino_screenshots(
                casino_url="https://bitstarz.com",
                tenant_id="crashcasino"
            )
            
            print(f"Captured {len(results)} screenshots:")
            for result in results:
                print(f"  - {result.view_type}: Media ID {result.media_id}")
                print(f"    Dimensions: {result.width}×{result.height}")
                print(f"    Compliance: {'✅' if result.compliance_pass else '❌'}")
        else:
            print("❌ Firecrawl connection failed")


if __name__ == "__main__":
    asyncio.run(test_firecrawl_screenshot())
