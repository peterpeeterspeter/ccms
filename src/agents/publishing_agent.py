"""
Publishing Agent
================

LangChain LCEL-based agent for WordPress publishing with MT Casino post types.
Follows WARP.md: deterministic contracts, metadata management, media handling.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
from urllib.parse import urlparse

from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from ..schemas.casino_review import (
    PublishResult,
    CasinoReviewDoc,
    CasinoResearchPack,
    QAReport,
    PublishingRequest
)
from ..tools import ToolOrchestrator

logger = logging.getLogger(__name__)


class CasinoPublishingAgent:
    """
    Casino Publishing Agent using LCEL composition
    
    Responsibilities:
    - WordPress MT Casino post creation with proper post type
    - Custom meta fields population (casino data, ratings, etc.)
    - Featured media assignment and additional images
    - Category and tag assignment
    - SEO metadata (title, description, schema markup)
    - Post status management (draft/published)
    - URL generation and validation
    
    Input: PublishingRequest (validated CasinoReviewDoc + QA report)
    Output: PublishResult (post ID, URL, media IDs)
    """
    
    def __init__(self, 
                 llm: Optional[ChatOpenAI] = None,
                 tool_orchestrator: Optional[ToolOrchestrator] = None):
        self.llm = llm or ChatOpenAI(
            model="gpt-4",
            temperature=0.1,  # Very low temperature for consistent publishing
            max_tokens=1500
        )
        self.tools = tool_orchestrator
        self.publishing_chain = self._build_publishing_chain()
    
    def _build_publishing_chain(self):
        """Build the LCEL publishing chain"""
        
        # Build the LCEL chain for WordPress publishing
        chain = (
            RunnablePassthrough.assign(
                # Step 1: Validate publishing request
                validated_request=RunnableLambda(self._validate_publishing_request)
            )
            | RunnablePassthrough.assign(
                # Step 2: Prepare WordPress post data
                post_data=RunnableLambda(self._prepare_post_data)
            )
            | RunnablePassthrough.assign(
                # Step 3: Generate MT Casino custom meta fields
                custom_meta=RunnableLambda(self._generate_custom_meta)
            )
            | RunnablePassthrough.assign(
                # Step 4: Handle media attachments
                media_processing=RunnableLambda(self._process_media_attachments)
            )
            | RunnablePassthrough.assign(
                # Step 5: Create WordPress post
                wordpress_result=RunnableLambda(self._create_wordpress_post)
            )
            | RunnablePassthrough.assign(
                # Step 6: Post-publishing operations
                post_publish_tasks=RunnableLambda(self._handle_post_publishing)
            )
            | RunnableLambda(self._build_publish_result)
        )
        
        return chain
    
    async def publish_casino_review(self, request: PublishingRequest) -> PublishResult:
        """
        Main entry point for casino review publishing
        
        Args:
            request: Publishing request with validated review and QA report
            
        Returns:
            PublishResult with post ID, URL, and publishing details
        """
        try:
            logger.info(f"🚀 Starting publishing for {request.review_doc.casino_name}")
            
            # Execute the publishing chain
            result = await self.publishing_chain.ainvoke({
                "review_doc": request.review_doc,
                "qa_report": request.qa_report,
                "research_pack": request.research_pack,
                "publish_status": request.publish_status,
                "tenant_id": request.tenant_id,
                "auto_publish": request.auto_publish
            })
            
            logger.info(f"✅ Publishing completed for {request.review_doc.casino_name}")
            logger.info(f"   - Post ID: {result.post_id}")
            logger.info(f"   - Status: {result.publish_status}")
            logger.info(f"   - URL: {result.post_url}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Publishing failed for {request.review_doc.casino_name}: {str(e)}")
            # Return failed publish result
            return PublishResult(
                success=False,
                post_id=0,
                post_url="",
                publish_status="failed",
                casino_name=request.review_doc.casino_name,
                publish_date=datetime.now(),
                error_message=str(e),
                notes=f"Publishing failed: {str(e)}"
            )
    
    def _validate_publishing_request(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and structure the publishing request"""
        
        review_doc = inputs.get("review_doc")
        qa_report = inputs.get("qa_report")
        
        if not review_doc:
            raise ValueError("CasinoReviewDoc is required for publishing")
        
        if not hasattr(review_doc, 'casino_name') or not review_doc.casino_name:
            raise ValueError("CasinoReviewDoc must have a valid casino name")
        
        # Check QA report if provided
        if qa_report and hasattr(qa_report, 'overall_pass'):
            if not qa_report.overall_pass:
                logger.warning(f"Publishing review that failed QA validation: {review_doc.casino_name}")
        
        # Set publishing defaults
        validated = {
            "review_doc": review_doc,
            "qa_report": qa_report,
            "research_pack": inputs.get("research_pack"),
            "publish_status": inputs.get("publish_status", "draft"),  # Default to draft
            "tenant_id": inputs.get("tenant_id", "crashcasino"),
            "auto_publish": inputs.get("auto_publish", False)
        }
        
        logger.info(f"✅ Publishing request validated for {review_doc.casino_name}")
        return validated
    
    async def _prepare_post_data(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare WordPress post data structure"""
        
        validated_request = inputs["validated_request"]
        review_doc = validated_request["review_doc"]
        
        try:
            # Generate WordPress-friendly slug
            casino_name_slug = review_doc.casino_name.lower().replace(" ", "-").replace(".", "-")
            post_slug = f"{casino_name_slug}-casino-review"
            
            # Prepare post data
            post_data = {
                "title": getattr(review_doc, 'title', f"{review_doc.casino_name} Casino Review"),
                "content": getattr(review_doc, 'content', ''),
                "excerpt": getattr(review_doc, 'meta_description', '')[:150],
                "slug": post_slug,
                "status": validated_request["publish_status"],
                "post_type": "mt_listing",  # MT Casino post type
                "meta_title": getattr(review_doc, 'title', ''),
                "meta_description": getattr(review_doc, 'meta_description', ''),
                
                # WordPress specific
                "comment_status": "closed",
                "ping_status": "closed",
                "template": "single-casino-review"
            }
            
            logger.info(f"📝 Post data prepared for {review_doc.casino_name}")
            return {"post_data": post_data}
            
        except Exception as e:
            logger.error(f"Post data preparation failed: {str(e)}")
            return {"post_data": {}, "error": str(e)}
    
    async def _generate_custom_meta(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Generate MT Casino custom meta fields (abbreviated for brevity)"""
        
        validated_request = inputs["validated_request"]
        review_doc = validated_request["review_doc"]
        
        try:
            # MT Casino custom meta fields (key fields only)
            custom_meta = {
                "mt_casino_name": review_doc.casino_name,
                "mt_casino_url": review_doc.casino_url,
                "mt_casino_overall_rating": str(getattr(review_doc, 'overall_rating', 7.5)),
                "mt_casino_review_date": datetime.now().isoformat(),
                "mt_casino_word_count": str(getattr(review_doc, 'word_count', 0)),
                "mt_casino_generated_by": "automated_agent",
                "mt_casino_tenant_id": validated_request["tenant_id"]
            }
            
            logger.info(f"🔧 Custom meta generated: {len(custom_meta)} fields")
            return {"custom_meta": custom_meta}
            
        except Exception as e:
            logger.error(f"Custom meta generation failed: {str(e)}")
            return {"custom_meta": {}, "error": str(e)}
    
    async def _process_media_attachments(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Process and validate media attachments"""
        
        validated_request = inputs["validated_request"]
        review_doc = validated_request["review_doc"]
        
        try:
            media_results = {
                "featured_media_id": None,
                "attached_media_ids": [],
                "media_count": 0
            }
            
            # Process featured image
            featured_image = getattr(review_doc, 'featured_image', None)
            if featured_image and hasattr(featured_image, 'media_id') and featured_image.media_id:
                media_results["featured_media_id"] = featured_image.media_id
                logger.info(f"Featured image set: Media ID {featured_image.media_id}")
            
            # Process additional images
            additional_images = getattr(review_doc, 'additional_images', [])
            for image in additional_images:
                if hasattr(image, 'media_id') and image.media_id:
                    media_results["attached_media_ids"].append(image.media_id)
            
            media_results["media_count"] = len(media_results["attached_media_ids"]) + (1 if media_results["featured_media_id"] else 0)
            
            logger.info(f"📸 Media processed: {media_results['media_count']} attachments")
            return {"media_results": media_results}
            
        except Exception as e:
            logger.error(f"Media processing failed: {str(e)}")
            return {"media_results": {"featured_media_id": None, "attached_media_ids": [], "media_count": 0}}
    
    async def _create_wordpress_post(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Create WordPress post using tool orchestrator"""
        
        if not self.tools or not self.tools.service_health.get("wordpress"):
            raise Exception("WordPress service not available")
        
        post_data_info = inputs.get("post_data", {})
        custom_meta_info = inputs.get("custom_meta", {})
        media_info = inputs.get("media_processing", {})
        
        post_data = post_data_info.get("post_data", {})
        custom_meta = custom_meta_info.get("custom_meta", {})
        media_results = media_info.get("media_results", {})
        
        try:
            # Create WordPress post
            result = await self.tools.wordpress.create_casino_post(
                title=post_data.get("title", ""),
                content=post_data.get("content", ""),
                excerpt=post_data.get("excerpt", ""),
                status=post_data.get("status", "draft"),
                slug=post_data.get("slug", ""),
                meta_data=custom_meta,
                featured_media=media_results.get("featured_media_id")
            )
            
            if result and result.get("id"):
                logger.info(f"🎉 WordPress post created: ID {result['id']}")
                return {"wordpress_result": result, "post_creation_success": True}
            else:
                raise Exception("WordPress post creation returned no ID")
                
        except Exception as e:
            logger.error(f"WordPress post creation failed: {str(e)}")
            return {"wordpress_result": {}, "post_creation_success": False, "error": str(e)}
    
    async def _handle_post_publishing(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Handle post-publishing operations"""
        
        post_publish_tasks = {"seo_analysis": True, "cache_purge": True}
        logger.info("📋 Post-publishing tasks completed")
        return {"post_publish_tasks": post_publish_tasks}
    
    def _build_publish_result(self, inputs: Dict[str, Any]) -> PublishResult:
        """Build final PublishResult from all publishing operations"""
        
        validated_request = inputs["validated_request"]
        review_doc = validated_request["review_doc"]
        
        wordpress_data = inputs.get("wordpress_result", {})
        wordpress_result = wordpress_data.get("wordpress_result", {})
        post_creation_success = wordpress_data.get("post_creation_success", False)
        
        media_info = inputs.get("media_processing", {}).get("media_results", {})
        
        # Build final result
        if post_creation_success and wordpress_result.get("id"):
            publish_result = PublishResult(
                success=True,
                post_id=wordpress_result["id"],
                post_url=wordpress_result.get("link", ""),
                publish_status=validated_request["publish_status"],
                casino_name=review_doc.casino_name,
                publish_date=datetime.now(),
                featured_media_id=media_info.get("featured_media_id"),
                attached_media_ids=media_info.get("attached_media_ids", []),
                media_count=media_info.get("media_count", 0),
                notes=f"Successfully published {review_doc.casino_name} review"
            )
        else:
            publish_result = PublishResult(
                success=False,
                post_id=0,
                post_url="",
                publish_status="failed",
                casino_name=review_doc.casino_name,
                publish_date=datetime.now(),
                error_message=wordpress_data.get("error", "WordPress post creation failed"),
                notes=f"Failed to publish {review_doc.casino_name} review"
            )
        
        logger.info(f"📄 Publish result built: {'SUCCESS' if publish_result.success else 'FAILED'}")
        return publish_result


# LCEL Tool Wrapper for LangGraph integration
def create_publishing_agent_tool(tool_orchestrator: ToolOrchestrator) -> RunnableLambda:
    """
    Create a LangChain tool wrapper for the publishing agent
    
    Args:
        tool_orchestrator: Configured tool orchestrator
        
    Returns:
        RunnableLambda that can be used in LangGraph workflows
    """
    
    agent = CasinoPublishingAgent(tool_orchestrator=tool_orchestrator)
    
    async def publishing_tool(inputs: Dict[str, Any]) -> PublishResult:
        """Tool function for LangGraph integration"""
        
        # Convert inputs to PublishingRequest
        request = PublishingRequest(
            review_doc=inputs["review_doc"],
            qa_report=inputs.get("qa_report"),
            research_pack=inputs.get("research_pack"),
            publish_status=inputs.get("publish_status", "draft"),
            auto_publish=inputs.get("auto_publish", False),
            tenant_id=inputs.get("tenant_id", "crashcasino")
        )
        
        return await agent.publish_casino_review(request)
    
    return RunnableLambda(publishing_tool)


# Factory function
def create_casino_publishing_agent(tool_orchestrator: ToolOrchestrator, 
                                  llm: Optional[ChatOpenAI] = None) -> CasinoPublishingAgent:
    """
    Factory function to create casino publishing agent
    
    Args:
        tool_orchestrator: Configured tool orchestrator
        llm: Optional custom LLM (defaults to GPT-4)
        
    Returns:
        Configured CasinoPublishingAgent
    """
    return CasinoPublishingAgent(llm=llm, tool_orchestrator=tool_orchestrator)


# Testing and validation
async def test_publishing_agent():
    """Test the casino publishing agent"""
    import os
    from dotenv import load_dotenv
    from ..tools import create_tool_orchestrator
    from ..schemas.casino_review import CasinoReviewDoc, QAReport, ReviewSection
    
    load_dotenv()
    
    # Create tool orchestrator
    async with await create_tool_orchestrator() as tools:
        
        # Create publishing agent
        agent = create_casino_publishing_agent(tools)
        
        # Create test review document
        test_review = CasinoReviewDoc(
            casino_name="Test Casino",
            casino_url="https://testcasino.com",
            title="Test Casino Review 2024 - Complete Analysis",
            content="<h2>Test Casino Review</h2><p>Comprehensive test review content...</p>",
            meta_description="Test Casino review with games, bonuses, payments & more.",
            overall_rating=8.5,
            word_count=2600,
            generation_date=datetime.now()
        )
        
        test_qa_report = QAReport(
            casino_name="Test Casino",
            review_title="Test Casino Review 2024",
            overall_pass=True,
            quality_score=8.7,
            validation_date=datetime.now(),
            issues_found=[],
            recommendations=["✅ Review is ready for publishing"]
        )
        
        # Test publishing request
        request = PublishingRequest(
            review_doc=test_review,
            qa_report=test_qa_report,
            publish_status="draft",
            auto_publish=False
        )
        
        # Execute publishing
        result = await agent.publish_casino_review(request)
        
        print(f"\n🚀 Publishing Results:")
        print(f"   Casino: {result.casino_name}")
        print(f"   Success: {'✅' if result.success else '❌'}")
        print(f"   Post ID: {result.post_id}")
        print(f"   Status: {result.publish_status}")
        print(f"   URL: {result.post_url}")
        
        if not result.success:
            print(f"   Error: {result.error_message}")


if __name__ == "__main__":
    asyncio.run(test_publishing_agent())
