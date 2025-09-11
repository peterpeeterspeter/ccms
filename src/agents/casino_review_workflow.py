"""
Casino Review Multi-Agent Workflow
=====================================

LangGraph-based multi-agent system for automated casino review generation and publishing.
Follows WARP.md LangChain-native principles with proper error handling and checkpointing.
Integrates all specialized agents with tool orchestrator.
"""

import asyncio
import logging
from typing import Dict, List, Optional, TypedDict, Annotated
from datetime import datetime

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.messages import HumanMessage, AIMessage
from pydantic import BaseModel, Field

from ..schemas.casino_review import (
    CasinoResearchPack, 
    CasinoReviewDoc, 
    ScreenshotResult,
    PublishResult,
    QAReport,
    CasinoResearchRequest,
    ScreenshotRequest,
    ContentGenerationRequest,
    QARequest,
    PublishingRequest
)
from ..tools import create_tool_orchestrator, ToolOrchestrator
from .research_agent import create_casino_research_agent
from .screenshot_agent import create_casino_screenshot_agent
from .content_agent import create_casino_content_agent
from .qa_agent import create_casino_qa_agent
from .publishing_agent import create_casino_publishing_agent

logger = logging.getLogger(__name__)


class CasinoReviewState(TypedDict):
    """Enhanced state management for casino review workflow"""
    # Input parameters
    casino_name: str
    casino_url: str
    tenant_id: str
    target_keywords: List[str]
    
    # Agent outputs
    research_pack: Optional[CasinoResearchPack]
    screenshots: List[ScreenshotResult]
    review_doc: Optional[CasinoReviewDoc]
    qa_report: Optional[QAReport]
    publish_result: Optional[PublishResult]
    
    # Workflow metadata
    current_step: str
    retry_count: int
    errors: List[str]
    start_time: datetime
    completion_time: Optional[datetime]


class CasinoReviewWorkflow:
    """
    Multi-agent casino review generation workflow using LangGraph
    
    Agents:
    1. Research Agent - DataForSEO-powered casino intelligence
    2. Screenshot Agent - Firecrawl-powered interface capture with compliance
    3. Content Agent - LLM-powered structured review generation (≥2,500 words)
    4. QA Agent - WARP.md compliance validation and quality assurance
    5. Publishing Agent - WordPress MT Casino post publishing
    
    Features:
    - Tool orchestrator for unified external service access
    - WARP.md compliance gates
    - Error handling and retry logic
    - Checkpointing for resume capability
    - Multi-tenant support
    """
    
    def __init__(self, tenant_id: str = "crashcasino", max_retries: int = 2):
        self.tenant_id = tenant_id
        self.max_retries = max_retries
        self.checkpointer = MemorySaver()  # Using MemorySaver for testing
        self.tools = None  # Will be initialized when workflow runs
        self.agents = {}   # Will hold agent instances
        
        self.graph = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow with all agents and transitions"""
        
        workflow = StateGraph(CasinoReviewState)
        
        # Add agent nodes
        workflow.add_node("research", self._research_agent)
        workflow.add_node("screenshot", self._screenshot_agent)  
        workflow.add_node("content", self._content_agent)
        workflow.add_node("qa", self._qa_agent)
        workflow.add_node("publish", self._publishing_agent)
        workflow.add_node("error_handler", self._error_handler)
        
        # Define workflow transitions
        workflow.set_entry_point("research")
        
        workflow.add_edge("research", "screenshot")
        workflow.add_edge("screenshot", "content")
        workflow.add_edge("content", "qa")
        
        # QA conditional routing
        workflow.add_conditional_edges(
            "qa",
            self._qa_decision,
            {
                "publish": "publish",
                "retry_content": "content", 
                "error": "error_handler"
            }
        )
        
        workflow.add_edge("publish", END)
        workflow.add_edge("error_handler", END)
        
        return workflow.compile(checkpointer=self.checkpointer)
    
    async def _initialize_agents(self, tools: ToolOrchestrator):
        """Initialize all agents with tool orchestrator"""
        self.agents = {
            "research": create_casino_research_agent(tools),
            "screenshot": create_casino_screenshot_agent(tools),
            "content": create_casino_content_agent(),
            "qa": create_casino_qa_agent(strict_compliance=True),
            "publishing": create_casino_publishing_agent(tools)
        }
        logger.info("All agents initialized with tool orchestrator")
    
    async def _research_agent(self, state: CasinoReviewState) -> CasinoReviewState:
        """Research Agent: DataForSEO-powered comprehensive casino intelligence"""
        try:
            state["current_step"] = "research"
            logger.info(f"🔍 Starting research for {state['casino_name']}")
            
            # Create research request
            request = CasinoResearchRequest(
                casino_name=state["casino_name"],
                casino_url=state["casino_url"],
                target_keywords=state.get("target_keywords", []),
                competitor_analysis=True,
                research_depth="comprehensive",
                tenant_id=state["tenant_id"]
            )
            
            # Execute research using specialized agent
            research_pack = await self.agents["research"].research_casino(request)
            
            state["research_pack"] = research_pack
            logger.info(f"✅ Research completed: {research_pack.research_accuracy:.1%} accuracy")
            
            return state
            
        except Exception as e:
            error_msg = f"Research failed: {str(e)}"
            state["errors"].append(error_msg)
            logger.error(error_msg)
            return state
    
    async def _screenshot_agent(self, state: CasinoReviewState) -> CasinoReviewState:
        """Screenshot Agent: Firecrawl-powered interface capture with WARP.md compliance"""
        try:
            state["current_step"] = "screenshot"
            logger.info(f"📸 Starting screenshot capture for {state['casino_name']}")
            
            # Create screenshot request
            request = ScreenshotRequest(
                casino_url=state["casino_url"],
                casino_name=state["casino_name"],
                compliance_strict=True,  # WARP.md requirement
                tenant_id=state["tenant_id"]
            )
            
            # Execute screenshot capture using specialized agent
            screenshots = await self.agents["screenshot"].capture_casino_screenshots(request)
            
            # Filter compliant screenshots only (WARP.md compliance gate)
            compliant_screenshots = [s for s in screenshots if s.compliance_pass]
            
            if not compliant_screenshots:
                raise Exception("No screenshots passed WARP.md compliance requirements")
            
            state["screenshots"] = compliant_screenshots
            logger.info(f"✅ Screenshot capture completed: {len(compliant_screenshots)} compliant images")
            
            return state
            
        except Exception as e:
            error_msg = f"Screenshot capture failed: {str(e)}"
            state["errors"].append(error_msg)
            logger.error(error_msg)
            return state
    
    async def _content_agent(self, state: CasinoReviewState) -> CasinoReviewState:
        """Content Agent: LLM-powered comprehensive review generation (≥2,500 words)"""
        try:
            state["current_step"] = "content"
            logger.info(f"✍️ Starting content generation for {state['casino_name']}")
            
            # Create content generation request
            request = ContentGenerationRequest(
                casino_name=state["casino_name"],
                casino_url=state["casino_url"],
                research_pack=state.get("research_pack"),
                screenshots=state.get("screenshots", []),
                target_keywords=state.get("target_keywords", []),
                content_style="professional",
                minimum_word_count=2500,  # WARP.md requirement
                tenant_id=state["tenant_id"]
            )
            
            # Execute content generation using specialized agent
            review_doc = await self.agents["content"].generate_casino_review(request)
            
            # Validate minimum word count (WARP.md requirement)
            if review_doc.word_count < 2500:
                raise Exception(f"Content too short: {review_doc.word_count} words (minimum 2,500)")
            
            state["review_doc"] = review_doc
            logger.info(f"✅ Content generation completed: {review_doc.word_count} words, {len(review_doc.sections)} sections")
            
            return state
            
        except Exception as e:
            error_msg = f"Content generation failed: {str(e)}"
            state["errors"].append(error_msg)
            logger.error(error_msg)
            return state
    
    async def _qa_agent(self, state: CasinoReviewState) -> CasinoReviewState:
        """QA Agent: Multi-layered compliance validation with WARP.md gates"""
        try:
            state["current_step"] = "qa"
            logger.info(f"🔍 Starting QA validation for {state['casino_name']}")
            
            # Create QA request
            request = QARequest(
                review_doc=state["review_doc"],
                research_pack=state.get("research_pack"),
                screenshots=state.get("screenshots", []),
                strict_compliance=True,  # WARP.md requirement
                tenant_id=state["tenant_id"]
            )
            
            # Execute QA validation using specialized agent
            qa_report = await self.agents["qa"].validate_review(request)
            
            state["qa_report"] = qa_report
            
            # WARP.md compliance gate - strict validation
            if not qa_report.overall_pass:
                logger.warning(f"❌ QA failed: {qa_report.failure_summary}")
                
                # Increment retry counter and attempt content regeneration
                state["retry_count"] = state.get("retry_count", 0) + 1
                
                if state["retry_count"] < 3:
                    logger.info(f"♻️ Retrying content generation (attempt {state['retry_count']}/3)")
                    # Include QA feedback for improvement
                    state["qa_feedback"] = qa_report.recommendations
                    return await self._content_agent(state)
                else:
                    error_msg = f"QA failed after {state['retry_count']} retries: {qa_report.failure_summary}"
                    state["errors"].append(error_msg)
                    logger.error(error_msg)
            else:
                logger.info(f"✅ QA validation passed: {qa_report.compliance_score:.1%} compliance")
            
            return state
            
        except Exception as e:
            error_msg = f"QA validation failed: {str(e)}"
            state["errors"].append(error_msg)
            logger.error(error_msg)
            return state
    
    async def _publishing_agent(self, state: CasinoReviewState) -> CasinoReviewState:
        """Publishing Agent: WordPress publication with comprehensive metadata and media"""
        try:
            state["current_step"] = "publishing"
            logger.info(f"📤 Starting WordPress publication for {state['casino_name']}")
            
            # Create publishing request
            request = PublishingRequest(
                review_doc=state["review_doc"],
                research_pack=state.get("research_pack"),
                screenshots=state.get("screenshots", []),
                qa_report=state["qa_report"],
                tenant_id=state["tenant_id"],
                post_status="draft"  # Start as draft for safety
            )
            
            # Execute publishing using specialized agent
            publish_result = await self.agents["publishing"].publish_casino_review(request)
            
            state["publish_result"] = publish_result
            state["current_step"] = "completed"
            
            logger.info(
                f"✅ Publishing completed: "
                f"Post ID {publish_result.post_id} at {publish_result.post_url}"
            )
            
            return state
            
        except Exception as e:
            error_msg = f"Publishing failed: {str(e)}"
            state["errors"].append(error_msg)
            logger.error(error_msg)
            return state
    
    def _qa_decision(self, state: CasinoReviewState) -> str:
        """QA conditional routing - BLOCKING gate for publication"""
        if not state["qa_report"]:
            return "error"
        
        qa_report = state["qa_report"]
        
        # Strict QA gates following WARP.md requirements  
        if not qa_report.overall_pass:
            # Check if we can retry or should error out
            if hasattr(qa_report, 'compliance_pass') and not qa_report.compliance_pass:
                return "error"  # Compliance failures block publication
            else:
                return "retry_content"  # Content quality issues can be retried
        
        return "publish"
    
    async def _error_handler(self, state: CasinoReviewState) -> CasinoReviewState:
        """Error handling with logging and recovery options"""
        state["current_step"] = "error"
        
        # Log structured errors following WARP.md requirements
        error_log = {
            "tenant_id": state["tenant_id"],
            "casino_url": state["casino_url"],
            "step": state["current_step"],
            "errors": state["errors"],
            "duration_ms": self._calculate_duration()
        }
        
        # Log to structured logging system (implement based on your setup)
        await self._log_structured_error(error_log)
        
        return state
    
    # Helper methods for agent operations
    async def _enhance_research_data(self, base_data: dict) -> dict:
        """Enhance base research with additional data sources"""
        # Implement multi-source data enhancement
        pass
    
    async def _image_compliance_guard(self, image_data: dict) -> dict:
        """Image compliance checking following WARP.md screenshot policy"""
        # Implement compliance checking (licensing, branding, dimensions)
        pass
    
    async def _generate_review_structure(self, data: dict) -> dict:
        """Generate review structure following your established content patterns"""
        # Implement structured content generation
        pass
    
    # Additional helper methods...
    
    async def run_casino_review(self, 
                                casino_name: str,
                                casino_url: str, 
                                target_keywords: List[str] = None) -> PublishResult:
        """
        Main entry point for casino review generation
        
        Args:
            casino_name: Name of the casino for review
            casino_url: Target casino URL for review  
            target_keywords: Optional target keywords for SEO optimization
            
        Returns:
            PublishResult with WordPress post details or error information
        """
        
        # Initialize tool orchestrator and agents for this run
        if not self.tools:
            self.tools = await create_tool_orchestrator()  # Uses .env by default
            await self._initialize_agents(self.tools)
            logger.info(f"Tool orchestrator and agents initialized for tenant: {self.tenant_id}")
        
        # Prepare initial state
        initial_state = CasinoReviewState(
            casino_name=casino_name,
            casino_url=casino_url,
            tenant_id=self.tenant_id,
            target_keywords=target_keywords or [],
            research_pack=None,
            screenshots=[],
            review_doc=None,
            qa_report=None,
            publish_result=None,
            errors=[],
            current_step="init",
            retry_count=0,
            start_time=datetime.now(),
            completion_time=None
        )
        
        try:
            # Execute the workflow with checkpointing
            thread_id = casino_url.replace('https://', '').replace('http://', '').replace('/', '_')
            config = {"configurable": {"thread_id": f"casino_review_{thread_id}"}}
            
            logger.info(f"🎰 Starting casino review workflow for {casino_name}")
            
            final_state = await self.graph.ainvoke(initial_state, config)
            final_state["completion_time"] = datetime.now()
            
            # Return publish result or raise error
            if final_state.get("publish_result"):
                logger.info(f"✅ Casino review workflow completed successfully for {casino_name}")
                return final_state["publish_result"]
            else:
                error_summary = "; ".join(final_state.get("errors", ["Unknown error"]))
                raise Exception(f"Casino review workflow failed for {casino_name}: {error_summary}")
                
        except Exception as e:
            logger.error(f"❌ Casino review workflow failed for {casino_name}: {str(e)}")
            raise
    
    async def _calculate_duration(self) -> int:
        """Calculate workflow duration in milliseconds"""
        # Implement duration calculation based on start_time
        return 0  # Placeholder
    
    async def _log_structured_error(self, error_log: dict):
        """Log structured errors following WARP.md requirements"""
        logger.error(f"Structured error log: {error_log}")
        # Implement your preferred structured logging (e.g., JSON to file, external service)


# Factory function for easy workflow creation
async def create_casino_review_workflow(
    tenant_id: str = "crashcasino", 
    max_retries: int = 2
) -> CasinoReviewWorkflow:
    """
    Factory function to create and initialize a casino review workflow
    
    Args:
        tenant_id: Tenant identifier for multi-tenancy
        max_retries: Maximum retry attempts for failed steps
        
    Returns:
        Initialized CasinoReviewWorkflow instance
    """
    workflow = CasinoReviewWorkflow(tenant_id=tenant_id, max_retries=max_retries)
    logger.info(f"Casino review workflow created for tenant: {tenant_id}")
    return workflow


# Main execution for testing/standalone usage
async def main():
    """
    Example workflow execution for testing
    """
    workflow = await create_casino_review_workflow(tenant_id="crashcasino")
    
    try:
        result = await workflow.run_casino_review(
            casino_name="Royal Vegas Casino",
            casino_url="https://www.royalvegascasino.com",
            target_keywords=["royal vegas", "online casino", "slots", "blackjack"]
        )
        
        print(f"Review published successfully!")
        print(f"Post ID: {result.post_id}")
        print(f"URL: {result.post_url}")
        print(f"Media uploaded: {len(result.media_ids)} images")
        
    except Exception as e:
        print(f"Workflow failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
