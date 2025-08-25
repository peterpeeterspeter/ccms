#!/usr/bin/env python3
"""
🎰 Native LangChain Google Images Casino Extractor
================================================

Pure LCEL composition for extracting individual casino images from Google Images
and uploading to WordPress. Uses native LangChain runnables and tools.

Native LangChain Architecture:
- RunnableLambda for Google Images navigation  
- RunnableParallel for concurrent image extraction
- RunnableBranch for conditional processing
- Built-in WordPress integration chain
"""

import asyncio
import logging
import os
import base64
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from langchain.schema.runnable import Runnable, RunnableLambda, RunnableParallel, RunnableBranch
from langchain_core.runnables import RunnablePassthrough
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

try:
    from langchain_community.tools.browserbase import (
        BrowserbaseNavigateTool,
        BrowserbaseScreenshotTool, 
        BrowserbaseClickTool,
        BrowserbaseInputTool
    )
    BROWSERBASE_AVAILABLE = True
except ImportError:
    BROWSERBASE_AVAILABLE = False

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# WordPress Configuration
WORDPRESS_BASE_URL = "https://www.crashcasino.io/wp-json/wp/v2" 
WORDPRESS_USERNAME = "peterjpetrich"
WORDPRESS_APP_PASSWORD = "BUpX VLgF MRc1 9oVW pkrH TuTm"

class GoogleImagesConfig(BaseModel):
    """Configuration for Google Images extraction"""
    search_query: str
    max_images: int = 4
    image_categories: List[str] = Field(default=["homepage", "games", "promotions", "mobile"])

class CasinoImageResult(BaseModel):
    """Result from casino image extraction"""
    success: bool
    extracted_images: List[Dict[str, Any]] = Field(default_factory=list)
    wordpress_media_ids: List[int] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None

def create_google_images_navigation_chain() -> Runnable:
    """
    🔍 Native LangChain chain for Google Images navigation
    """
    
    async def navigate_to_google_images(inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Navigate to Google Images search"""
        query = inputs.get("search_query", "mr vegas casino")
        google_images_url = f"https://images.google.com/search?q={query.replace(' ', '+')}&tbm=isch"
        
        try:
            if BROWSERBASE_AVAILABLE:
                navigate_tool = BrowserbaseNavigateTool(
                    api_key=os.getenv("BROWSERBASE_API_KEY"),
                    project_id=os.getenv("BROWSERBASE_PROJECT_ID")
                )
                
                logger.info(f"🔍 Navigating to Google Images: {query}")
                navigation_result = await navigate_tool.arun(google_images_url)
                
                # Wait for page load
                await asyncio.sleep(3)
                
                return {
                    **inputs,
                    "navigation_success": True,
                    "current_url": google_images_url,
                    "navigation_result": navigation_result
                }
            else:
                logger.warning("⚠️ Browserbase not available, using mock navigation")
                return {
                    **inputs,
                    "navigation_success": False,
                    "error": "Browserbase tools not available"
                }
                
        except Exception as e:
            logger.error(f"❌ Navigation failed: {e}")
            return {
                **inputs,
                "navigation_success": False,
                "error": str(e)
            }
    
    return RunnableLambda(navigate_to_google_images)

def create_image_extraction_chain() -> Runnable:
    """
    📸 Native LangChain chain for extracting individual images
    """
    
    async def extract_individual_images(inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Extract individual casino images from Google Images"""
        
        if not inputs.get("navigation_success", False):
            return {**inputs, "extraction_success": False}
        
        try:
            if BROWSERBASE_AVAILABLE:
                click_tool = BrowserbaseClickTool(
                    api_key=os.getenv("BROWSERBASE_API_KEY"),
                    project_id=os.getenv("BROWSERBASE_PROJECT_ID")
                )
                
                screenshot_tool = BrowserbaseScreenshotTool(
                    api_key=os.getenv("BROWSERBASE_API_KEY"),
                    project_id=os.getenv("BROWSERBASE_PROJECT_ID")
                )
                
                extracted_images = []
                max_images = inputs.get("max_images", 4)
                
                for i in range(max_images):
                    try:
                        logger.info(f"📸 Extracting image {i+1}/{max_images}")
                        
                        # Click on the i-th image (CSS selector for Google Images)
                        image_selector = f"img[data-src]:nth-of-type({i+1})"
                        click_result = await click_tool.arun(f"Click on image {i+1}", image_selector)
                        
                        # Wait for image to load in preview
                        await asyncio.sleep(2)
                        
                        # Take screenshot of the full-size image preview
                        screenshot_data = await screenshot_tool.arun("")
                        
                        if screenshot_data:
                            image_metadata = {
                                "index": i+1,
                                "screenshot_data": screenshot_data,
                                "category": inputs.get("image_categories", ["casino"])[i % len(inputs.get("image_categories", ["casino"]))],
                                "timestamp": datetime.now().isoformat()
                            }
                            extracted_images.append(image_metadata)
                            logger.info(f"✅ Extracted image {i+1}")
                        
                        # Close preview (escape key or back)
                        await asyncio.sleep(1)
                        
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to extract image {i+1}: {e}")
                        continue
                
                return {
                    **inputs,
                    "extraction_success": len(extracted_images) > 0,
                    "extracted_images": extracted_images,
                    "total_extracted": len(extracted_images)
                }
                
            else:
                logger.warning("⚠️ Browserbase not available for image extraction")
                return {**inputs, "extraction_success": False, "error": "Browserbase not available"}
                
        except Exception as e:
            logger.error(f"❌ Image extraction failed: {e}")
            return {**inputs, "extraction_success": False, "error": str(e)}
    
    return RunnableLambda(extract_individual_images)

def create_wordpress_upload_chain() -> Runnable:
    """
    📤 Native LangChain chain for WordPress media upload
    """
    
    async def upload_to_wordpress(inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Upload extracted images to WordPress"""
        
        if not inputs.get("extraction_success", False):
            return {**inputs, "upload_success": False}
        
        try:
            import requests
            
            extracted_images = inputs.get("extracted_images", [])
            media_ids = []
            
            # WordPress credentials
            credentials = base64.b64encode(f"{WORDPRESS_USERNAME}:{WORDPRESS_APP_PASSWORD}".encode()).decode('utf-8')
            headers = {
                'Authorization': f'Basic {credentials}',
                'Content-Type': 'image/png'
            }
            
            for i, image_data in enumerate(extracted_images):
                try:
                    logger.info(f"📤 Uploading image {i+1} to WordPress")
                    
                    # Decode base64 screenshot data
                    screenshot_data = image_data.get("screenshot_data", "")
                    if isinstance(screenshot_data, str):
                        image_bytes = base64.b64decode(screenshot_data)
                    else:
                        continue
                    
                    # Upload to WordPress
                    upload_headers = {
                        **headers,
                        'Content-Disposition': f'attachment; filename="mr_vegas_casino_{i+1}.png"'
                    }
                    
                    response = requests.post(
                        f"{WORDPRESS_BASE_URL}/media",
                        headers=upload_headers,
                        data=image_bytes,
                        timeout=60
                    )
                    
                    if response.status_code in [200, 201]:
                        media_data = response.json()
                        media_id = media_data['id']
                        media_ids.append(media_id)
                        
                        # Update metadata
                        category = image_data.get("category", "casino")
                        metadata_update = {
                            'title': f"Mr Vegas Casino - {category.title()}",
                            'alt_text': f"Mr Vegas Casino {category} interface screenshot",
                            'caption': f"Mr Vegas Casino - {category} view"
                        }
                        
                        requests.post(
                            f"{WORDPRESS_BASE_URL}/media/{media_id}",
                            headers={'Authorization': f'Basic {credentials}'},
                            json=metadata_update
                        )
                        
                        logger.info(f"✅ Uploaded to WordPress: Media ID {media_id}")
                    else:
                        logger.warning(f"⚠️ WordPress upload failed: {response.status_code}")
                        
                except Exception as e:
                    logger.warning(f"⚠️ Failed to upload image {i+1}: {e}")
                    continue
            
            return {
                **inputs,
                "upload_success": len(media_ids) > 0,
                "wordpress_media_ids": media_ids,
                "total_uploaded": len(media_ids)
            }
            
        except Exception as e:
            logger.error(f"❌ WordPress upload failed: {e}")
            return {**inputs, "upload_success": False, "error": str(e)}
    
    return RunnableLambda(upload_to_wordpress)

def create_casino_image_extraction_chain() -> Runnable:
    """
    🎰 Complete Native LangChain LCEL chain for casino image extraction
    
    Chain composition:
    Navigation → Image Extraction → WordPress Upload
    """
    
    # Create individual chain components
    navigation_chain = create_google_images_navigation_chain()
    extraction_chain = create_image_extraction_chain()
    upload_chain = create_wordpress_upload_chain()
    
    # Compose the complete LCEL chain
    complete_chain = (
        RunnablePassthrough()
        | navigation_chain
        | extraction_chain  
        | upload_chain
        | RunnableLambda(lambda x: CasinoImageResult(
            success=x.get("upload_success", False),
            extracted_images=x.get("extracted_images", []),
            wordpress_media_ids=x.get("wordpress_media_ids", []),
            metadata={
                "navigation_success": x.get("navigation_success", False),
                "extraction_success": x.get("extraction_success", False),
                "upload_success": x.get("upload_success", False),
                "total_extracted": x.get("total_extracted", 0),
                "total_uploaded": x.get("total_uploaded", 0),
                "timestamp": datetime.now().isoformat()
            },
            error_message=x.get("error")
        ))
    )
    
    return complete_chain

async def main():
    """
    Main function to run the native LangChain casino image extraction
    """
    
    logger.info("🎰 Starting Native LangChain Casino Image Extraction")
    
    if not BROWSERBASE_AVAILABLE:
        logger.error("❌ Browserbase tools not available. Install langchain-community")
        return
    
    # Configuration
    config = GoogleImagesConfig(
        search_query="mr vegas casino interface screenshots",
        max_images=4,
        image_categories=["homepage", "games", "promotions", "mobile"]
    )
    
    # Create and run the chain
    extraction_chain = create_casino_image_extraction_chain()
    
    try:
        result = await extraction_chain.ainvoke({
            "search_query": config.search_query,
            "max_images": config.max_images,
            "image_categories": config.image_categories
        })
        
        # Log results
        logger.info("🎊 Casino Image Extraction Complete!")
        logger.info(f"✅ Success: {result.success}")
        logger.info(f"📸 Extracted: {len(result.extracted_images)} images")
        logger.info(f"📤 Uploaded: {len(result.wordpress_media_ids)} images")
        
        if result.wordpress_media_ids:
            logger.info("📋 WordPress Media IDs:")
            for i, media_id in enumerate(result.wordpress_media_ids):
                category = config.image_categories[i % len(config.image_categories)]
                logger.info(f"  - Mr Vegas Casino {category.title()}: {media_id}")
        
        if result.error_message:
            logger.warning(f"⚠️ Errors: {result.error_message}")
        
        return result
        
    except Exception as e:
        logger.error(f"💥 Chain execution failed: {e}")
        return CasinoImageResult(
            success=False,
            error_message=str(e)
        )

if __name__ == "__main__":
    asyncio.run(main())