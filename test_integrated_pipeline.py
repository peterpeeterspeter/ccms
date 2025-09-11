#!/usr/bin/env python3
"""
Integrated Casino Review Pipeline Test with LangGraph

This script tests the complete casino review workflow using LangGraph
with mock agents to verify the pipeline architecture and flow.
"""

import asyncio
import logging
import sys
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import mock agents
from mock_agents import (
    create_casino_research_agent,
    create_casino_screenshot_agent,
    create_casino_content_agent,
    create_casino_qa_agent,
    create_casino_publishing_agent
)

# Import schemas  
from schemas.casino_review import (
    CasinoReviewRequest,
    CasinoResearchPack,
    ScreenshotResult,
    CasinoReviewDoc,
    QAReport,
    PublishResult
)

# Import LangGraph components
try:
    from langgraph.graph import StateGraph, START, END
    from langgraph.graph.state import CompiledStateGraph
    from langgraph.checkpoint.memory import MemorySaver
    from typing_extensions import TypedDict
    LANGGRAPH_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  LangGraph not available: {e}")
    LANGGRAPH_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Pipeline State Definition
class CasinoReviewState(TypedDict):
    """State object for casino review pipeline"""
    # Input
    request: CasinoReviewRequest
    
    # Agent outputs
    research_pack: Optional[CasinoResearchPack]
    screenshots: Optional[List[ScreenshotResult]]
    review_doc: Optional[CasinoReviewDoc]
    qa_report: Optional[QAReport]
    publish_result: Optional[PublishResult]
    
    # Pipeline metadata
    current_step: str
    step_count: int
    start_time: datetime
    errors: List[str]
    warnings: List[str]

class CasinoReviewPipeline:
    """LangGraph-based casino review pipeline with mock agents"""
    
    def __init__(self):
        """Initialize pipeline with mock agents"""
        logger.info("🏗️  Initializing Casino Review Pipeline")
        
        # Create mock agents
        self.research_agent = create_casino_research_agent()
        self.screenshot_agent = create_casino_screenshot_agent()
        self.content_agent = create_casino_content_agent()
        self.qa_agent = create_casino_qa_agent()
        self.publishing_agent = create_casino_publishing_agent()
        
        # Build LangGraph workflow
        self.workflow = self._build_workflow()
        
        logger.info("✅ Pipeline initialization complete")
    
    def _build_workflow(self) -> CompiledStateGraph:
        """Build the LangGraph workflow"""
        if not LANGGRAPH_AVAILABLE:
            raise ImportError("LangGraph is required for pipeline execution")
        
        # Create state graph
        builder = StateGraph(CasinoReviewState)
        
        # Add nodes
        builder.add_node("research", self._research_node)
        builder.add_node("screenshot", self._screenshot_node)
        builder.add_node("content", self._content_node)
        builder.add_node("qa", self._qa_node)
        builder.add_node("publish", self._publish_node)
        
        # Define edges (workflow flow)
        builder.add_edge(START, "research")
        builder.add_edge("research", "screenshot")
        builder.add_edge("screenshot", "content")
        builder.add_edge("content", "qa")
        builder.add_conditional_edges(
            "qa",
            self._qa_decision,
            {
                "publish": "publish",
                "revise": "content",  # Loop back to content generation
                "reject": END
            }
        )
        builder.add_edge("publish", END)
        
        # Compile without checkpointing to avoid serialization issues
        # TODO: Enable checkpointing once serialization is fixed
        return builder.compile()
    
    async def _research_node(self, state: CasinoReviewState) -> CasinoReviewState:
        """Research node: Gather casino information"""
        logger.info("🔍 Executing research node")
        
        try:
            # Update state
            state["current_step"] = "research"
            state["step_count"] += 1
            
            # Execute research
            research_pack = await self.research_agent.research_casino(state["request"])
            state["research_pack"] = research_pack
            
            logger.info(f"✅ Research completed for {research_pack.casino_name}")
            return state
            
        except Exception as e:
            error_msg = f"Research failed: {str(e)}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
            return state
    
    async def _screenshot_node(self, state: CasinoReviewState) -> CasinoReviewState:
        """Screenshot node: Capture casino interface"""
        logger.info("📸 Executing screenshot node")
        
        try:
            # Update state
            state["current_step"] = "screenshot"
            state["step_count"] += 1
            
            # Execute screenshot capture
            screenshots = await self.screenshot_agent.capture_casino_screenshots(state["request"])
            state["screenshots"] = screenshots
            
            logger.info(f"✅ Captured {len(screenshots)} screenshots")
            return state
            
        except Exception as e:
            error_msg = f"Screenshot capture failed: {str(e)}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
            return state
    
    async def _content_node(self, state: CasinoReviewState) -> CasinoReviewState:
        """Content node: Generate review content"""
        logger.info("✍️  Executing content node")
        
        try:
            # Update state
            state["current_step"] = "content"
            state["step_count"] += 1
            
            # Execute content generation
            review_doc = await self.content_agent.generate_review_content(
                state["research_pack"],
                state["screenshots"]
            )
            state["review_doc"] = review_doc
            
            logger.info(f"✅ Generated review content: {review_doc.word_count} words")
            return state
            
        except Exception as e:
            error_msg = f"Content generation failed: {str(e)}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
            return state
    
    async def _qa_node(self, state: CasinoReviewState) -> CasinoReviewState:
        """QA node: Validate content quality"""
        logger.info("🔍 Executing QA node")
        
        try:
            # Update state
            state["current_step"] = "qa"
            state["step_count"] += 1
            
            # Execute QA validation
            qa_report = await self.qa_agent.validate_review(
                state["review_doc"],
                state["research_pack"],
                state["screenshots"]
            )
            state["qa_report"] = qa_report
            
            logger.info(f"✅ QA completed: {qa_report.recommendation}")
            return state
            
        except Exception as e:
            error_msg = f"QA validation failed: {str(e)}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
            return state
    
    def _qa_decision(self, state: CasinoReviewState) -> str:
        """QA decision logic"""
        if not state.get("qa_report"):
            return "reject"
        
        recommendation = state["qa_report"].recommendation
        
        if recommendation == "PUBLISH":
            return "publish"
        elif recommendation == "REVISE":
            return "revise"
        else:
            return "reject"
    
    async def _publish_node(self, state: CasinoReviewState) -> CasinoReviewState:
        """Publish node: Deploy to WordPress"""
        logger.info("🚀 Executing publish node")
        
        try:
            # Update state
            state["current_step"] = "publish"
            state["step_count"] += 1
            
            # Execute publishing
            publish_result = await self.publishing_agent.publish_review(
                state["review_doc"],
                state["qa_report"],
                state["screenshots"]
            )
            state["publish_result"] = publish_result
            
            logger.info(f"✅ Published to WordPress: {publish_result.post_url}")
            return state
            
        except Exception as e:
            error_msg = f"Publishing failed: {str(e)}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
            return state
    
    async def run_pipeline(self, casino_name: str, casino_url: str, tenant_id: str = "crashcasino") -> Dict[str, Any]:
        """Run the complete pipeline"""
        logger.info(f"🚀 Starting pipeline for {casino_name}")
        
        # Create initial state
        request = CasinoReviewRequest(
            casino_name=casino_name,
            casino_url=casino_url,
            tenant_id=tenant_id
        )
        
        initial_state = CasinoReviewState(
            request=request,
            research_pack=None,
            screenshots=None,
            review_doc=None,
            qa_report=None,
            publish_result=None,
            current_step="start",
            step_count=0,
            start_time=datetime.now(),
            errors=[],
            warnings=[]
        )
        
        # Run workflow
        config = {"configurable": {"thread_id": f"casino-review-{datetime.now().isoformat()}"}}
        
        try:
            final_state = await self.workflow.ainvoke(initial_state, config=config)
            
            # Calculate execution time
            execution_time = (datetime.now() - final_state["start_time"]).total_seconds()
            
            # Prepare result
            result = {
                "success": len(final_state["errors"]) == 0,
                "execution_time_seconds": execution_time,
                "steps_completed": final_state["step_count"],
                "final_step": final_state["current_step"],
                "errors": final_state["errors"],
                "warnings": final_state["warnings"],
                "outputs": {
                    "research_pack": final_state.get("research_pack"),
                    "screenshots": final_state.get("screenshots"),
                    "review_doc": final_state.get("review_doc"),
                    "qa_report": final_state.get("qa_report"),
                    "publish_result": final_state.get("publish_result")
                }
            }
            
            if result["success"]:
                logger.info(f"🎉 Pipeline completed successfully in {execution_time:.2f} seconds")
            else:
                logger.error(f"❌ Pipeline failed with {len(final_state['errors'])} errors")
            
            return result
            
        except Exception as e:
            logger.error(f"Pipeline execution failed: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }

async def main():
    """Test the integrated pipeline"""
    print("🏗️  Casino Review Pipeline Integration Test")
    print("=" * 50)
    
    if not LANGGRAPH_AVAILABLE:
        print("❌ LangGraph not available - install with: pip install langgraph")
        return
    
    try:
        # Initialize pipeline
        pipeline = CasinoReviewPipeline()
        
        # Test casino data
        test_cases = [
            {
                "casino_name": "Test Casino Elite",
                "casino_url": "https://test-casino-elite.com",
                "tenant_id": "crashcasino"
            },
            {
                "casino_name": "Mock Gaming Palace",
                "casino_url": "https://mock-gaming-palace.com", 
                "tenant_id": "crashcasino"
            }
        ]
        
        # Run test cases
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n📝 Test Case {i}: {test_case['casino_name']}")
            print("-" * 40)
            
            result = await pipeline.run_pipeline(**test_case)
            
            if result["success"]:
                print(f"✅ Success - {result['steps_completed']} steps in {result['execution_time_seconds']:.2f}s")
                
                # Show key outputs
                outputs = result["outputs"]
                if outputs.get("research_pack"):
                    research = outputs['research_pack']
                    print(f"   🔍 Research: {research.casino_name} (License: {research.license_type})")
                
                if outputs.get("screenshots"):
                    print(f"   📸 Screenshots: {len(outputs['screenshots'])} captured")
                
                if outputs.get("review_doc"):
                    print(f"   ✍️  Content: {outputs['review_doc'].word_count} words (Rating: {outputs['review_doc'].overall_rating})")
                
                if outputs.get("qa_report"):
                    print(f"   🔍 QA: {outputs['qa_report'].recommendation} (Score: {outputs['qa_report'].compliance_score})")
                
                if outputs.get("publish_result"):
                    print(f"   🚀 Published: Post ID {outputs['publish_result'].post_id}")
            
            else:
                print(f"❌ Failed: {len(result.get('errors', []))} errors")
                for error in result.get("errors", []):
                    print(f"   • {error}")
        
        print(f"\n🎉 Integration test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(main())
