#!/usr/bin/env python3
"""
📝 WordPress Post Creation Tool - Claude.md Compliant
===================================================

LangChain BaseTool for creating new WordPress posts via REST API.
Handles WordPress post creation with content, title, and metadata.

Claude.md Compliance:
✅ All external I/O via /src/tools/* adapters  
✅ No ad-hoc HTTP inside chains
✅ BaseTool implementation for LCEL integration
"""

import requests
import base64
import logging
from typing import Dict, Any
from pydantic import BaseModel, Field

from langchain.tools import BaseTool

logger = logging.getLogger(__name__)

class WordPressPostCreationInput(BaseModel):
    """Input schema for WordPress post creation tool"""
    title: str = Field(description="Post title")
    content: str = Field(description="Post content (HTML or plain text)")
    excerpt: str = Field(default="", description="Post excerpt/summary")
    status: str = Field(default="draft", description="Post status: draft, publish, private")
    wordpress_base_url: str = Field(default="https://www.crashcasino.io/wp-json/wp/v2", description="WordPress REST API base URL")
    username: str = Field(default="nmlwh", description="WordPress username")
    app_password: str = Field(default="G4Vd TiTf k1Yn CCII j24L F4Ls", description="WordPress application password")

class WordPressPostCreationTool(BaseTool):
    """
    📝 LangChain tool for creating new WordPress posts
    
    Claude.md compliant tool that handles all HTTP operations for WordPress
    post creation. Used in LCEL chains via ToolNode.
    """
    
    name: str = "wordpress_post_creation"
    description: str = "Create new WordPress post with title, content, and metadata"
    args_schema: type = WordPressPostCreationInput
    
    def _run(
        self,
        title: str,
        content: str,
        excerpt: str = "",
        status: str = "draft",
        wordpress_base_url: str = "https://www.crashcasino.io/wp-json/wp/v2",
        username: str = "nmlwh",
        app_password: str = "G4Vd TiTf k1Yn CCII j24L F4Ls"
    ) -> Dict[str, Any]:
        """
        Create a new WordPress post
        
        Args:
            title: Post title
            content: Post content (HTML or plain text)
            excerpt: Post excerpt/summary
            status: Post status (draft, publish, private)
            wordpress_base_url: WordPress REST API base URL
            username: WordPress username
            app_password: WordPress application password
            
        Returns:
            Dictionary with creation results and new post ID
        """
        try:
            logger.info(f"📝 Creating WordPress post: {title}")
            
            # Prepare authentication
            credentials = base64.b64encode(f"{username}:{app_password}".encode()).decode('utf-8')
            headers = {
                'Authorization': f'Basic {credentials}',
                'Content-Type': 'application/json'
            }
            
            # Prepare post data
            post_data = {
                'title': title,
                'content': content,
                'excerpt': excerpt,
                'status': status,
                'comment_status': 'closed',  # Disable comments by default
                'ping_status': 'closed'      # Disable pingbacks by default
            }
            
            # Create post
            response = requests.post(
                f"{wordpress_base_url}/posts",
                headers=headers,
                json=post_data,
                timeout=60
            )
            
            if response.status_code in [200, 201]:
                post_data = response.json()
                post_id = post_data['id']
                post_url = post_data.get('link', '')
                
                logger.info(f"✅ WordPress post created successfully: ID {post_id}")
                
                return {
                    "creation_success": True,
                    "post_id": post_id,
                    "post_url": post_url,
                    "title": title,
                    "status": status,
                    "content_length": len(content),
                    "excerpt_length": len(excerpt)
                }
            else:
                logger.error(f"❌ Post creation failed: {response.status_code}")
                return {
                    "creation_success": False,
                    "error": f"Post creation failed: {response.status_code} - {response.text}"
                }
            
        except Exception as e:
            logger.error(f"❌ WordPress post creation failed: {e}")
            return {
                "creation_success": False,
                "error": str(e)
            }

    async def _arun(
        self,
        title: str,
        content: str,
        excerpt: str = "",
        status: str = "draft",
        wordpress_base_url: str = "https://www.crashcasino.io/wp-json/wp/v2",
        username: str = "nmlwh",
        app_password: str = "G4Vd TiTf k1Yn CCII j24L F4Ls"
    ) -> Dict[str, Any]:
        """Async version of the tool"""
        return self._run(title, content, excerpt, status, wordpress_base_url, username, app_password)

# Create tool instance for easy import
wordpress_post_creation_tool = WordPressPostCreationTool()