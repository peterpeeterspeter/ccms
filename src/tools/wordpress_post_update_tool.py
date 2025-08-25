#!/usr/bin/env python3
"""
📝 WordPress Post Update Tool - Claude.md Compliant
==================================================

LangChain BaseTool for updating WordPress post content with uploaded images.
Handles WordPress REST API post content updates.

Claude.md Compliance:
✅ All external I/O via /src/tools/* adapters  
✅ No ad-hoc HTTP inside chains
✅ BaseTool implementation for LCEL integration
"""

import requests
import base64
import logging
from typing import List, Dict, Any
from pydantic import BaseModel, Field

from langchain.tools import BaseTool

logger = logging.getLogger(__name__)

class WordPressPostUpdateInput(BaseModel):
    """Input schema for WordPress post update tool"""
    post_id: int = Field(description="WordPress post ID to update")
    media_results: List[Dict[str, Any]] = Field(description="Media upload results with IDs and URLs")
    wordpress_base_url: str = Field(default="https://www.crashcasino.io/wp-json/wp/v2", description="WordPress REST API base URL")
    username: str = Field(default="nmlwh", description="WordPress username")
    app_password: str = Field(default="G4Vd TiTf k1Yn CCII j24L F4Ls", description="WordPress application password")

class WordPressPostUpdateTool(BaseTool):
    """
    📝 LangChain tool for updating WordPress post content with images
    
    Claude.md compliant tool that handles all HTTP operations for WordPress
    post content updates. Used in LCEL chains via ToolNode.
    """
    
    name: str = "wordpress_post_update"
    description: str = "Update WordPress post content with uploaded casino images"
    args_schema: type = WordPressPostUpdateInput
    
    def _run(
        self,
        post_id: int,
        media_results: List[Dict[str, Any]],
        wordpress_base_url: str = "https://www.crashcasino.io/wp-json/wp/v2",
        username: str = "nmlwh",
        app_password: str = "G4Vd TiTf k1Yn CCII j24L F4Ls"
    ) -> Dict[str, Any]:
        """
        Update WordPress post content with uploaded images
        
        Args:
            post_id: WordPress post ID to update
            media_results: Results from media upload with IDs and URLs
            wordpress_base_url: WordPress REST API base URL
            username: WordPress username
            app_password: WordPress application password
            
        Returns:
            Dictionary with update results and success status
        """
        try:
            logger.info(f"📝 Updating WordPress post {post_id}")
            
            # Filter successful uploads
            successful_media = [m for m in media_results if m.get("upload_success", False)]
            
            if not successful_media:
                logger.warning("⚠️ No successful media uploads to add to post")
                return {
                    "update_success": False,
                    "error": "No successful media uploads available"
                }
            
            # Prepare authentication
            credentials = base64.b64encode(f"{username}:{app_password}".encode()).decode('utf-8')
            headers = {'Authorization': f'Basic {credentials}'}
            
            # Get current post content
            response = requests.get(f"{wordpress_base_url}/posts/{post_id}", headers=headers)
            
            if response.status_code != 200:
                logger.error(f"❌ Failed to fetch post: {response.status_code}")
                return {
                    "update_success": False,
                    "error": f"Failed to fetch post: {response.status_code}"
                }
            
            post_data = response.json()
            current_content = post_data.get('content', {})
            
            # Handle different content formats
            if isinstance(current_content, dict):
                content_text = current_content.get('raw', current_content.get('rendered', ''))
            else:
                content_text = str(current_content)
            
            # Create image HTML from uploaded media
            image_html_parts = []
            for media_info in successful_media:
                media_id = media_info["media_id"]
                title = media_info["title"]
                source_url = media_info["source_url"]
                
                img_html = f'<figure class="wp-block-image size-large"><img src="{source_url}" alt="{title}" class="wp-image-{media_id}"/><figcaption>{title}</figcaption></figure>'
                image_html_parts.append(img_html)
            
            # Insert images into content
            images_section = "\n\n".join(image_html_parts)
            
            # Look for existing image placeholders or add to end
            if "[casino-images]" in content_text:
                updated_content = content_text.replace("[casino-images]", images_section)
            else:
                # Add images before conclusion or at end
                if "</div>" in content_text:
                    # Insert before last closing div
                    updated_content = content_text.replace("</div>", f"\n\n{images_section}\n\n</div>")
                else:
                    updated_content = f"{content_text}\n\n{images_section}"
            
            # Update post
            update_data = {
                'content': updated_content
            }
            
            response = requests.post(
                f"{wordpress_base_url}/posts/{post_id}",
                headers=headers,
                json=update_data
            )
            
            if response.status_code == 200:
                logger.info("✅ WordPress post updated successfully")
                return {
                    "update_success": True,
                    "post_id": post_id,
                    "images_added": len(successful_media),
                    "content_length": len(updated_content),
                    "media_ids": [m["media_id"] for m in successful_media]
                }
            else:
                logger.error(f"❌ Post update failed: {response.status_code}")
                return {
                    "update_success": False,
                    "error": f"Post update failed: {response.status_code} - {response.text}"
                }
            
        except Exception as e:
            logger.error(f"❌ WordPress post update failed: {e}")
            return {
                "update_success": False,
                "error": str(e)
            }

    async def _arun(
        self,
        post_id: int,
        media_results: List[Dict[str, Any]],
        wordpress_base_url: str = "https://www.crashcasino.io/wp-json/wp/v2",
        username: str = "nmlwh",
        app_password: str = "G4Vd TiTf k1Yn CCII j24L F4Ls"
    ) -> Dict[str, Any]:
        """Async version of the tool"""
        return self._run(post_id, media_results, wordpress_base_url, username, app_password)

# Create tool instance for easy import
wordpress_post_update_tool = WordPressPostUpdateTool()