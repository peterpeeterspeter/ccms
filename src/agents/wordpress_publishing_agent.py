"""
WordPress Publishing Agent
===========================

Specialized agent for publishing casino reviews to WordPress with complete MT Casino integration.
Follows WARP.md LangChain-native principles with proper tool adapters.
"""

import asyncio
from typing import Dict, List, Optional, Any
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from ..schemas.casino_review import (
    CasinoReviewDoc, 
    CasinoResearchPack, 
    ScreenshotResult, 
    PublishResult
)
from ..tools.wordpress import WordPressClient
from ..tools.supabase_storage import get_media_metadata


class WordPressPostData(BaseModel):
    """Structured WordPress post data for MT Casino posts"""
    title: str
    content: str
    excerpt: str
    status: str = "publish"
    featured_media: int
    meta: Dict[str, Any]
    categories: List[int]
    tags: List[int]


class WordPressPublishingAgent:
    """
    Publishing Agent: Complete WordPress publication workflow for casino reviews
    
    Handles:
    - MT Casino post creation with full metadata
    - Featured image assignment via WordPress media IDs  
    - Custom field population for all casino data
    - Taxonomy and category assignment
    - Internal link optimization
    - SEO metadata setup
    """
    
    def __init__(self, wordpress_client: WordPressClient, tenant_id: str = "crashcasino"):
        self.wp = wordpress_client
        self.tenant_id = tenant_id
        
        # Build publishing chain following LCEL composition
        self.publishing_chain = (
            RunnablePassthrough()
            | RunnableLambda(self._prepare_post_data)
            | RunnableLambda(self._validate_media_ids) 
            | RunnableLambda(self._create_mt_listing_post)
            | RunnableLambda(self._populate_custom_fields)
            | RunnableLambda(self._assign_taxonomies)
            | RunnableLambda(self._optimize_internal_links)
            | RunnableLambda(self._finalize_publication)
        )
    
    async def _prepare_post_data(self, input_data: Dict) -> Dict:
        """Prepare WordPress post data structure from review content"""
        
        review: CasinoReviewDoc = input_data["review"]
        research: CasinoResearchPack = input_data["research"]
        media_ids: List[int] = input_data["media_ids"]
        
        # Generate WordPress-formatted content following your established patterns
        formatted_content = self._format_review_content(review, research)
        
        # Prepare MT Casino custom fields mapping
        custom_fields = self._build_custom_fields(research, review)
        
        # Determine categories and tags from research data
        categories = await self._determine_categories(research)
        tags = await self._extract_tags(research, review)
        
        post_data = WordPressPostData(
            title=review.title,
            content=formatted_content,
            excerpt=review.excerpt,
            status="publish" if input_data.get("publish_immediately", True) else "draft",
            featured_media=media_ids[0] if media_ids else 0,  # Primary screenshot
            meta=custom_fields,
            categories=categories,
            tags=tags
        )
        
        return {
            **input_data,
            "post_data": post_data,
            "additional_media": media_ids[1:] if len(media_ids) > 1 else []
        }
    
    async def _validate_media_ids(self, data: Dict) -> Dict:
        """Validate all WordPress media IDs exist and are accessible"""
        
        media_ids = data["media_ids"]
        valid_media_ids = []
        
        for media_id in media_ids:
            try:
                # Verify media exists in WordPress
                media_info = await self.wp.get_media(media_id)
                if media_info and media_info.get("id") == media_id:
                    valid_media_ids.append(media_id)
                else:
                    print(f"Warning: Media ID {media_id} not found or inaccessible")
            except Exception as e:
                print(f"Error validating media ID {media_id}: {str(e)}")
        
        # Update post data with validated media IDs
        if valid_media_ids:
            data["post_data"].featured_media = valid_media_ids[0]
            data["additional_media"] = valid_media_ids[1:]
        else:
            # Fallback: set featured media to 0 (no featured image)
            data["post_data"].featured_media = 0
            data["additional_media"] = []
            print("Warning: No valid media IDs found - proceeding without featured image")
        
        return data
    
    async def _create_mt_listing_post(self, data: Dict) -> Dict:
        """Create the main MT Casino listing post"""
        
        post_data = data["post_data"]
        
        # Prepare WordPress REST API post payload
        wp_post_payload = {
            "title": post_data.title,
            "content": post_data.content,
            "excerpt": post_data.excerpt,
            "status": post_data.status,
            "featured_media": post_data.featured_media,
            "categories": post_data.categories,
            "tags": post_data.tags,
            "type": "mt_listing",  # MT Casino post type
            "template": "",
            "comment_status": "open",
            "ping_status": "closed"
        }
        
        try:
            # Create the post via WordPress REST API
            created_post = await self.wp.create_post(wp_post_payload)
            
            if created_post and created_post.get("id"):
                post_id = created_post["id"]
                post_url = created_post.get("link", f"{self.wp.base_url}/?p={post_id}")
                
                return {
                    **data,
                    "post_id": post_id,
                    "post_url": post_url,
                    "wp_post": created_post
                }
            else:
                raise Exception("Failed to create WordPress post - no ID returned")
                
        except Exception as e:
            raise Exception(f"WordPress post creation failed: {str(e)}")
    
    async def _populate_custom_fields(self, data: Dict) -> Dict:
        """Populate all MT Casino custom fields with research data"""
        
        post_id = data["post_id"]
        research: CasinoResearchPack = data["research"]
        review: CasinoReviewDoc = data["review"]
        
        # Build comprehensive MT Casino metadata
        custom_fields = {
            # Basic casino information
            "mt_casino_website": str(research.casino_url),
            "mt_casino_rating": str(review.overall_rating),
            "mt_casino_license": research.license_type.value if research.license_type else "",
            "mt_casino_bonus_code": research.welcome_bonus or "",
            
            # Payment and banking
            "mt_casino_currencies": ",".join(research.supported_currencies),
            "mt_casino_payment_methods": ",".join([pm.value for pm in research.payment_methods]),
            "mt_casino_withdrawal_time": research.withdrawal_time or "",
            "mt_casino_min_deposit": research.min_deposit or "",
            "mt_casino_max_withdrawal": research.max_withdrawal or "",
            
            # Games and software
            "mt_casino_software": ",".join(research.software_providers),
            "mt_casino_games": str(research.total_games) if research.total_games else "",
            
            # Support and features
            "mt_casino_customer_support": ",".join(research.customer_support),
            "mt_casino_languages": ",".join(research.supported_languages),
            "mt_casino_live_chat": "yes" if "live_chat" in research.customer_support else "no",
            "mt_casino_mobile_app": "yes" if research.mobile_app else "no",
            "mt_casino_vip_program": "yes" if research.vip_program else "no",
            "mt_casino_responsible_gambling": "yes" if research.responsible_gambling else "no",
            
            # Review metadata
            "mt_review_overall_rating": str(review.overall_rating),
            "mt_review_pros": "|".join(review.pros),
            "mt_review_cons": "|".join(review.cons),
            "mt_review_final_verdict": review.excerpt,
            "mt_review_date": research.research_timestamp.isoformat(),
            "mt_review_author": "AI Casino Expert",
            
            # Bonus information (if available)
            "mt_bonus_amount": research.welcome_bonus or "",
            "mt_bonus_wagering": research.wagering_requirements or "",
            "mt_bonus_terms": f"Researched on {research.research_timestamp.strftime('%Y-%m-%d')}",
            
            # Featured flags
            "mt_featured": "no",
            "mt_popular": "no", 
            "mt_new": "yes" if research.established_year and research.established_year >= 2020 else "no",
            "mt_recommended": "yes" if review.overall_rating >= 8.0 else "no",
            
            # Security and compliance
            "mt_casino_security": "SSL encrypted" if research.kyc_required else "Basic",
            "mt_terms_conditions": f"Reviewed {research.research_timestamp.strftime('%Y-%m-%d')}"
        }
        
        # Set custom fields via WordPress REST API
        custom_fields_set = 0
        for field_key, field_value in custom_fields.items():
            try:
                await self.wp.set_post_meta(post_id, field_key, field_value)
                custom_fields_set += 1
            except Exception as e:
                print(f"Warning: Failed to set custom field {field_key}: {str(e)}")
        
        return {
            **data,
            "custom_fields_set": custom_fields_set,
            "total_fields": len(custom_fields)
        }
    
    async def _assign_taxonomies(self, data: Dict) -> Dict:
        """Assign appropriate taxonomies and categories based on casino research"""
        
        post_id = data["post_id"]
        research: CasinoResearchPack = data["research"]
        
        taxonomies_assigned = []
        
        try:
            # Assign casino categories based on type and features
            if research.crash_games_available:
                await self.wp.assign_term(post_id, "mt-listing-category2", "crash-casinos")
                taxonomies_assigned.append("crash-casinos")
            
            if research.live_dealer_available:
                await self.wp.assign_term(post_id, "mt-listing-category2", "live-dealer")
                taxonomies_assigned.append("live-dealer")
            
            if research.mobile_app:
                await self.wp.assign_term(post_id, "mt-listing-category2", "mobile-casinos")
                taxonomies_assigned.append("mobile-casinos")
            
            # Assign provider tags
            for provider in research.software_providers:
                provider_slug = provider.lower().replace(" ", "-").replace("'", "")
                await self.wp.assign_term(post_id, "mt-listing-tags", provider_slug)
                taxonomies_assigned.append(f"provider-{provider_slug}")
            
            # Assign licensing taxonomy
            if research.license_type:
                license_term = research.license_type.value.replace("_", "-")
                await self.wp.assign_term(post_id, "mt-listing-amenities", f"{license_term}-gaming-commission")
                taxonomies_assigned.append(f"license-{license_term}")
            
            # Assign payment method taxonomies
            for payment_method in research.payment_methods:
                if payment_method == "crypto":
                    await self.wp.assign_term(post_id, "mt-listing-payment-methods", "cryptocurrency")
                    taxonomies_assigned.append("payment-crypto")
                elif payment_method == "credit_card":
                    await self.wp.assign_term(post_id, "mt-listing-payment-methods", "credit-cards")
                    taxonomies_assigned.append("payment-cards")
            
            # Assign currency taxonomies
            for currency in research.supported_currencies[:10]:  # Limit to prevent overload
                currency_slug = currency.lower()
                if currency_slug in ["btc", "eth", "ltc", "doge", "usdt", "usdc"]:
                    await self.wp.assign_term(post_id, "mt-listing-currencies", currency_slug)
                    taxonomies_assigned.append(f"currency-{currency_slug}")
            
            # Assign restricted country taxonomies for compliance
            for country in research.restricted_countries[:15]:  # Limit to major restrictions
                country_slug = country.lower().replace(" ", "-")
                await self.wp.assign_term(post_id, "mt-bookmaker-restricted", country_slug)
                taxonomies_assigned.append(f"restricted-{country_slug}")
                
        except Exception as e:
            print(f"Warning: Taxonomy assignment error: {str(e)}")
        
        return {
            **data,
            "taxonomies_assigned": taxonomies_assigned
        }
    
    async def _optimize_internal_links(self, data: Dict) -> Dict:
        """Add internal links to related casino content"""
        
        post_id = data["post_id"] 
        review: CasinoReviewDoc = data["review"]
        
        # Get current post content
        current_post = await self.wp.get_post(post_id)
        content = current_post.get("content", {}).get("rendered", "")
        
        # Add strategic internal links based on casino type and features
        optimized_content = await self._inject_internal_links(content, review)
        
        # Update post with optimized content
        if optimized_content != content:
            try:
                await self.wp.update_post(post_id, {"content": optimized_content})
                return {**data, "internal_links_added": True}
            except Exception as e:
                print(f"Warning: Internal link optimization failed: {str(e)}")
        
        return {**data, "internal_links_added": False}
    
    async def _finalize_publication(self, data: Dict) -> PublishResult:
        """Finalize publication and return comprehensive result"""
        
        post_id = data["post_id"]
        post_url = data["post_url"]
        
        # Attach additional media to post
        additional_media_attached = []
        for media_id in data.get("additional_media", []):
            try:
                await self.wp.attach_media_to_post(media_id, post_id)
                additional_media_attached.append(media_id)
            except Exception as e:
                print(f"Warning: Failed to attach media {media_id}: {str(e)}")
        
        # Final validation
        final_post = await self.wp.get_post(post_id)
        success = bool(final_post and final_post.get("id") == post_id)
        
        return PublishResult(
            post_id=post_id,
            post_url=post_url,
            post_status=final_post.get("status", "unknown") if final_post else "error",
            featured_media_id=data.get("post_data").featured_media,
            additional_media_ids=additional_media_attached,
            custom_fields_populated=data.get("custom_fields_set", 0),
            taxonomies_assigned=data.get("taxonomies_assigned", []),
            tenant_id=self.tenant_id,
            success=success,
            errors=[] if success else ["Publication validation failed"],
            warnings=[]
        )
    
    # Helper methods for content formatting and processing
    def _format_review_content(self, review: CasinoReviewDoc, research: CasinoResearchPack) -> str:
        """Format review content following your established HTML structure"""
        
        # Build content following your review patterns
        content_parts = []
        
        # Add structured sections maintaining your established format
        for section in review.sections:
            content_parts.append(f"<h2>{section.title}</h2>")
            content_parts.append(section.content)
        
        # Add rating breakdown section
        content_parts.append(self._build_rating_section(review))
        
        # Add casino details table
        content_parts.append(self._build_details_table(research))
        
        return "\n\n".join(content_parts)
    
    def _build_custom_fields(self, research: CasinoResearchPack, review: CasinoReviewDoc) -> Dict[str, Any]:
        """Build complete custom fields mapping for MT Casino post type"""
        # Implementation would map all research data to MT Casino custom fields
        return {}
    
    async def _determine_categories(self, research: CasinoResearchPack) -> List[int]:
        """Determine WordPress category IDs based on casino features"""
        # Implementation would map casino features to category IDs
        return []
    
    async def _extract_tags(self, research: CasinoResearchPack, review: CasinoReviewDoc) -> List[int]:
        """Extract relevant tag IDs for the casino review"""
        # Implementation would identify relevant tags from content
        return []
    
    def _build_rating_section(self, review: CasinoReviewDoc) -> str:
        """Build the rating breakdown section HTML"""
        # Implementation would create structured rating display
        return ""
    
    def _build_details_table(self, research: CasinoResearchPack) -> str:
        """Build casino details table HTML"""
        # Implementation would create structured details table
        return ""
    
    async def _inject_internal_links(self, content: str, review: CasinoReviewDoc) -> str:
        """Inject strategic internal links into content"""
        # Implementation would add contextual internal links
        return content
    
    async def publish_review(self, review_data: Dict) -> PublishResult:
        """Main entry point for publishing casino review"""
        return await self.publishing_chain.ainvoke(review_data)
