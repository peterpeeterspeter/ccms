"""
🎯 Enhanced Content Generation Workflow - PHASE 3 INTEGRATION
============================================================

Complete workflow orchestration integrating Phase 1, Phase 2, and Phase 3:
- Phase 1: Foundation (Retrieval, Research, Schemas)
- Phase 2: Content Generation (Narrative + QA Validation)
- Phase 3: Visual Content & Screenshot Pipeline

This enhanced workflow provides:
- Automated visual content capture and processing
- Visual compliance validation integrated with QA chain
- Enhanced narrative generation with visual context
- Complete end-to-end content creation with visual assets
- Multi-tenant visual content management

Author: AI Assistant & TaskMaster System
Created: 2025-08-24
Task: Enhanced workflow with Phase 3 visual integration
Version: 3.0.0
"""

from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
import logging
import asyncio

from langchain_core.runnables import (
    RunnablePassthrough, 
    RunnableLambda, 
    RunnableParallel,
    RunnableBranch,
    Runnable
)
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

# Import Phase 1 components
from src.chains.multi_tenant_retrieval_system import (
    MultiTenantRetrievalSystem,
    MultiTenantQuery,
    RetrievalResult
)
from src.integrations.supabase_vector_store import AgenticSupabaseVectorStore

# Import Phase 2 components
from src.chains.narrative_generation_lcel import (
    NarrativeGenerationChain,
    NarrativeGenerationInput,
    NarrativeGenerationOutput
)
from src.chains.qa_compliance_chain import (
    QAComplianceChain,
    QAValidationLevel,
    QAReport
)
from src.workflows.content_generation_workflow import (
    ContentGenerationRequest,
    ContentGenerationResult,
    WorkflowStatus
)

# Import Phase 3 components
from src.chains.visual_content_pipeline import (
    VisualContentPipeline,
    VisualContentRequest,
    VisualContentResult,
    VisualContentType
)

# Import schemas
from src.schemas.review_doc import ReviewDoc, TenantConfiguration, MediaAsset, MediaType
from src.schemas.casino_intelligence_schema import CasinoIntelligence


logger = logging.getLogger(__name__)


# ============================================================================
# ENHANCED WORKFLOW SCHEMAS
# ============================================================================

class EnhancedContentGenerationRequest(BaseModel):
    """Enhanced request with visual content requirements"""
    casino_name: str = Field(description="Casino name to review")
    tenant_config: TenantConfiguration = Field(description="Tenant configuration")
    query_context: str = Field(description="Content generation context")
    
    # Visual content requirements
    target_urls: List[str] = Field(default_factory=list, description="URLs for screenshot capture")
    visual_content_types: List[VisualContentType] = Field(
        default_factory=lambda: [VisualContentType.CASINO_LOBBY, VisualContentType.GAME_SCREENSHOTS],
        description="Types of visual content to capture"
    )
    visual_capture_settings: Dict[str, Any] = Field(default_factory=dict, description="Screenshot capture settings")
    
    # Existing content generation settings
    validation_level: QAValidationLevel = Field(default=QAValidationLevel.STANDARD, description="QA validation level")
    auto_publish_threshold: float = Field(default=8.0, description="Auto-publish quality threshold")
    max_improvement_iterations: int = Field(default=3, description="Maximum improvement iterations")
    
    # Processing options
    include_visual_content: bool = Field(default=True, description="Include visual content processing")
    visual_compliance_required: bool = Field(default=True, description="Require visual compliance validation")
    parallel_processing: bool = Field(default=True, description="Enable parallel visual and content processing")


class EnhancedContentGenerationResult(BaseModel):
    """Enhanced result with visual content integration"""
    # Core workflow results
    workflow_status: WorkflowStatus = Field(description="Overall workflow status")
    success: bool = Field(description="Overall success status")
    
    # Content generation results
    review_doc: Optional[ReviewDoc] = Field(default=None, description="Generated review document")
    qa_report: Optional[QAReport] = Field(default=None, description="QA validation report")
    final_quality_score: Optional[float] = Field(default=None, description="Final quality score")
    publish_approved: bool = Field(default=False, description="Publishing approval status")
    
    # Visual content results
    visual_content_result: Optional[VisualContentResult] = Field(default=None, description="Visual content processing result")
    visual_assets_count: int = Field(default=0, description="Number of processed visual assets")
    visual_compliance_approved: bool = Field(default=False, description="Visual compliance approval")
    
    # Enhanced metrics
    processing_stages: Dict[str, Any] = Field(default_factory=dict, description="Processing stage results")
    performance_metrics: Dict[str, Any] = Field(default_factory=dict, description="Performance timing metrics")
    improvement_iterations: int = Field(default=0, description="Number of improvement iterations")
    total_duration_ms: float = Field(default=0.0, description="Total processing duration")
    
    # Error handling
    warnings: List[str] = Field(default_factory=list, description="Processing warnings")
    error_details: Optional[str] = Field(default=None, description="Error details if failed")


# ============================================================================
# ENHANCED WORKFLOW ORCHESTRATION
# ============================================================================

class EnhancedContentGenerationWorkflow:
    """Complete content generation workflow with visual content integration"""
    
    def __init__(self,
                 retrieval_system: MultiTenantRetrievalSystem,
                 narrative_chain: Optional[NarrativeGenerationChain] = None,
                 qa_chain: Optional[QAComplianceChain] = None,
                 visual_pipeline: Optional[VisualContentPipeline] = None,
                 llm: Optional[ChatOpenAI] = None):
        
        self.retrieval_system = retrieval_system
        self.llm = llm or ChatOpenAI(model="gpt-4o", temperature=0.1)
        
        # Initialize chains with factory functions if not provided
        self.narrative_chain = narrative_chain or self._create_narrative_chain()
        self.qa_chain = qa_chain or self._create_qa_chain()
        self.visual_pipeline = visual_pipeline or self._create_visual_pipeline()
        
        # Build the complete workflow chain
        self.workflow_chain = self._build_enhanced_workflow_chain()
    
    def _create_narrative_chain(self) -> NarrativeGenerationChain:
        """Create narrative generation chain"""
        from src.chains.narrative_generation_lcel import create_narrative_generation_chain
        return create_narrative_generation_chain(
            retrieval_system=self.retrieval_system,
            llm_model="gpt-4o"
        )
    
    def _create_qa_chain(self) -> QAComplianceChain:
        """Create QA compliance chain"""
        from src.chains.qa_compliance_chain import create_qa_compliance_chain
        return create_qa_compliance_chain(llm_model="gpt-4o")
    
    def _create_visual_pipeline(self) -> VisualContentPipeline:
        """Create visual content pipeline"""
        from src.chains.visual_content_pipeline import create_visual_content_pipeline
        return create_visual_content_pipeline(llm_model="gpt-4o")
    
    def _build_enhanced_workflow_chain(self) -> Runnable:
        """Build the complete enhanced workflow LCEL chain"""
        
        return (
            # Initialize processing metadata
            RunnablePassthrough.assign(
                start_time=RunnableLambda(lambda x: datetime.now()),
                processing_stages=RunnableLambda(lambda x: {})
            )
            
            # Stage 1: Parallel Visual Content and Content Research
            | RunnableBranch(
                (
                    lambda x: x.get("include_visual_content", True) and x.get("parallel_processing", True),
                    RunnableParallel({
                        "visual_content": RunnableLambda(self._process_visual_content),
                        "content_research": RunnableLambda(self._process_content_research),
                        **RunnablePassthrough()
                    })
                ),
                # Sequential processing fallback
                RunnablePassthrough.assign(
                    content_research=RunnableLambda(self._process_content_research)
                ).assign(
                    visual_content=RunnableLambda(self._process_visual_content_conditional)
                )
            )
            
            # Stage 2: Narrative Generation with Visual Integration
            | RunnablePassthrough.assign(
                narrative_result=RunnableLambda(self._generate_narrative_with_visuals)
            )
            
            # Stage 3: Enhanced QA Validation (Content + Visual Compliance)
            | RunnablePassthrough.assign(
                qa_result=RunnableLambda(self._perform_enhanced_qa_validation)
            )
            
            # Stage 4: Publishing Decision with Visual Compliance
            | RunnablePassthrough.assign(
                publishing_decision=RunnableLambda(self._make_enhanced_publishing_decision)
            )
            
            # Stage 5: Final Result Assembly
            | RunnableLambda(self._create_enhanced_final_result)
        )
    
    def _process_visual_content(self, input_data: Dict[str, Any]) -> VisualContentResult:
        """Process visual content capture and validation"""
        try:
            if not input_data.get("include_visual_content", True):
                return VisualContentResult(
                    success=False,
                    casino_name=input_data["casino_name"],
                    error_details="Visual content processing disabled"
                )
            
            # Create visual content request
            visual_request = VisualContentRequest(
                casino_name=input_data["casino_name"],
                target_urls=input_data.get("target_urls", []),
                content_types=input_data.get("visual_content_types", [VisualContentType.CASINO_LOBBY]),
                tenant_config=input_data["tenant_config"],
                capture_settings=input_data.get("visual_capture_settings", {}),
                processing_requirements={}
            )
            
            # Process through visual pipeline
            result = self.visual_pipeline.process_visual_content(visual_request)
            
            # Update processing stages
            stages = input_data.get("processing_stages", {})
            stages["visual_content"] = {
                "completed": True,
                "timestamp": datetime.now().isoformat(),
                "assets_processed": len(result.assets),
                "success": result.success
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Visual content processing failed: {str(e)}")
            return VisualContentResult(
                success=False,
                casino_name=input_data.get("casino_name", "unknown"),
                error_details=str(e)
            )
    
    def _process_visual_content_conditional(self, input_data: Dict[str, Any]) -> Optional[VisualContentResult]:
        """Process visual content conditionally (for sequential mode)"""
        if input_data.get("include_visual_content", True):
            return self._process_visual_content(input_data)
        return None
    
    def _process_content_research(self, input_data: Dict[str, Any]) -> RetrievalResult:
        """Process content research and retrieval"""
        try:
            # Create multi-tenant query
            query = MultiTenantQuery(
                query=f"{input_data['casino_name']} {input_data['query_context']}",
                tenant_id=input_data["tenant_config"].tenant_id,
                brand=input_data["tenant_config"].brand_name,
                locale=input_data["tenant_config"].locale,
                voice=input_data["tenant_config"].voice_profile
            )
            
            # Perform retrieval
            result = self.retrieval_system.retrieve(query)
            
            # Update processing stages
            stages = input_data.get("processing_stages", {})
            stages["content_research"] = {
                "completed": True,
                "timestamp": datetime.now().isoformat(),
                "documents_retrieved": len(result.documents),
                "confidence": result.confidence_score
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Content research failed: {str(e)}")
            # Return empty result
            return RetrievalResult(
                query_text=input_data.get("query_context", ""),
                documents=[],
                confidence_score=0.0,
                metadata={"error": str(e)}
            )
    
    def _generate_narrative_with_visuals(self, input_data: Dict[str, Any]) -> NarrativeGenerationOutput:
        """Generate narrative content with visual integration"""
        try:
            # Prepare visual assets from visual processing result
            visual_assets = []
            visual_result = input_data.get("visual_content")
            
            if visual_result and visual_result.success:
                for asset in visual_result.assets:
                    media_asset = MediaAsset(
                        filename=asset.filename,
                        url=asset.storage_url,
                        type=MediaType.SCREENSHOT,
                        alt_text=asset.alt_text,
                        caption=asset.caption
                    )
                    visual_assets.append(media_asset)
            
            # Create narrative generation input
            narrative_input = NarrativeGenerationInput(
                casino_name=input_data["casino_name"],
                tenant_config=input_data["tenant_config"],
                query_context=input_data["query_context"],
                visual_assets=visual_assets,
                affiliate_metadata=input_data.get("affiliate_metadata", {})
            )
            
            # Generate narrative
            result = self.narrative_chain.generate_narrative(narrative_input)
            
            # Update processing stages
            stages = input_data.get("processing_stages", {})
            stages["narrative_generation"] = {
                "completed": True,
                "timestamp": datetime.now().isoformat(),
                "content_length": len(result.generated_content),
                "visual_assets_integrated": len(visual_assets)
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Narrative generation failed: {str(e)}")
            # Create fallback result
            return NarrativeGenerationOutput(
                generated_content=f"Error generating content for {input_data.get('casino_name', 'unknown')}: {str(e)}",
                review_doc=ReviewDoc(
                    casino_name=input_data.get("casino_name", "unknown"),
                    content="Error in content generation",
                    tenant_config=input_data["tenant_config"]
                ),
                retrieval_context=[],
                generation_metadata={"error": str(e)}
            )
    
    def _perform_enhanced_qa_validation(self, input_data: Dict[str, Any]) -> QAReport:
        """Perform enhanced QA validation including visual compliance"""
        try:
            narrative_result = input_data["narrative_result"]
            visual_result = input_data.get("visual_content")
            
            # Perform standard QA validation
            qa_result = self.qa_chain.validate_content(
                review_doc=narrative_result.review_doc,
                source_documents=narrative_result.retrieval_context,
                validation_level=input_data.get("validation_level", QAValidationLevel.STANDARD),
                tenant_config=input_data["tenant_config"]
            )
            
            # Enhance with visual compliance if available
            if visual_result and visual_result.success and input_data.get("visual_compliance_required", True):
                visual_compliance = visual_result.compliance_summary
                
                # Integrate visual compliance into QA report
                qa_result.visual_compliance_score = visual_compliance.get("overall_compliance_score", 0.0)
                qa_result.visual_assets_approved = visual_compliance.get("approved_count", 0)
                qa_result.visual_assets_total = visual_compliance.get("total_assets", 0)
                
                # Adjust overall score based on visual compliance
                if visual_compliance.get("overall_compliance_score", 0.0) < 0.6:
                    qa_result.overall_score = min(qa_result.overall_score, 7.0)  # Cap score if visual compliance poor
            
            # Update processing stages
            stages = input_data.get("processing_stages", {})
            stages["qa_validation"] = {
                "completed": True,
                "timestamp": datetime.now().isoformat(),
                "overall_score": qa_result.overall_score,
                "compliance_status": qa_result.compliance_status.value
            }
            
            return qa_result
            
        except Exception as e:
            logger.error(f"Enhanced QA validation failed: {str(e)}")
            # Return failed QA result
            from src.schemas.review_doc import ComplianceStatus
            return QAReport(
                overall_score=0.0,
                compliance_status=ComplianceStatus.FAILED,
                validation_details={"error": str(e)},
                recommendations=["Manual review required due to validation error"],
                created_at=datetime.now()
            )
    
    def _make_enhanced_publishing_decision(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Make publishing decision considering content and visual compliance"""
        try:
            qa_result = input_data["qa_result"]
            visual_result = input_data.get("visual_content")
            auto_publish_threshold = input_data.get("auto_publish_threshold", 8.0)
            
            # Base decision on QA score
            content_approved = qa_result.overall_score >= auto_publish_threshold
            
            # Consider visual compliance if required
            visual_approved = True
            if visual_result and input_data.get("visual_compliance_required", True):
                visual_compliance = visual_result.compliance_summary
                visual_approved = (
                    visual_compliance.get("overall_compliance_score", 0.0) >= 0.7 and
                    visual_compliance.get("rejected_count", 1) == 0
                )
            
            # Final publishing decision
            publish_approved = content_approved and visual_approved
            
            decision = {
                "publish_approved": publish_approved,
                "content_approved": content_approved,
                "visual_approved": visual_approved,
                "overall_score": qa_result.overall_score,
                "decision_timestamp": datetime.now().isoformat(),
                "decision_reasons": []
            }
            
            # Add decision reasoning
            if not content_approved:
                decision["decision_reasons"].append(f"Content quality score {qa_result.overall_score} below threshold {auto_publish_threshold}")
            
            if not visual_approved:
                decision["decision_reasons"].append("Visual content compliance requirements not met")
            
            if publish_approved:
                decision["decision_reasons"].append("All quality and compliance requirements met")
            
            return decision
            
        except Exception as e:
            logger.error(f"Publishing decision failed: {str(e)}")
            return {
                "publish_approved": False,
                "content_approved": False,
                "visual_approved": False,
                "overall_score": 0.0,
                "decision_timestamp": datetime.now().isoformat(),
                "decision_reasons": [f"Decision process failed: {str(e)}"]
            }
    
    def _create_enhanced_final_result(self, input_data: Dict[str, Any]) -> EnhancedContentGenerationResult:
        """Create the enhanced final workflow result"""
        try:
            start_time = input_data.get("start_time", datetime.now())
            end_time = datetime.now()
            duration_ms = (end_time - start_time).total_seconds() * 1000
            
            narrative_result = input_data.get("narrative_result")
            qa_result = input_data.get("qa_result")
            visual_result = input_data.get("visual_content")
            publishing_decision = input_data.get("publishing_decision", {})
            
            # Determine workflow status
            if publishing_decision.get("publish_approved", False):
                workflow_status = WorkflowStatus.COMPLETED
            elif qa_result and qa_result.overall_score > 0:
                workflow_status = WorkflowStatus.NEEDS_IMPROVEMENT
            else:
                workflow_status = WorkflowStatus.FAILED
            
            # Create enhanced result
            result = EnhancedContentGenerationResult(
                workflow_status=workflow_status,
                success=publishing_decision.get("publish_approved", False),
                review_doc=narrative_result.review_doc if narrative_result else None,
                qa_report=qa_result,
                final_quality_score=qa_result.overall_score if qa_result else None,
                publish_approved=publishing_decision.get("publish_approved", False),
                visual_content_result=visual_result,
                visual_assets_count=len(visual_result.assets) if visual_result else 0,
                visual_compliance_approved=publishing_decision.get("visual_approved", False),
                processing_stages=input_data.get("processing_stages", {}),
                performance_metrics={
                    "total_duration_ms": duration_ms,
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat()
                },
                improvement_iterations=0,  # TODO: Implement improvement loops
                total_duration_ms=duration_ms
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Final result creation failed: {str(e)}")
            return EnhancedContentGenerationResult(
                workflow_status=WorkflowStatus.FAILED,
                success=False,
                error_details=str(e),
                total_duration_ms=0.0
            )
    
    def execute_enhanced_workflow(self, request: EnhancedContentGenerationRequest) -> EnhancedContentGenerationResult:
        """Execute the complete enhanced workflow"""
        try:
            logger.info(f"Starting enhanced content generation workflow for {request.casino_name}")
            
            # Execute workflow chain
            result = self.workflow_chain.invoke(request.dict())
            
            logger.info(f"Enhanced workflow completed for {request.casino_name}: "
                       f"Status={result.workflow_status.value}, Success={result.success}")
            
            return result
            
        except Exception as e:
            logger.error(f"Enhanced workflow execution failed for {request.casino_name}: {str(e)}")
            return EnhancedContentGenerationResult(
                workflow_status=WorkflowStatus.FAILED,
                success=False,
                error_details=str(e)
            )


# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================

def create_enhanced_content_generation_workflow(
    vector_store: AgenticSupabaseVectorStore,
    llm_model: str = "gpt-4o",
    temperature: float = 0.1
) -> EnhancedContentGenerationWorkflow:
    """Factory function to create enhanced content generation workflow"""
    
    # Create retrieval system
    from src.chains.multi_tenant_retrieval_system import create_multi_tenant_retrieval_system
    retrieval_system = create_multi_tenant_retrieval_system(
        vector_store=vector_store,
        llm_model=llm_model
    )
    
    # Create LLM
    llm = ChatOpenAI(model=llm_model, temperature=temperature)
    
    return EnhancedContentGenerationWorkflow(
        retrieval_system=retrieval_system,
        llm=llm
    )


def create_enhanced_workflow_demo_scenarios() -> Dict[str, EnhancedContentGenerationRequest]:
    """Create demo scenarios for enhanced workflow testing"""
    
    base_tenant_config = TenantConfiguration(
        tenant_id="crashcasino",
        brand_name="CrashCasino",
        locale="en",
        voice_profile="professional-enthusiastic"
    )
    
    scenarios = {
        "visual_premium_review": EnhancedContentGenerationRequest(
            casino_name="Betway Casino",
            tenant_config=base_tenant_config,
            query_context="comprehensive review with visual showcase of game lobby, bonuses, and mobile experience",
            target_urls=[
                "https://betway.com",
                "https://betway.com/casino",
                "https://betway.com/promotions"
            ],
            visual_content_types=[
                VisualContentType.CASINO_LOBBY,
                VisualContentType.GAME_SCREENSHOTS,
                VisualContentType.BONUS_PROMOTIONS,
                VisualContentType.MOBILE_INTERFACE
            ],
            validation_level=QAValidationLevel.PREMIUM,
            auto_publish_threshold=8.5,
            include_visual_content=True,
            visual_compliance_required=True,
            parallel_processing=True
        ),
        
        "visual_mobile_focus": EnhancedContentGenerationRequest(
            casino_name="LeoVegas Casino",
            tenant_config=base_tenant_config,
            query_context="mobile-first review emphasizing app experience and mobile gaming",
            target_urls=[
                "https://leovegas.com",
                "https://mobile.leovegas.com"
            ],
            visual_content_types=[
                VisualContentType.MOBILE_INTERFACE,
                VisualContentType.CASINO_LOBBY,
                VisualContentType.GAME_SCREENSHOTS
            ],
            validation_level=QAValidationLevel.STANDARD,
            auto_publish_threshold=7.5,
            include_visual_content=True,
            visual_compliance_required=True,
            parallel_processing=True
        )
    }
    
    return scenarios