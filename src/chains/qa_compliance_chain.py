"""
🛡️ QA & Compliance Chain
Task-014: LCEL QA chain for affiliate compliance, fact-checking, and brand style validation

Features:
- Affiliate compliance validation (18+, responsible gambling, disclosure)
- Factual accuracy verification against source data
- Brand style and voice consistency checking
- Multi-tenant compliance rules per jurisdiction
- Human-in-the-loop override workflow integration
- Publishing gate with detailed failure reporting
"""

from typing import Dict, Any, List, Optional, Union, Tuple
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum
import logging
import re
from pathlib import Path

from langchain_core.runnables import (
    RunnablePassthrough, 
    RunnableLambda, 
    RunnableParallel,
    RunnableBranch
)
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import StrOutputParser, PydanticOutputParser
from langchain_openai import ChatOpenAI
from langchain_core.documents import Document

# Import our components
from src.schemas.review_doc import ReviewDoc, QAReport, QualityScore, ComplianceStatus, TenantConfiguration
from src.schemas.casino_intelligence_schema import CasinoIntelligence


logger = logging.getLogger(__name__)


class QAValidationLevel(str, Enum):
    """QA validation intensity levels"""
    BASIC = "basic"              # Essential compliance only
    STANDARD = "standard"        # Full fact-checking and style
    STRICT = "strict"           # Enhanced validation for premium content
    PREMIUM = "premium"         # Maximum validation with human review


class QAValidationInput(BaseModel):
    """Input for QA validation chain"""
    review_doc: ReviewDoc = Field(description="Review document to validate")
    validation_level: QAValidationLevel = Field(default=QAValidationLevel.STANDARD)
    source_documents: List[Document] = Field(default_factory=list, description="Source documents for fact-checking")
    brand_guidelines: Optional[Dict[str, Any]] = Field(default=None, description="Brand-specific guidelines")
    compliance_rules: Optional[Dict[str, Any]] = Field(default=None, description="Jurisdiction-specific compliance rules")
    human_reviewer_available: bool = Field(default=False, description="Whether human reviewer is available for override")


class QAValidationOutput(BaseModel):
    """Output from QA validation chain"""
    qa_report: QAReport = Field(description="Complete QA validation report")
    publish_approved: bool = Field(description="Whether content is approved for publishing")
    validation_score: float = Field(description="Overall validation score (0-10)", ge=0, le=10)
    detailed_feedback: Dict[str, Any] = Field(description="Detailed validation feedback")
    human_review_required: bool = Field(description="Whether human review is required")
    blocking_issues: List[str] = Field(description="Issues that block publishing")
    warnings: List[str] = Field(description="Non-blocking warnings")
    processing_metadata: Dict[str, Any] = Field(description="Validation processing metadata")


class AffiliateComplianceValidator:
    """Validates affiliate compliance requirements"""
    
    # Required compliance elements
    REQUIRED_DISCLAIMERS = {
        "age_verification": r"18\+|eighteen|adult|age",
        "responsible_gambling": r"responsible.{0,20}gambl|gambl.{0,20}responsible|problem.{0,20}gambl",
        "affiliate_disclosure": r"affiliate|partner|commission|earn|paid"
    }
    
    # Prohibited content patterns
    PROHIBITED_PATTERNS = {
        "guaranteed_wins": r"guaranteed.{0,20}win|sure.{0,20}win|cannot.{0,20}lose",
        "underage_targeting": r"kids|children|teen|school|young",
        "medical_claims": r"cure|treat|therapy|medical|health.{0,20}benefit",
        "investment_language": r"investment|return|profit.{0,20}guaranteed"
    }
    
    def __init__(self, tenant_config: TenantConfiguration):
        self.tenant_config = tenant_config
        self.jurisdiction_rules = self._load_jurisdiction_rules()
    
    def _load_jurisdiction_rules(self) -> Dict[str, Any]:
        """Load jurisdiction-specific compliance rules"""
        # In a real implementation, this would load from configuration files
        jurisdiction_rules = {
            "UK": {
                "required_disclaimers": ["18+", "gambleaware.org"],
                "prohibited_terms": ["guaranteed", "risk-free"],
                "license_display": True
            },
            "DE": {
                "required_disclaimers": ["18+", "spielen-mit-verantwortung.de"],
                "prohibited_terms": ["sicher gewinnen", "garantiert"],
                "license_display": True
            },
            "US": {
                "required_disclaimers": ["21+", "responsible gambling"],
                "prohibited_terms": ["guaranteed wins", "sure thing"],
                "state_specific_rules": True
            }
        }
        
        # Determine jurisdiction from tenant config
        locale = self.tenant_config.locale.upper()
        if locale.startswith("DE"):
            return jurisdiction_rules.get("DE", {})
        elif locale.startswith("EN") and "UK" in self.tenant_config.compliance_requirements:
            return jurisdiction_rules.get("UK", {})
        elif locale.startswith("EN") and "US" in self.tenant_config.compliance_requirements:
            return jurisdiction_rules.get("US", {})
        else:
            return {}
    
    def validate_affiliate_compliance(self, content: str) -> Dict[str, Any]:
        """Validate affiliate compliance requirements"""
        results = {
            "passed": True,
            "score": 10.0,
            "violations": [],
            "missing_disclaimers": [],
            "prohibited_content": []
        }
        
        content_lower = content.lower()
        
        # Check required disclaimers
        for disclaimer_type, pattern in self.REQUIRED_DISCLAIMERS.items():
            if not re.search(pattern, content_lower):
                results["missing_disclaimers"].append(disclaimer_type)
                results["passed"] = False
                results["score"] -= 2.0
        
        # Check prohibited content
        for violation_type, pattern in self.PROHIBITED_PATTERNS.items():
            if re.search(pattern, content_lower):
                results["prohibited_content"].append(violation_type)
                results["passed"] = False
                results["score"] -= 3.0
        
        # Jurisdiction-specific checks
        if self.jurisdiction_rules:
            for term in self.jurisdiction_rules.get("prohibited_terms", []):
                if term.lower() in content_lower:
                    results["violations"].append(f"Jurisdiction prohibited term: {term}")
                    results["passed"] = False
                    results["score"] -= 2.0
        
        # Ensure score doesn't go below 0
        results["score"] = max(0.0, results["score"])
        
        return results


class FactualAccuracyValidator:
    """Validates factual accuracy against source documents"""
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self._build_validation_chain()
    
    def _build_validation_chain(self):
        """Build LCEL chain for fact validation"""
        fact_check_prompt = ChatPromptTemplate.from_template("""
You are a fact-checking expert. Compare the CONTENT against the SOURCE DOCUMENTS and identify any factual errors.

CONTENT TO CHECK:
{content}

SOURCE DOCUMENTS:
{sources}

Check for:
1. Incorrect license numbers or regulatory information
2. Wrong bonus amounts or terms
3. Inaccurate payment methods or timeframes
4. Incorrect game provider information
5. False claims about features or services

Respond with JSON format:
{
    "factual_errors": [
        {
            "claim": "specific claim from content",
            "issue": "description of factual error",
            "severity": "high|medium|low",
            "source_contradiction": "what the source actually says"
        }
    ],
    "accuracy_score": 8.5,
    "verified_claims": ["list of claims that are factually correct"],
    "unverifiable_claims": ["claims that cannot be verified from sources"]
}
""")
        
        self.fact_check_chain = (
            fact_check_prompt 
            | self.llm 
            | StrOutputParser()
        )
    
    def validate_factual_accuracy(self, content: str, source_documents: List[Document]) -> Dict[str, Any]:
        """Validate factual accuracy of content"""
        if not source_documents:
            return {
                "passed": False,
                "score": 0.0,
                "errors": ["No source documents provided for fact-checking"],
                "verified_claims": [],
                "unverifiable_claims": ["All claims unverifiable without sources"]
            }
        
        # Format source documents
        sources_text = "\n\n".join([
            f"Source {i+1}: {doc.page_content}"
            for i, doc in enumerate(source_documents)
        ])
        
        try:
            # Execute fact-checking chain
            result = self.fact_check_chain.invoke({
                "content": content[:4000],  # Truncate for token limits
                "sources": sources_text[:4000]
            })
            
            # Parse JSON response (in real implementation, would use PydanticOutputParser)
            import json
            try:
                parsed_result = json.loads(result)
                return {
                    "passed": len(parsed_result.get("factual_errors", [])) == 0,
                    "score": parsed_result.get("accuracy_score", 0.0),
                    "errors": [error["claim"] + ": " + error["issue"] 
                             for error in parsed_result.get("factual_errors", [])],
                    "verified_claims": parsed_result.get("verified_claims", []),
                    "unverifiable_claims": parsed_result.get("unverifiable_claims", [])
                }
            except json.JSONDecodeError:
                return {
                    "passed": False,
                    "score": 0.0,
                    "errors": ["Unable to parse fact-checking results"],
                    "verified_claims": [],
                    "unverifiable_claims": []
                }
                
        except Exception as e:
            logger.error(f"Fact-checking failed: {str(e)}")
            return {
                "passed": False,
                "score": 0.0,
                "errors": [f"Fact-checking error: {str(e)}"],
                "verified_claims": [],
                "unverifiable_claims": []
            }


class BrandStyleValidator:
    """Validates brand voice and style consistency"""
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self._build_style_validation_chain()
    
    def _build_style_validation_chain(self):
        """Build LCEL chain for style validation"""
        style_check_prompt = ChatPromptTemplate.from_template("""
You are a brand style expert. Evaluate the CONTENT against the BRAND GUIDELINES for voice, tone, and style consistency.

CONTENT TO EVALUATE:
{content}

BRAND GUIDELINES:
- Voice Profile: {voice_profile}
- Target Audience: {target_audience}
- Brand Values: {brand_values}
- Content Guidelines: {content_guidelines}
- Prohibited Language: {prohibited_language}

Evaluate for:
1. Voice consistency (professional, friendly, enthusiastic, etc.)
2. Tone appropriateness for target audience
3. Brand value alignment
4. Content guideline adherence
5. Prohibited language usage

Respond with JSON format:
{
    "style_score": 8.5,
    "voice_consistency": true,
    "tone_issues": ["specific tone issues if any"],
    "brand_alignment": true,
    "guideline_violations": ["specific violations if any"],
    "prohibited_language_found": ["any prohibited terms found"],
    "improvement_suggestions": ["specific suggestions for improvement"]
}
""")
        
        self.style_check_chain = (
            style_check_prompt 
            | self.llm 
            | StrOutputParser()
        )
    
    def validate_brand_style(self, content: str, tenant_config: TenantConfiguration, 
                           brand_guidelines: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Validate brand style and voice consistency"""
        
        guidelines = brand_guidelines or {}
        
        try:
            # Execute style validation chain
            result = self.style_check_chain.invoke({
                "content": content[:3000],  # Truncate for token limits
                "voice_profile": tenant_config.voice_profile or "professional",
                "target_audience": ", ".join(tenant_config.target_demographics or []),
                "brand_values": guidelines.get("brand_values", "integrity, transparency"),
                "content_guidelines": tenant_config.content_guidelines or "high-quality, informative",
                "prohibited_language": ", ".join(guidelines.get("prohibited_terms", []))
            })
            
            # Parse JSON response
            import json
            try:
                parsed_result = json.loads(result)
                
                # Calculate pass/fail
                style_issues = (
                    len(parsed_result.get("tone_issues", [])) +
                    len(parsed_result.get("guideline_violations", [])) +
                    len(parsed_result.get("prohibited_language_found", []))
                )
                
                return {
                    "passed": style_issues == 0,
                    "score": parsed_result.get("style_score", 0.0),
                    "voice_consistent": parsed_result.get("voice_consistency", False),
                    "issues": (
                        parsed_result.get("tone_issues", []) +
                        parsed_result.get("guideline_violations", []) +
                        parsed_result.get("prohibited_language_found", [])
                    ),
                    "suggestions": parsed_result.get("improvement_suggestions", [])
                }
            except json.JSONDecodeError:
                return {
                    "passed": False,
                    "score": 0.0,
                    "voice_consistent": False,
                    "issues": ["Unable to parse style validation results"],
                    "suggestions": []
                }
                
        except Exception as e:
            logger.error(f"Style validation failed: {str(e)}")
            return {
                "passed": False,
                "score": 0.0,
                "voice_consistent": False,
                "issues": [f"Style validation error: {str(e)}"],
                "suggestions": []
            }


class ContentQualityValidator:
    """Validates overall content quality metrics"""
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self._build_quality_validation_chain()
    
    def _build_quality_validation_chain(self):
        """Build LCEL chain for quality validation"""
        quality_check_prompt = ChatPromptTemplate.from_template("""
You are a content quality expert. Evaluate the CONTENT for overall quality, completeness, and readability.

CONTENT TO EVALUATE:
{content}

Evaluate for:
1. Content completeness (covers all required sections)
2. Information depth and detail
3. Readability and structure
4. Grammar and language quality
5. Professional presentation
6. Call-to-action presence and effectiveness

Required sections to check for:
{required_sections}

Respond with JSON format:
{
    "quality_score": 8.5,
    "completeness_score": 9.0,
    "readability_score": 8.0,
    "structure_score": 8.5,
    "grammar_score": 9.5,
    "missing_sections": ["sections not found"],
    "quality_issues": ["specific quality problems"],
    "improvement_areas": ["areas needing improvement"],
    "word_count": 2450,
    "paragraph_count": 15
}
""")
        
        self.quality_check_chain = (
            quality_check_prompt 
            | self.llm 
            | StrOutputParser()
        )
    
    def validate_content_quality(self, content: str, required_sections: List[str] = None) -> Dict[str, Any]:
        """Validate overall content quality"""
        
        default_sections = [
            "introduction", "games", "bonuses", "payments", 
            "support", "mobile", "conclusion", "disclaimer"
        ]
        sections_to_check = required_sections or default_sections
        
        try:
            # Execute quality validation chain
            result = self.quality_check_chain.invoke({
                "content": content,
                "required_sections": ", ".join(sections_to_check)
            })
            
            # Parse JSON response
            import json
            try:
                parsed_result = json.loads(result)
                
                # Calculate overall quality pass/fail (threshold: 7.0)
                quality_score = parsed_result.get("quality_score", 0.0)
                
                return {
                    "passed": quality_score >= 7.0,
                    "score": quality_score,
                    "completeness": parsed_result.get("completeness_score", 0.0),
                    "readability": parsed_result.get("readability_score", 0.0),
                    "structure": parsed_result.get("structure_score", 0.0),
                    "grammar": parsed_result.get("grammar_score", 0.0),
                    "missing_sections": parsed_result.get("missing_sections", []),
                    "issues": parsed_result.get("quality_issues", []),
                    "improvements": parsed_result.get("improvement_areas", []),
                    "word_count": parsed_result.get("word_count", 0),
                    "paragraph_count": parsed_result.get("paragraph_count", 0)
                }
            except json.JSONDecodeError:
                return {
                    "passed": False,
                    "score": 0.0,
                    "completeness": 0.0,
                    "readability": 0.0,
                    "structure": 0.0,
                    "grammar": 0.0,
                    "missing_sections": ["Unable to parse quality results"],
                    "issues": ["Quality parsing error"],
                    "improvements": [],
                    "word_count": len(content.split()),
                    "paragraph_count": content.count('</p>')
                }
                
        except Exception as e:
            logger.error(f"Quality validation failed: {str(e)}")
            return {
                "passed": False,
                "score": 0.0,
                "completeness": 0.0,
                "readability": 0.0,
                "structure": 0.0,
                "grammar": 0.0,
                "missing_sections": [],
                "issues": [f"Quality validation error: {str(e)}"],
                "improvements": [],
                "word_count": len(content.split()) if content else 0,
                "paragraph_count": content.count('</p>') if content else 0
            }


class HumanReviewGateway:
    """Manages human-in-the-loop review workflow"""
    
    def __init__(self):
        self.pending_reviews: Dict[str, Dict[str, Any]] = {}
    
    def requires_human_review(self, validation_results: Dict[str, Any], 
                            validation_level: QAValidationLevel) -> bool:
        """Determine if human review is required"""
        
        # Always require human review for premium content
        if validation_level == QAValidationLevel.PREMIUM:
            return True
        
        # Require human review for serious compliance violations
        compliance_score = validation_results.get("compliance", {}).get("score", 10.0)
        if compliance_score < 5.0:
            return True
        
        # Require human review for factual accuracy issues
        factual_score = validation_results.get("factual", {}).get("score", 10.0)
        if factual_score < 6.0:
            return True
        
        # Require human review for poor overall quality
        quality_score = validation_results.get("quality", {}).get("score", 10.0)
        if quality_score < 6.0:
            return True
        
        return False
    
    def submit_for_human_review(self, review_doc: ReviewDoc, 
                               validation_results: Dict[str, Any]) -> str:
        """Submit content for human review and return review ID"""
        
        review_id = f"human_review_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.pending_reviews[review_id] = {
            "review_doc": review_doc,
            "validation_results": validation_results,
            "submitted_at": datetime.now(),
            "status": "pending",
            "reviewer": None,
            "review_notes": None
        }
        
        logger.info(f"Content submitted for human review: {review_id}")
        return review_id
    
    def get_human_review_status(self, review_id: str) -> Dict[str, Any]:
        """Get status of human review"""
        return self.pending_reviews.get(review_id, {"status": "not_found"})


class QAComplianceChain:
    """
    Complete LCEL chain for QA validation and compliance checking
    """
    
    def __init__(
        self,
        llm: Optional[ChatOpenAI] = None,
        validation_level: QAValidationLevel = QAValidationLevel.STANDARD
    ):
        self.llm = llm or ChatOpenAI(
            model="gpt-4o",
            temperature=0.1,  # Low temperature for consistent validation
            max_tokens=2048
        )
        self.validation_level = validation_level
        
        # Initialize validators
        self.factual_validator = FactualAccuracyValidator(self.llm)
        self.style_validator = BrandStyleValidator(self.llm)
        self.quality_validator = ContentQualityValidator(self.llm)
        self.human_gateway = HumanReviewGateway()
        
        # Build the LCEL chain
        self.chain = self._build_chain()
    
    def _build_chain(self):
        """Build the complete QA validation LCEL chain"""
        
        # Step 1: Initialize compliance validator for tenant
        def create_compliance_validator(input_data: QAValidationInput):
            """Create tenant-specific compliance validator"""
            return AffiliateComplianceValidator(input_data.review_doc.tenant_config)
        
        # Step 2: Run parallel validation
        def run_parallel_validation(data: Dict[str, Any]) -> Dict[str, Any]:
            """Execute all validation checks in parallel"""
            input_data = data["input"]
            compliance_validator = data["compliance_validator"]
            
            content = input_data.review_doc.content
            
            # Compliance validation
            compliance_results = compliance_validator.validate_affiliate_compliance(content)
            
            # Factual accuracy validation (if source documents provided)
            if input_data.source_documents:
                factual_results = self.factual_validator.validate_factual_accuracy(
                    content, input_data.source_documents
                )
            else:
                factual_results = {
                    "passed": True,  # Skip if no sources
                    "score": 10.0,
                    "errors": [],
                    "verified_claims": [],
                    "unverifiable_claims": []
                }
            
            # Brand style validation
            style_results = self.style_validator.validate_brand_style(
                content, 
                input_data.review_doc.tenant_config,
                input_data.brand_guidelines
            )
            
            # Content quality validation
            quality_results = self.quality_validator.validate_content_quality(content)
            
            return {
                "compliance": compliance_results,
                "factual": factual_results,
                "style": style_results,
                "quality": quality_results
            }
        
        # Step 3: Calculate overall validation results
        def calculate_validation_results(data: Dict[str, Any]) -> Dict[str, Any]:
            """Calculate overall validation results and recommendations"""
            input_data = data["input"]
            validation_results = data["validation_results"]
            
            # Calculate weighted overall score
            weights = {
                "compliance": 0.3,  # Critical for legal requirements
                "factual": 0.25,    # Important for credibility
                "style": 0.2,       # Important for brand consistency
                "quality": 0.25     # Important for user experience
            }
            
            overall_score = sum(
                validation_results[category]["score"] * weight
                for category, weight in weights.items()
                if category in validation_results
            )
            
            # Determine if all validations passed
            all_passed = all(
                validation_results[category]["passed"]
                for category in validation_results
            )
            
            # Collect all blocking issues
            blocking_issues = []
            warnings = []
            
            for category, results in validation_results.items():
                if not results["passed"]:
                    category_issues = results.get("errors", results.get("issues", []))
                    if results["score"] < 5.0:  # Critical failure threshold
                        blocking_issues.extend([f"{category}: {issue}" for issue in category_issues])
                    else:
                        warnings.extend([f"{category}: {issue}" for issue in category_issues])
            
            # Check if human review is required
            human_review_required = self.human_gateway.requires_human_review(
                validation_results, input_data.validation_level
            )
            
            # Determine publish approval
            publish_approved = (
                all_passed and 
                overall_score >= 7.0 and 
                len(blocking_issues) == 0 and
                (not human_review_required or input_data.human_reviewer_available)
            )
            
            return {
                "overall_score": overall_score,
                "all_passed": all_passed,
                "publish_approved": publish_approved,
                "blocking_issues": blocking_issues,
                "warnings": warnings,
                "human_review_required": human_review_required
            }
        
        # Step 4: Create QA Report
        def create_qa_report(data: Dict[str, Any]) -> QAReport:
            """Create comprehensive QA report"""
            input_data = data["input"]
            validation_results = data["validation_results"] 
            calculated_results = data["calculated_results"]
            
            # Determine overall quality score enum
            score = calculated_results["overall_score"]
            if score >= 9.0:
                quality_score = QualityScore.EXCELLENT
            elif score >= 7.5:
                quality_score = QualityScore.GOOD
            elif score >= 6.0:
                quality_score = QualityScore.ACCEPTABLE
            elif score >= 3.0:
                quality_score = QualityScore.POOR
            else:
                quality_score = QualityScore.FAILED
            
            # Determine compliance status
            compliance_passed = validation_results["compliance"]["passed"]
            if compliance_passed and calculated_results["all_passed"]:
                compliance_status = ComplianceStatus.PASSED
            elif len(calculated_results["blocking_issues"]) > 0:
                compliance_status = ComplianceStatus.FAILED
            elif len(calculated_results["warnings"]) > 0:
                compliance_status = ComplianceStatus.WARNING
            else:
                compliance_status = ComplianceStatus.PENDING_REVIEW
            
            return QAReport(
                review_doc_id=input_data.review_doc.title,  # Use title as ID for now
                overall_quality=quality_score,
                compliance_status=compliance_status,
                factual_accuracy_score=validation_results["factual"]["score"],
                brand_voice_consistency=validation_results["style"]["voice_consistent"],
                content_completeness=validation_results["quality"]["completeness"],
                readability_score=validation_results["quality"]["readability"],
                seo_optimization_score=8.0,  # Placeholder - would be calculated separately
                image_compliance=ComplianceStatus.PASSED,  # Placeholder
                affiliate_compliance=ComplianceStatus.PASSED if compliance_passed else ComplianceStatus.FAILED,
                validation_errors=calculated_results["blocking_issues"],
                improvement_suggestions=(
                    validation_results["quality"].get("improvements", []) +
                    validation_results["style"].get("suggestions", [])
                ),
                human_review_required=calculated_results["human_review_required"],
                reviewer_notes="Automated QA validation completed",
                qa_timestamp=datetime.now()
            )
        
        # Step 5: Create final output
        def create_output(data: Dict[str, Any]) -> QAValidationOutput:
            """Create final validation output"""
            input_data = data["input"]
            validation_results = data["validation_results"]
            calculated_results = data["calculated_results"]
            qa_report = data["qa_report"]
            
            # Detailed feedback compilation
            detailed_feedback = {
                "compliance_details": validation_results["compliance"],
                "factual_details": validation_results["factual"],
                "style_details": validation_results["style"],
                "quality_details": validation_results["quality"],
                "validation_level": input_data.validation_level.value,
                "tenant_id": input_data.review_doc.tenant_id
            }
            
            # Processing metadata
            processing_metadata = {
                "validation_timestamp": datetime.now().isoformat(),
                "llm_model_used": self.llm.model_name,
                "validation_level": input_data.validation_level.value,
                "source_documents_count": len(input_data.source_documents),
                "content_word_count": validation_results["quality"]["word_count"],
                "processing_duration_ms": 0,  # Would track actual duration
                "validators_used": ["compliance", "factual", "style", "quality"]
            }
            
            return QAValidationOutput(
                qa_report=qa_report,
                publish_approved=calculated_results["publish_approved"],
                validation_score=calculated_results["overall_score"],
                detailed_feedback=detailed_feedback,
                human_review_required=calculated_results["human_review_required"],
                blocking_issues=calculated_results["blocking_issues"],
                warnings=calculated_results["warnings"],
                processing_metadata=processing_metadata
            )
        
        # Build the complete LCEL chain
        chain = (
            RunnablePassthrough.assign(
                # Step 1: Create compliance validator
                compliance_validator=RunnableLambda(create_compliance_validator)
            )
            | RunnablePassthrough.assign(
                # Step 2: Run parallel validation
                validation_results=RunnableLambda(run_parallel_validation)
            )
            | RunnablePassthrough.assign(
                # Step 3: Calculate results
                calculated_results=RunnableLambda(calculate_validation_results)
            )
            | RunnablePassthrough.assign(
                # Step 4: Create QA report
                qa_report=RunnableLambda(create_qa_report)
            )
            | RunnableLambda(create_output)
        )
        
        return chain
    
    def validate_content(self, input_data: QAValidationInput) -> QAValidationOutput:
        """
        Validate content using the complete QA chain
        
        Args:
            input_data: Complete validation input specification
            
        Returns:
            Comprehensive validation results with publish recommendation
        """
        try:
            # Execute the chain
            result = self.chain.invoke({"input": input_data})
            
            logger.info(f"QA validation completed for {input_data.review_doc.title}")
            logger.info(f"Validation score: {result.validation_score:.2f}")
            logger.info(f"Publish approved: {result.publish_approved}")
            
            # Submit for human review if required
            if result.human_review_required and input_data.human_reviewer_available:
                review_id = self.human_gateway.submit_for_human_review(
                    input_data.review_doc, 
                    result.detailed_feedback
                )
                result.processing_metadata["human_review_id"] = review_id
                logger.info(f"Submitted for human review: {review_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"QA validation failed: {str(e)}")
            
            # Return failure result
            return QAValidationOutput(
                qa_report=QAReport(
                    review_doc_id=input_data.review_doc.title,
                    overall_quality=QualityScore.FAILED,
                    compliance_status=ComplianceStatus.FAILED,
                    validation_errors=[f"Validation system error: {str(e)}"],
                    human_review_required=True,
                    qa_timestamp=datetime.now()
                ),
                publish_approved=False,
                validation_score=0.0,
                detailed_feedback={"error": str(e)},
                human_review_required=True,
                blocking_issues=[f"System error: {str(e)}"],
                warnings=[],
                processing_metadata={
                    "error": str(e),
                    "validation_timestamp": datetime.now().isoformat()
                }
            )


# Factory function for easy instantiation
def create_qa_compliance_chain(
    llm_model: str = "gpt-4o",
    validation_level: QAValidationLevel = QAValidationLevel.STANDARD,
    temperature: float = 0.1
) -> QAComplianceChain:
    """
    Create a QA compliance chain with specified parameters
    
    Args:
        llm_model: LLM model name
        validation_level: Validation intensity level
        temperature: LLM temperature (low for consistency)
        
    Returns:
        Configured QA compliance chain
    """
    llm = ChatOpenAI(
        model=llm_model,
        temperature=temperature,
        max_tokens=2048
    )
    
    return QAComplianceChain(
        llm=llm,
        validation_level=validation_level
    )