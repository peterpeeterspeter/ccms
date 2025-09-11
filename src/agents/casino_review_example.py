"""
Casino Review Agent System Usage Example
========================================

This example shows how to integrate the advanced multi-agent system with your existing
WordPress casino review site, following WARP.md LangChain-native principles.
"""

import asyncio
from typing import List, Dict
from langchain_core.runnables import RunnablePassthrough, RunnableLambda

from .casino_review_workflow import CasinoReviewWorkflow
from ..schemas.casino_review import CasinoReviewRequest, PublishResult
from ..tools.wordpress import WordPressClient
from ..tools.supabase_storage import SupabaseStorage
from ..tools.firecrawl import FirecrawlClient


class CasinoReviewOrchestrator:
    """
    Main orchestrator for automated casino review generation and publishing.
    Integrates with your existing WordPress MT Casino infrastructure.
    """
    
    def __init__(self):
        # Initialize tool adapters following WARP.md /src/tools/* pattern
        self.wordpress = WordPressClient(
            base_url="https://www.crashcasino.io",
            username="your_wp_user",
            password="your_app_password"  # WordPress Application Password
        )
        
        self.workflow = CasinoReviewWorkflow(tenant_id="crashcasino")
        
        # LangSmith tracing setup (optional but recommended per WARP.md)
        self._setup_langsmith_tracing()
    
    def _setup_langsmith_tracing(self):
        """Setup LangSmith for tracing agent workflows"""
        import os
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_PROJECT"] = "casino-review-agents"
    
    async def generate_casino_review(self, casino_url: str, **kwargs) -> PublishResult:
        """
        Main entry point for automated casino review generation
        
        This orchestrates the entire multi-agent workflow:
        1. Research Agent gathers comprehensive casino data
        2. Screenshot Agent captures compliant interface images
        3. Content Agent generates structured review following your patterns
        4. QA Agent validates content (BLOCKING gate per WARP.md)
        5. Publishing Agent publishes to WordPress with full MT Casino metadata
        
        Args:
            casino_url: Target casino URL (e.g., "https://bitstarz.com")
            **kwargs: Additional options like target_keywords, custom_instructions
            
        Returns:
            PublishResult with WordPress post details and success metrics
        """
        
        # Create structured request
        request = CasinoReviewRequest(
            casino_url=casino_url,
            tenant_id="crashcasino",
            **kwargs
        )
        
        try:
            # Execute the full multi-agent workflow
            result = await self.workflow.run_casino_review(casino_url)
            
            print(f"✅ Casino review published successfully!")
            print(f"   Post ID: {result.post_id}")
            print(f"   URL: {result.post_url}")
            print(f"   Custom fields populated: {result.custom_fields_populated}")
            print(f"   Media attachments: {len(result.additional_media_ids) + 1}")
            
            return result
            
        except Exception as e:
            print(f"❌ Casino review generation failed: {str(e)}")
            raise
    
    async def batch_generate_reviews(self, casino_urls: List[str]) -> List[PublishResult]:
        """
        Generate multiple casino reviews in batch with proper rate limiting
        
        Args:
            casino_urls: List of casino URLs to review
            
        Returns:
            List of PublishResult objects
        """
        
        results = []
        
        for i, casino_url in enumerate(casino_urls):
            try:
                print(f"🎰 Processing casino {i+1}/{len(casino_urls)}: {casino_url}")
                
                result = await self.generate_casino_review(casino_url)
                results.append(result)
                
                # Rate limiting to respect API quotas (per WARP.md cost guidelines)
                if i < len(casino_urls) - 1:
                    await asyncio.sleep(30)  # 30 second delay between reviews
                    
            except Exception as e:
                print(f"❌ Failed to process {casino_url}: {str(e)}")
                # Continue with next casino rather than failing entire batch
                continue
        
        print(f"📊 Batch complete: {len(results)}/{len(casino_urls)} reviews generated")
        return results
    
    async def update_existing_review(self, post_id: int, casino_url: str) -> PublishResult:
        """
        Update an existing casino review with fresh data
        
        This is useful for maintaining review accuracy over time by re-researching
        casinos and updating their reviews with current information.
        """
        
        # Generate fresh review content
        new_review_result = await self.workflow.run_casino_review(casino_url)
        
        # Update the existing post rather than creating new one
        try:
            updated_post = await self.wordpress.update_post(post_id, {
                "content": new_review_result.post_content,
                "modified": "now"  # Update modification timestamp
            })
            
            print(f"✅ Updated existing review (Post ID: {post_id})")
            return new_review_result
            
        except Exception as e:
            print(f"❌ Failed to update existing review: {str(e)}")
            raise


async def main_example():
    """
    Example usage of the casino review agent system
    """
    
    # Initialize the orchestrator
    orchestrator = CasinoReviewOrchestrator()
    
    # Example 1: Generate single casino review
    print("🚀 Generating single casino review...")
    
    result = await orchestrator.generate_casino_review(
        casino_url="https://bitstarz.com",
        target_keywords=["BitStarz review", "crypto casino", "Bitcoin gambling"],
        custom_instructions="Focus on crypto features and provably fair games"
    )
    
    print(f"Published review: {result.post_url}")
    
    # Example 2: Batch generate multiple reviews
    print("\\n🚀 Batch generating multiple casino reviews...")
    
    casino_urls = [
        "https://wildtornado.casino",
        "https://trustdice.win",
        "https://bitspincasino.com"
    ]
    
    batch_results = await orchestrator.batch_generate_reviews(casino_urls)
    
    for result in batch_results:
        print(f"  - {result.post_url}")
    
    # Example 3: Update existing review
    print("\\n🚀 Updating existing review with fresh data...")
    
    updated_result = await orchestrator.update_existing_review(
        post_id=51611,  # Napoleon Games Casino from your data
        casino_url="https://napoleon-games.be"
    )


class CasinoReviewAPI:
    """
    RESTful API wrapper for the casino review agent system
    
    This allows you to trigger casino review generation via HTTP requests,
    useful for integrating with n8n workflows or other automation systems.
    """
    
    def __init__(self):
        self.orchestrator = CasinoReviewOrchestrator()
    
    async def handle_review_request(self, request_data: Dict) -> Dict:
        """
        Handle API request for casino review generation
        
        Expected request format:
        {
            "casino_url": "https://example-casino.com",
            "tenant_id": "crashcasino",
            "target_keywords": ["casino review", "crypto gambling"],
            "publish_immediately": true
        }
        """
        
        try:
            result = await self.orchestrator.generate_casino_review(
                casino_url=request_data["casino_url"],
                **{k: v for k, v in request_data.items() if k != "casino_url"}
            )
            
            return {
                "success": True,
                "post_id": result.post_id,
                "post_url": str(result.post_url),
                "custom_fields_populated": result.custom_fields_populated,
                "taxonomies_assigned": result.taxonomies_assigned,
                "message": "Casino review generated and published successfully"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Casino review generation failed"
            }


# Integration with your existing WARP.md chains
def integrate_with_existing_chains():
    """
    Example of how to integrate the casino review agents with your existing
    LangChain-native workflows and n8n automations.
    """
    
    # Create composable chain that can be used in larger workflows
    casino_review_chain = (
        RunnablePassthrough()
        | RunnableLambda(lambda x: CasinoReviewOrchestrator().generate_casino_review(x["casino_url"]))
        | RunnableLambda(lambda result: {
            "post_id": result.post_id,
            "post_url": str(result.post_url),
            "success": result.success
        })
    )
    
    # This chain can now be composed with other chains
    # Example: research → review generation → social media promotion
    full_casino_pipeline = (
        RunnablePassthrough()
        | casino_review_chain
        | RunnableLambda(lambda x: promote_on_social_media(x["post_url"]))
    )
    
    return full_casino_pipeline


if __name__ == "__main__":
    # Run the example
    asyncio.run(main_example())
