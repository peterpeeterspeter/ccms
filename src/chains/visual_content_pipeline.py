"""
🎨 Visual Content & Screenshot Pipeline - PHASE 3
================================================

Complete visual content management system for the Agentic Multi-Tenant RAG CMS:
- Automated screenshot capture with Browserbase/Playwright integration
- Visual content processing and quality assessment
- Compliance validation for images and media assets
- Integration with narrative generation and QA chains
- Multi-tenant visual content management

Author: AI Assistant & TaskMaster System
Created: 2025-08-24
Task: task-015 - Visual Content & Screenshot Pipeline (Phase 3)
Version: 1.0.0
"""

from typing import Dict, Any, List, Optional, Union, Tuple
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum
import logging
import asyncio
import base64
import hashlib
from pathlib import Path

from langchain_core.runnables import (
    RunnablePassthrough, 
    RunnableLambda, 
    RunnableParallel,
    RunnableBranch,
    Runnable
)
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser, PydanticOutputParser
from langchain_core.documents import Document

# Import our existing components
from src.schemas.review_doc import ReviewDoc, MediaAsset, TenantConfiguration
from src.chains.multi_tenant_retrieval_system import MultiTenantRetrievalSystem
from src.integrations.supabase_vector_store import AgenticSupabaseVectorStore

# Import existing screenshot tools
try:
    from src.integrations.browserbase_screenshot_toolkit import (
        BrowserbaseScreenshotToolkit,
        CasinoScreenshotConfig,
        CasinoScreenshotResult
    )
    BROWSERBASE_AVAILABLE = True
except ImportError:
    BROWSERBASE_AVAILABLE = False
    logging.warning("Browserbase screenshot toolkit not available")

try:
    from src.integrations.playwright_screenshot_engine import (
        ScreenshotService,
        ScreenshotResult,
        ScreenshotConfig
    )
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logging.warning("Playwright screenshot engine not available")


logger = logging.getLogger(__name__)


# ============================================================================
# VISUAL CONTENT SCHEMAS AND TYPES
# ============================================================================

class VisualContentType(str, Enum):
    """Types of visual content for processing"""
    CASINO_LOBBY = "casino_lobby"
    GAME_SCREENSHOTS = "game_screenshots"
    BONUS_PROMOTIONS = "bonus_promotions"
    MOBILE_INTERFACE = "mobile_interface"
    PAYMENT_METHODS = "payment_methods"
    REGISTRATION_FLOW = "registration_flow"
    CUSTOMER_SUPPORT = "customer_support"
    RESPONSIBLE_GAMING = "responsible_gaming"


class VisualQuality(str, Enum):
    """Visual content quality assessment"""
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    REJECTED = "rejected"


class VisualComplianceStatus(str, Enum):
    """Visual content compliance status"""
    APPROVED = "approved"
    REQUIRES_REVIEW = "requires_review"
    REJECTED = "rejected"


class VisualContentRequest(BaseModel):
    """Request for visual content capture and processing"""
    casino_name: str = Field(description="Target casino name")
    target_urls: List[str] = Field(description="URLs to capture screenshots from")
    content_types: List[VisualContentType] = Field(description="Types of visual content needed")
    tenant_config: TenantConfiguration = Field(description="Tenant configuration")
    capture_settings: Dict[str, Any] = Field(default_factory=dict, description="Screenshot capture settings")
    processing_requirements: Dict[str, Any] = Field(default_factory=dict, description="Content processing requirements")


class VisualContentAsset(BaseModel):
    """Processed visual content asset"""
    asset_id: str = Field(description="Unique asset identifier")
    filename: str = Field(description="Asset filename")
    content_type: VisualContentType = Field(description="Type of visual content")
    original_url: str = Field(description="Source URL")
    storage_url: str = Field(description="Storage location URL")
    thumbnail_url: Optional[str] = Field(default=None, description="Thumbnail URL")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Asset metadata")
    quality_score: float = Field(description="Quality assessment score (0-1)")
    compliance_status: VisualComplianceStatus = Field(description="Compliance validation status")
    alt_text: str = Field(description="Generated alt text for accessibility")
    caption: Optional[str] = Field(default=None, description="Generated caption")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")


class VisualContentResult(BaseModel):
    """Result from visual content processing pipeline"""
    success: bool = Field(description="Overall processing success")
    casino_name: str = Field(description="Casino name")
    assets: List[VisualContentAsset] = Field(default_factory=list, description="Processed visual assets")
    processing_metadata: Dict[str, Any] = Field(default_factory=dict, description="Processing metadata")
    quality_summary: Dict[str, Any] = Field(default_factory=dict, description="Quality assessment summary")
    compliance_summary: Dict[str, Any] = Field(default_factory=dict, description="Compliance validation summary")
    error_details: Optional[str] = Field(default=None, description="Error details if processing failed")


# ============================================================================
# VISUAL CONTENT PROCESSORS
# ============================================================================

class VisualContentCapture:
    """Handles automated visual content capture from casino websites"""
    
    def __init__(self, 
                 browserbase_toolkit: Optional[BrowserbaseScreenshotToolkit] = None,
                 playwright_service: Optional[ScreenshotService] = None):
        self.browserbase_toolkit = browserbase_toolkit
        self.playwright_service = playwright_service
        
        # Prioritize Browserbase for production, fallback to Playwright
        self.primary_service = browserbase_toolkit if browserbase_toolkit else playwright_service
    
    def capture_casino_screenshots(self, request: VisualContentRequest) -> Dict[str, Any]:
        """Capture screenshots for a casino using available services"""
        if not self.primary_service:
            raise ValueError("No screenshot service available")
        
        results = {
            "screenshots": [],
            "metadata": {
                "capture_method": "browserbase" if self.browserbase_toolkit else "playwright",
                "timestamp": datetime.now().isoformat(),
                "casino_name": request.casino_name,
                "total_urls": len(request.target_urls)
            }
        }
        
        for url in request.target_urls:
            try:
                if self.browserbase_toolkit:
                    screenshot_result = self._capture_with_browserbase(url, request)
                else:
                    screenshot_result = self._capture_with_playwright(url, request)
                
                results["screenshots"].append(screenshot_result)
                
            except Exception as e:
                logger.error(f"Screenshot capture failed for {url}: {str(e)}")
                results["screenshots"].append({
                    "url": url,
                    "success": False,
                    "error": str(e)
                })
        
        return results
    
    def _capture_with_browserbase(self, url: str, request: VisualContentRequest) -> Dict[str, Any]:
        """Capture screenshot using Browserbase toolkit"""
        config = CasinoScreenshotConfig(
            casino_name=request.casino_name,
            target_urls=[url],
            **request.capture_settings
        )
        
        result = self.browserbase_toolkit.capture_casino_screenshots(config)
        
        return {
            "url": url,
            "success": result.success,
            "screenshots": result.screenshots,
            "storage_urls": result.storage_urls,
            "metadata": result.metadata
        }
    
    def _capture_with_playwright(self, url: str, request: VisualContentRequest) -> Dict[str, Any]:
        """Capture screenshot using Playwright service"""
        config = ScreenshotConfig(
            url=url,
            **request.capture_settings
        )
        
        result = self.playwright_service.capture_screenshot(config)
        
        return {
            "url": url,
            "success": result.success,
            "screenshot_path": result.screenshot_path,
            "metadata": result.metadata
        }


class VisualContentProcessor:
    """Processes and analyzes captured visual content"""
    
    def __init__(self, llm: Optional[ChatOpenAI] = None):
        self.llm = llm or ChatOpenAI(model="gpt-4o", temperature=0.1)
        
        # Visual analysis prompt
        self.analysis_prompt = ChatPromptTemplate.from_template("""
You are an expert visual content analyst for casino review websites.

Analyze this screenshot and provide:
1. Content type identification (lobby, games, bonuses, mobile, payments, etc.)
2. Quality assessment (excellent/good/acceptable/poor/rejected)
3. Alt text for accessibility (concise, descriptive)
4. Caption for content (optional, if notable features present)
5. Compliance concerns (if any)

Screenshot context:
- Casino: {casino_name}
- Source URL: {source_url}
- Tenant: {tenant_id}

Provide analysis in the following JSON format:
{{
    "content_type": "casino_lobby|game_screenshots|bonus_promotions|mobile_interface|payment_methods|registration_flow|customer_support|responsible_gaming",
    "quality": "excellent|good|acceptable|poor|rejected",
    "quality_score": 0.0-1.0,
    "alt_text": "descriptive alt text",
    "caption": "optional caption or null",
    "compliance_status": "approved|requires_review|rejected",
    "compliance_notes": "any compliance concerns",
    "key_features": ["list", "of", "notable", "features"],
    "technical_quality": {{
        "clarity": 0.0-1.0,
        "composition": 0.0-1.0,
        "relevance": 0.0-1.0
    }}
}}
""")
    
    def process_visual_assets(self, capture_results: Dict[str, Any], 
                            request: VisualContentRequest) -> List[VisualContentAsset]:
        """Process captured screenshots into structured visual assets"""
        assets = []
        
        for screenshot_data in capture_results.get("screenshots", []):
            if not screenshot_data.get("success", False):
                continue
            
            try:
                # Analyze the screenshot
                analysis = self._analyze_screenshot(screenshot_data, request)
                
                # Create visual content asset
                asset = self._create_visual_asset(screenshot_data, analysis, request)
                assets.append(asset)
                
            except Exception as e:
                logger.error(f"Visual asset processing failed: {str(e)}")
                continue
        
        return assets
    
    def _analyze_screenshot(self, screenshot_data: Dict[str, Any], 
                          request: VisualContentRequest) -> Dict[str, Any]:
        """Analyze screenshot using LLM"""
        try:
            analysis_chain = self.analysis_prompt | self.llm | StrOutputParser()
            
            result = analysis_chain.invoke({
                "casino_name": request.casino_name,
                "source_url": screenshot_data.get("url", "unknown"),
                "tenant_id": request.tenant_config.tenant_id
            })
            
            # Parse JSON result
            import json
            return json.loads(result)
            
        except Exception as e:
            logger.error(f"Screenshot analysis failed: {str(e)}")
            # Return default analysis
            return {
                "content_type": "casino_lobby",
                "quality": "acceptable",
                "quality_score": 0.6,
                "alt_text": f"Screenshot of {request.casino_name} website",
                "caption": None,
                "compliance_status": "requires_review",
                "compliance_notes": "Automated analysis failed",
                "key_features": [],
                "technical_quality": {"clarity": 0.6, "composition": 0.6, "relevance": 0.6}
            }
    
    def _create_visual_asset(self, screenshot_data: Dict[str, Any], 
                           analysis: Dict[str, Any], 
                           request: VisualContentRequest) -> VisualContentAsset:
        """Create structured visual asset from screenshot data and analysis"""
        
        # Generate asset ID
        asset_id = hashlib.md5(
            f"{request.casino_name}_{screenshot_data.get('url', '')}_"
            f"{datetime.now().isoformat()}".encode()
        ).hexdigest()
        
        # Determine filename
        filename = f"{request.casino_name}_{analysis['content_type']}_{asset_id[:8]}.png"
        
        return VisualContentAsset(
            asset_id=asset_id,
            filename=filename,
            content_type=VisualContentType(analysis.get("content_type", "casino_lobby")),
            original_url=screenshot_data.get("url", ""),
            storage_url=screenshot_data.get("storage_urls", [""])[0] if screenshot_data.get("storage_urls") else "",
            metadata=screenshot_data.get("metadata", {}),
            quality_score=analysis.get("quality_score", 0.6),
            compliance_status=VisualComplianceStatus(analysis.get("compliance_status", "requires_review")),
            alt_text=analysis.get("alt_text", f"Screenshot of {request.casino_name}"),
            caption=analysis.get("caption")
        )


class VisualContentValidator:
    """Validates visual content for compliance and quality standards"""
    
    def __init__(self, llm: Optional[ChatOpenAI] = None):
        self.llm = llm or ChatOpenAI(model="gpt-4o", temperature=0.0)
        
        # Compliance validation prompt
        self.compliance_prompt = ChatPromptTemplate.from_template("""
You are a compliance expert for online casino content validation.

Review this visual asset for compliance issues:

Asset Details:
- Casino: {casino_name}
- Content Type: {content_type}
- Quality Score: {quality_score}
- Alt Text: {alt_text}
- Tenant: {tenant_id}
- Jurisdiction: {jurisdiction}

Compliance Requirements:
1. Age verification (18+ or 21+ depending on jurisdiction)
2. Responsible gambling messaging
3. No misleading bonus claims
4. Proper licensing information visibility
5. No prohibited content (violence, inappropriate imagery)
6. Accessibility compliance

Provide validation result in JSON format:
{{
    "compliance_approved": true|false,
    "compliance_score": 0.0-1.0,
    "violations": ["list of specific violations"],
    "recommendations": ["list of improvement recommendations"],
    "jurisdiction_specific": {{
        "uk_compliance": true|false,
        "de_compliance": true|false,
        "us_compliance": true|false
    }},
    "accessibility_score": 0.0-1.0,
    "final_status": "approved|requires_review|rejected"
}}
""")
    
    def validate_visual_assets(self, assets: List[VisualContentAsset],
                             tenant_config: TenantConfiguration) -> Dict[str, Any]:
        """Validate a collection of visual assets"""
        validation_results = {
            "total_assets": len(assets),
            "approved_count": 0,
            "requires_review_count": 0,
            "rejected_count": 0,
            "overall_compliance_score": 0.0,
            "asset_validations": []
        }
        
        total_compliance_score = 0.0
        
        for asset in assets:
            try:
                validation = self._validate_single_asset(asset, tenant_config)
                validation_results["asset_validations"].append({
                    "asset_id": asset.asset_id,
                    "validation": validation
                })
                
                # Update counts
                if validation["final_status"] == "approved":
                    validation_results["approved_count"] += 1
                elif validation["final_status"] == "requires_review":
                    validation_results["requires_review_count"] += 1
                else:
                    validation_results["rejected_count"] += 1
                
                total_compliance_score += validation.get("compliance_score", 0.0)
                
            except Exception as e:
                logger.error(f"Asset validation failed for {asset.asset_id}: {str(e)}")
                validation_results["rejected_count"] += 1
        
        # Calculate overall compliance score
        if len(assets) > 0:
            validation_results["overall_compliance_score"] = total_compliance_score / len(assets)
        
        return validation_results
    
    def _validate_single_asset(self, asset: VisualContentAsset,
                             tenant_config: TenantConfiguration) -> Dict[str, Any]:
        """Validate a single visual asset"""
        try:
            validation_chain = self.compliance_prompt | self.llm | StrOutputParser()
            
            result = validation_chain.invoke({
                "casino_name": asset.original_url,  # Extract casino from URL
                "content_type": asset.content_type,
                "quality_score": asset.quality_score,
                "alt_text": asset.alt_text,
                "tenant_id": tenant_config.tenant_id,
                "jurisdiction": tenant_config.locale
            })
            
            # Parse JSON result
            import json
            return json.loads(result)
            
        except Exception as e:
            logger.error(f"Asset validation failed: {str(e)}")
            return {
                "compliance_approved": False,
                "compliance_score": 0.0,
                "violations": ["Validation process failed"],
                "recommendations": ["Manual review required"],
                "jurisdiction_specific": {
                    "uk_compliance": False,
                    "de_compliance": False,
                    "us_compliance": False
                },
                "accessibility_score": 0.0,
                "final_status": "requires_review"
            }


# ============================================================================
# MAIN VISUAL CONTENT PIPELINE CHAIN
# ============================================================================

class VisualContentPipeline:
    """Complete visual content processing pipeline"""
    
    def __init__(self,
                 vector_store: Optional[AgenticSupabaseVectorStore] = None,
                 llm: Optional[ChatOpenAI] = None):
        
        self.llm = llm or ChatOpenAI(model="gpt-4o", temperature=0.1)
        self.vector_store = vector_store
        
        # Initialize components
        self.capture_service = VisualContentCapture()
        self.processor = VisualContentProcessor(self.llm)
        self.validator = VisualContentValidator(self.llm)
        
        # Build LCEL chain
        self.chain = self._build_pipeline_chain()
    
    def _build_pipeline_chain(self) -> Runnable:
        """Build the complete visual content processing LCEL chain"""
        
        return (
            RunnablePassthrough.assign(
                capture_results=RunnableLambda(self._capture_visual_content)
            )
            | RunnablePassthrough.assign(
                processed_assets=RunnableLambda(self._process_visual_assets)
            )
            | RunnablePassthrough.assign(
                validation_results=RunnableLambda(self._validate_visual_assets)
            )
            | RunnableLambda(self._create_final_result)
        )
    
    def _capture_visual_content(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Capture visual content from casino websites"""
        request = VisualContentRequest(**input_data)
        return self.capture_service.capture_casino_screenshots(request)
    
    def _process_visual_assets(self, input_data: Dict[str, Any]) -> List[VisualContentAsset]:
        """Process captured screenshots into structured assets"""
        request = VisualContentRequest(**{k: v for k, v in input_data.items() 
                                        if k != "capture_results"})
        capture_results = input_data["capture_results"]
        
        return self.processor.process_visual_assets(capture_results, request)
    
    def _validate_visual_assets(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate processed visual assets for compliance"""
        assets = input_data["processed_assets"]
        request_data = {k: v for k, v in input_data.items() 
                       if k not in ["capture_results", "processed_assets"]}
        request = VisualContentRequest(**request_data)
        
        return self.validator.validate_visual_assets(assets, request.tenant_config)
    
    def _create_final_result(self, input_data: Dict[str, Any]) -> VisualContentResult:
        """Create final visual content pipeline result"""
        assets = input_data["processed_assets"]
        validation_results = input_data["validation_results"]
        
        # Extract casino name from input
        casino_name = input_data.get("casino_name", "Unknown")
        
        return VisualContentResult(
            success=validation_results["approved_count"] > 0,
            casino_name=casino_name,
            assets=assets,
            processing_metadata={
                "total_processed": len(assets),
                "processing_timestamp": datetime.now().isoformat()
            },
            quality_summary={
                "average_quality": sum(a.quality_score for a in assets) / len(assets) if assets else 0.0,
                "quality_distribution": self._calculate_quality_distribution(assets)
            },
            compliance_summary=validation_results
        )
    
    def _calculate_quality_distribution(self, assets: List[VisualContentAsset]) -> Dict[str, int]:
        """Calculate quality score distribution"""
        distribution = {"excellent": 0, "good": 0, "acceptable": 0, "poor": 0, "rejected": 0}
        
        for asset in assets:
            if asset.quality_score >= 0.9:
                distribution["excellent"] += 1
            elif asset.quality_score >= 0.8:
                distribution["good"] += 1
            elif asset.quality_score >= 0.6:
                distribution["acceptable"] += 1
            elif asset.quality_score >= 0.4:
                distribution["poor"] += 1
            else:
                distribution["rejected"] += 1
        
        return distribution
    
    def process_visual_content(self, request: VisualContentRequest) -> VisualContentResult:
        """Process visual content through the complete pipeline"""
        try:
            result = self.chain.invoke(request.dict())
            return result
        except Exception as e:
            logger.error(f"Visual content pipeline failed: {str(e)}")
            return VisualContentResult(
                success=False,
                casino_name=request.casino_name,
                error_details=str(e)
            )


# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================

def create_visual_content_pipeline(
    vector_store: Optional[AgenticSupabaseVectorStore] = None,
    llm_model: str = "gpt-4o",
    temperature: float = 0.1
) -> VisualContentPipeline:
    """Factory function to create a visual content pipeline"""
    
    llm = ChatOpenAI(model=llm_model, temperature=temperature)
    
    return VisualContentPipeline(
        vector_store=vector_store,
        llm=llm
    )


def create_visual_content_chain() -> Runnable:
    """Factory function to create a visual content processing chain"""
    pipeline = create_visual_content_pipeline()
    return pipeline.chain


# ============================================================================
# INTEGRATION WITH EXISTING CHAINS
# ============================================================================

def integrate_visual_content_with_narrative_generation(
    narrative_chain: Runnable,
    visual_pipeline: VisualContentPipeline
) -> Runnable:
    """Integrate visual content pipeline with narrative generation"""
    
    def process_with_visuals(input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process visual content and integrate with narrative generation"""
        
        # Create visual content request from narrative input
        visual_request = VisualContentRequest(
            casino_name=input_data["casino_name"],
            target_urls=input_data.get("target_urls", []),
            content_types=[VisualContentType.CASINO_LOBBY],  # Default type
            tenant_config=input_data["tenant_config"]
        )
        
        # Process visual content
        visual_result = visual_pipeline.process_visual_content(visual_request)
        
        # Convert to MediaAssets for narrative generation
        media_assets = []
        for asset in visual_result.assets:
            media_asset = MediaAsset(
                url=asset.storage_url,
                alt_text=asset.alt_text,
                caption=asset.caption,
                media_type="image/png",  # Map to existing media_type field
                source_method=asset.source_method if hasattr(asset, 'source_method') else "browserbase",
                compliance_checked=asset.compliance_status == "approved" if hasattr(asset, 'compliance_status') else False,
                license_status=asset.compliance_status if hasattr(asset, 'compliance_status') else "pending"
            )
            media_assets.append(media_asset)
        
        # Add visual assets to input data
        input_data["visual_assets"] = media_assets
        input_data["visual_processing_result"] = visual_result
        
        return input_data
    
    return (
        RunnableLambda(process_with_visuals)
        | narrative_chain
    )