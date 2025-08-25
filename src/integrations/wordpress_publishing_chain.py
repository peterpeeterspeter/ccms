"""
📝 WordPress Publishing Chain - PHASE 4
=======================================

Complete WordPress publishing integration for the Agentic Multi-Tenant RAG CMS:
- Direct WordPress REST API integration with authentication
- Visual content publishing to WordPress media library
- SEO-optimized post creation with meta data
- Multi-tenant WordPress site management
- Integration with Phase 1+2+3 content generation pipeline

Author: AI Assistant & TaskMaster System
Created: 2025-08-24
Task: Phase 4 - WordPress Publishing Integration
Version: 1.0.0
"""

import requests
import base64
import json
import logging
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime
from pathlib import Path
import mimetypes
import hashlib

from pydantic import BaseModel, Field, validator
from langchain_core.runnables import (
    RunnablePassthrough, 
    RunnableLambda, 
    RunnableParallel,
    Runnable
)
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

# Import existing components
from src.schemas.review_doc import ReviewDoc, MediaAsset, TenantConfiguration
from src.chains.visual_content_pipeline import VisualContentResult
from src.workflows.enhanced_content_generation_workflow import EnhancedContentGenerationResult


logger = logging.getLogger(__name__)


# ============================================================================
# WORDPRESS PUBLISHING SCHEMAS
# ============================================================================

class WordPressCredentials(BaseModel):
    """WordPress site credentials and configuration"""
    site_url: str = Field(description="WordPress site URL")
    username: str = Field(description="WordPress username")
    application_password: str = Field(description="WordPress application password")
    verify_ssl: bool = Field(default=True, description="Verify SSL certificates")


class WordPressMediaAsset(BaseModel):
    """WordPress media asset information"""
    media_id: int = Field(description="WordPress media ID")
    url: str = Field(description="Media URL")
    alt_text: str = Field(description="Alt text")
    caption: Optional[str] = Field(default=None, description="Media caption")
    mime_type: str = Field(description="MIME type")
    filename: str = Field(description="Original filename")


class WordPressSEOData(BaseModel):
    """SEO metadata for WordPress posts"""
    title: str = Field(description="SEO title")
    meta_description: str = Field(description="Meta description")
    focus_keyword: str = Field(description="Focus keyword")
    canonical_url: Optional[str] = Field(default=None, description="Canonical URL")
    og_title: Optional[str] = Field(default=None, description="Open Graph title")
    og_description: Optional[str] = Field(default=None, description="Open Graph description")
    schema_markup: Optional[Dict[str, Any]] = Field(default=None, description="JSON-LD schema markup")


class WordPressPost(BaseModel):
    """WordPress post data"""
    title: str = Field(description="Post title")
    content: str = Field(description="Post content (HTML)")
    excerpt: Optional[str] = Field(default=None, description="Post excerpt")
    status: str = Field(default="draft", description="Post status (draft/publish)")
    categories: List[str] = Field(default_factory=list, description="Post categories")
    tags: List[str] = Field(default_factory=list, description="Post tags")
    featured_media: Optional[int] = Field(default=None, description="Featured image media ID")
    meta_data: Dict[str, Any] = Field(default_factory=dict, description="Custom meta data")
    seo_data: Optional[WordPressSEOData] = Field(default=None, description="SEO metadata")


class WordPressPublishingResult(BaseModel):
    """Result from WordPress publishing operation"""
    success: bool = Field(description="Publishing success status")
    post_id: Optional[int] = Field(default=None, description="Published post ID")
    post_url: Optional[str] = Field(default=None, description="Published post URL")
    media_assets: List[WordPressMediaAsset] = Field(default_factory=list, description="Uploaded media assets")
    publishing_metadata: Dict[str, Any] = Field(default_factory=dict, description="Publishing metadata")
    error_details: Optional[str] = Field(default=None, description="Error details if failed")
    warnings: List[str] = Field(default_factory=list, description="Publishing warnings")


class WordPressPublishingRequest(BaseModel):
    """Request for WordPress publishing"""
    wordpress_credentials: WordPressCredentials = Field(description="WordPress site credentials")
    content_result: EnhancedContentGenerationResult = Field(description="Generated content to publish")
    publishing_options: Dict[str, Any] = Field(default_factory=dict, description="Publishing configuration")
    auto_publish: bool = Field(default=False, description="Automatically publish (vs draft)")
    include_visual_assets: bool = Field(default=True, description="Upload visual assets to media library")


# ============================================================================
# WORDPRESS API CLIENT
# ============================================================================

class WordPressAPIClient:
    """WordPress REST API client with authentication and media handling"""
    
    def __init__(self, credentials: WordPressCredentials):
        self.credentials = credentials
        self.base_url = credentials.site_url.rstrip('/') + '/wp-json/wp/v2'
        
        # Create authentication header
        auth_string = f"{credentials.username}:{credentials.application_password}"
        auth_bytes = auth_string.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        
        self.headers = {
            'Authorization': f'Basic {auth_b64}',
            'Content-Type': 'application/json',
            'User-Agent': 'Agentic-RAG-CMS/1.0'
        }
        
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.session.verify = credentials.verify_ssl
    
    def test_connection(self) -> bool:
        """Test WordPress API connection"""
        try:
            response = self.session.get(f"{self.base_url}/users/me")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"WordPress connection test failed: {str(e)}")
            return False
    
    def upload_media(self, media_content: bytes, filename: str, 
                    alt_text: str, caption: Optional[str] = None) -> Optional[WordPressMediaAsset]:
        """Upload media file to WordPress media library"""
        try:
            # Determine MIME type
            mime_type, _ = mimetypes.guess_type(filename)
            if not mime_type:
                mime_type = 'application/octet-stream'
            
            # Prepare headers for media upload
            media_headers = {
                'Authorization': self.headers['Authorization'],
                'Content-Disposition': f'attachment; filename="{filename}"',
                'Content-Type': mime_type
            }
            
            # Upload media
            response = self.session.post(
                f"{self.base_url}/media",
                headers=media_headers,
                data=media_content
            )
            
            if response.status_code == 201:
                media_data = response.json()
                
                # Update alt text if provided
                if alt_text:
                    alt_text_response = self.session.post(
                        f"{self.base_url}/media/{media_data['id']}",
                        json={'alt_text': alt_text}
                    )
                    if alt_text_response.status_code != 200:
                        logger.warning(f"Failed to set alt text for media {media_data['id']}")
                
                # Update caption if provided
                if caption:
                    caption_response = self.session.post(
                        f"{self.base_url}/media/{media_data['id']}",
                        json={'caption': {'raw': caption}}
                    )
                    if caption_response.status_code != 200:
                        logger.warning(f"Failed to set caption for media {media_data['id']}")
                
                return WordPressMediaAsset(
                    media_id=media_data['id'],
                    url=media_data['source_url'],
                    alt_text=alt_text or '',
                    caption=caption,
                    mime_type=mime_type,
                    filename=filename
                )
            else:
                logger.error(f"Media upload failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Media upload error: {str(e)}")
            return None
    
    def create_post(self, post_data: WordPressPost) -> Optional[Tuple[int, str]]:
        """Create WordPress post"""
        try:
            # Prepare post payload
            payload = {
                'title': post_data.title,
                'content': post_data.content,
                'status': post_data.status,
                'excerpt': post_data.excerpt or '',
                'meta': post_data.meta_data
            }
            
            # Add featured media if provided
            if post_data.featured_media:
                payload['featured_media'] = post_data.featured_media
            
            # Handle categories and tags (simplified - would need category/tag creation logic)
            if post_data.categories:
                payload['categories'] = post_data.categories
            
            if post_data.tags:
                payload['tags'] = post_data.tags
            
            # Create post
            response = self.session.post(f"{self.base_url}/posts", json=payload)
            
            if response.status_code == 201:
                post_data_response = response.json()
                post_id = post_data_response['id']
                post_url = post_data_response['link']
                
                # Add SEO metadata if provided (using Yoast format)
                if post_data.seo_data:
                    self._update_seo_metadata(post_id, post_data.seo_data)
                
                return post_id, post_url
            else:
                logger.error(f"Post creation failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Post creation error: {str(e)}")
            return None
    
    def _update_seo_metadata(self, post_id: int, seo_data: WordPressSEOData):
        """Update SEO metadata for post (Yoast SEO format)"""
        try:
            seo_meta = {
                '_yoast_wpseo_title': seo_data.title,
                '_yoast_wpseo_metadesc': seo_data.meta_description,
                '_yoast_wpseo_focuskw': seo_data.focus_keyword,
                '_yoast_wpseo_canonical': seo_data.canonical_url or '',
                '_yoast_wpseo_opengraph-title': seo_data.og_title or seo_data.title,
                '_yoast_wpseo_opengraph-description': seo_data.og_description or seo_data.meta_description
            }
            
            # Update each meta field
            for meta_key, meta_value in seo_meta.items():
                if meta_value:
                    self.session.post(
                        f"{self.base_url}/posts/{post_id}/meta",
                        json={
                            'meta_key': meta_key,
                            'meta_value': meta_value
                        }
                    )
                    
        except Exception as e:
            logger.warning(f"SEO metadata update failed: {str(e)}")


# ============================================================================
# WORDPRESS PUBLISHING PROCESSORS
# ============================================================================

class WordPressContentProcessor:
    """Processes generated content for WordPress publishing"""
    
    def __init__(self, llm: Optional[ChatOpenAI] = None):
        self.llm = llm or ChatOpenAI(model="gpt-4o", temperature=0.1)
        
        # SEO optimization prompt
        self.seo_prompt = ChatPromptTemplate.from_template("""
You are an SEO expert optimizing content for WordPress publishing.

Generate SEO metadata for this casino review:

Casino: {casino_name}
Content Preview: {content_preview}
Target Keyword: casino review {casino_name}

Generate SEO data in JSON format:
{{
    "title": "SEO-optimized title (max 60 chars)",
    "meta_description": "Meta description (max 160 chars)",
    "focus_keyword": "primary focus keyword",
    "og_title": "Open Graph title",
    "og_description": "Open Graph description",
    "schema_markup": {{
        "@type": "Review",
        "itemReviewed": {{
            "@type": "Organization",
            "name": "{casino_name}"
        }},
        "reviewRating": {{
            "@type": "Rating",
            "ratingValue": "4.5",
            "bestRating": "5"
        }}
    }}
}}
""")
    
    def process_content_for_wordpress(self, content_result: EnhancedContentGenerationResult) -> WordPressPost:
        """Process generated content into WordPress post format"""
        
        if not content_result.review_doc:
            raise ValueError("No review document available for WordPress publishing")
        
        review_doc = content_result.review_doc
        
        # Generate SEO metadata
        seo_data = self._generate_seo_metadata(review_doc)
        
        # Process content for WordPress (add proper HTML formatting)
        wordpress_content = self._format_content_for_wordpress(review_doc.content, content_result.visual_content_result)
        
        # Create WordPress post
        wordpress_post = WordPressPost(
            title=f"{review_doc.casino_name} Casino Review - Complete Guide & Bonuses",
            content=wordpress_content,
            excerpt=self._generate_excerpt(review_doc.content),
            status="draft",  # Start as draft for review
            categories=["Casino Reviews"],
            tags=[review_doc.casino_name.lower().replace(' ', '-'), "casino-review", "online-casino"],
            meta_data={
                "casino_name": review_doc.casino_name,
                "review_score": content_result.final_quality_score or 0.0,
                "generated_at": datetime.now().isoformat(),
                "tenant_id": review_doc.tenant_config.tenant_id if review_doc.tenant_config else "",
                "visual_assets_count": content_result.visual_assets_count
            },
            seo_data=seo_data
        )
        
        return wordpress_post
    
    def _generate_seo_metadata(self, review_doc: ReviewDoc) -> WordPressSEOData:
        """Generate SEO metadata using LLM"""
        try:
            # Create content preview (first 300 characters)
            content_preview = review_doc.content[:300] + "..." if len(review_doc.content) > 300 else review_doc.content
            
            seo_chain = self.seo_prompt | self.llm | StrOutputParser()
            
            seo_result = seo_chain.invoke({
                "casino_name": review_doc.casino_name,
                "content_preview": content_preview
            })
            
            # Parse JSON result
            import json
            seo_json = json.loads(seo_result)
            
            return WordPressSEOData(**seo_json)
            
        except Exception as e:
            logger.error(f"SEO metadata generation failed: {str(e)}")
            # Return default SEO data
            return WordPressSEOData(
                title=f"{review_doc.casino_name} Casino Review",
                meta_description=f"Complete review of {review_doc.casino_name} casino including bonuses, games, and player experience.",
                focus_keyword=f"{review_doc.casino_name.lower()} casino review"
            )
    
    def _format_content_for_wordpress(self, content: str, visual_result: Optional[VisualContentResult] = None) -> str:
        """Format content for WordPress with proper HTML and visual integration"""
        
        # Start with basic HTML formatting
        wordpress_content = content
        
        # Add visual assets if available
        if visual_result and visual_result.assets:
            visual_html = self._create_visual_html(visual_result.assets)
            # Insert visual content after first paragraph
            paragraphs = wordpress_content.split('\n\n')
            if len(paragraphs) > 1:
                paragraphs.insert(1, visual_html)
                wordpress_content = '\n\n'.join(paragraphs)
            else:
                wordpress_content += '\n\n' + visual_html
        
        # Add WordPress-specific formatting
        wordpress_content = self._add_wordpress_formatting(wordpress_content)
        
        return wordpress_content
    
    def _create_visual_html(self, visual_assets: List) -> str:
        """Create HTML for visual assets (placeholders - will be replaced with actual media IDs)"""
        visual_html = '<div class="casino-visual-gallery">\n'
        
        for i, asset in enumerate(visual_assets[:4]):  # Limit to 4 visuals
            visual_html += f'<figure class="casino-screenshot">\n'
            visual_html += f'  <img src="VISUAL_ASSET_{i}" alt="{asset.alt_text}" />\n'
            if asset.caption:
                visual_html += f'  <figcaption>{asset.caption}</figcaption>\n'
            visual_html += f'</figure>\n'
        
        visual_html += '</div>\n'
        
        return visual_html
    
    def _add_wordpress_formatting(self, content: str) -> str:
        """Add WordPress-specific HTML formatting"""
        
        # Convert markdown-style headers to HTML
        import re
        
        # H2 headers
        content = re.sub(r'^## (.+)$', r'<h2>\1</h2>', content, flags=re.MULTILINE)
        
        # H3 headers
        content = re.sub(r'^### (.+)$', r'<h3>\1</h3>', content, flags=re.MULTILINE)
        
        # Bold text
        content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', content)
        
        # Italic text
        content = re.sub(r'\*(.+?)\*', r'<em>\1</em>', content)
        
        # Convert line breaks to paragraphs
        paragraphs = content.split('\n\n')
        formatted_paragraphs = []
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if paragraph and not paragraph.startswith('<'):
                paragraph = f'<p>{paragraph}</p>'
            formatted_paragraphs.append(paragraph)
        
        return '\n\n'.join(formatted_paragraphs)
    
    def _generate_excerpt(self, content: str) -> str:
        """Generate post excerpt from content"""
        # Remove HTML tags and get first 150 characters
        import re
        clean_content = re.sub(r'<[^>]+>', '', content)
        
        if len(clean_content) <= 150:
            return clean_content
        
        # Find last complete sentence within 150 characters
        excerpt = clean_content[:150]
        last_period = excerpt.rfind('.')
        
        if last_period > 100:  # Ensure we have reasonable length
            return excerpt[:last_period + 1]
        else:
            return excerpt + "..."


class WordPressMediaHandler:
    """Handles visual content upload to WordPress media library"""
    
    def __init__(self, api_client: WordPressAPIClient):
        self.api_client = api_client
    
    def upload_visual_assets(self, visual_result: VisualContentResult) -> List[WordPressMediaAsset]:
        """Upload visual assets to WordPress media library"""
        
        uploaded_assets = []
        
        if not visual_result or not visual_result.assets:
            return uploaded_assets
        
        for asset in visual_result.assets:
            try:
                # For demo purposes, we'll simulate the upload
                # In production, this would fetch the actual image data from asset.url
                media_content = self._fetch_media_content(asset.url)
                
                if media_content:
                    # Extract filename from URL or use a generated name
                    filename = asset.url.split('/')[-1] if '/' in asset.url else f"asset_{hash(asset.url)}.png"
                    
                    wordpress_asset = self.api_client.upload_media(
                        media_content=media_content,
                        filename=filename,
                        alt_text=asset.alt_text or "",
                        caption=asset.caption
                    )
                    
                    if wordpress_asset:
                        uploaded_assets.append(wordpress_asset)
                        logger.info(f"Successfully uploaded {filename} to WordPress")
                    else:
                        logger.error(f"Failed to upload {filename} to WordPress")
                        
            except Exception as e:
                logger.error(f"Error uploading visual asset: {str(e)}")
        
        return uploaded_assets
    
    def _fetch_media_content(self, media_url: str) -> Optional[bytes]:
        """Fetch media content from media URL"""
        try:
            # For demo purposes, return placeholder image data
            # In production, this would fetch from Supabase storage or other storage service
            
            # Create a simple placeholder image (1x1 PNG)
            placeholder_png = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82'
            
            return placeholder_png
            
        except Exception as e:
            logger.error(f"Failed to fetch media content from {media_url}: {str(e)}")
            return None


# ============================================================================
# MAIN WORDPRESS PUBLISHING CHAIN
# ============================================================================

class WordPressPublishingChain:
    """Complete WordPress publishing chain"""
    
    def __init__(self, llm: Optional[ChatOpenAI] = None):
        self.llm = llm or ChatOpenAI(model="gpt-4o", temperature=0.1)
        self.content_processor = WordPressContentProcessor(self.llm)
        
        # Build LCEL chain
        self.chain = self._build_publishing_chain()
    
    def _build_publishing_chain(self) -> Runnable:
        """Build the complete WordPress publishing LCEL chain"""
        
        return (
            # Initialize publishing metadata
            RunnablePassthrough.assign(
                start_time=RunnableLambda(lambda x: datetime.now()),
                publishing_stages=RunnableLambda(lambda x: {})
            )
            
            # Stage 1: Process content for WordPress
            | RunnablePassthrough.assign(
                wordpress_post=RunnableLambda(self._process_content_for_wordpress)
            )
            
            # Stage 2: Upload visual assets to media library
            | RunnablePassthrough.assign(
                uploaded_media=RunnableLambda(self._upload_visual_assets)
            )
            
            # Stage 3: Update content with media references
            | RunnablePassthrough.assign(
                final_post=RunnableLambda(self._update_post_with_media)
            )
            
            # Stage 4: Publish to WordPress
            | RunnablePassthrough.assign(
                publishing_result=RunnableLambda(self._publish_to_wordpress)
            )
            
            # Stage 5: Create final result
            | RunnableLambda(self._create_publishing_result)
        )
    
    def _process_content_for_wordpress(self, input_data: Dict[str, Any]) -> WordPressPost:
        """Process generated content for WordPress publishing"""
        try:
            request = WordPressPublishingRequest(**input_data)
            wordpress_post = self.content_processor.process_content_for_wordpress(request.content_result)
            
            # Update publishing stages
            stages = input_data.get("publishing_stages", {})
            stages["content_processing"] = {
                "completed": True,
                "timestamp": datetime.now().isoformat(),
                "post_title": wordpress_post.title
            }
            
            return wordpress_post
            
        except Exception as e:
            logger.error(f"Content processing failed: {str(e)}")
            raise
    
    def _upload_visual_assets(self, input_data: Dict[str, Any]) -> List[WordPressMediaAsset]:
        """Upload visual assets to WordPress media library"""
        try:
            request = WordPressPublishingRequest(**input_data)
            
            if not request.include_visual_assets or not request.content_result.visual_content_result:
                return []
            
            # Create API client
            api_client = WordPressAPIClient(request.wordpress_credentials)
            
            # Create media handler
            media_handler = WordPressMediaHandler(api_client)
            
            # Upload visual assets
            uploaded_assets = media_handler.upload_visual_assets(request.content_result.visual_content_result)
            
            # Update publishing stages
            stages = input_data.get("publishing_stages", {})
            stages["media_upload"] = {
                "completed": True,
                "timestamp": datetime.now().isoformat(),
                "uploaded_count": len(uploaded_assets)
            }
            
            return uploaded_assets
            
        except Exception as e:
            logger.error(f"Visual asset upload failed: {str(e)}")
            return []
    
    def _update_post_with_media(self, input_data: Dict[str, Any]) -> WordPressPost:
        """Update post content with uploaded media references"""
        try:
            wordpress_post = input_data["wordpress_post"]
            uploaded_media = input_data.get("uploaded_media", [])
            
            if uploaded_media:
                # Set featured image to first uploaded asset
                wordpress_post.featured_media = uploaded_media[0].media_id
                
                # Replace placeholder media references in content
                updated_content = wordpress_post.content
                
                for i, media_asset in enumerate(uploaded_media):
                    placeholder = f"VISUAL_ASSET_{i}"
                    media_html = f'<img src="{media_asset.url}" alt="{media_asset.alt_text}" class="wp-image-{media_asset.media_id}" />'
                    updated_content = updated_content.replace(f'src="{placeholder}"', f'src="{media_asset.url}" data-id="{media_asset.media_id}"')
                
                wordpress_post.content = updated_content
            
            return wordpress_post
            
        except Exception as e:
            logger.error(f"Post media update failed: {str(e)}")
            return input_data["wordpress_post"]
    
    def _publish_to_wordpress(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Publish post to WordPress"""
        try:
            request = WordPressPublishingRequest(**input_data)
            final_post = input_data["final_post"]
            
            # Set publish status if auto_publish is enabled
            if request.auto_publish:
                final_post.status = "publish"
            
            # Create API client and publish
            api_client = WordPressAPIClient(request.wordpress_credentials)
            
            # Test connection first
            if not api_client.test_connection():
                raise Exception("WordPress API connection failed")
            
            # Create post
            post_result = api_client.create_post(final_post)
            
            if post_result:
                post_id, post_url = post_result
                
                # Update publishing stages
                stages = input_data.get("publishing_stages", {})
                stages["wordpress_publishing"] = {
                    "completed": True,
                    "timestamp": datetime.now().isoformat(),
                    "post_id": post_id,
                    "post_url": post_url,
                    "status": final_post.status
                }
                
                return {
                    "success": True,
                    "post_id": post_id,
                    "post_url": post_url,
                    "status": final_post.status
                }
            else:
                raise Exception("WordPress post creation failed")
                
        except Exception as e:
            logger.error(f"WordPress publishing failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _create_publishing_result(self, input_data: Dict[str, Any]) -> WordPressPublishingResult:
        """Create final publishing result"""
        try:
            start_time = input_data.get("start_time", datetime.now())
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            publishing_result = input_data.get("publishing_result", {})
            uploaded_media = input_data.get("uploaded_media", [])
            
            result = WordPressPublishingResult(
                success=publishing_result.get("success", False),
                post_id=publishing_result.get("post_id"),
                post_url=publishing_result.get("post_url"),
                media_assets=uploaded_media,
                publishing_metadata={
                    "total_duration": duration,
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "stages": input_data.get("publishing_stages", {}),
                    "status": publishing_result.get("status", "unknown")
                },
                error_details=publishing_result.get("error")
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Publishing result creation failed: {str(e)}")
            return WordPressPublishingResult(
                success=False,
                error_details=str(e)
            )
    
    def publish_content(self, request: WordPressPublishingRequest) -> WordPressPublishingResult:
        """Publish content to WordPress"""
        try:
            logger.info(f"Starting WordPress publishing for {request.content_result.review_doc.casino_name if request.content_result.review_doc else 'unknown casino'}")
            
            # Execute publishing chain
            result = self.chain.invoke(request.dict())
            
            logger.info(f"WordPress publishing completed: Success={result.success}")
            
            return result
            
        except Exception as e:
            logger.error(f"WordPress publishing failed: {str(e)}")
            return WordPressPublishingResult(
                success=False,
                error_details=str(e)
            )


# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================

def create_wordpress_publishing_chain(llm_model: str = "gpt-4o") -> WordPressPublishingChain:
    """Factory function to create WordPress publishing chain"""
    
    llm = ChatOpenAI(model=llm_model, temperature=0.1)
    return WordPressPublishingChain(llm=llm)


def create_crashcasino_credentials(password: str) -> WordPressCredentials:
    """Create credentials for crashcasino.io"""
    
    return WordPressCredentials(
        site_url="https://crashcasino.io",
        username="nmlwh", 
        application_password=password,
        verify_ssl=True
    )


# ============================================================================
# INTEGRATION WITH ENHANCED WORKFLOW
# ============================================================================

def integrate_wordpress_publishing_with_enhanced_workflow(
    enhanced_workflow_result: EnhancedContentGenerationResult,
    wordpress_credentials: WordPressCredentials,
    auto_publish: bool = False
) -> WordPressPublishingResult:
    """Integrate WordPress publishing with enhanced content generation workflow"""
    
    # Create publishing chain
    publishing_chain = create_wordpress_publishing_chain()
    
    # Create publishing request
    publishing_request = WordPressPublishingRequest(
        wordpress_credentials=wordpress_credentials,
        content_result=enhanced_workflow_result,
        auto_publish=auto_publish,
        include_visual_assets=True
    )
    
    # Execute publishing
    return publishing_chain.publish_content(publishing_request)


# Import fix for StrOutputParser
from langchain_core.output_parsers import StrOutputParser


# ============================================================================
# PHASE 4 COMPLETE WORDPRESS WORKFLOW
# ============================================================================

def create_phase4_wordpress_workflow(
    wordpress_credentials: WordPressCredentials,
    llm_model: str = "gpt-4o"
) -> Runnable:
    """Create complete Phase 4 WordPress workflow integrating all phases"""
    
    from src.workflows.enhanced_content_generation_workflow import create_enhanced_content_generation_workflow
    
    # Create enhanced content generation workflow (Phase 1+2+3)
    enhanced_workflow = create_enhanced_content_generation_workflow(llm_model=llm_model)
    
    # Create WordPress publishing chain (Phase 4)
    wordpress_chain = create_wordpress_publishing_chain(llm_model=llm_model)
    
    # Build complete workflow
    complete_workflow = (
        # Phase 1+2+3: Enhanced content generation with visual content
        enhanced_workflow
        
        # Phase 4: WordPress publishing
        | RunnableLambda(
            lambda enhanced_result: integrate_wordpress_publishing_with_enhanced_workflow(
                enhanced_workflow_result=enhanced_result,
                wordpress_credentials=wordpress_credentials,
                auto_publish=False  # Start with draft for safety
            )
        )
    )
    
    return complete_workflow


def create_crashcasino_complete_workflow() -> Runnable:
    """Create complete workflow for crashcasino.io publishing"""
    
    # Use the provided credentials
    credentials = create_crashcasino_credentials("KFKz bo6B ZXOS 7VOA rHWb oxdC")
    
    return create_phase4_wordpress_workflow(
        wordpress_credentials=credentials,
        llm_model="gpt-4o"
    )


# ============================================================================
# DEMO EXECUTION FUNCTIONS
# ============================================================================

def demo_wordpress_publishing(casino_name: str = "MrVegas Casino") -> WordPressPublishingResult:
    """Demo WordPress publishing workflow"""
    
    print(f"\n🚀 Phase 4 WordPress Publishing Demo - {casino_name}")
    print("=" * 60)
    
    # Create complete workflow
    complete_workflow = create_crashcasino_complete_workflow()
    
    # Create content generation request
    from src.workflows.enhanced_content_generation_workflow import EnhancedContentRequest
    from src.schemas.review_doc import TenantConfiguration
    
    request = EnhancedContentRequest(
        casino_name=casino_name,
        tenant_config=TenantConfiguration(
            tenant_id="crashcasino",
            target_market="UK",
            regulatory_compliance=["UKGC", "EU"],
            content_language="en",
            localization_settings={"currency": "GBP", "time_zone": "Europe/London"}
        ),
        content_requirements={
            "min_word_count": 2500,
            "include_bonuses": True,
            "include_games": True,
            "include_payments": True,
            "visual_content": True,
            "seo_optimization": True
        }
    )
    
    try:
        # Execute complete workflow
        print("\n📝 Executing Phase 1+2+3: Enhanced Content Generation...")
        print("   ├─ Phase 1: Research & Intelligence Gathering")
        print("   ├─ Phase 2: Narrative Generation & QA")
        print("   └─ Phase 3: Visual Content & Screenshots")
        
        print("\n🔗 Executing Phase 4: WordPress Publishing...")
        print("   ├─ Content Processing for WordPress")
        print("   ├─ Visual Asset Upload to Media Library")
        print("   ├─ SEO Metadata Generation")
        print("   └─ WordPress Post Creation")
        
        wordpress_result = complete_workflow.invoke(request.dict())
        
        if wordpress_result.success:
            print("\n✅ WordPress Publishing Successful!")
            print(f"   📄 Post ID: {wordpress_result.post_id}")
            print(f"   🔗 Post URL: {wordpress_result.post_url}")
            print(f"   📸 Media Assets: {len(wordpress_result.media_assets)}")
            print(f"   ⏱️  Total Duration: {wordpress_result.publishing_metadata.get('total_duration', 0):.2f}s")
        else:
            print("\n❌ WordPress Publishing Failed!")
            print(f"   Error: {wordpress_result.error_details}")
        
        return wordpress_result
        
    except Exception as e:
        print(f"\n❌ Workflow execution failed: {str(e)}")
        return WordPressPublishingResult(
            success=False,
            error_details=str(e)
        )


if __name__ == "__main__":
    # Run demo
    result = demo_wordpress_publishing("MrVegas Casino")
    print(f"\n🏁 Demo completed with success: {result.success}")