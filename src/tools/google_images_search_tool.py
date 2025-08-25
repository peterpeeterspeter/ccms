#!/usr/bin/env python3
"""
🔍 Google Images Search Tool - Claude.md Compliant
================================================

LangChain BaseTool for extracting casino image URLs from Google Images.
Moves all HTTP logic into proper tool abstraction as required by Claude.md.

Claude.md Compliance:
✅ All external I/O via /src/tools/* adapters  
✅ No ad-hoc HTTP inside chains
✅ BaseTool implementation for LCEL integration
"""

import requests
import re
import logging
from typing import List, Dict, Any, Optional
from urllib.parse import unquote
from pydantic import BaseModel, Field

from langchain.tools import BaseTool

logger = logging.getLogger(__name__)

class GoogleImagesSearchInput(BaseModel):
    """Input schema for Google Images search tool"""
    query: str = Field(description="Search query for casino images")
    max_images: int = Field(default=6, description="Maximum number of images to extract")

class GoogleImagesSearchTool(BaseTool):
    """
    🎰 LangChain tool for extracting casino image URLs from Google Images
    
    Claude.md compliant tool that handles all HTTP operations for Google Images
    search and URL extraction. Used in LCEL chains via ToolNode.
    """
    
    name: str = "google_images_search"
    description: str = "Extract casino image URLs from Google Images search results"
    args_schema: type = GoogleImagesSearchInput
    
    def _run(self, query: str, max_images: int = 6) -> List[str]:
        """
        Extract casino image URLs from Google Images
        
        Args:
            query: Search query for casino images
            max_images: Maximum number of image URLs to extract
            
        Returns:
            List of image URLs extracted from Google Images
        """
        try:
            logger.info(f"🔍 Google Images search: {query}")
            
            # Construct Google Images search URL
            google_url = f"https://images.google.com/search?q={query.replace(' ', '+')}&tbm=isch"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # Fetch Google Images HTML
            response = requests.get(google_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Extract image URLs using multiple patterns
            image_urls = self._extract_image_urls(response.text, query, max_images)
            
            logger.info(f"✅ Extracted {len(image_urls)} image URLs")
            return image_urls
            
        except Exception as e:
            logger.error(f"❌ Google Images search failed: {e}")
            return []
    
    def _extract_image_urls(self, html_content: str, query: str, max_images: int) -> List[str]:
        """
        Extract actual image URLs from Google Images HTML using multiple patterns
        """
        image_urls = []
        
        # Pattern 1: "ou":"<url>" (original URL)
        ou_pattern = r'"ou":"([^"]+)"'
        ou_matches = re.findall(ou_pattern, html_content)
        
        for match in ou_matches:
            decoded_url = unquote(match)
            if (decoded_url.startswith('http') and 
                any(ext in decoded_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']) and
                ('casino' in decoded_url.lower() or 'vegas' in decoded_url.lower())):
                image_urls.append(decoded_url)
        
        # Pattern 2: ["<url>", width, height, ...] arrays
        array_pattern = r'\["(https://[^"]+\.(jpg|jpeg|png|webp)[^"]*)",\d+,\d+'
        array_matches = re.findall(array_pattern, html_content, re.IGNORECASE)
        
        for match_tuple in array_matches:
            url = match_tuple[0]
            if (url not in image_urls and 
                ('casino' in url.lower() or 'vegas' in url.lower() or len(url) > 100)):
                image_urls.append(url)
        
        # Pattern 3: JavaScript object with image data
        js_pattern = r'"(https://[^"]+\.(?:jpg|jpeg|png|webp))"[^}]*"casino|vegas"'
        js_matches = re.findall(js_pattern, html_content, re.IGNORECASE)
        
        for match in js_matches:
            if match not in image_urls:
                image_urls.append(match)
        
        # Pattern 4: Any large image URLs (fallback)
        if len(image_urls) < 2:
            large_image_pattern = r'"(https://[^"]+\.(jpg|jpeg|png|webp)[^"]*)"'
            large_matches = re.findall(large_image_pattern, html_content, re.IGNORECASE)
            
            for match in large_matches:
                if (match not in image_urls and 
                    len(match) > 80 and  # Longer URLs likely to be actual images
                    'gstatic.com' not in match and  # Skip Google static assets
                    'googleapis.com' not in match):
                    image_urls.append(match)
        
        # Filter and validate URLs
        valid_urls = []
        for url in image_urls:
            # Skip obvious non-casino images
            if any(skip in url.lower() for skip in ['icon', 'logo', 'button', 'arrow', 'gstatic']):
                continue
            # Prefer URLs that might contain casino content
            valid_urls.append(url)
        
        return valid_urls[:max_images]

    async def _arun(self, query: str, max_images: int = 6) -> List[str]:
        """Async version of the tool"""
        return self._run(query, max_images)

# Create tool instance for easy import
google_images_search_tool = GoogleImagesSearchTool()