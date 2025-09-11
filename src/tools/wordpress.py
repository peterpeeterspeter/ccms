"""
WordPress Tool Adapter
======================

WordPress REST API client for casino review publishing.
Follows WARP.md /src/tools/* adapter pattern with proper error handling and authentication.
"""

import asyncio
import aiohttp
import base64
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urljoin
from pydantic import BaseModel, Field, HttpUrl
import json
import logging

logger = logging.getLogger(__name__)


class WordPressConfig(BaseModel):
    """WordPress connection configuration"""
    base_url: HttpUrl = Field(..., description="WordPress site URL")
    username: str = Field(..., description="WordPress username")
    app_password: str = Field(..., description="WordPress application password")
    timeout: int = Field(30, description="Request timeout in seconds")
    max_retries: int = Field(3, description="Maximum retry attempts")


class WordPressClient:
    """
    WordPress REST API client with comprehensive MT Casino post type support.
    
    Features:
    - Application password authentication
    - Automatic retry logic with exponential backoff
    - Comprehensive error handling and logging
    - Full MT Casino custom post type integration
    - Media upload and management
    - Taxonomy and custom field management
    """
    
    def __init__(self, config: WordPressConfig):
        self.config = config
        self.base_url = str(config.base_url).rstrip('/')
        self.api_base = f"{self.base_url}/wp-json/wp/v2"
        
        # Setup authentication header
        credentials = f"{config.username}:{config.app_password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        self.auth_header = f"Basic {encoded_credentials}"
        
        self.session = None
        self._setup_session()
    
    def _setup_session(self):
        """Setup aiohttp session with proper headers and timeout"""
        timeout = aiohttp.ClientTimeout(total=self.config.timeout)
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            headers={
                "Authorization": self.auth_header,
                "Content-Type": "application/json",
                "User-Agent": "CrashCasino-Agent/1.0"
            }
        )
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _make_request(self, 
                          method: str, 
                          endpoint: str, 
                          data: Optional[Dict] = None,
                          params: Optional[Dict] = None) -> Dict:
        """
        Make authenticated HTTP request to WordPress REST API with retry logic
        """
        url = urljoin(self.api_base + "/", endpoint)
        
        for attempt in range(self.config.max_retries):
            try:
                async with self.session.request(
                    method=method,
                    url=url,
                    json=data,
                    params=params
                ) as response:
                    
                    # Log request for debugging
                    logger.debug(f"WordPress API {method} {url} - Status: {response.status}")
                    
                    if response.status == 401:
                        raise Exception("WordPress authentication failed - check credentials")
                    
                    if response.status == 403:
                        raise Exception("WordPress permission denied - check user capabilities")
                    
                    response_data = await response.json()
                    
                    if response.status >= 400:
                        error_message = response_data.get('message', f'HTTP {response.status}')
                        raise Exception(f"WordPress API error: {error_message}")
                    
                    return response_data
                    
            except aiohttp.ClientError as e:
                logger.warning(f"WordPress API request failed (attempt {attempt + 1}): {str(e)}")
                if attempt == self.config.max_retries - 1:
                    raise Exception(f"WordPress API connection failed after {self.config.max_retries} attempts")
                
                # Exponential backoff
                await asyncio.sleep(2 ** attempt)
            
            except json.JSONDecodeError as e:
                raise Exception(f"WordPress API returned invalid JSON: {str(e)}")
    
    # Core WordPress operations
    
    async def create_post(self, post_data: Dict) -> Dict:
        """
        Create a new WordPress post
        
        Args:
            post_data: Post data including title, content, type, etc.
            
        Returns:
            Created post data with ID and URL
        """
        # Ensure required fields
        if 'title' not in post_data:
            raise ValueError("Post title is required")
        
        # Set default values for MT Casino posts
        defaults = {
            'status': 'publish',
            'comment_status': 'open',
            'ping_status': 'closed',
            'type': 'mt_listing'  # Default to MT Casino listing type
        }
        
        # Merge with defaults
        final_data = {**defaults, **post_data}
        
        try:
            result = await self._make_request('POST', 'posts', data=final_data)
            logger.info(f"Created WordPress post ID {result.get('id')} - {result.get('link')}")
            return result
        
        except Exception as e:
            logger.error(f"Failed to create WordPress post: {str(e)}")
            raise
    
    async def update_post(self, post_id: int, post_data: Dict) -> Dict:
        """Update existing WordPress post"""
        try:
            result = await self._make_request('POST', f'posts/{post_id}', data=post_data)
            logger.info(f"Updated WordPress post ID {post_id}")
            return result
        
        except Exception as e:
            logger.error(f"Failed to update WordPress post {post_id}: {str(e)}")
            raise
    
    async def get_post(self, post_id: int) -> Dict:
        """Get WordPress post by ID"""
        try:
            return await self._make_request('GET', f'posts/{post_id}')
        
        except Exception as e:
            logger.error(f"Failed to get WordPress post {post_id}: {str(e)}")
            raise
    
    async def delete_post(self, post_id: int, force: bool = False) -> Dict:
        """Delete WordPress post"""
        params = {'force': 'true'} if force else {}
        
        try:
            result = await self._make_request('DELETE', f'posts/{post_id}', params=params)
            logger.info(f"Deleted WordPress post ID {post_id}")
            return result
        
        except Exception as e:
            logger.error(f"Failed to delete WordPress post {post_id}: {str(e)}")
            raise
    
    # Custom post type operations (MT Casino specific)
    
    async def create_mt_listing(self, listing_data: Dict) -> Dict:
        """Create MT Casino listing post with proper type"""
        listing_data['type'] = 'mt_listing'
        return await self.create_post(listing_data)
    
    async def create_mt_review(self, review_data: Dict) -> Dict:
        """Create MT Casino review post"""
        review_data['type'] = 'mt_reviews'
        return await self.create_post(review_data)
    
    # Media operations
    
    async def upload_media(self, file_path: str, title: str = None, description: str = None) -> Dict:
        """
        Upload media file to WordPress
        
        Args:
            file_path: Path to the file to upload
            title: Media title
            description: Media description
            
        Returns:
            Media object with ID and URL
        """
        import aiofiles
        import os
        from pathlib import Path
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Media file not found: {file_path}")
        
        file_name = Path(file_path).name
        mime_type = self._get_mime_type(file_path)
        
        # Prepare headers for media upload
        headers = {
            "Authorization": self.auth_header,
            "Content-Disposition": f'attachment; filename="{file_name}"'
        }
        
        if title:
            headers["Content-Description"] = title
        
        try:
            async with aiofiles.open(file_path, 'rb') as f:
                file_data = await f.read()
            
            url = urljoin(self.api_base + "/", "media")
            
            async with self.session.post(
                url=url,
                data=file_data,
                headers=headers
            ) as response:
                
                if response.status >= 400:
                    error_data = await response.json()
                    raise Exception(f"Media upload failed: {error_data.get('message', 'Unknown error')}")
                
                result = await response.json()
                logger.info(f"Uploaded media ID {result.get('id')} - {file_name}")
                
                return result
        
        except Exception as e:
            logger.error(f"Failed to upload media {file_path}: {str(e)}")
            raise
    
    async def get_media(self, media_id: int) -> Dict:
        """Get media information by ID"""
        try:
            return await self._make_request('GET', f'media/{media_id}')
        
        except Exception as e:
            logger.error(f"Failed to get media {media_id}: {str(e)}")
            raise
    
    async def attach_media_to_post(self, media_id: int, post_id: int) -> Dict:
        """Attach media to a post"""
        try:
            result = await self._make_request('POST', f'media/{media_id}', data={
                'post': post_id
            })
            logger.info(f"Attached media {media_id} to post {post_id}")
            return result
        
        except Exception as e:
            logger.error(f"Failed to attach media {media_id} to post {post_id}: {str(e)}")
            raise
    
    # Custom fields (meta) operations
    
    async def set_post_meta(self, post_id: int, meta_key: str, meta_value: Any) -> bool:
        """
        Set post meta field
        
        Note: WordPress REST API requires custom endpoint or plugin for meta fields.
        This is a simplified version - you may need to adjust based on your setup.
        """
        try:
            # Try to update post with meta data
            result = await self._make_request('POST', f'posts/{post_id}', data={
                'meta': {meta_key: meta_value}
            })
            
            return True
        
        except Exception as e:
            logger.warning(f"Failed to set meta {meta_key} for post {post_id}: {str(e)}")
            # For MT Casino custom fields, you might need a custom endpoint
            # or use a plugin like Advanced Custom Fields REST API
            return False
    
    async def get_post_meta(self, post_id: int, meta_key: str = None) -> Union[Dict, Any]:
        """Get post meta fields"""
        try:
            post = await self.get_post(post_id)
            meta_data = post.get('meta', {})
            
            if meta_key:
                return meta_data.get(meta_key)
            
            return meta_data
        
        except Exception as e:
            logger.error(f"Failed to get meta for post {post_id}: {str(e)}")
            raise
    
    # Taxonomy operations
    
    async def assign_term(self, post_id: int, taxonomy: str, term_slug: str) -> bool:
        """
        Assign taxonomy term to a post
        
        Args:
            post_id: WordPress post ID
            taxonomy: Taxonomy name (e.g., 'category', 'mt-listing-tags')
            term_slug: Term slug to assign
        """
        try:
            # First, try to get the term ID
            term_id = await self._get_term_id(taxonomy, term_slug)
            
            if not term_id:
                # Create the term if it doesn't exist
                term_id = await self._create_term(taxonomy, term_slug)
            
            # Get current terms
            post = await self.get_post(post_id)
            current_terms = post.get(taxonomy, [])
            
            if term_id not in current_terms:
                current_terms.append(term_id)
                
                # Update post with new terms
                await self._make_request('POST', f'posts/{post_id}', data={
                    taxonomy: current_terms
                })
            
            logger.info(f"Assigned term '{term_slug}' ({taxonomy}) to post {post_id}")
            return True
        
        except Exception as e:
            logger.warning(f"Failed to assign term {term_slug} to post {post_id}: {str(e)}")
            return False
    
    async def _get_term_id(self, taxonomy: str, term_slug: str) -> Optional[int]:
        """Get term ID by slug"""
        try:
            result = await self._make_request('GET', f'{taxonomy}', params={
                'slug': term_slug
            })
            
            if result and len(result) > 0:
                return result[0]['id']
            
            return None
        
        except Exception:
            return None
    
    async def _create_term(self, taxonomy: str, term_slug: str, term_name: str = None) -> int:
        """Create new taxonomy term"""
        if not term_name:
            term_name = term_slug.replace('-', ' ').replace('_', ' ').title()
        
        try:
            result = await self._make_request('POST', taxonomy, data={
                'name': term_name,
                'slug': term_slug
            })
            
            logger.info(f"Created new term '{term_name}' in taxonomy {taxonomy}")
            return result['id']
        
        except Exception as e:
            logger.error(f"Failed to create term {term_slug} in taxonomy {taxonomy}: {str(e)}")
            raise
    
    # Utility methods
    
    def _get_mime_type(self, file_path: str) -> str:
        """Get MIME type for file"""
        import mimetypes
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type or 'application/octet-stream'
    
    async def test_connection(self) -> bool:
        """Test WordPress API connection and authentication"""
        try:
            # Try to get site info
            result = await self._make_request('GET', '../wp/v2/types')
            logger.info("WordPress API connection successful")
            return True
        
        except Exception as e:
            logger.error(f"WordPress API connection failed: {str(e)}")
            return False
    
    async def get_site_info(self) -> Dict:
        """Get WordPress site information"""
        try:
            return await self._make_request('GET', '../wp/v2')
        
        except Exception as e:
            logger.error(f"Failed to get site info: {str(e)}")
            raise


# Factory function for easy instantiation
def create_wordpress_client(base_url: str, username: str, app_password: str) -> WordPressClient:
    """
    Factory function to create WordPress client
    
    Args:
        base_url: WordPress site URL
        username: WordPress username  
        app_password: WordPress application password
        
    Returns:
        Configured WordPressClient instance
    """
    config = WordPressConfig(
        base_url=base_url,
        username=username,
        app_password=app_password
    )
    
    return WordPressClient(config)


# Example usage for testing
async def test_wordpress_connection():
    """Test function for WordPress API connection"""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    client = create_wordpress_client(
        base_url=os.getenv("WORDPRESS_BASE_URL", "https://www.crashcasino.io"),
        username=os.getenv("WORDPRESS_USERNAME"),
        app_password=os.getenv("WORDPRESS_APP_PASSWORD")
    )
    
    async with client:
        # Test connection
        success = await client.test_connection()
        
        if success:
            print("✅ WordPress API connection successful")
            
            # Get site info
            site_info = await client.get_site_info()
            print(f"Site: {site_info.get('name')}")
            print(f"URL: {site_info.get('url')}")
        else:
            print("❌ WordPress API connection failed")


if __name__ == "__main__":
    asyncio.run(test_wordpress_connection())
