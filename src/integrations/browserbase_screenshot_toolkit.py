#!/usr/bin/env python3
"""
🌐 Browserbase Screenshot Toolkit Integration
============================================

Lean replacement for the complex Playwright system using managed headless Chrome
with anti-bot hardening and native LangChain tools.

Key Features:
- Native LangChain tools for LCEL composition
- Managed Chrome with anti-bot features
- Zero infrastructure maintenance
- JS-heavy site support (crucial for casinos)
- Simple Supabase storage integration

Usage in LCEL chains:
```python
from integrations.browserbase_screenshot_toolkit import create_casino_screenshot_chain

screenshot_chain = create_casino_screenshot_chain()
full_chain = research_chain | screenshot_chain | content_chain
```
"""

import asyncio
import logging
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import base64
import hashlib

try:
    from langchain_community.tools.browserbase import (
        BrowserbaseTool,
        BrowserbaseNavigateTool,
        BrowserbaseScreenshotTool,
        BrowserbaseClickTool,
        BrowserbaseInputTool
    )
    BROWSERBASE_AVAILABLE = True
except ImportError:
    BROWSERBASE_AVAILABLE = False
    logging.warning("⚠️ Browserbase tools not available - install langchain-community")

from langchain.tools import BaseTool
from langchain.schema.runnable import Runnable, RunnableLambda
from langchain_core.runnables import RunnableParallel
from pydantic import BaseModel, Field

try:
    from ..utils.supabase_client import get_supabase_client
except ImportError:
    try:
        from utils.supabase_client import get_supabase_client
    except ImportError:
        logging.warning("⚠️ Supabase client not available")
        get_supabase_client = None

logger = logging.getLogger(__name__)

class CasinoScreenshotConfig(BaseModel):
    """Configuration for casino screenshot capture"""
    casino_name: str
    target_urls: List[str] = Field(default_factory=list)
    categories: List[str] = Field(default=["lobby", "games", "bonuses", "mobile"])
    max_screenshots: int = 4
    wait_time: int = 3  # seconds to wait for page load
    viewport_width: int = 1920
    viewport_height: int = 1080

class CasinoScreenshotResult(BaseModel):
    """Result from casino screenshot capture"""
    success: bool
    casino_name: str
    screenshots: List[Dict[str, Any]] = Field(default_factory=list)
    storage_urls: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None

class BrowserbaseScreenshotToolkit:
    """
    🌐 Lean Browserbase Screenshot Toolkit
    
    Replaces the complex 4,700-line Playwright system with managed Chrome
    and native LangChain tools for LCEL composition.
    """
    
    def __init__(
        self, 
        browserbase_api_key: Optional[str] = None,
        project_id: Optional[str] = None,
        session_id: Optional[str] = None
    ):
        self.api_key = browserbase_api_key or os.getenv("BROWSERBASE_API_KEY")
        self.project_id = project_id or os.getenv("BROWSERBASE_PROJECT_ID")
        self.session_id = session_id
        
        if not self.api_key:
            raise ValueError("BROWSERBASE_API_KEY required")
            
        # Initialize Browserbase tools
        if BROWSERBASE_AVAILABLE:
            self._init_browserbase_tools()
        else:
            raise ImportError("Browserbase tools not available - install langchain-community")
            
        # Initialize Supabase storage
        self.supabase_client = get_supabase_client() if get_supabase_client else None
        self.storage_bucket = "casino-screenshots"
    
    def _init_browserbase_tools(self):
        """Initialize native Browserbase LangChain tools"""
        
        # Core navigation tool
        self.navigate_tool = BrowserbaseNavigateTool(
            api_key=self.api_key,
            project_id=self.project_id,
            session_id=self.session_id
        )
        
        # Screenshot capture tool
        self.screenshot_tool = BrowserbaseScreenshotTool(
            api_key=self.api_key,
            project_id=self.project_id,
            session_id=self.session_id
        )
        
        # Interaction tools (for complex casino sites)
        self.click_tool = BrowserbaseClickTool(
            api_key=self.api_key,
            project_id=self.project_id,
            session_id=self.session_id
        )
        
        self.input_tool = BrowserbaseInputTool(
            api_key=self.api_key,
            project_id=self.project_id,
            session_id=self.session_id
        )
        
        logger.info("✅ Browserbase tools initialized")
    
    async def capture_casino_screenshots(self, config: CasinoScreenshotConfig) -> CasinoScreenshotResult:
        """
        🎰 Capture casino screenshots using managed Chrome
        
        This replaces the complex Playwright capture_casino_screenshots method
        with a lean Browserbase implementation.
        """
        
        try:
            logger.info(f"🌐 Starting Browserbase casino screenshot capture: {config.casino_name}")
            
            screenshots = []
            storage_urls = []
            
            # Generate casino URLs if not provided
            if not config.target_urls:
                config.target_urls = self._generate_casino_urls(config.casino_name)
            
            # Capture screenshots for each category
            for i, url in enumerate(config.target_urls[:config.max_screenshots]):
                try:
                    logger.info(f"📸 Capturing screenshot {i+1}/{len(config.target_urls)}: {url}")
                    
                    # Navigate to casino page with managed Chrome
                    nav_result = await self.navigate_tool.arun(url)
                    
                    # Wait for page load (casino sites often have heavy JS)
                    await asyncio.sleep(config.wait_time)
                    
                    # Capture screenshot with anti-bot hardening
                    screenshot_data = await self.screenshot_tool.arun("")
                    
                    if screenshot_data:
                        # Store screenshot in Supabase
                        storage_url = await self._store_screenshot(
                            screenshot_data, 
                            config.casino_name,
                            f"category_{i+1}",
                            url
                        )
                        
                        screenshot_metadata = {
                            "url": url,
                            "category": f"casino_view_{i+1}",
                            "timestamp": datetime.now().isoformat(),
                            "storage_url": storage_url,
                            "viewport": f"{config.viewport_width}x{config.viewport_height}"
                        }
                        
                        screenshots.append(screenshot_metadata)
                        if storage_url:
                            storage_urls.append(storage_url)
                        
                        logger.info(f"✅ Screenshot {i+1} captured and stored")
                    
                except Exception as e:
                    logger.error(f"❌ Failed to capture screenshot {i+1}: {e}")
                    continue
            
            result = CasinoScreenshotResult(
                success=len(screenshots) > 0,
                casino_name=config.casino_name,
                screenshots=screenshots,
                storage_urls=storage_urls,
                metadata={
                    "total_captured": len(screenshots),
                    "target_categories": config.categories,
                    "browserbase_session": self.session_id,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            logger.info(f"🎊 Casino screenshot capture complete: {len(screenshots)} screenshots")
            return result
            
        except Exception as e:
            logger.error(f"💥 Casino screenshot capture failed: {e}")
            return CasinoScreenshotResult(
                success=False,
                casino_name=config.casino_name,
                error_message=str(e)
            )
    
    def _generate_casino_urls(self, casino_name: str) -> List[str]:
        """Generate target URLs for casino screenshot capture"""
        
        base_url = f"https://www.{casino_name.lower().replace(' ', '')}.com"
        
        # Common casino page patterns
        urls = [
            base_url,  # Homepage/lobby
            f"{base_url}/games",  # Games section
            f"{base_url}/promotions",  # Bonuses/promotions
            f"{base_url}/mobile"  # Mobile version
        ]
        
        return urls
    
    async def _store_screenshot(
        self, 
        screenshot_data: str, 
        casino_name: str, 
        category: str,
        source_url: str
    ) -> Optional[str]:
        """Store screenshot in Supabase storage"""
        
        if not self.supabase_client:
            logger.warning("⚠️ Supabase client not available - screenshot not stored")
            return None
        
        try:
            # Decode base64 screenshot data
            if isinstance(screenshot_data, str):
                image_data = base64.b64decode(screenshot_data)
            else:
                image_data = screenshot_data
            
            # Generate filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{casino_name.replace(' ', '_')}_{category}_{timestamp}.png"
            
            # Upload to Supabase storage
            response = self.supabase_client.storage.from_(self.storage_bucket).upload(
                filename, 
                image_data,
                {
                    "content-type": "image/png",
                    "cache-control": "3600"
                }
            )
            
            if response.get('error'):
                logger.error(f"❌ Screenshot upload failed: {response['error']}")
                return None
            
            # Get public URL
            public_url = self.supabase_client.storage.from_(self.storage_bucket).get_public_url(filename)
            
            # Store metadata in database
            await self._store_screenshot_metadata(filename, casino_name, category, source_url, public_url)
            
            logger.info(f"✅ Screenshot stored: {filename}")
            return public_url
            
        except Exception as e:
            logger.error(f"❌ Screenshot storage failed: {e}")
            return None
    
    async def _store_screenshot_metadata(
        self, 
        filename: str, 
        casino_name: str, 
        category: str,
        source_url: str,
        public_url: str
    ):
        """Store screenshot metadata in Supabase database"""
        
        if not self.supabase_client:
            return
        
        try:
            metadata = {
                "filename": filename,
                "casino_name": casino_name,
                "category": category,
                "source_url": source_url,
                "storage_url": public_url,
                "created_at": datetime.now().isoformat(),
                "capture_method": "browserbase_toolkit"
            }
            
            self.supabase_client.table("casino_screenshots").insert(metadata).execute()
            logger.info(f"✅ Screenshot metadata stored: {filename}")
            
        except Exception as e:
            logger.error(f"❌ Screenshot metadata storage failed: {e}")

# LCEL Chain Creation Functions
# =============================

def create_casino_screenshot_chain(
    browserbase_api_key: Optional[str] = None,
    project_id: Optional[str] = None
) -> Runnable:
    """
    🏗️ Create LCEL chain for casino screenshot capture
    
    This creates a native LangChain runnable that can be composed
    with other chains using the | operator.
    
    Usage:
    ```python
    screenshot_chain = create_casino_screenshot_chain()
    full_chain = research_chain | screenshot_chain | content_chain
    ```
    """
    
    toolkit = BrowserbaseScreenshotToolkit(
        browserbase_api_key=browserbase_api_key,
        project_id=project_id
    )
    
    async def capture_screenshots_runnable(inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Runnable function for LCEL composition"""
        
        casino_name = inputs.get("casino_name", "")
        if not casino_name:
            return {**inputs, "screenshot_error": "No casino name provided"}
        
        config = CasinoScreenshotConfig(
            casino_name=casino_name,
            target_urls=inputs.get("target_urls", []),
            categories=inputs.get("screenshot_categories", ["lobby", "games", "bonuses"]),
            max_screenshots=inputs.get("max_screenshots", 3)
        )
        
        result = await toolkit.capture_casino_screenshots(config)
        
        # Add screenshot results to chain output
        return {
            **inputs,
            "screenshots": result.screenshots,
            "screenshot_urls": result.storage_urls,
            "screenshot_metadata": result.metadata,
            "screenshot_success": result.success
        }
    
    return RunnableLambda(capture_screenshots_runnable)

def create_browserbase_tools_parallel() -> Runnable:
    """
    🔧 Create parallel Browserbase tools for complex casino interactions
    
    Useful for casinos that require navigation, clicking, or input
    before screenshot capture.
    """
    
    toolkit = BrowserbaseScreenshotToolkit()
    
    return RunnableParallel({
        "navigate": RunnableLambda(lambda x: toolkit.navigate_tool.arun(x.get("url", ""))),
        "screenshot": RunnableLambda(lambda x: toolkit.screenshot_tool.arun("")),
        "metadata": RunnableLambda(lambda x: {"timestamp": datetime.now().isoformat()})
    })

# Testing and Examples
# ===================

async def test_browserbase_casino_screenshots():
    """Test Browserbase casino screenshot capture"""
    
    print("🧪 Testing Browserbase Casino Screenshots")
    print("=" * 50)
    
    if not BROWSERBASE_AVAILABLE:
        print("❌ Browserbase tools not available")
        return
    
    try:
        toolkit = BrowserbaseScreenshotToolkit()
        
        config = CasinoScreenshotConfig(
            casino_name="Betway Casino",
            categories=["lobby", "games"],
            max_screenshots=2
        )
        
        result = await toolkit.capture_casino_screenshots(config)
        
        print(f"✅ Success: {result.success}")
        print(f"📸 Screenshots: {len(result.screenshots)}")
        print(f"🔗 Storage URLs: {len(result.storage_urls)}")
        
        return result
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return None

if __name__ == "__main__":
    asyncio.run(test_browserbase_casino_screenshots())