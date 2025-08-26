#!/usr/bin/env python3
"""
📸 Firecrawl Screenshot Tool
===========================

Production-ready tool for capturing casino screenshots using Firecrawl API
"""

import os
import logging
import requests
import time
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from langchain.tools import BaseTool
from dotenv import load_dotenv

# Load production environment
load_dotenv('.env.production')

logger = logging.getLogger(__name__)

class FirecrawlScreenshotInput(BaseModel):
    """Input schema for Firecrawl screenshot tool"""
    url: str = Field(description="URL to capture screenshot from")
    casino_name: str = Field(description="Casino name for file naming")
    
class FirecrawlScreenshotTool(BaseTool):
    """
    📸 Production screenshot capture tool using Firecrawl API
    
    Captures high-quality screenshots of casino websites for review articles
    """
    
    name: str = "firecrawl_screenshot"
    description: str = "Capture high-quality casino screenshots using Firecrawl API"
    args_schema: type = FirecrawlScreenshotInput
    
    def _run(self, url: str, casino_name: str) -> Dict[str, Any]:
        """Capture screenshot using Firecrawl API"""
        
        try:
            api_key = os.getenv('FIRECRAWL_API_KEY')
            if not api_key:
                logger.warning("⚠️  FIRECRAWL_API_KEY not found - using placeholder")
                return self._create_placeholder_screenshot(url, casino_name)
            
            logger.info(f"📸 Capturing screenshot: {url}")
            
            # Firecrawl screenshot API call
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            # Use correct V1 API with screenshot actions
            payload = {
                'url': url,
                'actions': [
                    {
                        'type': 'screenshot',
                        'fullPage': False,
                        'quality': 85,
                        'viewport': {
                            'width': 1920,
                            'height': 1080
                        }
                    }
                ]
            }
            
            response = requests.post(
                'https://api.firecrawl.dev/v1/scrape',
                headers=headers,
                json=payload,
                timeout=45
            )
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    # V1 API returns screenshots in data.actions.screenshots array
                    actions = data.get('data', {}).get('actions', {})
                    screenshots_list = actions.get('screenshots', [])
                    screenshot_url = screenshots_list[0] if screenshots_list else None
                    
                    if screenshot_url:
                        logger.info(f"✅ Screenshot captured successfully")
                        return {
                            "success": True,
                            "screenshot_url": screenshot_url,
                            "casino_name": casino_name,
                            "source_url": url,
                            "width": 1920,
                            "height": 1080,
                            "method": "firecrawl",
                            "compliance_status": "approved",
                            "timestamp": int(time.time())
                        }
                    else:
                        logger.warning(f"⚠️  No screenshot in response: {data}")
                        return self._create_placeholder_screenshot(url, casino_name)
                except ValueError as e:
                    logger.error(f"❌ JSON decode error: {e} - Response: {response.text[:200]}")
                    return self._create_placeholder_screenshot(url, casino_name)
            else:
                logger.error(f"❌ Firecrawl API error: {response.status_code} - {response.text[:200]}")
                return self._create_placeholder_screenshot(url, casino_name)
                
        except Exception as e:
            logger.error(f"❌ Screenshot capture failed: {e}")
            return self._create_placeholder_screenshot(url, casino_name)
    
    def _create_placeholder_screenshot(self, url: str, casino_name: str) -> Dict[str, Any]:
        """Create placeholder screenshot data when real capture fails"""
        
        return {
            "success": False,
            "screenshot_url": f"https://via.placeholder.com/1920x1080/1a1a2e/ffffff?text={casino_name.replace(' ', '+')}+Casino",
            "casino_name": casino_name,
            "source_url": url,
            "width": 1920,
            "height": 1080,
            "method": "placeholder",
            "compliance_status": "pending",
            "timestamp": int(time.time()),
            "note": "Placeholder image - Firecrawl API not available"
        }
    
    async def _arun(self, url: str, casino_name: str) -> Dict[str, Any]:
        """Async version of screenshot capture"""
        return self._run(url, casino_name)

# Create tool instance for easy import
firecrawl_screenshot_tool = FirecrawlScreenshotTool()