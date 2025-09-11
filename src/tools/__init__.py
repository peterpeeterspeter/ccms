"""
Tool Orchestrator
=================

Coordinated access to all external tools for the casino review workflow.
Follows WARP.md principles: LangChain-native, adapters only, rate limiting.
"""

import asyncio
import logging
from typing import Dict, Optional, Any
from dataclasses import dataclass
import os

from .wordpress import WordPressClient, create_wordpress_client
from .firecrawl import FirecrawlClient, create_firecrawl_client, FallbackScreenshotClient
from .dataforseo import DataForSEOClient, create_dataforseo_client

logger = logging.getLogger(__name__)


@dataclass
class ToolConfig:
    """Configuration for all external tools"""
    
    # WordPress
    wordpress_base_url: str
    wordpress_username: str  
    wordpress_app_password: str
    
    # Firecrawl
    firecrawl_api_key: str
    
    # DataForSEO
    dataforseo_login: str
    dataforseo_password: str
    
    # Fallback screenshot services
    cf_browser_token: Optional[str] = None
    browserless_token: Optional[str] = None
    
    # Rate limiting and performance
    max_concurrent_requests: int = 3
    rate_limit_delay: float = 1.0
    
    @classmethod
    def from_env(cls) -> 'ToolConfig':
        """Create configuration from environment variables"""
        
        return cls(
            # WordPress
            wordpress_base_url=os.getenv("WORDPRESS_BASE_URL", "https://www.crashcasino.io"),
            wordpress_username=os.getenv("WORDPRESS_USERNAME"),
            wordpress_app_password=os.getenv("WORDPRESS_APP_PASSWORD"),
            
            # Firecrawl
            firecrawl_api_key=os.getenv("FIRECRAWL_API_KEY"),
            
            # DataForSEO
            dataforseo_login=os.getenv("DATAFORSEO_LOGIN"),
            dataforseo_password=os.getenv("DATAFORSEO_PASSWORD"),
            
            # Fallbacks
            cf_browser_token=os.getenv("CF_BROWSER_TOKEN"),
            browserless_token=os.getenv("BROWSERLESS_TOKEN"),
            
            # Performance
            max_concurrent_requests=int(os.getenv("MAX_CONCURRENT_REQUESTS", "3")),
            rate_limit_delay=float(os.getenv("RATE_LIMIT_DELAY", "1.0"))
        )


class ToolOrchestrator:
    """
    Central orchestrator for all external tools
    
    Provides:
    - Unified tool access with proper resource management
    - Rate limiting and concurrency control
    - Error handling and fallback mechanisms
    - Service health monitoring
    - LangChain-compatible tool wrapping
    """
    
    def __init__(self, config: ToolConfig):
        self.config = config
        self.clients = {}
        self._semaphore = asyncio.Semaphore(config.max_concurrent_requests)
        self._last_request_time = 0.0
        
        # Service health status
        self.service_health = {
            "wordpress": False,
            "firecrawl": False,
            "dataforseo": False,
            "fallback_screenshots": False
        }
    
    async def __aenter__(self):
        """Initialize all tool clients"""
        try:
            logger.info("Initializing tool orchestrator...")
            
            # Initialize WordPress client
            self.clients["wordpress"] = create_wordpress_client(
                base_url=self.config.wordpress_base_url,
                username=self.config.wordpress_username,
                app_password=self.config.wordpress_app_password
            )
            
            # Initialize Firecrawl client
            self.clients["firecrawl"] = create_firecrawl_client(
                api_key=self.config.firecrawl_api_key,
                wordpress_client=self.clients["wordpress"]
            )
            
            # Initialize DataForSEO client
            self.clients["dataforseo"] = create_dataforseo_client(
                login=self.config.dataforseo_login,
                password=self.config.dataforseo_password
            )
            
            # Initialize fallback screenshot client
            if self.config.cf_browser_token or self.config.browserless_token:
                self.clients["fallback_screenshots"] = FallbackScreenshotClient(
                    cf_token=self.config.cf_browser_token,
                    browserless_token=self.config.browserless_token
                )
            
            # Enter all client contexts
            for client_name, client in self.clients.items():
                if hasattr(client, "__aenter__"):
                    await client.__aenter__()
            
            # Health check all services
            await self._perform_health_checks()
            
            logger.info("✅ Tool orchestrator initialized successfully")
            return self
            
        except Exception as e:
            logger.error(f"Failed to initialize tool orchestrator: {str(e)}")
            raise
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup all tool clients"""
        
        logger.info("Shutting down tool orchestrator...")
        
        # Exit all client contexts
        for client_name, client in self.clients.items():
            try:
                if hasattr(client, "__aexit__"):
                    await client.__aexit__(exc_type, exc_val, exc_tb)
            except Exception as e:
                logger.warning(f"Error shutting down {client_name} client: {str(e)}")
        
        logger.info("Tool orchestrator shutdown complete")
    
    async def _perform_health_checks(self):
        """Check health of all external services"""
        
        logger.info("Performing service health checks...")
        
        # WordPress health check
        try:
            if await self.clients["wordpress"].test_connection():
                self.service_health["wordpress"] = True
                logger.info("✅ WordPress connection healthy")
            else:
                logger.warning("⚠️ WordPress connection unhealthy")
        except Exception as e:
            logger.error(f"❌ WordPress health check failed: {str(e)}")
        
        # Firecrawl health check
        try:
            if await self.clients["firecrawl"].test_connection():
                self.service_health["firecrawl"] = True
                logger.info("✅ Firecrawl connection healthy")
            else:
                logger.warning("⚠️ Firecrawl connection unhealthy")
        except Exception as e:
            logger.error(f"❌ Firecrawl health check failed: {str(e)}")
        
        # DataForSEO health check
        try:
            if await self.clients["dataforseo"].test_connection():
                self.service_health["dataforseo"] = True
                logger.info("✅ DataForSEO connection healthy")
            else:
                logger.warning("⚠️ DataForSEO connection unhealthy")
        except Exception as e:
            logger.error(f"❌ DataForSEO health check failed: {str(e)}")
        
        # Log overall health status
        healthy_services = sum(self.service_health.values())
        total_services = len(self.service_health)
        
        logger.info(f"Service health: {healthy_services}/{total_services} services healthy")
        
        if healthy_services == 0:
            raise Exception("No external services are available - cannot proceed")
    
    async def _rate_limit(self):
        """Enforce rate limiting between requests"""
        
        current_time = asyncio.get_event_loop().time()
        time_since_last = current_time - self._last_request_time
        
        if time_since_last < self.config.rate_limit_delay:
            wait_time = self.config.rate_limit_delay - time_since_last
            await asyncio.sleep(wait_time)
        
        self._last_request_time = asyncio.get_event_loop().time()
    
    # Public tool access methods
    
    @property
    def wordpress(self) -> WordPressClient:
        """Access WordPress client"""
        return self.clients["wordpress"]
    
    @property
    def firecrawl(self) -> FirecrawlClient:
        """Access Firecrawl client"""
        return self.clients["firecrawl"]
    
    @property
    def dataforseo(self) -> DataForSEOClient:
        """Access DataForSEO client"""
        return self.clients["dataforseo"]
    
    @property
    def fallback_screenshots(self) -> Optional[FallbackScreenshotClient]:
        """Access fallback screenshot client"""
        return self.clients.get("fallback_screenshots")
    
    # Orchestrated operations
    
    async def comprehensive_casino_research(self, 
                                          casino_name: str, 
                                          casino_url: str) -> Dict[str, Any]:
        """
        Perform comprehensive casino research using multiple tools
        
        Args:
            casino_name: Name of the casino
            casino_url: Casino website URL
            
        Returns:
            Dictionary containing all research data
        """
        
        async with self._semaphore:
            await self._rate_limit()
            
            logger.info(f"Starting comprehensive research for {casino_name}")
            
            research_tasks = []
            
            # DataForSEO research (if available)
            if self.service_health["dataforseo"]:
                research_tasks.append(
                    self.dataforseo.research_casino_comprehensive(casino_name, casino_url)
                )
            
            # Screenshot capture (if available)
            if self.service_health["firecrawl"]:
                research_tasks.append(
                    self.firecrawl.capture_casino_screenshots(casino_url)
                )
            elif self.service_health.get("fallback_screenshots"):
                # Use fallback screenshot service
                logger.info("Using fallback screenshot service")
                # Implementation would go here
            
            # Execute research tasks in parallel
            results = await asyncio.gather(*research_tasks, return_exceptions=True)
            
            # Parse results
            research_data = {}
            screenshot_data = []
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Research task {i} failed: {str(result)}")
                    continue
                
                if hasattr(result, "casino_name"):  # DataForSEO result
                    research_data = result
                elif isinstance(result, list):  # Screenshot results
                    screenshot_data = result
            
            return {
                "research_pack": research_data,
                "screenshots": screenshot_data,
                "service_health": self.service_health.copy()
            }
    
    async def publish_casino_review(self, 
                                  review_content: Dict[str, Any],
                                  media_attachments: Optional[list] = None) -> Dict[str, Any]:
        """
        Publish completed casino review to WordPress
        
        Args:
            review_content: Structured review content
            media_attachments: List of media items to attach
            
        Returns:
            Publishing result with post ID and URL
        """
        
        async with self._semaphore:
            await self._rate_limit()
            
            if not self.service_health["wordpress"]:
                raise Exception("WordPress service is not available for publishing")
            
            logger.info(f"Publishing casino review: {review_content.get('title', 'Untitled')}")
            
            # Create WordPress post
            result = await self.wordpress.create_casino_post(
                title=review_content["title"],
                content=review_content["content"],
                meta_data=review_content.get("meta", {}),
                featured_media=media_attachments[0]["media_id"] if media_attachments else None,
                status="draft"  # Default to draft for QA
            )
            
            if result and result.get("id"):
                logger.info(f"✅ Casino review published successfully: Post ID {result['id']}")
                return {
                    "success": True,
                    "post_id": result["id"],
                    "post_url": result.get("link", ""),
                    "edit_url": f"{self.config.wordpress_base_url}/wp-admin/post.php?post={result['id']}&action=edit"
                }
            else:
                raise Exception("WordPress post creation failed")
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get current status of all services"""
        
        return {
            "service_health": self.service_health.copy(),
            "configuration": {
                "wordpress_url": self.config.wordpress_base_url,
                "rate_limit_delay": self.config.rate_limit_delay,
                "max_concurrent": self.config.max_concurrent_requests
            },
            "available_tools": list(self.clients.keys())
        }


# Factory function for easy setup
async def create_tool_orchestrator(config: Optional[ToolConfig] = None) -> ToolOrchestrator:
    """
    Create and initialize tool orchestrator
    
    Args:
        config: Tool configuration (defaults to environment variables)
        
    Returns:
        Initialized ToolOrchestrator instance
    """
    
    if config is None:
        config = ToolConfig.from_env()
    
    orchestrator = ToolOrchestrator(config)
    
    # Return orchestrator - caller must use as async context manager
    return orchestrator


# Example usage
async def example_workflow():
    """Example of using the tool orchestrator for a complete workflow"""
    
    async with await create_tool_orchestrator() as tools:
        
        # Check service status
        status = tools.get_service_status()
        print(f"Service Status: {status['service_health']}")
        
        # Perform comprehensive research
        research_results = await tools.comprehensive_casino_research(
            casino_name="Bitstarz",
            casino_url="https://bitstarz.com"
        )
        
        print(f"Research completed:")
        print(f"  - Research pack: {bool(research_results['research_pack'])}")
        print(f"  - Screenshots: {len(research_results['screenshots'])}")
        
        # Example: Publish a review (would normally be generated by content agent)
        example_review = {
            "title": "Bitstarz Casino Review 2024",
            "content": "<p>Comprehensive review content...</p>",
            "meta": {
                "mt_casino_rating": "8.5",
                "mt_casino_license": "Curacao",
                "mt_casino_min_deposit": "20"
            }
        }
        
        # Publish review
        publish_result = await tools.publish_casino_review(
            review_content=example_review,
            media_attachments=research_results["screenshots"]
        )
        
        print(f"Publishing result: {publish_result}")


if __name__ == "__main__":
    asyncio.run(example_workflow())
