#!/usr/bin/env python3
"""
📥 Image Download Tool - Claude.md Compliant
==========================================

LangChain BaseTool for downloading casino images from URLs.
Handles actual image downloading with validation and storage.

Claude.md Compliance:
✅ All external I/O via /src/tools/* adapters  
✅ No ad-hoc HTTP inside chains
✅ BaseTool implementation for LCEL integration
"""

import requests
import logging
import time
from typing import List, Dict, Any
from pathlib import Path
from urllib.parse import urlparse
from pydantic import BaseModel, Field

from langchain.tools import BaseTool

logger = logging.getLogger(__name__)

class ImageDownloadInput(BaseModel):
    """Input schema for image download tool"""
    image_urls: List[str] = Field(description="List of image URLs to download")
    output_dir: str = Field(default="temp_casino_images", description="Directory to save images")

class ImageDownloadTool(BaseTool):
    """
    📥 LangChain tool for downloading casino images from URLs
    
    Claude.md compliant tool that handles all HTTP operations for image
    downloading. Used in LCEL chains via ToolNode.
    """
    
    name: str = "image_download"
    description: str = "Download casino images from provided URLs with validation"
    args_schema: type = ImageDownloadInput
    
    def _run(self, image_urls: List[str], output_dir: str = "temp_casino_images") -> List[Dict[str, Any]]:
        """
        Download casino images from URLs
        
        Args:
            image_urls: List of image URLs to download
            output_dir: Directory to save downloaded images
            
        Returns:
            List of dictionaries with download results and metadata
        """
        try:
            logger.info(f"📥 Starting download of {len(image_urls)} images")
            
            # Create output directory
            output_path = Path(output_dir)
            output_path.mkdir(exist_ok=True)
            
            downloaded_images = []
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer': 'https://www.google.com/'
            }
            
            for i, url in enumerate(image_urls):
                try:
                    logger.info(f"⬇️ Downloading image {i+1}/{len(image_urls)}")
                    
                    # Download image
                    response = requests.get(url, headers=headers, timeout=30, stream=True)
                    response.raise_for_status()
                    
                    # Validate content type
                    content_type = response.headers.get('content-type', '')
                    if not content_type.startswith('image/'):
                        logger.warning(f"⚠️ Not an image: {content_type}")
                        continue
                    
                    # Determine file extension
                    if 'jpeg' in content_type or 'jpg' in content_type:
                        ext = '.jpg'
                    elif 'png' in content_type:
                        ext = '.png'
                    elif 'webp' in content_type:
                        ext = '.webp'
                    else:
                        ext = '.jpg'  # Default
                    
                    # Save image
                    filename = output_path / f"casino_image_{i+1}{ext}"
                    with open(filename, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    # Check file size (filter out small logos/icons)
                    file_size = filename.stat().st_size
                    if file_size < 10000:  # Less than 10KB
                        logger.warning(f"⚠️ Image {i+1} too small: {file_size} bytes")
                        filename.unlink()
                        continue
                    
                    # Store image metadata
                    image_data = {
                        "file_path": str(filename),
                        "original_url": url,
                        "file_size": file_size,
                        "content_type": content_type,
                        "index": i + 1,
                        "filename": filename.name
                    }
                    
                    downloaded_images.append(image_data)
                    logger.info(f"✅ Downloaded: {filename.name} ({file_size:,} bytes)")
                    
                    # Rate limiting
                    time.sleep(1)
                    
                except Exception as e:
                    logger.warning(f"⚠️ Failed to download image {i+1}: {e}")
                    continue
            
            logger.info(f"📥 Download complete: {len(downloaded_images)} images saved")
            return downloaded_images
            
        except Exception as e:
            logger.error(f"❌ Image download failed: {e}")
            return []

    async def _arun(self, image_urls: List[str], output_dir: str = "temp_casino_images") -> List[Dict[str, Any]]:
        """Async version of the tool"""
        return self._run(image_urls, output_dir)

# Create tool instance for easy import
image_download_tool = ImageDownloadTool()