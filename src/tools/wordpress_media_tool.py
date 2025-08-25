#!/usr/bin/env python3
"""
📤 WordPress Media Upload Tool - Claude.md Compliant
==================================================

LangChain BaseTool for uploading images to WordPress media library.
Handles WordPress REST API authentication and media management.

Claude.md Compliance:
✅ All external I/O via /src/tools/* adapters  
✅ No ad-hoc HTTP inside chains
✅ BaseTool implementation for LCEL integration
"""

import requests
import base64
import logging
from typing import List, Dict, Any
from pathlib import Path
from pydantic import BaseModel, Field

from langchain.tools import BaseTool

logger = logging.getLogger(__name__)

class WordPressMediaUploadInput(BaseModel):
    """Input schema for WordPress media upload tool"""
    images: List[Dict[str, Any]] = Field(description="List of image data dictionaries to upload")
    wordpress_base_url: str = Field(default="https://www.crashcasino.io/wp-json/wp/v2", description="WordPress REST API base URL")
    username: str = Field(default="nmlwh", description="WordPress username")
    app_password: str = Field(default="G4Vd TiTf k1Yn CCII j24L F4Ls", description="WordPress application password")

class WordPressMediaUploadTool(BaseTool):
    """
    📤 LangChain tool for uploading images to WordPress media library
    
    Claude.md compliant tool that handles all HTTP operations for WordPress
    media uploads. Used in LCEL chains via ToolNode.
    """
    
    name: str = "wordpress_media_upload"
    description: str = "Upload casino images to WordPress media library via REST API"
    args_schema: type = WordPressMediaUploadInput
    
    def _run(
        self, 
        images: List[Dict[str, Any]], 
        wordpress_base_url: str = "https://www.crashcasino.io/wp-json/wp/v2",
        username: str = "nmlwh",
        app_password: str = "G4Vd TiTf k1Yn CCII j24L F4Ls"
    ) -> List[Dict[str, Any]]:
        """
        Upload images to WordPress media library
        
        Args:
            images: List of image data dictionaries from image download
            wordpress_base_url: WordPress REST API base URL
            username: WordPress username
            app_password: WordPress application password
            
        Returns:
            List of media upload results with WordPress media IDs
        """
        try:
            logger.info(f"📤 Starting WordPress upload of {len(images)} images")
            
            media_results = []
            
            # Prepare authentication
            credentials = base64.b64encode(f"{username}:{app_password}".encode()).decode('utf-8')
            
            for image_data in images:
                try:
                    file_path = image_data["file_path"]
                    content_type = image_data["content_type"]
                    index = image_data["index"]
                    filename = image_data["filename"]
                    
                    logger.info(f"📤 Uploading to WordPress: {filename}")
                    
                    # Read image data
                    with open(file_path, 'rb') as f:
                        image_bytes = f.read()
                    
                    # Upload headers
                    headers = {
                        'Authorization': f'Basic {credentials}',
                        'Content-Type': content_type,
                        'Content-Disposition': f'attachment; filename="{filename}"'
                    }
                    
                    # Upload to WordPress
                    response = requests.post(
                        f"{wordpress_base_url}/media",
                        headers=headers,
                        data=image_bytes,
                        timeout=60
                    )
                    
                    if response.status_code in [200, 201]:
                        media_data = response.json()
                        media_id = media_data['id']
                        source_url = media_data.get('source_url', '')
                        
                        # Update metadata
                        metadata_update = {
                            'title': f"Casino Interface Screenshot {index}",
                            'alt_text': f"Casino interface screenshot {index}",
                            'caption': f"Casino Interface View {index}"
                        }
                        
                        requests.post(
                            f"{wordpress_base_url}/media/{media_id}",
                            headers={'Authorization': f'Basic {credentials}'},
                            json=metadata_update
                        )
                        
                        media_result = {
                            "media_id": media_id,
                            "source_url": source_url,
                            "title": f"Casino Interface Screenshot {index}",
                            "index": index,
                            "original_file": file_path,
                            "upload_success": True
                        }
                        
                        media_results.append(media_result)
                        logger.info(f"✅ Uploaded: Media ID {media_id}")
                        
                    else:
                        logger.warning(f"⚠️ Upload failed: {response.status_code} - {response.text}")
                        media_results.append({
                            "media_id": None,
                            "upload_success": False,
                            "error": f"{response.status_code}: {response.text}",
                            "original_file": file_path
                        })
                
                except Exception as e:
                    logger.warning(f"⚠️ Failed to upload {image_data.get('file_path', 'unknown')}: {e}")
                    media_results.append({
                        "media_id": None,
                        "upload_success": False,
                        "error": str(e),
                        "original_file": image_data.get('file_path', 'unknown')
                    })
                    continue
            
            successful_uploads = [r for r in media_results if r["upload_success"]]
            logger.info(f"📤 WordPress upload complete: {len(successful_uploads)} successful")
            
            return media_results
            
        except Exception as e:
            logger.error(f"❌ WordPress media upload failed: {e}")
            return []

    async def _arun(
        self, 
        images: List[Dict[str, Any]], 
        wordpress_base_url: str = "https://www.crashcasino.io/wp-json/wp/v2",
        username: str = "nmlwh",
        app_password: str = "G4Vd TiTf k1Yn CCII j24L F4Ls"
    ) -> List[Dict[str, Any]]:
        """Async version of the tool"""
        return self._run(images, wordpress_base_url, username, app_password)

# Create tool instance for easy import
wordpress_media_upload_tool = WordPressMediaUploadTool()