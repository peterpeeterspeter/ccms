"""
🎰 AGENTIC RAG CMS: REVIEW DOCUMENT & QA SCHEMAS
===============================================

Comprehensive Pydantic schemas for the Agentic Multi-Tenant RAG CMS:
- ReviewDoc: Complete structured output for generated content
- QAReport: Compliance and quality validation results
- Multi-tenant support with affiliate intelligence integration

Author: AI Assistant & TaskMaster System  
Created: 2025-08-24
Task: task-023 - Define ReviewDoc and QAReport Pydantic Schemas
Version: 2.0.0
"""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator, model_validator
from datetime import datetime
from enum import Enum
from .casino_intelligence_schema import CasinoIntelligence


# ============================================================================
# ENUMS AND TYPE DEFINITIONS
# ============================================================================

class ContentType(str, Enum):
    """Content types for multi-domain support"""
    CASINO_REVIEW = "casino_review"
    NEWS_ARTICLE = "news_article"
    PRODUCT_COMPARISON = "product_comparison"
    TECHNICAL_DOCUMENTATION = "technical_documentation"
    MARKETING_COPY = "marketing_copy"
    EDUCATIONAL_TUTORIAL = "educational_tutorial"


class QualityScore(str, Enum):
    """Quality assessment levels"""
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    FAILED = "failed"


class WorkflowStatus(str, Enum):
    """Workflow execution status for content generation pipeline"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_IMPROVEMENT = "needs_improvement"
    FAILED = "failed"


class MediaType(str, Enum):
    """Media asset types for content generation"""
    SCREENSHOT = "screenshot"
    PROMOTIONAL = "promotional"
    INFOGRAPHIC = "infographic"
    VIDEO = "video"
    LOGO = "logo"
    BANNER = "banner"


class ComplianceStatus(str, Enum):
    """Compliance validation status"""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    PENDING_REVIEW = "pending_review"


class PublishingStatus(str, Enum):
    """Publishing workflow status"""
    DRAFT = "draft"
    READY_FOR_QA = "ready_for_qa"
    QA_APPROVED = "qa_approved"
    QA_REJECTED = "qa_rejected"
    PUBLISHED = "published"
    ARCHIVED = "archived"


# ============================================================================
# MEDIA AND VISUAL CONTENT SCHEMAS
# ============================================================================

class MediaAsset(BaseModel):
    """Individual media asset information"""
    url: str = Field(..., description="Media asset URL")
    alt_text: Optional[str] = Field(None, description="Alt text for accessibility")
    caption: Optional[str] = Field(None, description="Media caption")
    media_type: str = Field(..., description="Media type: image, video, audio")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    dimensions: Optional[str] = Field(None, description="Dimensions (e.g., '1200x800')")
    source_method: str = Field(..., description="Capture method: firecrawl, cf_browser, browserless")
    compliance_checked: bool = Field(False, description="Compliance validation completed")
    license_status: Optional[str] = Field(None, description="License/copyright status")


class VisualContent(BaseModel):
    """Visual content and media assets"""
    featured_image: Optional[MediaAsset] = Field(None, description="Primary featured image")
    gallery_images: List[MediaAsset] = Field(default_factory=list, description="Additional gallery images")
    screenshots: List[MediaAsset] = Field(default_factory=list, description="Website/product screenshots")
    videos: List[MediaAsset] = Field(default_factory=list, description="Video content")
    total_assets: int = Field(0, description="Total number of media assets")


# ============================================================================
# SEO AND METADATA SCHEMAS
# ============================================================================

class SEOMetadata(BaseModel):
    """SEO optimization metadata"""
    meta_title: str = Field(..., description="SEO-optimized title (50-60 chars)")
    meta_description: str = Field(..., description="Meta description (150-160 chars)")
    focus_keyword: Optional[str] = Field(None, description="Primary focus keyword")
    secondary_keywords: List[str] = Field(default_factory=list, description="Secondary keywords")
    internal_links: List[Dict[str, str]] = Field(default_factory=list, description="Internal link suggestions")
    external_links: List[Dict[str, str]] = Field(default_factory=list, description="External authoritative links")
    schema_markup: Optional[Dict[str, Any]] = Field(None, description="JSON-LD schema markup")
    readability_score: Optional[float] = Field(None, description="Content readability score", ge=0, le=100)


# ============================================================================
# WORDPRESS PUBLISHING SCHEMAS
# ============================================================================

class WordPressMetadata(BaseModel):
    """WordPress-specific publishing metadata"""
    post_status: str = Field("draft", description="WordPress post status")
    categories: List[str] = Field(default_factory=list, description="WordPress categories")
    tags: List[str] = Field(default_factory=list, description="WordPress tags")
    custom_fields: Dict[str, Any] = Field(default_factory=dict, description="Custom field values")
    taxonomies: Dict[str, List[str]] = Field(default_factory=dict, description="Custom taxonomy values")
    featured_media_id: Optional[int] = Field(None, description="WordPress media ID for featured image")
    template: Optional[str] = Field(None, description="Page template to use")
    excerpt: Optional[str] = Field(None, description="Post excerpt")


# ============================================================================
# MULTI-TENANT CONFIGURATION SCHEMAS
# ============================================================================

class TenantConfiguration(BaseModel):
    """Tenant-specific configuration and branding"""
    tenant_id: str = Field(..., description="Unique tenant identifier")
    brand_name: str = Field(..., description="Brand/site name")
    locale: str = Field(..., description="Content locale (e.g., 'en-US', 'de-DE')")
    voice_profile: Optional[str] = Field(None, description="Brand voice profile identifier")
    compliance_level: str = Field("standard", description="Compliance requirement level")
    target_audience: Optional[str] = Field(None, description="Primary target audience")
    brand_guidelines: Dict[str, Any] = Field(default_factory=dict, description="Brand-specific guidelines")


# ============================================================================
# AFFILIATE INTELLIGENCE INTEGRATION
# ============================================================================

class AffiliateIntelligence(BaseModel):
    """Affiliate intelligence integration"""
    casino_intelligence: Optional[CasinoIntelligence] = Field(None, description="Complete 95-field casino intelligence")
    intelligence_completeness: float = Field(0.0, description="Completeness score (0-1)", ge=0, le=1)
    affiliate_compliance_score: Optional[float] = Field(None, description="Affiliate compliance score (0-10)", ge=0, le=10)
    key_affiliate_points: List[str] = Field(default_factory=list, description="Key affiliate selling points")
    compliance_warnings: List[str] = Field(default_factory=list, description="Compliance warnings/flags")


# ============================================================================
# MAIN REVIEW DOCUMENT SCHEMA
# ============================================================================

class ReviewDoc(BaseModel):
    """
    🎰 COMPREHENSIVE REVIEW DOCUMENT SCHEMA
    ========================================
    
    Complete structured output for agentic content generation supporting:
    - Multi-tenant branding and localization
    - 95-field affiliate intelligence integration
    - World-class narrative content generation
    - SEO optimization and WordPress publishing
    - Compliance validation and quality control
    """
    
    # ========================================================================
    # CORE IDENTIFICATION & METADATA
    # ========================================================================
    title: str = Field(..., description="Primary content title")
    slug: str = Field(..., description="URL-friendly slug")
    content_type: ContentType = Field(ContentType.CASINO_REVIEW, description="Type of content generated")
    
    # ========================================================================
    # MULTI-TENANT CONFIGURATION
    # ========================================================================
    tenant_config: TenantConfiguration = Field(..., description="Tenant-specific configuration")
    
    # Legacy fields for backward compatibility
    tenant_id: str = Field(..., description="Tenant identifier (legacy)")
    brand: str = Field(..., description="Brand name (legacy)")
    locale: str = Field(..., description="Content locale (legacy)")
    
    # ========================================================================
    # CONTENT BODY & STRUCTURE
    # ========================================================================
    body_html: str = Field(..., description="Long-form narrative content; flowing paragraphs, no bullet lists")
    word_count: int = Field(0, description="Total word count", ge=0)
    reading_time_minutes: int = Field(0, description="Estimated reading time", ge=0)
    content_outline: List[str] = Field(default_factory=list, description="Content section headings")
    
    # ========================================================================
    # VISUAL CONTENT & MEDIA
    # ========================================================================
    visual_content: VisualContent = Field(default_factory=VisualContent, description="Visual assets and media")
    
    # ========================================================================
    # SEO & OPTIMIZATION
    # ========================================================================
    seo_metadata: SEOMetadata = Field(..., description="SEO optimization metadata")
    
    # ========================================================================
    # AFFILIATE INTELLIGENCE INTEGRATION
    # ========================================================================
    affiliate_intel: Optional[AffiliateIntelligence] = Field(None, description="Integrated affiliate intelligence")
    
    # ========================================================================
    # SOURCES & RESEARCH
    # ========================================================================
    sources: List[str] = Field(default_factory=list, description="Research sources and citations")
    research_depth_score: Optional[float] = Field(None, description="Research comprehensiveness (0-10)", ge=0, le=10)
    fact_check_status: Optional[str] = Field(None, description="Fact-checking validation status")
    
    # ========================================================================
    # WORDPRESS PUBLISHING INTEGRATION
    # ========================================================================
    wordpress_metadata: Optional[WordPressMetadata] = Field(None, description="WordPress publishing metadata")
    
    # ========================================================================
    # CONTENT GENERATION METADATA
    # ========================================================================
    generation_timestamp: datetime = Field(default_factory=datetime.now, description="Content generation timestamp")
    llm_model_used: Optional[str] = Field(None, description="LLM model used for generation")
    generation_parameters: Dict[str, Any] = Field(default_factory=dict, description="Generation parameters used")
    content_version: str = Field("1.0", description="Content version")
    
    # ========================================================================
    # QUALITY & PUBLISHING STATUS
    # ========================================================================
    quality_score: Optional[float] = Field(None, description="Overall quality score (0-10)", ge=0, le=10)
    publishing_status: PublishingStatus = Field(PublishingStatus.DRAFT, description="Current publishing status")
    qa_approved: bool = Field(False, description="QA approval status")
    compliance_approved: bool = Field(False, description="Compliance approval status")
    
    # ========================================================================
    # VALIDATION & PROCESSING
    # ========================================================================
    
    @model_validator(mode='before')
    @classmethod
    def validate_tenant_consistency(cls, values):
        """Ensure tenant configuration consistency"""
        if isinstance(values, dict):
            # Sync legacy fields with tenant_config
            tenant_config = values.get('tenant_config', {})
            if isinstance(tenant_config, dict):
                values['tenant_id'] = values.get('tenant_id') or tenant_config.get('tenant_id')
                values['brand'] = values.get('brand') or tenant_config.get('brand_name')
                values['locale'] = values.get('locale') or tenant_config.get('locale')
        return values
    
    @validator('body_html')
    def validate_content_quality(cls, v):
        """Validate content meets quality standards"""
        if not v or len(v.strip()) < 500:
            raise ValueError("Content body must be substantial (minimum 500 characters)")
        return v
    
    @validator('word_count', always=True)
    def calculate_word_count(cls, v, values):
        """Auto-calculate word count from body content"""
        body_html = values.get('body_html', '')
        if body_html:
            # Simple word count from HTML (could be enhanced with proper HTML parsing)
            import re
            text = re.sub(r'<[^>]+>', '', body_html)
            word_count = len(text.split())
            return word_count
        return v or 0
    
    @validator('reading_time_minutes', always=True)
    def calculate_reading_time(cls, v, values):
        """Auto-calculate reading time (average 200 words per minute)"""
        word_count = values.get('word_count', 0)
        if word_count > 0:
            return max(1, word_count // 200)
        return v or 0


# ============================================================================
# QA REPORT SCHEMAS
# ============================================================================

class QACheck(BaseModel):
    """Individual QA check result"""
    check_name: str = Field(..., description="Name of the QA check")
    status: ComplianceStatus = Field(..., description="Check result status")
    score: Optional[float] = Field(None, description="Check score (0-10)", ge=0, le=10)
    message: str = Field(..., description="Detailed check result message")
    suggestions: List[str] = Field(default_factory=list, description="Improvement suggestions")
    severity: str = Field("info", description="Issue severity: critical, high, medium, low, info")


class ContentQualityAssessment(BaseModel):
    """Content quality assessment results"""
    overall_quality: QualityScore = Field(..., description="Overall content quality rating")
    narrative_flow: float = Field(0.0, description="Narrative flow score (0-10)", ge=0, le=10)
    factual_accuracy: float = Field(0.0, description="Factual accuracy score (0-10)", ge=0, le=10)
    brand_voice_consistency: float = Field(0.0, description="Brand voice consistency (0-10)", ge=0, le=10)
    readability: float = Field(0.0, description="Content readability score (0-10)", ge=0, le=10)
    engagement_potential: float = Field(0.0, description="Engagement potential (0-10)", ge=0, le=10)
    length_appropriateness: bool = Field(True, description="Content length appropriate for type")


class AffiliateComplianceAssessment(BaseModel):
    """Affiliate compliance validation results"""
    compliance_score: float = Field(0.0, description="Overall compliance score (0-10)", ge=0, le=10)
    field_completeness: float = Field(0.0, description="95-field completeness percentage", ge=0, le=100)
    missing_critical_fields: List[str] = Field(default_factory=list, description="Critical missing fields")
    regulatory_compliance: ComplianceStatus = Field(ComplianceStatus.PENDING_REVIEW, description="Regulatory compliance status")
    disclosure_requirements: bool = Field(False, description="Proper affiliate disclosures included")
    responsible_gambling: bool = Field(False, description="Responsible gambling mentions included")
    accuracy_warnings: List[str] = Field(default_factory=list, description="Data accuracy warnings")


class TechnicalQAAssessment(BaseModel):
    """Technical quality assessment"""
    html_validation: bool = Field(True, description="HTML markup validation passed")
    seo_optimization: float = Field(0.0, description="SEO optimization score (0-10)", ge=0, le=10)
    media_compliance: bool = Field(True, description="All media assets comply with licensing")
    performance_score: Optional[float] = Field(None, description="Content performance score", ge=0, le=10)
    accessibility_score: Optional[float] = Field(None, description="Accessibility compliance score", ge=0, le=10)
    schema_markup_valid: bool = Field(True, description="Schema markup validation passed")


class QAReport(BaseModel):
    """
    🔍 COMPREHENSIVE QA VALIDATION REPORT
    =====================================
    
    Complete quality assurance and compliance validation for generated content:
    - Content quality assessment
    - Affiliate compliance validation  
    - Technical quality checks
    - Multi-tenant compliance verification
    """
    
    # ========================================================================
    # REPORT IDENTIFICATION & METADATA
    # ========================================================================
    report_id: str = Field(..., description="Unique QA report identifier")
    review_doc_title: str = Field(..., description="Title of reviewed document")
    tenant_id: str = Field(..., description="Tenant identifier")
    qa_timestamp: datetime = Field(default_factory=datetime.now, description="QA execution timestamp")
    qa_version: str = Field("1.0", description="QA framework version")
    
    # ========================================================================
    # OVERALL QA RESULTS
    # ========================================================================
    overall_status: ComplianceStatus = Field(..., description="Overall QA result status")
    overall_score: float = Field(0.0, description="Overall quality score (0-10)", ge=0, le=10)
    pass_threshold: float = Field(7.0, description="Minimum score required to pass", ge=0, le=10)
    approved_for_publishing: bool = Field(False, description="Approved for publication")
    
    # ========================================================================
    # DETAILED QA ASSESSMENTS
    # ========================================================================
    content_quality: ContentQualityAssessment = Field(..., description="Content quality assessment results")
    affiliate_compliance: AffiliateComplianceAssessment = Field(..., description="Affiliate compliance validation")
    technical_qa: TechnicalQAAssessment = Field(..., description="Technical quality assessment")
    
    # ========================================================================
    # INDIVIDUAL QA CHECKS
    # ========================================================================
    qa_checks: List[QACheck] = Field(default_factory=list, description="Individual QA check results")
    
    # ========================================================================
    # CRITICAL ISSUES & BLOCKING FACTORS
    # ========================================================================
    critical_issues: List[str] = Field(default_factory=list, description="Critical issues blocking publication")
    warnings: List[str] = Field(default_factory=list, description="Non-blocking warnings")
    recommendations: List[str] = Field(default_factory=list, description="Improvement recommendations")
    
    # ========================================================================
    # HUMAN-IN-THE-LOOP WORKFLOW
    # ========================================================================
    requires_human_review: bool = Field(False, description="Requires human reviewer attention")
    human_reviewer_notes: Optional[str] = Field(None, description="Notes from human reviewer")
    escalation_reason: Optional[str] = Field(None, description="Reason for escalation to human review")
    review_priority: str = Field("normal", description="Review priority: critical, high, normal, low")
    
    # ========================================================================
    # VALIDATION METHODS
    # ========================================================================
    
    def is_publishing_approved(self) -> bool:
        """Check if content is approved for publishing"""
        return (
            self.approved_for_publishing and 
            self.overall_status == ComplianceStatus.PASSED and
            len(self.critical_issues) == 0 and
            self.overall_score >= self.pass_threshold
        )
    
    def get_blocking_issues(self) -> List[str]:
        """Get all issues that block publishing"""
        blocking = self.critical_issues.copy()
        
        # Add failed QA checks
        for check in self.qa_checks:
            if check.status == ComplianceStatus.FAILED and check.severity in ["critical", "high"]:
                blocking.append(f"{check.check_name}: {check.message}")
        
        return blocking
    
    def calculate_improvement_score(self) -> float:
        """Calculate how much improvement is needed to pass"""
        if self.overall_score >= self.pass_threshold:
            return 0.0
        return self.pass_threshold - self.overall_score
    
    @model_validator(mode='before')
    @classmethod
    def validate_qa_consistency(cls, values):
        """Validate QA result consistency"""
        if isinstance(values, dict):
            # Ensure overall status matches component results
            content_quality = values.get('content_quality', {})
            affiliate_compliance = values.get('affiliate_compliance', {})
            
            # Auto-set approval based on scores
            overall_score = values.get('overall_score', 0.0)
            pass_threshold = values.get('pass_threshold', 7.0)
            critical_issues = values.get('critical_issues', [])
            
            if overall_score >= pass_threshold and len(critical_issues) == 0:
                values['approved_for_publishing'] = True
                values['overall_status'] = ComplianceStatus.PASSED.value
            else:
                values['approved_for_publishing'] = False
                values['overall_status'] = ComplianceStatus.FAILED.value
                
        return values


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def create_empty_review_doc(
    title: str, 
    tenant_id: str, 
    brand: str, 
    locale: str,
    content_type: ContentType = ContentType.CASINO_REVIEW
) -> ReviewDoc:
    """Create an empty ReviewDoc with basic tenant configuration"""
    tenant_config = TenantConfiguration(
        tenant_id=tenant_id,
        brand_name=brand,
        locale=locale
    )
    
    seo_metadata = SEOMetadata(
        meta_title=title[:60],  # Truncate to SEO length
        meta_description=f"Comprehensive review of {title}"[:160]  # Truncate to SEO length
    )
    
    return ReviewDoc(
        title=title,
        slug=title.lower().replace(' ', '-').replace('_', '-'),
        content_type=content_type,
        tenant_config=tenant_config,
        tenant_id=tenant_id,
        brand=brand,
        locale=locale,
        body_html="",
        seo_metadata=seo_metadata
    )


def create_qa_report(
    review_doc: ReviewDoc,
    overall_score: float = 0.0,
    pass_threshold: float = 7.0
) -> QAReport:
    """Create a QA report for a ReviewDoc"""
    return QAReport(
        report_id=f"qa-{review_doc.slug}-{int(datetime.now().timestamp())}",
        review_doc_title=review_doc.title,
        tenant_id=review_doc.tenant_id,
        overall_score=overall_score,
        pass_threshold=pass_threshold,
        content_quality=ContentQualityAssessment(
            overall_quality=QualityScore.ACCEPTABLE
        ),
        affiliate_compliance=AffiliateComplianceAssessment(),
        technical_qa=TechnicalQAAssessment()
    )


if __name__ == "__main__":
    # Test the schemas
    print("🎰 Testing Agentic RAG CMS Schemas")
    print("=" * 50)
    
    # Test ReviewDoc creation
    review = create_empty_review_doc(
        title="Test Casino Review",
        tenant_id="crashcasino",
        brand="Crash Casino",
        locale="en-US"
    )
    print(f"ReviewDoc created: {review.title}")
    print(f"Tenant: {review.tenant_config.brand_name}")
    print(f"Word count: {review.word_count}")
    
    # Test QAReport creation
    qa_report = create_qa_report(review, overall_score=8.5)
    print(f"\nQA Report created: {qa_report.report_id}")
    print(f"Approved for publishing: {qa_report.is_publishing_approved()}")
    print(f"Blocking issues: {len(qa_report.get_blocking_issues())}")
    
    print("\n✅ Schema validation complete!")