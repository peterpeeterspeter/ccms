#!/usr/bin/env python3
"""
🏗️ NATIVE LANGCHAIN WordPress Publishing Tool
Proper BaseTool implementation following LangChain patterns
"""

import asyncio
import base64
import json
import logging
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Type, Union
from urllib.parse import urljoin

import aiohttp
from pydantic import BaseModel, Field

# LangChain native imports
from langchain_core.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate

# Configure logging
logger = logging.getLogger(__name__)

class WordPressPostSchema(BaseModel):
    """🏗️ Pydantic schema for WordPress post data"""
    title: str = Field(description="Post title, SEO optimized")
    content: str = Field(description="Post content in HTML format")
    status: str = Field(default="publish", description="Post status: draft, publish, private")
    categories: List[str] = Field(default_factory=list, description="Post categories")
    tags: List[str] = Field(default_factory=list, description="Post tags")
    excerpt: Optional[str] = Field(default=None, description="Post excerpt/meta description")
    featured_image_url: Optional[str] = Field(default=None, description="Featured image URL")
    custom_fields: Dict[str, Any] = Field(default_factory=dict, description="Custom fields metadata")

class CasinoReviewSchema(BaseModel):
    """🎰 Specialized schema for casino review posts"""
    title: str = Field(description="Casino review title")
    content: str = Field(description="Review content in HTML format")
    casino_name: str = Field(description="Name of the casino")
    overall_rating: float = Field(description="Overall rating 0-10", ge=0, le=10)
    license_info: str = Field(description="Licensing information")
    welcome_bonus: str = Field(description="Welcome bonus description")
    pros: List[str] = Field(description="Casino advantages")
    cons: List[str] = Field(description="Casino disadvantages")
    payment_methods: List[str] = Field(description="Available payment methods")
    game_providers: List[str] = Field(description="Game software providers")
    
    # CoinFlip theme specific fields
    small_description: Optional[str] = Field(default=None, description="Subtitle for single page")
    casino_features: List[str] = Field(default_factory=list, description="Features for About section")
    bonus_message: Optional[str] = Field(default=None, description="CTA bonus message")
    casino_website_url: Optional[str] = Field(default=None, description="Official casino URL")

class WordPressPublishingTool(BaseTool):
    """🏗️ Native LangChain WordPress Publishing Tool"""
    
    name: str = "wordpress_publisher"
    description: str = """Publish content to WordPress with full formatting and metadata.
    Input should be a dictionary with 'title', 'content', and optional fields like 'categories', 'tags', etc.
    For casino reviews, include casino-specific fields like 'casino_name', 'rating', etc."""
    
    # WordPress configuration
    site_url: str = Field(default_factory=lambda: os.getenv("WORDPRESS_SITE_URL", ""))
    username: str = Field(default_factory=lambda: os.getenv("WORDPRESS_USERNAME", ""))
    application_password: str = Field(default_factory=lambda: os.getenv("WORDPRESS_APP_PASSWORD", ""))
    
    # Tool configuration
    return_direct: bool = True
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._session: Optional[aiohttp.ClientSession] = None
        self._auth_headers = self._setup_auth_headers()
    
    def _setup_auth_headers(self) -> Dict[str, str]:
        """Setup WordPress authentication headers"""
        if not all([self.site_url, self.username, self.application_password]):
            raise ValueError("WordPress credentials not properly configured")
        
        credentials = f"{self.username}:{self.application_password}"
        encoded = base64.b64encode(credentials.encode()).decode()
        
        return {
            "Authorization": f"Basic {encoded}",
            "Content-Type": "application/json",
            "User-Agent": "LangChain-WordPress-Tool/1.0"
        }
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if not self._session or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def _close_session(self):
        """Close HTTP session"""
        if self._session and not self._session.closed:
            await self._session.close()
    
    def _run(
        self,
        query: Union[str, Dict[str, Any]],
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> Dict[str, Any]:
        """Synchronous wrapper for async publishing"""
        return asyncio.run(self._arun(query, run_manager))
    
    async def _arun(
        self,
        query: Union[str, Dict[str, Any]],
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> Dict[str, Any]:
        """🏗️ Native LangChain async tool execution"""
        
        try:
            # Parse and validate input
            post_data = self._parse_input(query)
            
            # Detect content type and apply appropriate processing
            if self._is_casino_content(post_data):
                return await self._publish_casino_review(post_data, run_manager)
            else:
                return await self._publish_standard_post(post_data, run_manager)
                
        except Exception as e:
            logger.error(f"WordPress publishing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "tool": "wordpress_publisher"
            }
        finally:
            await self._close_session()
    
    def _parse_input(self, query: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Parse and validate tool input"""
        
        if isinstance(query, str):
            # Try to parse as JSON first
            try:
                data = json.loads(query)
            except json.JSONDecodeError:
                # Treat as simple content
                data = {
                    "title": "Generated Content",
                    "content": query
                }
        elif isinstance(query, dict):
            data = query.copy()
        else:
            raise ValueError(f"Unsupported input type: {type(query)}")
        
        # Clean content from raw answer format
        if "content" in data:
            data["content"] = self._clean_content(data["content"])
        
        return data
    
    def _clean_content(self, content: str) -> str:
        """🔧 Clean content from raw answer format to proper HTML"""
        if not content:
            return ""
        
        # Handle raw answer format
        if content.startswith('answer="') or 'answer="' in content:
            match = re.search(r'answer="(.+?)"(?:\s+sources=|$)', content, re.DOTALL)
            if match:
                raw_markdown = match.group(1)
                # Decode escaped newlines
                cleaned_markdown = raw_markdown.replace('\\n\\n', '\n\n').replace('\\n', '\n')
                
                # Convert markdown to HTML
                try:
                    import markdown
                    html_content = markdown.markdown(
                        cleaned_markdown, 
                        extensions=['tables', 'fenced_code', 'codehilite']
                    )
                    logger.info("✅ Cleaned raw answer format and converted to HTML")
                    return html_content
                except ImportError:
                    logger.warning("⚠️ Markdown not available, returning cleaned text")
                    return cleaned_markdown
                except Exception as e:
                    logger.error(f"❌ Markdown conversion failed: {e}")
                    return cleaned_markdown
        
        # If already HTML, return as-is
        if '<' in content and '>' in content:
            return content
            
        # If markdown, convert to HTML
        if any(marker in content for marker in ['#', '*', '[', '```']):
            try:
                import markdown
                return markdown.markdown(content, extensions=['tables', 'fenced_code'])
            except ImportError:
                return content
                
        return content
    
    def _is_casino_content(self, data: Dict[str, Any]) -> bool:
        """Detect if content is casino-related"""
        casino_indicators = [
            'casino', 'gambling', 'slots', 'poker', 'blackjack', 
            'roulette', 'bonus', 'wagering', 'license'
        ]
        
        text_to_check = f"{data.get('title', '')} {data.get('content', '')}".lower()
        
        return (
            any(indicator in text_to_check for indicator in casino_indicators) or
            'casino_name' in data or
            'overall_rating' in data or
            'license_info' in data
        )
    
    async def _publish_casino_review(
        self, 
        data: Dict[str, Any],
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> Dict[str, Any]:
        """🎰 Publish casino review with specialized handling"""
        
        # Extract and validate casino-specific fields
        casino_data = self._extract_casino_fields(data)
        
        # Enhance content with embedded images
        if casino_data.get('casino_name'):
            data['content'] = self._enhance_content_with_images(data.get('content', ''), casino_data['casino_name'])
        
        # Generate SEO-optimized title if not provided
        if not data.get('title') and casino_data.get('casino_name'):
            rating = casino_data.get('overall_rating', 0)
            casino_name = casino_data['casino_name']
            data['title'] = f"{casino_name} Review {rating}/10 - Complete Analysis with Images 2024"
        
        # Search for casino image if not provided
        if not data.get('featured_image_url') and casino_data.get('casino_name'):
            featured_image = await self._search_casino_image(casino_data['casino_name'])
            if featured_image:
                data['featured_image_url'] = featured_image
        
        # Generate categories and tags
        data['categories'] = self._generate_casino_categories(casino_data)
        data['tags'] = self._generate_casino_tags(casino_data)
        
        # Create CoinFlip theme structured data
        content_with_coinflip = self._embed_coinflip_fields(
            data['content'], 
            casino_data
        )
        data['content'] = content_with_coinflip
        
        # Create custom fields for WordPress
        data['custom_fields'] = self._create_casino_custom_fields(casino_data)
        
        if run_manager:
            run_manager.on_text(f"Publishing casino review: {casino_data.get('casino_name', 'Unknown')}")
        
        return await self._execute_wordpress_publish(data)
    
    async def _search_casino_image(self, casino_name: str) -> Optional[str]:
        """Search for casino logo or promotional image"""
        try:
            # Use reliable placeholder service with working URLs
            casino_slug = casino_name.lower().replace(' ', '-').replace('casino', '').strip('-')
            
            # Create different image URLs for variety
            image_options = [
                f"https://picsum.photos/800/400?random=1",  # Random casino-style image
                f"https://picsum.photos/800/400?random=2",  # Alternative random image
                "https://images.unsplash.com/photo-1596838132731-3301c3fd4317?w=800&h=400&fit=crop&crop=center&q=80",  # Casino chips
                "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=800&h=400&fit=crop&crop=center&q=80",  # Casino scene
            ]
            
            # Test each URL to find a working one
            session = await self._get_session()
            
            for image_url in image_options:
                try:
                    async with session.head(image_url) as response:
                        if response.status == 200:
                            logger.info(f"✅ Found working image for {casino_name}: {image_url}")
                            return image_url
                except Exception:
                    continue
            
            # Fallback to a basic working placeholder
            return "https://picsum.photos/800/400?random=5"
            
        except Exception as e:
            logger.warning(f"⚠️ Casino image search failed: {e}")
            return "https://picsum.photos/800/400?random=10"
    
    def _enhance_content_with_images(self, content: str, casino_name: str) -> str:
        """Enhance content by embedding relevant images throughout"""
        try:
            # Define image sources for different sections
            casino_images = {
                'hero': f"https://images.unsplash.com/photo-1596838132731-3301c3fd4317?w=800&h=400&fit=crop&crop=center&q=80",  # Casino chips
                'games': f"https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=800&h=400&fit=crop&crop=center&q=80",  # Casino scene
                'mobile': f"https://images.unsplash.com/photo-1512941937669-90a1b58e7e9c?w=600&h=400&fit=crop&crop=center&q=80",  # Mobile phone
                'security': f"https://images.unsplash.com/photo-1563013544-824ae1b704d3?w=600&h=400&fit=crop&crop=center&q=80",  # Security/locks
                'payment': f"https://images.unsplash.com/photo-1556742049-0cfed4f6a45d?w=600&h=400&fit=crop&crop=center&q=80",  # Credit cards
                'support': f"https://images.unsplash.com/photo-1516321318423-f06f85e504b3?w=600&h=400&fit=crop&crop=center&q=80",  # Customer support
            }
            
            # Add hero image after first heading
            if '<h1>' in content or '<h2>' in content:
                first_heading_match = re.search(r'(<h[12][^>]*>.*?</h[12]>)', content, re.IGNORECASE | re.DOTALL)
                if first_heading_match:
                    hero_image = f'''
<div class="casino-hero-image" style="text-align: center; margin: 20px 0;">
    <img src="{casino_images['hero']}" alt="{casino_name} - Premium Online Casino Experience" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
    <p style="font-size: 12px; color: #666; margin-top: 5px; font-style: italic;">Experience premium gaming at {casino_name}</p>
</div>
'''
                    content = content.replace(first_heading_match.group(1), first_heading_match.group(1) + hero_image)
            
            # Add images to specific sections
            section_mappings = [
                (r'(.*?game.*?portfolio.*?|.*?slot.*?games.*?|.*?table.*?games.*?)', 'games', 'Extensive Gaming Portfolio'),
                (r'(.*?mobile.*?experience.*?|.*?mobile.*?platform.*?)', 'mobile', 'Mobile-Optimized Gaming'),
                (r'(.*?security.*?|.*?license.*?|.*?licensing.*?)', 'security', 'Secure & Licensed Gaming'),
                (r'(.*?payment.*?method.*?|.*?banking.*?)', 'payment', 'Secure Payment Options'),
                (r'(.*?customer.*?support.*?|.*?support.*?quality.*?)', 'support', '24/7 Customer Support')
            ]
            
            for pattern, image_key, alt_text in section_mappings:
                section_match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
                if section_match and image_key in casino_images:
                    # Find the next heading after this section
                    start_pos = section_match.end()
                    next_heading = re.search(r'<h[2-6][^>]*>', content[start_pos:], re.IGNORECASE)
                    
                    if next_heading:
                        insert_pos = start_pos + next_heading.start()
                        image_html = f'''
<div class="casino-section-image" style="text-align: center; margin: 20px 0;">
    <img src="{casino_images[image_key]}" alt="{alt_text} - {casino_name}" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
    <p style="font-size: 11px; color: #666; margin-top: 5px; font-style: italic;">{alt_text}</p>
</div>
'''
                        content = content[:insert_pos] + image_html + content[insert_pos:]
            
            return content
            
        except Exception as e:
            logger.warning(f"⚠️ Error enhancing content with images: {e}")
            return content
    
    async def _publish_standard_post(
        self, 
        data: Dict[str, Any],
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> Dict[str, Any]:
        """📝 Publish standard WordPress post"""
        
        # Apply standard formatting and SEO
        if not data.get('categories'):
            data['categories'] = ['General']
        
        if not data.get('tags'):
            data['tags'] = self._extract_tags_from_content(data.get('content', ''))
        
        if run_manager:
            run_manager.on_text(f"Publishing standard post: {data.get('title', 'Untitled')}")
        
        return await self._execute_wordpress_publish(data)
    
    def _extract_casino_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract casino-specific fields from data"""
        
        casino_fields = {}
        
        # Direct field mapping
        field_mappings = {
            'casino_name': 'casino_name',
            'overall_rating': 'overall_rating',
            'license_info': 'license_info',
            'welcome_bonus': 'welcome_bonus',
            'pros': 'pros',
            'cons': 'cons',
            'payment_methods': 'payment_methods',
            'game_providers': 'game_providers',
            'small_description': 'small_description',
            'casino_features': 'casino_features',
            'bonus_message': 'bonus_message',
            'casino_website_url': 'casino_website_url'
        }
        
        for data_key, field_key in field_mappings.items():
            if data_key in data:
                casino_fields[field_key] = data[data_key]
        
        # Extract from structured metadata if present
        if 'structured_metadata' in data:
            metadata = data['structured_metadata']
            
            # Extract from coinflip_fields
            if 'coinflip_fields' in metadata:
                coinflip_data = metadata['coinflip_fields']
                for key, value in coinflip_data.items():
                    if value and key not in casino_fields:
                        casino_fields[key] = value
            
            # Extract from other structured data
            if 'casino_name' in metadata:
                casino_fields.setdefault('casino_name', metadata['casino_name'])
            if 'overall_rating' in metadata:
                casino_fields.setdefault('overall_rating', metadata['overall_rating'])
        
        # Try to extract casino name from title if not found
        if 'casino_name' not in casino_fields and 'title' in data:
            title = data['title'].lower()
            # Simple extraction - look for "X casino" pattern
            match = re.search(r'(\w+)\s+casino', title)
            if match:
                casino_fields['casino_name'] = match.group(1).title()
        
        return casino_fields
    
    def _generate_casino_categories(self, casino_data: Dict[str, Any]) -> List[str]:
        """Generate WordPress categories for casino content"""
        categories = ['Casino Reviews']
        
        # Add license-based categories
        license_info = casino_data.get('license_info', '').lower()
        if 'malta' in license_info or 'mga' in license_info:
            categories.append('MGA Licensed')
        elif 'uk gambling commission' in license_info or 'ukgc' in license_info:
            categories.append('UKGC Licensed')
        elif 'curacao' in license_info:
            categories.append('Curacao Licensed')
        
        # Add rating-based categories
        rating = casino_data.get('overall_rating', 0)
        if isinstance(rating, (int, float)):
            if rating >= 9:
                categories.append('Top Rated')
            elif rating >= 7:
                categories.append('Recommended')
        
        return categories
    
    def _generate_casino_tags(self, casino_data: Dict[str, Any]) -> List[str]:
        """Generate WordPress tags for casino content"""
        tags = ['online casino', 'casino review', '2024']
        
        # Add casino name tag
        if casino_data.get('casino_name'):
            casino_name = casino_data['casino_name'].lower().replace(' ', '-')
            tags.append(casino_name)
        
        # Add feature-based tags
        features = casino_data.get('casino_features', [])
        if isinstance(features, list):
            for feature in features[:3]:  # Limit to 3 features
                if isinstance(feature, str) and len(feature) < 20:
                    tags.append(feature.lower().replace(' ', '-'))
        elif isinstance(features, str):
            # Split comma-separated features
            feature_list = [f.strip() for f in features.split(',')]
            for feature in feature_list[:3]:
                if len(feature) < 20:
                    tags.append(feature.lower().replace(' ', '-'))
        
        # Add payment method tags
        payment_methods = casino_data.get('payment_methods', [])
        if isinstance(payment_methods, list):
            for method in payment_methods[:2]:  # Limit to 2 methods
                if isinstance(method, str):
                    tags.append(method.lower().replace(' ', '-'))
        
        return tags
    
    def _embed_coinflip_fields(self, content: str, casino_data: Dict[str, Any]) -> str:
        """Embed CoinFlip theme fields in content"""
        
        # Extract CoinFlip-specific fields
        coinflip_fields = {
            'small_description': casino_data.get('small_description', ''),
            'casino_features': self._format_list_field(casino_data.get('casino_features', [])),
            'pros': self._format_list_field(casino_data.get('pros', [])),
            'cons': self._format_list_field(casino_data.get('cons', [])),
            'bonus_message': casino_data.get('bonus_message', ''),
            'casino_website_url': casino_data.get('casino_website_url', '')
        }
        
        # Remove empty fields
        coinflip_fields = {k: v for k, v in coinflip_fields.items() if v}
        
        if not coinflip_fields:
            return content
        
        # Create structured data for CoinFlip theme
        structured_data = '<!-- CoinFlip Theme Structured Data -->\n'
        structured_data += '<div class="coinflip-casino-data" style="display: none;">\n'
        
        for field_name, field_value in coinflip_fields.items():
            css_class = field_name.replace("_", "-")
            structured_data += f'  <div class="{css_class}">{field_value}</div>\n'
        
        structured_data += '</div>\n\n'
        
        # Create meta tags for theme compatibility
        meta_tags = '<!-- CoinFlip Theme Meta Tags -->\n'
        for field_name, field_value in coinflip_fields.items():
            escaped_value = field_value.replace('"', '&quot;')
            meta_tags += f'<meta name="casino-{field_name.replace("_", "-")}" content="{escaped_value}">\n'
        
        # Combine everything
        final_content = f'''<div class="mt-casino-listing coinflip-theme-optimized">
{structured_data}
{meta_tags}

<!-- Original Casino Review Content -->
{content}
</div>'''
        
        return final_content
    
    def _format_list_field(self, field: Union[str, List[str]]) -> str:
        """Format list fields for CoinFlip theme"""
        if isinstance(field, list):
            return ', '.join(str(item) for item in field if item)
        elif isinstance(field, str):
            return field
        else:
            return ''
    
    def _create_casino_custom_fields(self, casino_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create WordPress custom fields from casino data with MT Casino theme compatibility"""
        
        custom_fields = {}
        
        # MT Casino theme specific fields
        custom_fields['mt_rating'] = str(casino_data.get('overall_rating', 8.0))
        custom_fields['mt_bonus_amount'] = casino_data.get('welcome_bonus', '')
        custom_fields['mt_license'] = casino_data.get('license_info', '')
        custom_fields['mt_established'] = '2018'  # Default establishment year
        custom_fields['mt_min_deposit'] = '$20'   # Default minimum deposit
        
        # Casino Details section fields
        if 'casino_features' in casino_data and casino_data['casino_features']:
            features = casino_data['casino_features']
            if isinstance(features, list):
                # Format as HTML list for Casino Details display
                features_html = '<ul class="casino-features-list">' + ''.join(f'<li>{feature}</li>' for feature in features) + '</ul>'
                custom_fields['mt_casino_features'] = features_html
                # Also keep as comma-separated for compatibility
                custom_fields['casino_features_list'] = ', '.join(features)
                # Plain text version for theme flexibility
                custom_fields['casino_features_text'] = '\n'.join(f'• {feature}' for feature in features)
            else:
                custom_fields['mt_casino_features'] = str(features)
                custom_fields['casino_features_list'] = str(features)
                custom_fields['casino_features_text'] = str(features)
        
        # Social Accounts section fields (MT Casino theme specific)
        custom_fields['mt_social_facebook'] = ''      # Empty for manual entry
        custom_fields['mt_social_twitter'] = ''       # Empty for manual entry  
        custom_fields['mt_social_instagram'] = ''     # Empty for manual entry
        custom_fields['mt_social_youtube'] = ''       # Empty for manual entry
        custom_fields['mt_social_telegram'] = ''      # Empty for manual entry
        custom_fields['mt_social_linkedin'] = ''      # Empty for manual entry
        
        # Website and contact info
        if casino_data.get('casino_website_url'):
            custom_fields['mt_website'] = casino_data['casino_website_url']
            custom_fields['casino_official_url'] = casino_data['casino_website_url']
        
        # Payment methods for display
        if 'payment_methods' in casino_data:
            methods = casino_data['payment_methods']
            if isinstance(methods, list):
                custom_fields['mt_payment_methods'] = ', '.join(methods)
                custom_fields['payment_methods_list'] = ', '.join(methods)
            else:
                custom_fields['mt_payment_methods'] = str(methods)
        
        # Game providers
        if 'game_providers' in casino_data:
            providers = casino_data['game_providers']
            if isinstance(providers, list):
                custom_fields['mt_software_providers'] = ', '.join(providers)
                custom_fields['game_providers_list'] = ', '.join(providers)
            else:
                custom_fields['mt_software_providers'] = str(providers)
        
        # Pros and cons
        if 'pros' in casino_data:
            pros = casino_data['pros']
            if isinstance(pros, list):
                custom_fields['mt_pros'] = '\n'.join(f'+ {pro}' for pro in pros)
                custom_fields['casino_pros'] = ', '.join(pros)
            else:
                custom_fields['mt_pros'] = str(pros)
                custom_fields['casino_pros'] = str(pros)
        
        if 'cons' in casino_data:
            cons = casino_data['cons']
            if isinstance(cons, list):
                custom_fields['mt_cons'] = '\n'.join(f'- {con}' for con in cons)
                custom_fields['casino_cons'] = ', '.join(cons)
            else:
                custom_fields['mt_cons'] = str(cons)
                custom_fields['casino_cons'] = str(cons)
        
        # CoinFlip theme specific fields  
        custom_fields['casino_small_description'] = casino_data.get('small_description', '')
        custom_fields['casino_bonus_cta'] = casino_data.get('bonus_message', '')
        
        # Additional MT Casino fields
        custom_fields['mt_payout_speed'] = 'Instant - 24 hours'
        custom_fields['mt_customer_support'] = '24/7 Live Chat, Email, Phone'
        custom_fields['mt_mobile_compatible'] = 'Yes'
        custom_fields['mt_live_chat'] = 'Yes'
        custom_fields['mt_withdrawal_limit'] = '$25,000/week'
        
        # Metadata
        custom_fields['review_date'] = datetime.now().strftime('%Y-%m-%d')
        custom_fields['review_type'] = 'mt_casino_review'
        custom_fields['content_source'] = 'langchain_native_tool'
        
        return custom_fields
    
    def _extract_tags_from_content(self, content: str) -> List[str]:
        """Extract relevant tags from content"""
        # Simple tag extraction based on common patterns
        tags = []
        
        # Look for common gaming terms
        gaming_terms = ['casino', 'slots', 'poker', 'blackjack', 'roulette', 'bonus', 'jackpot']
        content_lower = content.lower()
        
        for term in gaming_terms:
            if term in content_lower:
                tags.append(term)
        
        # Add year tag
        current_year = datetime.now().year
        tags.append(str(current_year))
        
        return tags[:10]  # Limit to 10 tags
    
    async def _execute_wordpress_publish(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the actual WordPress API call with MT Casino support"""
        
        session = await self._get_session()
        
        try:
            # Determine if this is casino content for MT Casino post type
            is_casino = self._is_casino_content(data)
            post_type = 'mt_listing' if is_casino else 'posts'
            
            # Prepare WordPress post data
            post_data = {
                'title': data.get('title', 'Untitled Post'),
                'content': data.get('content', ''),
                'status': data.get('status', 'publish'),
                'excerpt': data.get('excerpt', '')[:150] if data.get('excerpt') else '',
                'meta': data.get('custom_fields', {})
            }
            
            # Add featured image if available
            if data.get('featured_image_url'):
                # Try to upload and set featured image
                image_id = await self._upload_featured_image(data['featured_image_url'], session)
                if image_id:
                    post_data['featured_media'] = image_id
            
            # For MT Casino posts, handle MT taxonomies
            if is_casino:
                await self._handle_mt_casino_taxonomies(post_data, data, session)
            else:
                # Handle regular categories and tags
                if data.get('categories'):
                    category_ids = await self._get_or_create_categories(data['categories'], session)
                    if category_ids:
                        post_data['categories'] = category_ids
                
                if data.get('tags'):
                    tag_ids = await self._get_or_create_tags(data['tags'], session)
                    if tag_ids:
                        post_data['tags'] = tag_ids
            
            # Make the API call to appropriate endpoint
            url = f"{self.site_url.rstrip('/')}/wp-json/wp/v2/{post_type}"
            
            logger.info(f"🚀 Publishing to WordPress: {url}")
            logger.info(f"📝 Post type: {post_type}, title: '{post_data['title']}', content_length: {len(post_data['content'])}")
            
            async with session.post(url, headers=self._auth_headers, json=post_data) as response:
                if response.status in [200, 201]:
                    result = await response.json()
                    
                    logger.info(f"✅ WordPress {post_type} published successfully: ID {result['id']}")
                    
                    return {
                        "success": True,
                        "post_id": result['id'],
                        "url": result['link'],
                        "title": result['title']['rendered'],
                        "status": result['status'],
                        "post_type": post_type,
                        "edit_url": f"{self.site_url}/wp-admin/post.php?post={result['id']}&action=edit",
                        "custom_fields_count": len(data.get('custom_fields', {})),
                        "categories": data.get('categories', []),
                        "tags": data.get('tags', []),
                        "has_featured_image": 'featured_media' in post_data,
                        "tool": "wordpress_publisher"
                    }
                else:
                    error_text = await response.text()
                    logger.error(f"❌ WordPress API error {response.status}: {error_text}")
                    
                    return {
                        "success": False,
                        "error": f"WordPress API error {response.status}: {error_text}",
                        "tool": "wordpress_publisher"
                    }
                    
        except Exception as e:
            logger.error(f"❌ WordPress publishing exception: {e}")
            return {
                "success": False,
                "error": str(e),
                "tool": "wordpress_publisher"
            }
    
    async def _handle_mt_casino_taxonomies(self, post_data: Dict, casino_data: Dict, session) -> None:
        """Handle MT Casino specific taxonomies"""
        try:
            # MT Casino Categories (mt-listing-category2)
            mt_categories = []
            if casino_data.get('overall_rating', 0) >= 8:
                mt_categories.append('Top Rated Casinos')
            mt_categories.extend(['Online Casinos', 'Casino Reviews'])
            
            if mt_categories:
                category_ids = await self._get_or_create_mt_taxonomy(mt_categories, 'mt-listing-category2', session)
                if category_ids:
                    post_data['mt-listing-category2'] = category_ids
            
            # MT Casino Software (mt_software) 
            game_providers = casino_data.get('game_providers', [])
            if game_providers:
                software_ids = await self._get_or_create_mt_taxonomy(game_providers, 'mt_software', session)
                if software_ids:
                    post_data['mt_software'] = software_ids
            
            # MT Casino Payment Methods (mt_payment_methods)
            payment_methods = casino_data.get('payment_methods', [])
            if payment_methods:
                payment_ids = await self._get_or_create_mt_taxonomy(payment_methods, 'mt_payment_methods', session)
                if payment_ids:
                    post_data['mt_payment_methods'] = payment_ids
            
            # MT Casino Licenses (mt_licences)
            license_info = casino_data.get('license_info', '')
            if license_info:
                # Extract license authorities from license info
                licenses = []
                if 'malta' in license_info.lower() or 'mga' in license_info.lower():
                    licenses.append('Malta Gaming Authority')
                elif 'curacao' in license_info.lower():
                    licenses.append('Curacao eGaming')
                elif 'uk gambling' in license_info.lower():
                    licenses.append('UK Gambling Commission')
                else:
                    licenses.append('Licensed')
                
                if licenses:
                    license_ids = await self._get_or_create_mt_taxonomy(licenses, 'mt_licences', session)
                    if license_ids:
                        post_data['mt_licences'] = license_ids
            
            # MT Casino Languages (default to English)
            lang_ids = await self._get_or_create_mt_taxonomy(['English'], 'mt_languages', session)
            if lang_ids:
                post_data['mt_languages'] = lang_ids
            
            # MT Casino Currencies (default to USD)
            currency_ids = await self._get_or_create_mt_taxonomy(['USD', 'EUR'], 'mt_currencies', session)  
            if currency_ids:
                post_data['mt_currencies'] = currency_ids
                
        except Exception as e:
            logger.warning(f"⚠️ Error handling MT Casino taxonomies: {e}")
    
    async def _get_or_create_mt_taxonomy(self, terms: List[str], taxonomy: str, session) -> List[int]:
        """Get or create MT Casino taxonomy terms"""
        term_ids = []
        
        for term_name in terms:
            try:
                # Search for existing term
                search_url = f"{self.site_url.rstrip('/')}/wp-json/wp/v2/{taxonomy}?search={term_name}"
                async with session.get(search_url, headers=self._auth_headers) as response:
                    if response.status == 200:
                        terms_result = await response.json()
                        if terms_result:
                            term_ids.append(terms_result[0]['id'])
                            continue
                
                # Create new term if not found
                create_url = f"{self.site_url.rstrip('/')}/wp-json/wp/v2/{taxonomy}"
                term_data = {
                    'name': term_name,
                    'slug': term_name.lower().replace(' ', '-').replace('/', '-')
                }
                
                async with session.post(create_url, headers=self._auth_headers, json=term_data) as response:
                    if response.status in [200, 201]:
                        result = await response.json()
                        term_ids.append(result['id'])
                    else:
                        logger.warning(f"⚠️ Failed to create MT taxonomy term '{term_name}' in {taxonomy}")
                        
            except Exception as e:
                logger.warning(f"⚠️ Error processing MT taxonomy term '{term_name}': {e}")
        
        return term_ids
    
    async def _upload_featured_image(self, image_url: str, session) -> Optional[int]:
        """Upload and set featured image from URL"""
        try:
            # Download image
            async with session.get(image_url) as img_response:
                if img_response.status != 200:
                    logger.warning(f"⚠️ Failed to download image from {image_url}")
                    return None
                
                image_data = await img_response.read()
                content_type = img_response.headers.get('content-type', 'image/jpeg')
                
                # Determine filename
                from urllib.parse import urlparse
                parsed = urlparse(image_url)
                filename = parsed.path.split('/')[-1] or 'casino-image.jpg'
                if '.' not in filename:
                    filename += '.jpg'
            
            # Upload to WordPress media library
            media_url = f"{self.site_url.rstrip('/')}/wp-json/wp/v2/media"
            
            # Create form data
            import aiohttp
            data = aiohttp.FormData()
            data.add_field('file', image_data, filename=filename, content_type=content_type)
            
            # Upload with media-specific headers
            upload_headers = self._auth_headers.copy()
            upload_headers.pop('Content-Type', None)  # Let aiohttp set it for form data
            
            async with session.post(media_url, headers=upload_headers, data=data) as response:
                if response.status in [200, 201]:
                    result = await response.json()
                    logger.info(f"✅ Image uploaded successfully: ID {result['id']}")
                    return result['id']
                else:
                    error_text = await response.text()
                    logger.warning(f"⚠️ Image upload failed: {response.status} - {error_text}")
                    return None
                    
        except Exception as e:
            logger.warning(f"⚠️ Error uploading featured image: {e}")
            return None
    
    async def _get_or_create_categories(self, category_names: List[str], session: aiohttp.ClientSession) -> List[int]:
        """Get existing categories or create new ones"""
        category_ids = []
        
        for category_name in category_names:
            try:
                # Search for existing category
                search_url = f"{self.site_url.rstrip('/')}/wp-json/wp/v2/categories?search={category_name}"
                async with session.get(search_url, headers=self._auth_headers) as response:
                    if response.status == 200:
                        categories = await response.json()
                        if categories:
                            category_ids.append(categories[0]['id'])
                            continue
                
                # Create new category if not found
                create_url = f"{self.site_url.rstrip('/')}/wp-json/wp/v2/categories"
                category_data = {
                    'name': category_name,
                    'slug': category_name.lower().replace(' ', '-')
                }
                
                async with session.post(create_url, headers=self._auth_headers, json=category_data) as response:
                    if response.status in [200, 201]:
                        result = await response.json()
                        category_ids.append(result['id'])
                    else:
                        logger.warning(f"⚠️ Failed to create category '{category_name}'")
                        
            except Exception as e:
                logger.warning(f"⚠️ Error processing category '{category_name}': {e}")
        
        return category_ids
    
    async def _get_or_create_tags(self, tag_names: List[str], session: aiohttp.ClientSession) -> List[int]:
        """Get existing tags or create new ones"""
        tag_ids = []
        
        for tag_name in tag_names:
            try:
                # Search for existing tag
                search_url = f"{self.site_url.rstrip('/')}/wp-json/wp/v2/tags?search={tag_name}"
                async with session.get(search_url, headers=self._auth_headers) as response:
                    if response.status == 200:
                        tags = await response.json()
                        if tags:
                            tag_ids.append(tags[0]['id'])
                            continue
                
                # Create new tag if not found
                create_url = f"{self.site_url.rstrip('/')}/wp-json/wp/v2/tags"
                tag_data = {
                    'name': tag_name,
                    'slug': tag_name.lower().replace(' ', '-')
                }
                
                async with session.post(create_url, headers=self._auth_headers, json=tag_data) as response:
                    if response.status in [200, 201]:
                        result = await response.json()
                        tag_ids.append(result['id'])
                    else:
                        logger.warning(f"⚠️ Failed to create tag '{tag_name}'")
                        
            except Exception as e:
                logger.warning(f"⚠️ Error processing tag '{tag_name}': {e}")
        
        return tag_ids

# Factory function for easy integration
def create_wordpress_tool(**kwargs) -> WordPressPublishingTool:
    """Create WordPress publishing tool with configuration"""
    return WordPressPublishingTool(**kwargs)

# Pydantic output parser for structured content
wordpress_parser = PydanticOutputParser(pydantic_object=WordPressPostSchema)

def get_wordpress_prompt_template() -> PromptTemplate:
    """Get prompt template for WordPress content generation"""
    return PromptTemplate(
        template="""Convert the following content into a properly formatted WordPress post.
        
Content: {content}
Additional Info: {additional_info}

{format_instructions}

Make sure to:
1. Create an SEO-friendly title
2. Format content as clean HTML
3. Extract relevant categories and tags
4. Include a compelling excerpt
5. For casino content, include all relevant fields
""",
        input_variables=["content", "additional_info"],
        partial_variables={"format_instructions": wordpress_parser.get_format_instructions()}
    )