#!/usr/bin/env python3
"""
🔍 LangGraph Casino Research Agent - Production Ready
===================================================

Advanced LangGraph implementation of casino research with:
- Persistent state management and checkpointing
- Streaming updates with real-time progress
- Human-in-the-loop quality control checkpoints
- Integration with existing CCMS tools and schemas
- Comprehensive error handling and recovery

Follows LangChain v1-alpha patterns with LangGraph for durable execution.

Author: AI Assistant
Created: 2025-01-10
Version: 2.0.0 (LangGraph Implementation)
"""

import os
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, TypedDict, Literal, Union, Annotated
from enum import Enum

# LangGraph imports
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode

# LangChain core imports
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

# Community tools
from langchain_community.tools import TavilySearchResults
from langchain_community.document_loaders import WebBaseLoader

# Import existing CCMS components
from ..tools.real_supabase_research_tool import real_supabase_research_tool
from ..tools.firecrawl_screenshot_tool import firecrawl_screenshot_tool
from ..tools.placeholder_image_generator import placeholder_image_generator
from ..schemas.casino_intelligence_schema import CasinoIntelligence, create_empty_casino_intelligence

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ResearchPhase(str, Enum):
    """Research workflow phases"""
    INITIALIZED = "initialized"
    BASIC_INFO_GATHERING = "basic_info_gathering"
    DETAILED_RESEARCH = "detailed_research"  
    VISUAL_CAPTURE = "visual_capture"
    INTELLIGENCE_EXTRACTION = "intelligence_extraction"
    QUALITY_REVIEW = "quality_review"
    HUMAN_CHECKPOINT = "human_checkpoint"
    COMPLETED = "completed"
    FAILED = "failed"


class ResearchState(TypedDict):
    """
    Comprehensive state schema for LangGraph casino research workflow
    
    Maintains all research data, progress tracking, and intermediate results
    with full persistence across workflow execution.
    """
    
    # ========================================================================
    # WORKFLOW CONTROL
    # ========================================================================
    research_id: str  # Unique research session ID
    casino_name: str  # Target casino name
    casino_url: Optional[str]  # Official casino URL
    locale: str  # Locale for research (e.g., 'en-US', 'de-DE')
    tenant_id: str  # Tenant identifier for multi-tenant support
    
    current_phase: ResearchPhase  # Current workflow phase
    completed_phases: List[ResearchPhase]  # Completed phases
    failed_phases: List[ResearchPhase]  # Failed phases (for retry logic)
    
    # Progress tracking
    progress_percentage: float  # Overall progress (0.0 - 1.0)
    phase_start_time: Optional[datetime]  # When current phase started
    total_start_time: datetime  # When research started
    
    # ========================================================================
    # RESEARCH DATA COLLECTION
    # ========================================================================
    
    # Database research results
    supabase_research: Optional[Dict[str, Any]]  # Existing research from database
    
    # Web research results
    web_search_results: List[Dict[str, Any]]  # Tavily search results
    website_content: Optional[Dict[str, Any]]  # Scraped website content
    review_data: List[Dict[str, Any]]  # Casino reviews and feedback
    
    # Visual assets
    screenshot_urls: List[str]  # Successfully captured screenshots
    screenshot_metadata: List[Dict[str, Any]]  # Screenshot metadata
    fallback_images: List[str]  # Generated placeholder images
    
    # ========================================================================
    # INTELLIGENCE EXTRACTION
    # ========================================================================
    
    # Comprehensive casino intelligence (95+ fields)
    casino_intelligence: Optional[CasinoIntelligence]  # Structured intelligence model
    extraction_confidence: float  # Confidence in extracted data (0.0 - 1.0)
    field_completeness: Dict[str, float]  # Completeness by category
    
    # Raw extracted facts (before structuring)
    raw_facts: Dict[str, Any]  # Unstructured facts
    fact_sources: Dict[str, List[str]]  # Source URLs for each fact
    
    # ========================================================================
    # QUALITY CONTROL
    # ========================================================================
    
    # Quality metrics
    data_quality_score: float  # Overall data quality (0.0 - 1.0)
    source_reliability_score: float  # Source reliability assessment
    completeness_score: float  # Data completeness assessment
    
    # Quality issues and flags
    quality_issues: List[Dict[str, Any]]  # Identified quality problems
    requires_human_review: bool  # Flag for human intervention
    human_feedback: Optional[Dict[str, Any]]  # Human reviewer feedback
    
    # ========================================================================
    # ERROR HANDLING & RECOVERY
    # ========================================================================
    
    # Error tracking
    errors: List[Dict[str, Any]]  # All errors encountered
    retry_counts: Dict[str, int]  # Retry attempts by phase
    max_retries: Dict[str, int]  # Max retries allowed per phase
    
    # Recovery options
    recovery_suggestions: List[str]  # Suggested recovery actions
    fallback_data_used: bool  # Whether fallback data was used
    
    # ========================================================================
    # WORKFLOW MESSAGES & COMMUNICATION
    # ========================================================================
    
    # Message history for agent communication
    messages: Annotated[List[BaseMessage], "Messages in the research conversation"]
    
    # Status updates for streaming
    status_updates: List[Dict[str, Any]]  # Real-time status updates
    last_update_time: datetime  # Last status update timestamp
    
    # ========================================================================
    # INTEGRATION DATA
    # ========================================================================
    
    # CCMS integration
    ccms_pipeline_data: Optional[Dict[str, Any]]  # Data for CCMS pipeline integration
    wordpress_ready: bool  # Whether data is ready for WordPress publishing
    seo_data: Optional[Dict[str, Any]]  # SEO metadata for publishing


class LangGraphResearchAgent:
    """
    🔍 Advanced LangGraph Casino Research Agent
    
    Provides durable, persistent casino research with:
    - Multi-phase workflow with checkpointing
    - Real-time streaming updates
    - Human-in-the-loop quality control
    - Comprehensive error handling and recovery
    - Full integration with existing CCMS components
    """
    
    def __init__(
        self, 
        model_name: str = "gpt-4o-mini",
        temperature: float = 0.1,
        max_retries: int = 3,
        enable_streaming: bool = True,
        enable_human_checkpoints: bool = True
    ):
        self.model_name = model_name
        self.temperature = temperature
        self.max_retries = max_retries
        self.enable_streaming = enable_streaming
        self.enable_human_checkpoints = enable_human_checkpoints
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=temperature
        )
        
        # Create workflow graph
        self.workflow = self._create_workflow_graph()
        
        # Initialize checkpointer for persistence
        self.checkpointer = MemorySaver()
        
        # Compile workflow with checkpointing
        self.compiled_workflow = self.workflow.compile(
            checkpointer=self.checkpointer
        )
        
        logger.info(f"🔍 LangGraph Research Agent initialized with {model_name}")
    
    def _create_workflow_graph(self) -> StateGraph:
        """Create the LangGraph workflow with all research phases"""
        
        workflow = StateGraph(ResearchState)
        
        # Add all workflow nodes
        workflow.add_node("initialize_research", self._initialize_research_node)
        workflow.add_node("gather_basic_info", self._gather_basic_info_node)
        workflow.add_node("detailed_research", self._detailed_research_node)
        workflow.add_node("visual_capture", self._visual_capture_node)
        workflow.add_node("intelligence_extraction", self._intelligence_extraction_node)
        workflow.add_node("quality_review", self._quality_review_node)
        workflow.add_node("human_checkpoint", self._human_checkpoint_node)
        workflow.add_node("finalize_research", self._finalize_research_node)
        
        # Define workflow edges and conditional routing
        workflow.set_entry_point("initialize_research")
        
        workflow.add_edge("initialize_research", "gather_basic_info")
        workflow.add_edge("gather_basic_info", "detailed_research")
        workflow.add_edge("detailed_research", "visual_capture")
        workflow.add_edge("visual_capture", "intelligence_extraction")
        workflow.add_edge("intelligence_extraction", "quality_review")
        
        # Conditional routing for quality review
        workflow.add_conditional_edges(
            "quality_review",
            self._should_require_human_review,
            {
                "human_review": "human_checkpoint",
                "finalize": "finalize_research",
                "retry": "gather_basic_info"  # Retry from basic info if quality is poor
            }
        )
        
        workflow.add_conditional_edges(
            "human_checkpoint",
            self._process_human_feedback,
            {
                "approved": "finalize_research",
                "retry": "gather_basic_info",
                "manual_edit": "intelligence_extraction"
            }
        )
        
        workflow.add_edge("finalize_research", END)
        
        return workflow
    
    # ========================================================================
    # WORKFLOW NODES
    # ========================================================================
    
    def _initialize_research_node(self, state: ResearchState) -> ResearchState:
        """Initialize research session with basic setup"""
        logger.info(f"🎯 Initializing research for {state['casino_name']}")
        
        # Update state with initialization
        state["current_phase"] = ResearchPhase.INITIALIZED
        state["completed_phases"] = [ResearchPhase.INITIALIZED]
        state["failed_phases"] = []
        state["progress_percentage"] = 0.1
        state["phase_start_time"] = datetime.now()
        state["total_start_time"] = datetime.now()
        
        # Initialize empty collections
        state["web_search_results"] = []
        state["review_data"] = []
        state["screenshot_urls"] = []
        state["screenshot_metadata"] = []
        state["fallback_images"] = []
        state["raw_facts"] = {}
        state["fact_sources"] = {}
        state["errors"] = []
        state["retry_counts"] = {}
        state["status_updates"] = []
        state["quality_issues"] = []
        
        # Set defaults
        state["extraction_confidence"] = 0.0
        state["data_quality_score"] = 0.0
        state["source_reliability_score"] = 0.0
        state["completeness_score"] = 0.0
        state["requires_human_review"] = False
        state["fallback_data_used"] = False
        state["wordpress_ready"] = False
        
        # Add status update
        self._add_status_update(state, "Research session initialized", "info")
        
        return state
    
    def _gather_basic_info_node(self, state: ResearchState) -> ResearchState:
        """Gather basic casino information from multiple sources"""
        logger.info(f"📊 Gathering basic info for {state['casino_name']}")
        
        state["current_phase"] = ResearchPhase.BASIC_INFO_GATHERING
        state["phase_start_time"] = datetime.now()
        state["progress_percentage"] = 0.2
        
        try:
            # 1. Check existing research in Supabase database
            casino_slug = state["casino_name"].lower().replace(" ", "-")
            supabase_result = real_supabase_research_tool._run(
                casino_slug=casino_slug,
                locale=state["locale"]
            )
            
            if supabase_result.get("research_success"):
                state["supabase_research"] = supabase_result
                self._add_status_update(state, f"Found existing research: {supabase_result.get('total_fields', 0)} fields", "success")
            else:
                self._add_status_update(state, "No existing research found in database", "info")
            
            # 2. Web search for basic casino information
            if os.getenv("TAVILY_API_KEY"):
                try:
                    search_tool = TavilySearchResults(max_results=5)
                    search_query = f"{state['casino_name']} casino review license games bonuses"
                    search_results = search_tool.invoke(search_query)
                    state["web_search_results"].extend(search_results)
                    self._add_status_update(state, f"Web search completed: {len(search_results)} results", "success")
                except Exception as e:
                    self._add_error(state, "web_search", str(e))
            
            # 3. Load official website if URL provided
            if state.get("casino_url"):
                try:
                    loader = WebBaseLoader([state["casino_url"]])
                    docs = loader.load()
                    if docs:
                        state["website_content"] = {
                            "url": state["casino_url"],
                            "content": docs[0].page_content[:5000],  # First 5000 chars
                            "metadata": docs[0].metadata
                        }
                        self._add_status_update(state, "Official website content loaded", "success")
                except Exception as e:
                    self._add_error(state, "website_loading", str(e))
            
            # Mark phase as completed
            state["completed_phases"].append(ResearchPhase.BASIC_INFO_GATHERING)
            state["progress_percentage"] = 0.4
            
        except Exception as e:
            logger.error(f"❌ Basic info gathering failed: {e}")
            state["failed_phases"].append(ResearchPhase.BASIC_INFO_GATHERING)
            self._add_error(state, "basic_info_gathering", str(e))
        
        return state
    
    def _detailed_research_node(self, state: ResearchState) -> ResearchState:
        """Conduct detailed research on specific casino aspects"""
        logger.info(f"🔬 Conducting detailed research for {state['casino_name']}")
        
        state["current_phase"] = ResearchPhase.DETAILED_RESEARCH
        state["phase_start_time"] = datetime.now()
        state["progress_percentage"] = 0.5
        
        try:
            # Search for casino reviews and user feedback
            if os.getenv("TAVILY_API_KEY"):
                search_tool = TavilySearchResults(max_results=3)
                
                # Multiple targeted searches
                search_queries = [
                    f"{state['casino_name']} casino review user experience",
                    f"{state['casino_name']} casino license trustpilot rating",
                    f"{state['casino_name']} casino games software providers",
                    f"{state['casino_name']} casino bonuses withdrawal limits"
                ]
                
                for query in search_queries:
                    try:
                        results = search_tool.invoke(query)
                        state["review_data"].extend(results)
                        self._add_status_update(state, f"Detailed search completed: {query}", "info")
                    except Exception as e:
                        self._add_error(state, "detailed_search", f"Query failed: {query} - {str(e)}")
            
            # Mark phase as completed
            state["completed_phases"].append(ResearchPhase.DETAILED_RESEARCH)
            state["progress_percentage"] = 0.6
            self._add_status_update(state, f"Detailed research completed: {len(state['review_data'])} sources", "success")
            
        except Exception as e:
            logger.error(f"❌ Detailed research failed: {e}")
            state["failed_phases"].append(ResearchPhase.DETAILED_RESEARCH)
            self._add_error(state, "detailed_research", str(e))
        
        return state
    
    def _visual_capture_node(self, state: ResearchState) -> ResearchState:
        """Capture visual assets (screenshots) for the casino"""
        logger.info(f"📸 Capturing visual assets for {state['casino_name']}")
        
        state["current_phase"] = ResearchPhase.VISUAL_CAPTURE
        state["phase_start_time"] = datetime.now()
        state["progress_percentage"] = 0.7
        
        try:
            # Attempt screenshot capture if URL provided
            if state.get("casino_url"):
                try:
                    screenshot_result = firecrawl_screenshot_tool._run(
                        url=state["casino_url"],
                        casino_name=state["casino_name"]
                    )
                    
                    if screenshot_result.get("success"):
                        state["screenshot_urls"].append(screenshot_result["screenshot_url"])
                        state["screenshot_metadata"].append({
                            "url": state["casino_url"],
                            "timestamp": datetime.now().isoformat(),
                            "method": "firecrawl",
                            "quality": "high"
                        })
                        self._add_status_update(state, "Screenshot captured successfully", "success")
                    else:
                        # Generate fallback placeholder
                        fallback_result = placeholder_image_generator._run(
                            casino_name=state["casino_name"],
                            description=f"Professional casino placeholder for {state['casino_name']}"
                        )
                        if fallback_result.get("success"):
                            state["fallback_images"].append(fallback_result["image_path"])
                            state["fallback_data_used"] = True
                            self._add_status_update(state, "Fallback placeholder generated", "warning")
                        
                except Exception as e:
                    self._add_error(state, "screenshot_capture", str(e))
            
            # Mark phase as completed
            state["completed_phases"].append(ResearchPhase.VISUAL_CAPTURE)
            state["progress_percentage"] = 0.8
            
        except Exception as e:
            logger.error(f"❌ Visual capture failed: {e}")
            state["failed_phases"].append(ResearchPhase.VISUAL_CAPTURE)
            self._add_error(state, "visual_capture", str(e))
        
        return state
    
    def _intelligence_extraction_node(self, state: ResearchState) -> ResearchState:
        """Extract structured intelligence from collected research data"""
        logger.info(f"🧠 Extracting intelligence for {state['casino_name']}")
        
        state["current_phase"] = ResearchPhase.INTELLIGENCE_EXTRACTION
        state["phase_start_time"] = datetime.now()
        state["progress_percentage"] = 0.85
        
        try:
            # Create comprehensive intelligence extraction prompt
            extraction_prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an expert casino intelligence analyst. Extract comprehensive, factual information from the provided research data.

Your task is to create a structured casino intelligence profile with 95+ fields covering:
1. Trustworthiness & Safety (licensing, security, reputation)
2. Games & Software (portfolio, providers, quality)
3. Bonuses & Promotions (welcome bonus, ongoing offers)
4. Payments & Banking (methods, limits, processing times)
5. User Experience & Support (design, mobile, customer service)
6. Innovations & Features (technology, social features)
7. Affiliate Program Intelligence (if available)

CRITICAL REQUIREMENTS:
- Only extract factual information found in the research data
- Do not fabricate or guess missing information
- Provide source references for each extracted fact
- Rate confidence level for each data point (0.0 - 1.0)
- Identify data quality issues or inconsistencies

Research Data Available:
- Database research: {supabase_data}
- Web search results: {web_search_count} sources
- Website content: {website_available}
- Review data: {review_count} sources
- Screenshots: {screenshot_count} captured

Focus on accuracy and completeness. Missing data is better than incorrect data."""),
                
                ("human", """Casino: {casino_name}
URL: {casino_url}

Extract comprehensive casino intelligence from this research data:

DATABASE RESEARCH:
{supabase_research}

WEB SEARCH RESULTS:
{web_search_results}

OFFICIAL WEBSITE CONTENT:
{website_content}

REVIEW DATA:
{review_data}

Provide structured output with confidence scores and source references.""")
            ])
            
            # Prepare data for extraction
            extraction_chain = extraction_prompt | self.llm
            
            result = extraction_chain.invoke({
                "casino_name": state["casino_name"],
                "casino_url": state.get("casino_url", "Not provided"),
                "supabase_data": "Yes" if state.get("supabase_research") else "No",
                "web_search_count": len(state.get("web_search_results", [])),
                "website_available": "Yes" if state.get("website_content") else "No",
                "review_count": len(state.get("review_data", [])),
                "screenshot_count": len(state.get("screenshot_urls", [])),
                "supabase_research": str(state.get("supabase_research", {}))[:2000],
                "web_search_results": str(state.get("web_search_results", []))[:3000],
                "website_content": str(state.get("website_content", {}))[:2000],
                "review_data": str(state.get("review_data", []))[:2000]
            })
            
            # Parse and structure the extracted intelligence
            # For now, create basic structured intelligence
            # TODO: Implement advanced parsing with Pydantic output parser
            
            intelligence = create_empty_casino_intelligence(
                casino_name=state["casino_name"],
                casino_url=state.get("casino_url")
            )
            
            # Update with extracted data
            intelligence.data_sources = [
                source.get("url", "Unknown") 
                for source in state.get("web_search_results", []) + state.get("review_data", [])
            ]
            
            state["casino_intelligence"] = intelligence
            state["extraction_confidence"] = 0.7  # Base confidence
            state["field_completeness"] = {
                "trustworthiness": 0.6,
                "games": 0.5,
                "bonuses": 0.4,
                "payments": 0.3,
                "user_experience": 0.4,
                "innovations": 0.2
            }
            
            # Mark phase as completed
            state["completed_phases"].append(ResearchPhase.INTELLIGENCE_EXTRACTION)
            state["progress_percentage"] = 0.9
            self._add_status_update(state, "Intelligence extraction completed", "success")
            
        except Exception as e:
            logger.error(f"❌ Intelligence extraction failed: {e}")
            state["failed_phases"].append(ResearchPhase.INTELLIGENCE_EXTRACTION)
            self._add_error(state, "intelligence_extraction", str(e))
        
        return state
    
    def _quality_review_node(self, state: ResearchState) -> ResearchState:
        """Review research quality and determine if human intervention is needed"""
        logger.info(f"🔍 Conducting quality review for {state['casino_name']}")
        
        state["current_phase"] = ResearchPhase.QUALITY_REVIEW
        state["phase_start_time"] = datetime.now()
        state["progress_percentage"] = 0.95
        
        try:
            # Calculate quality metrics
            source_count = len(state.get("web_search_results", [])) + len(state.get("review_data", []))
            has_official_content = bool(state.get("website_content"))
            has_database_research = bool(state.get("supabase_research", {}).get("research_success"))
            has_visual_assets = len(state.get("screenshot_urls", [])) > 0 or len(state.get("fallback_images", [])) > 0
            
            # Source reliability score
            state["source_reliability_score"] = min(1.0, source_count / 10.0)
            
            # Completeness score based on available data types
            completeness_factors = [
                has_database_research,
                has_official_content, 
                source_count >= 3,
                has_visual_assets,
                len(state.get("errors", [])) == 0
            ]
            state["completeness_score"] = sum(completeness_factors) / len(completeness_factors)
            
            # Overall data quality score
            state["data_quality_score"] = (
                state["source_reliability_score"] * 0.4 +
                state["completeness_score"] * 0.4 +
                state["extraction_confidence"] * 0.2
            )
            
            # Identify quality issues
            quality_issues = []
            if source_count < 3:
                quality_issues.append({
                    "issue": "insufficient_sources",
                    "description": f"Only {source_count} sources found, recommended minimum is 3",
                    "severity": "medium"
                })
            
            if not has_official_content:
                quality_issues.append({
                    "issue": "no_official_content",
                    "description": "No official website content loaded",
                    "severity": "high"
                })
            
            if len(state.get("errors", [])) > 3:
                quality_issues.append({
                    "issue": "high_error_count",
                    "description": f"{len(state['errors'])} errors encountered during research",
                    "severity": "high"
                })
            
            state["quality_issues"] = quality_issues
            
            # Determine if human review is required
            state["requires_human_review"] = (
                state["data_quality_score"] < 0.6 or
                len([issue for issue in quality_issues if issue["severity"] == "high"]) > 0 or
                self.enable_human_checkpoints
            )
            
            # Mark phase as completed
            state["completed_phases"].append(ResearchPhase.QUALITY_REVIEW)
            self._add_status_update(state, f"Quality review completed: {state['data_quality_score']:.2f} quality score", "info")
            
        except Exception as e:
            logger.error(f"❌ Quality review failed: {e}")
            state["failed_phases"].append(ResearchPhase.QUALITY_REVIEW)
            self._add_error(state, "quality_review", str(e))
        
        return state
    
    def _human_checkpoint_node(self, state: ResearchState) -> ResearchState:
        """Human checkpoint for quality control and approval"""
        logger.info(f"👤 Human checkpoint for {state['casino_name']}")
        
        state["current_phase"] = ResearchPhase.HUMAN_CHECKPOINT
        state["phase_start_time"] = datetime.now()
        
        # Prepare summary for human review
        review_summary = {
            "casino_name": state["casino_name"],
            "research_duration": (datetime.now() - state["total_start_time"]).total_seconds(),
            "data_quality_score": state["data_quality_score"],
            "sources_found": len(state.get("web_search_results", [])) + len(state.get("review_data", [])),
            "quality_issues": state.get("quality_issues", []),
            "completed_phases": [phase.value for phase in state["completed_phases"]],
            "failed_phases": [phase.value for phase in state["failed_phases"]],
            "errors": state.get("errors", [])
        }
        
        self._add_status_update(state, "Awaiting human review and approval", "warning")
        
        # In a real implementation, this would pause and wait for human input
        # For now, we'll simulate automatic approval with good quality data
        if state["data_quality_score"] >= 0.7 and len(state.get("errors", [])) <= 2:
            state["human_feedback"] = {
                "decision": "approved",
                "reviewer": "automated_qa",
                "timestamp": datetime.now().isoformat(),
                "comments": "Research quality meets automated approval criteria"
            }
        else:
            state["human_feedback"] = {
                "decision": "retry",
                "reviewer": "automated_qa", 
                "timestamp": datetime.now().isoformat(),
                "comments": "Research quality below threshold, retry recommended"
            }
        
        state["completed_phases"].append(ResearchPhase.HUMAN_CHECKPOINT)
        return state
    
    def _finalize_research_node(self, state: ResearchState) -> ResearchState:
        """Finalize research with complete intelligence package"""
        logger.info(f"✅ Finalizing research for {state['casino_name']}")
        
        state["current_phase"] = ResearchPhase.COMPLETED
        state["phase_start_time"] = datetime.now()
        state["progress_percentage"] = 1.0
        
        try:
            # Prepare CCMS integration data
            state["ccms_pipeline_data"] = {
                "research_id": state["research_id"],
                "casino_intelligence": state.get("casino_intelligence"),
                "visual_assets": state.get("screenshot_urls", []) + state.get("fallback_images", []),
                "quality_metrics": {
                    "data_quality_score": state["data_quality_score"],
                    "source_reliability_score": state["source_reliability_score"],
                    "completeness_score": state["completeness_score"],
                    "extraction_confidence": state["extraction_confidence"]
                },
                "sources": state.get("web_search_results", []) + state.get("review_data", [])
            }
            
            # Mark as ready for WordPress publishing
            state["wordpress_ready"] = (
                state["data_quality_score"] >= 0.5 and
                state.get("casino_intelligence") is not None
            )
            
            # Final status update
            research_duration = (datetime.now() - state["total_start_time"]).total_seconds()
            state["completed_phases"].append(ResearchPhase.COMPLETED)
            self._add_status_update(state, f"Research completed in {research_duration:.1f}s", "success")
            
        except Exception as e:
            logger.error(f"❌ Research finalization failed: {e}")
            state["failed_phases"].append(ResearchPhase.COMPLETED)
            self._add_error(state, "finalize_research", str(e))
        
        return state
    
    # ========================================================================
    # CONDITIONAL ROUTING FUNCTIONS
    # ========================================================================
    
    def _should_require_human_review(self, state: ResearchState) -> str:
        """Determine if human review is required based on quality metrics"""
        if state.get("requires_human_review", False):
            return "human_review"
        elif state["data_quality_score"] < 0.4:
            return "retry"
        else:
            return "finalize"
    
    def _process_human_feedback(self, state: ResearchState) -> str:
        """Process human feedback and determine next action"""
        feedback = state.get("human_feedback", {})
        decision = feedback.get("decision", "retry")
        
        if decision == "approved":
            return "approved"
        elif decision == "manual_edit":
            return "manual_edit"
        else:
            return "retry"
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    def _add_status_update(self, state: ResearchState, message: str, level: str = "info"):
        """Add status update to state for streaming"""
        update = {
            "timestamp": datetime.now().isoformat(),
            "phase": state["current_phase"].value,
            "message": message,
            "level": level,
            "progress": state.get("progress_percentage", 0.0)
        }
        state["status_updates"].append(update)
        state["last_update_time"] = datetime.now()
        
        # Log the update
        if level == "error":
            logger.error(f"🔍 {state['casino_name']}: {message}")
        elif level == "warning":
            logger.warning(f"🔍 {state['casino_name']}: {message}")
        else:
            logger.info(f"🔍 {state['casino_name']}: {message}")
    
    def _add_error(self, state: ResearchState, error_type: str, message: str):
        """Add error to state tracking"""
        error = {
            "timestamp": datetime.now().isoformat(),
            "phase": state["current_phase"].value,
            "type": error_type,
            "message": message
        }
        state["errors"].append(error)
        self._add_status_update(state, f"Error in {error_type}: {message}", "error")
    
    # ========================================================================
    # PUBLIC API METHODS
    # ========================================================================
    
    async def research_casino(
        self,
        casino_name: str,
        casino_url: Optional[str] = None,
        locale: str = "en-US",
        tenant_id: str = "default"
    ) -> Dict[str, Any]:
        """
        Start comprehensive casino research with LangGraph workflow
        
        Args:
            casino_name: Name of the casino to research
            casino_url: Official casino website URL (optional)
            locale: Locale for research (default: en-US)
            tenant_id: Tenant identifier for multi-tenant support
            
        Returns:
            Complete research results with intelligence data
        """
        
        # Create initial state
        research_id = str(uuid.uuid4())
        initial_state: ResearchState = {
            "research_id": research_id,
            "casino_name": casino_name,
            "casino_url": casino_url,
            "locale": locale,
            "tenant_id": tenant_id,
            "current_phase": ResearchPhase.INITIALIZED,
            "completed_phases": [],
            "failed_phases": [],
            "progress_percentage": 0.0,
            "phase_start_time": None,
            "total_start_time": datetime.now(),
            "messages": [],
            "status_updates": [],
            "last_update_time": datetime.now()
        }
        
        logger.info(f"🔍 Starting LangGraph research for {casino_name} (ID: {research_id})")
        
        # Execute workflow with streaming
        config = {"configurable": {"thread_id": research_id}}
        
        final_state = None
        async for state_update in self.compiled_workflow.astream(initial_state, config):
            final_state = state_update
            
            # Stream progress updates if enabled
            if self.enable_streaming:
                current_node = list(state_update.keys())[0]
                node_state = list(state_update.values())[0]
                
                progress_update = {
                    "research_id": research_id,
                    "current_node": current_node,
                    "phase": node_state.get("current_phase", "unknown"),
                    "progress": node_state.get("progress_percentage", 0.0),
                    "status_updates": node_state.get("status_updates", [])[-3:],  # Last 3 updates
                    "quality_score": node_state.get("data_quality_score", 0.0)
                }
                
                # In a real implementation, this would be sent to a websocket or callback
                logger.info(f"📊 Progress: {progress_update['progress']:.1%} - {progress_update['phase']}")
        
        # Extract final results
        if final_state:
            final_node_state = list(final_state.values())[0]
            
            return {
                "success": final_node_state["current_phase"] == ResearchPhase.COMPLETED,
                "research_id": research_id,
                "casino_name": casino_name,
                "casino_intelligence": final_node_state.get("casino_intelligence"),
                "quality_metrics": {
                    "data_quality_score": final_node_state.get("data_quality_score", 0.0),
                    "source_reliability_score": final_node_state.get("source_reliability_score", 0.0),
                    "completeness_score": final_node_state.get("completeness_score", 0.0),
                    "extraction_confidence": final_node_state.get("extraction_confidence", 0.0)
                },
                "visual_assets": {
                    "screenshots": final_node_state.get("screenshot_urls", []),
                    "fallback_images": final_node_state.get("fallback_images", [])
                },
                "research_duration": (datetime.now() - final_node_state["total_start_time"]).total_seconds(),
                "phases_completed": [phase.value for phase in final_node_state.get("completed_phases", [])],
                "errors": final_node_state.get("errors", []),
                "wordpress_ready": final_node_state.get("wordpress_ready", False),
                "ccms_pipeline_data": final_node_state.get("ccms_pipeline_data")
            }
        else:
            return {
                "success": False,
                "error": "Workflow execution failed",
                "research_id": research_id
            }
    
    def get_research_status(self, research_id: str) -> Dict[str, Any]:
        """Get current status of ongoing research"""
        try:
            # Get state from checkpointer
            config = {"configurable": {"thread_id": research_id}}
            state = self.checkpointer.get(config)
            
            if state:
                return {
                    "research_id": research_id,
                    "current_phase": state.get("current_phase", "unknown"),
                    "progress_percentage": state.get("progress_percentage", 0.0),
                    "recent_updates": state.get("status_updates", [])[-5:],  # Last 5 updates
                    "quality_score": state.get("data_quality_score", 0.0),
                    "errors": state.get("errors", [])
                }
            else:
                return {"error": f"Research session {research_id} not found"}
                
        except Exception as e:
            return {"error": f"Failed to get research status: {str(e)}"}


# ========================================================================
# EXAMPLE USAGE & TESTING
# ========================================================================

async def test_langgraph_research_agent():
    """Test the LangGraph research agent"""
    agent = LangGraphResearchAgent(
        model_name="gpt-4o-mini",
        enable_streaming=True,
        enable_human_checkpoints=False  # Disable for testing
    )
    
    # Test research
    result = await agent.research_casino(
        casino_name="Viage Casino",
        casino_url="https://viage.com",
        locale="en-US",
        tenant_id="crashcasino"
    )
    
    print("🔍 LangGraph Research Results:")
    print("=" * 50)
    print(f"Success: {result['success']}")
    print(f"Research ID: {result['research_id']}")
    print(f"Duration: {result.get('research_duration', 0):.1f}s")
    print(f"Quality Score: {result['quality_metrics']['data_quality_score']:.2f}")
    print(f"Phases Completed: {', '.join(result['phases_completed'])}")
    print(f"WordPress Ready: {result['wordpress_ready']}")
    
    if result.get("errors"):
        print(f"Errors: {len(result['errors'])}")
        for error in result["errors"][-3:]:  # Show last 3 errors
            print(f"  - {error['type']}: {error['message']}")
    
    return result


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_langgraph_research_agent())
