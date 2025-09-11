"""
Casino Review Schemas
======================

Pydantic v2 models for casino review workflow data structures.
All inputs/outputs live in /src/schemas per WARP.md Schema-First principle.
"""

from typing import List, Optional, Dict, Union, Any
from pydantic import BaseModel, Field, HttpUrl, validator
from datetime import datetime
from enum import Enum


class LicenseType(str, Enum):
    """Casino licensing jurisdictions"""
    CURACAO = "curacao"
    MALTA = "malta"
    UK = "uk"
    GIBRALTAR = "gibraltar"
    KAHNAWAKE = "kahnawake"
    COSTA_RICA = "costa_rica"
    PANAMA = "panama"
    UNLICENSED = "unlicensed"


class CasinoType(str, Enum):
    """Casino category types"""
    TRADITIONAL = "traditional"
    CRYPTO = "crypto" 
    CRASH = "crash"
    LIVE_DEALER = "live_dealer"
    MOBILE = "mobile"
    SWEEPSTAKES = "sweepstakes"


class PaymentMethod(str, Enum):
    """Supported payment methods"""
    CREDIT_CARD = "credit_card"
    CRYPTO = "crypto"
    E_WALLET = "e_wallet"
    BANK_TRANSFER = "bank_transfer"
    PREPAID = "prepaid"


class CasinoResearchPack(BaseModel):
    """
    Research Agent output: Comprehensive casino data
    Sources: DataForSEO, Firecrawl scraping, manual research
    """
    casino_name: str = Field(..., description="Official casino name")
    casino_url: HttpUrl = Field(..., description="Primary casino website URL")
    
    # Licensing & Regulation
    license_type: LicenseType = Field(..., description="Primary licensing jurisdiction")
    license_number: Optional[str] = Field(None, description="License registration number")
    established_year: Optional[int] = Field(None, description="Year casino was established")
    operator_company: Optional[str] = Field(None, description="Operating company name")
    
    # Games & Software
    total_games: Optional[int] = Field(None, description="Total number of games")
    software_providers: List[str] = Field(default_factory=list, description="Game software providers")
    game_categories: List[str] = Field(default_factory=list, description="Available game categories")
    crash_games_available: bool = Field(False, description="Offers crash gambling games")
    live_dealer_available: bool = Field(False, description="Offers live dealer games")
    
    # Payments & Banking
    supported_currencies: List[str] = Field(default_factory=list, description="Accepted currencies")
    payment_methods: List[PaymentMethod] = Field(default_factory=list, description="Payment options")
    withdrawal_time: Optional[str] = Field(None, description="Typical withdrawal processing time")
    min_deposit: Optional[str] = Field(None, description="Minimum deposit amount")
    max_withdrawal: Optional[str] = Field(None, description="Maximum withdrawal limit")
    
    # Bonuses & Promotions
    welcome_bonus: Optional[str] = Field(None, description="Welcome bonus offer")
    wagering_requirements: Optional[str] = Field(None, description="Bonus wagering requirements")
    ongoing_promotions: List[str] = Field(default_factory=list, description="Regular promotional offers")
    vip_program: bool = Field(False, description="VIP/loyalty program available")
    
    # Support & Features
    customer_support: List[str] = Field(default_factory=list, description="Support channels")
    supported_languages: List[str] = Field(default_factory=list, description="Interface languages")
    mobile_app: bool = Field(False, description="Dedicated mobile application")
    responsible_gambling: bool = Field(False, description="Responsible gambling tools")
    
    # Compliance & Restrictions
    restricted_countries: List[str] = Field(default_factory=list, description="Restricted jurisdictions")
    kyc_required: bool = Field(True, description="KYC verification required")
    
    # Research metadata
    research_sources: List[str] = Field(default_factory=list, description="Data sources used")
    research_timestamp: datetime = Field(default_factory=datetime.now, description="Research completion time")
    confidence_score: float = Field(0.0, ge=0.0, le=1.0, description="Data confidence rating")
    research_date: datetime = Field(default_factory=datetime.now, description="Research completion date")
    research_accuracy: float = Field(0.0, ge=0.0, le=1.0, description="Research accuracy score")
    
    # SERP Intelligence (from DataForSEO)
    serp_ranking: List[Dict[str, Any]] = Field(default_factory=list, description="SERP ranking data")
    competitor_analysis: List[Dict[str, Any]] = Field(default_factory=list, description="Competitor analysis data")
    top_ranking_content: List[Dict[str, Any]] = Field(default_factory=list, description="Top ranking content analysis")
    
    # SEO Data (from DataForSEO)
    primary_keywords: List[str] = Field(default_factory=list, description="Primary target keywords")
    long_tail_keywords: List[str] = Field(default_factory=list, description="Long-tail keyword opportunities")
    related_queries: List[str] = Field(default_factory=list, description="Related search queries")
    search_volume_data: Dict[str, int] = Field(default_factory=dict, description="Keyword search volumes")
    
    # Authority & Trust Signals (from DataForSEO)
    backlink_profile: Dict[str, Any] = Field(default_factory=dict, description="Backlink profile data")
    domain_authority_score: float = Field(0.0, description="Domain authority score")
    trust_signals: List[str] = Field(default_factory=list, description="Trust and credibility signals")
    
    # Brand Intelligence (from DataForSEO)
    brand_mentions: List[Dict[str, Any]] = Field(default_factory=list, description="Brand mention data")
    sentiment_analysis: Dict[str, Any] = Field(default_factory=dict, description="Brand sentiment analysis")
    
    # Image Discovery (NOT for publishing - reference only)
    discovered_images: List[Dict[str, Any]] = Field(default_factory=list, description="Reference images (DO NOT PUBLISH)")
    
    # Additional metadata
    data_sources: List[str] = Field(default_factory=list, description="Research data sources")
    notes: str = Field("", description="Research notes and observations")


class ScreenshotResult(BaseModel):
    """
    Screenshot Agent output: Casino interface captures with compliance data
    """
    view_type: str = Field(..., description="Screenshot view type (homepage, games, mobile)")
    image_url: HttpUrl = Field(..., description="Screenshot image URL")
    media_id: int = Field(..., description="WordPress media attachment ID")
    
    # Image metadata
    width: int = Field(..., description="Image width in pixels")
    height: int = Field(..., description="Image height in pixels")  
    file_size: int = Field(..., description="File size in bytes")
    format: str = Field(..., description="Image format (PNG, JPEG, WebP)")
    
    # Compliance data per WARP.md screenshot policy
    compliance_pass: bool = Field(..., description="Passed compliance guard")
    licensing_compliant: bool = Field(..., description="No licensing violations detected")
    branding_compliant: bool = Field(..., description="Proper branding/attribution")
    dimensions_compliant: bool = Field(..., description="Meets minimum 900×600 requirement")
    
    # Capture metadata
    capture_timestamp: datetime = Field(default_factory=datetime.now, description="Screenshot capture time")
    capture_method: str = Field(..., description="Capture tool used (firecrawl, cf_browser, etc)")
    source_url: HttpUrl = Field(..., description="Original page URL")
    
    # Supabase storage path following WARP.md structure
    storage_path: str = Field(..., description="images/{tenant}/{brand}/{category}/{ISO8601}.png")


class ReviewSection(BaseModel):
    """Individual review section with structured content"""
    title: str = Field(..., description="Section heading")
    content: str = Field(..., description="Section content in HTML")
    order: int = Field(..., description="Display order")
    word_count: int = Field(..., description="Section word count")


class CasinoReviewDoc(BaseModel):
    """
    Content Agent output: Structured casino review document
    Follows established content patterns from existing reviews
    """
    # Core content
    title: str = Field(..., description="Review title/headline")
    meta_description: str = Field(..., description="SEO meta description")
    excerpt: str = Field(..., description="Review excerpt/summary")
    
    # Review structure (following your established pattern)
    sections: List[ReviewSection] = Field(..., description="Ordered review sections")
    
    # Key highlights
    pros: List[str] = Field(..., description="Casino strengths/advantages") 
    cons: List[str] = Field(..., description="Casino limitations/disadvantages")
    overall_rating: float = Field(..., ge=1.0, le=10.0, description="Overall rating out of 10")
    
    # Category ratings
    game_variety_rating: float = Field(..., ge=1.0, le=10.0, description="Game selection rating")
    bonus_rating: float = Field(..., ge=1.0, le=10.0, description="Bonus offers rating")
    mobile_rating: float = Field(..., ge=1.0, le=10.0, description="Mobile experience rating")
    payment_rating: float = Field(..., ge=1.0, le=10.0, description="Payment speed/options rating")
    support_rating: float = Field(..., ge=1.0, le=10.0, description="Customer support rating")
    trust_rating: float = Field(..., ge=1.0, le=10.0, description="Trust & licensing rating")
    
    # Target audience
    ideal_for: List[str] = Field(..., description="Target player profiles")
    not_recommended_for: List[str] = Field(..., description="Players who should avoid")
    
    # Internal linking
    related_casinos: List[str] = Field(default_factory=list, description="Related casino review URLs")
    internal_links: List[Dict[str, str]] = Field(default_factory=list, description="Internal link suggestions")
    
    # Content metadata
    word_count: int = Field(..., description="Total review word count")
    reading_time: int = Field(..., description="Estimated reading time in minutes")
    content_template: str = Field(..., description="Template used for generation")
    
    # SEO optimization
    focus_keywords: List[str] = Field(..., description="Primary SEO keywords")
    semantic_keywords: List[str] = Field(default_factory=list, description="Semantic keyword variations")


class QAReport(BaseModel):
    """
    QA Agent output: Content validation report (BLOCKING)
    Implements WARP.md compliance requirements
    """
    # Core validation results
    overall_pass: bool = Field(..., description="Overall QA validation passed")
    compliance_score: float = Field(..., ge=0.0, le=1.0, description="Overall compliance score")
    failure_summary: str = Field("", description="Summary of validation failures")
    recommendations: List[str] = Field(default_factory=list, description="Improvement recommendations")
    
    # Detailed validation results
    factual_accuracy_pass: bool = Field(..., description="Factual accuracy verified")
    completeness_score: float = Field(..., ge=0.0, le=1.0, description="Content completeness (95% required)")
    compliance_pass: bool = Field(..., description="Regulatory/legal compliance")
    content_quality_pass: bool = Field(..., description="Content quality standards met")
    
    # Detailed validation results
    missing_fields: List[str] = Field(default_factory=list, description="Required fields not populated")
    factual_issues: List[str] = Field(default_factory=list, description="Potential factual errors")
    compliance_issues: List[str] = Field(default_factory=list, description="Compliance violations")
    quality_issues: List[str] = Field(default_factory=list, description="Content quality problems")
    
    # Content analysis
    word_count_adequate: bool = Field(..., description="Meets minimum word count (≥2500)")
    readability_score: float = Field(..., ge=0.0, le=100.0, description="Flesch reading ease score")
    keyword_density_ok: bool = Field(..., description="Keyword density within acceptable range")
    
    # Image and media validation
    featured_image_set: bool = Field(..., description="Featured image properly assigned")
    all_images_compliant: bool = Field(..., description="All images pass compliance guard")
    media_ids_valid: bool = Field(..., description="WordPress media IDs valid")
    
    # Final recommendation
    recommendation: str = Field(..., description="QA recommendation (PUBLISH/REVISE/REJECT)")
    priority_fixes: List[str] = Field(default_factory=list, description="Must-fix issues before publish")
    
    # QA metadata
    qa_timestamp: datetime = Field(default_factory=datetime.now, description="QA completion time")
    qa_agent_version: str = Field("1.0", description="QA agent version")


class PublishResult(BaseModel):
    """
    Publishing Agent output: WordPress publication result
    """
    # WordPress post data
    post_id: int = Field(..., description="WordPress post ID")
    post_url: HttpUrl = Field(..., description="Published post URL")
    post_status: str = Field(..., description="Post status (publish, draft, pending)")
    
    # Media assignments - flexible naming for compatibility
    featured_media_id: Optional[int] = Field(None, description="Featured image media ID")
    featured_image_id: Optional[int] = Field(None, description="Featured image media ID (alias)")
    additional_media_ids: List[int] = Field(default_factory=list, description="Additional attached media")
    media_ids: List[int] = Field(default_factory=list, description="All media IDs assigned")
    
    # MT Casino custom fields populated
    custom_fields_populated: int = Field(0, description="Number of custom fields set")
    taxonomies_assigned: List[str] = Field(default_factory=list, description="Assigned taxonomies/categories")
    categories_assigned: List[str] = Field(default_factory=list, description="Assigned categories")
    tags_assigned: List[str] = Field(default_factory=list, description="Assigned tags")
    
    # SEO Information
    meta_title: Optional[str] = Field(None, description="Published meta title")
    meta_description: Optional[str] = Field(None, description="Published meta description")
    
    # Content Information
    word_count: Optional[int] = Field(None, description="Published content word count")
    
    # Performance metrics
    processing_time_seconds: Optional[float] = Field(None, description="Total processing time")
    compliance_score: Optional[float] = Field(None, description="Compliance score")
    
    # Publication metadata
    published_timestamp: datetime = Field(default_factory=datetime.now, description="Publication time")
    tenant_id: str = Field(..., description="Publishing tenant")
    
    # Success metrics
    success: bool = Field(..., description="Publication successful")
    errors: List[str] = Field(default_factory=list, description="Any publication errors")
    warnings: List[str] = Field(default_factory=list, description="Non-critical warnings")


class CasinoResearchRequest(BaseModel):
    """
    Research Agent input schema
    """
    casino_name: str = Field(..., description="Target casino name")
    casino_url: HttpUrl = Field(..., description="Target casino URL")
    target_keywords: List[str] = Field(default_factory=list, description="Target SEO keywords")
    competitor_analysis: bool = Field(True, description="Include competitor analysis")
    research_depth: str = Field("comprehensive", description="Research depth (basic, standard, comprehensive)")
    tenant_id: str = Field("crashcasino", description="Tenant identifier")


class ScreenshotRequest(BaseModel):
    """
    Screenshot Agent input schema
    """
    casino_url: HttpUrl = Field(..., description="Target casino URL")
    casino_name: str = Field(..., description="Casino name for compliance")
    compliance_strict: bool = Field(True, description="Strict compliance checking")
    tenant_id: str = Field("crashcasino", description="Tenant identifier")
    
    # Optional advanced configuration
    viewport_configs: Optional[List[Dict[str, Any]]] = Field(None, description="Viewport configurations")
    capture_options: Dict[str, Any] = Field(default_factory=dict, description="Additional capture options")


class ContentGenerationRequest(BaseModel):
    """
    Content Generation Agent input schema
    """
    casino_name: str = Field(..., description="Casino name")
    casino_url: HttpUrl = Field(..., description="Casino URL")
    research_pack: Optional[CasinoResearchPack] = Field(None, description="Research data")
    screenshots: List[ScreenshotResult] = Field(default_factory=list, description="Screenshots")
    target_keywords: List[str] = Field(default_factory=list, description="Target keywords")
    content_style: str = Field("professional", description="Content writing style")
    minimum_word_count: int = Field(4000, description="Minimum word count")
    tenant_id: str = Field("crashcasino", description="Tenant identifier")


class QARequest(BaseModel):
    """
    QA Agent input schema
    """
    review_doc: CasinoReviewDoc = Field(..., description="Review document to validate")
    research_pack: Optional[CasinoResearchPack] = Field(None, description="Original research data")
    screenshots: List[ScreenshotResult] = Field(default_factory=list, description="Screenshots")
    strict_compliance: bool = Field(True, description="Strict compliance mode")
    tenant_id: str = Field("crashcasino", description="Tenant identifier")


class SEOPlan(BaseModel):
    """
    SEO optimization plan for casino reviews
    """
    primary_keywords: List[str] = Field(..., description="Primary target keywords")
    secondary_keywords: List[str] = Field(default_factory=list, description="Secondary keywords")
    meta_title: str = Field(..., description="Optimized meta title")
    meta_description: str = Field(..., description="Optimized meta description")
    content_strategy: str = Field(..., description="Content optimization strategy")
    internal_linking: List[Dict[str, str]] = Field(default_factory=list, description="Internal link suggestions")
    competitor_gaps: List[str] = Field(default_factory=list, description="Content gaps vs competitors")


class PublishingRequest(BaseModel):
    """
    Publishing Agent input schema
    """
    review_doc: CasinoReviewDoc = Field(..., description="Review document to publish")
    research_pack: Optional[CasinoResearchPack] = Field(None, description="Research data")
    screenshots: List[ScreenshotResult] = Field(default_factory=list, description="Screenshots")
    qa_report: QAReport = Field(..., description="QA validation report")
    tenant_id: str = Field("crashcasino", description="Tenant identifier")
    post_status: str = Field("draft", description="Post status (draft, publish)")


class CasinoReviewRequest(BaseModel):
    """
    Input schema for casino review generation request
    """
    casino_name: str = Field(..., description="Target casino name")
    casino_url: HttpUrl = Field(..., description="Target casino URL")
    tenant_id: str = Field("crashcasino", description="Tenant identifier")
    priority: str = Field("normal", description="Processing priority (low, normal, high)")
    custom_instructions: Optional[str] = Field(None, description="Special review instructions")
    target_keywords: List[str] = Field(default_factory=list, description="Target SEO keywords")
    publish_immediately: bool = Field(True, description="Publish immediately or save as draft")
    
    # Override settings
    skip_qa: bool = Field(False, description="Skip QA validation (NOT RECOMMENDED)")
    force_publish: bool = Field(False, description="Force publish despite QA failures (DANGEROUS)")


# Validation helpers
@validator('word_count_adequate')
def validate_word_count(cls, v, values):
    """Ensure minimum word count requirement is met"""
    if 'word_count' in values and values['word_count'] < 2500:
        return False
    return v
