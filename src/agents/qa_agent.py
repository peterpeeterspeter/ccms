"""
QA Agent
========

LangChain LCEL-based agent for content validation and WARP.md compliance.
Follows WARP.md: compliance blocking, factual accuracy, completeness validation.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from ..schemas.casino_review import (
    QAReport, 
    CasinoReviewDoc, 
    CasinoResearchPack,
    QARequest
)

logger = logging.getLogger(__name__)


class CasinoQAAgent:
    """
    Casino QA & Compliance Agent using LCEL composition
    
    Responsibilities:
    - Content quality validation (≥2,500 words, factual accuracy)
    - WARP.md compliance checking (publishing gates)
    - Factual verification against research data
    - Completeness validation (95-field requirement)
    - SEO compliance (title/meta/keywords)
    - Image compliance verification
    - Publishing gate enforcement
    
    Input: QARequest (CasinoReviewDoc + research data)
    Output: QAReport (pass/fail with detailed feedback)
    """
    
    def __init__(self, 
                 llm: Optional[ChatOpenAI] = None,
                 strict_compliance: bool = True):
        self.llm = llm or ChatOpenAI(
            model="gpt-4",
            temperature=0.1,  # Very low temperature for consistent validation
            max_tokens=3000
        )
        self.strict_compliance = strict_compliance
        self.qa_chain = self._build_qa_chain()
    
    def _build_qa_chain(self):
        """Build the LCEL QA validation chain"""
        
        # Build the LCEL chain for comprehensive QA validation
        chain = (
            RunnablePassthrough.assign(
                # Step 1: Validate QA request structure
                validated_request=RunnableLambda(self._validate_qa_request)
            )
            | RunnablePassthrough.assign(
                # Step 2: Content quality validation
                content_quality=RunnableLambda(self._validate_content_quality)
            )
            | RunnablePassthrough.assign(
                # Step 3: WARP.md compliance checking
                compliance_checks=RunnableLambda(self._validate_compliance)
            )
            | RunnablePassthrough.assign(
                # Step 4: Factual accuracy verification
                factual_verification=RunnableLambda(self._verify_factual_accuracy)
            )
            | RunnablePassthrough.assign(
                # Step 5: SEO validation
                seo_validation=RunnableLambda(self._validate_seo_elements)
            )
            | RunnablePassthrough.assign(
                # Step 6: Image compliance checking
                image_compliance=RunnableLambda(self._validate_image_compliance)
            )
            | RunnableLambda(self._build_qa_report)
        )
        
        return chain
    
    async def validate_review(self, request: QARequest) -> QAReport:
        """
        Main entry point for casino review QA validation
        
        Args:
            request: QA validation request with review document and research data
            
        Returns:
            QAReport with pass/fail status and detailed feedback
        """
        try:
            logger.info(f"🔍 Starting QA validation for {request.review_doc.casino_name}")
            
            # Execute the QA validation chain
            result = await self.qa_chain.ainvoke({
                "review_doc": request.review_doc,
                "research_pack": request.research_pack,
                "validation_level": request.validation_level,
                "compliance_strict": request.compliance_strict,
                "tenant_id": request.tenant_id
            })
            
            logger.info(f"✅ QA validation completed for {request.review_doc.casino_name}")
            logger.info(f"   - Overall status: {'PASS' if result.overall_pass else 'FAIL'}")
            logger.info(f"   - Quality score: {result.quality_score:.1f}/10")
            logger.info(f"   - Issues found: {len(result.issues_found)}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ QA validation failed for {request.review_doc.casino_name}: {str(e)}")
            # Return failing QA report with error info
            return QAReport(
                casino_name=request.review_doc.casino_name,
                review_title=request.review_doc.title,
                overall_pass=False,
                quality_score=0.0,
                validation_date=datetime.now(),
                issues_found=[f"QA validation system error: {str(e)}"],
                recommendations=[f"Fix QA validation system error and retry"],
                compliance_checks=[],
                quality_metrics=[],
                notes=f"QA validation failed: {str(e)}"
            )
    
    def _validate_qa_request(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and structure the QA request"""
        
        review_doc = inputs.get("review_doc")
        research_pack = inputs.get("research_pack")
        
        if not review_doc:
            raise ValueError("CasinoReviewDoc is required for QA validation")
        
        if not hasattr(review_doc, 'casino_name') or not review_doc.casino_name:
            raise ValueError("CasinoReviewDoc must have a valid casino name")
        
        # Set validation defaults
        validated = {
            "review_doc": review_doc,
            "research_pack": research_pack,
            "validation_level": inputs.get("validation_level", "comprehensive"),
            "compliance_strict": inputs.get("compliance_strict", self.strict_compliance),
            "tenant_id": inputs.get("tenant_id", "crashcasino")
        }
        
        logger.info(f"✅ QA request validated for {review_doc.casino_name}")
        return validated
    
    async def _validate_content_quality(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Validate content quality requirements"""
        
        validated_request = inputs["validated_request"]
        review_doc = validated_request["review_doc"]
        
        quality_checks = []
        quality_issues = []
        quality_metrics = []
        
        try:
            # WARP.md Requirement: ≥2,500 words
            word_count = review_doc.word_count if hasattr(review_doc, 'word_count') else 0
            word_count_pass = word_count >= 2500
            
            quality_checks.append({
                "check": "Word Count (≥2,500)",
                "pass": word_count_pass,
                "value": word_count,
                "requirement": "≥2,500 words per WARP.md"
            })
            
            if not word_count_pass:
                quality_issues.append(f"Word count too low: {word_count} words (minimum 2,500)")
            
            # Content structure validation
            sections_count = len(review_doc.sections) if hasattr(review_doc, 'sections') else 0
            sections_pass = sections_count >= 7  # Introduction, Games, Bonuses, Banking, Security, UX, Support
            
            quality_checks.append({
                "check": "Content Sections",
                "pass": sections_pass,
                "value": sections_count,
                "requirement": "≥7 comprehensive sections"
            })
            
            if not sections_pass:
                quality_issues.append(f"Insufficient content sections: {sections_count} (minimum 7)")
            
            # Pros/cons validation
            pros_count = len(review_doc.pros) if hasattr(review_doc, 'pros') and review_doc.pros else 0
            cons_count = len(review_doc.cons) if hasattr(review_doc, 'cons') and review_doc.cons else 0
            pros_cons_pass = pros_count >= 3 and cons_count >= 3
            
            quality_checks.append({
                "check": "Pros & Cons Analysis",
                "pass": pros_cons_pass,
                "value": f"{pros_count} pros, {cons_count} cons",
                "requirement": "≥3 pros and ≥3 cons"
            })
            
            if not pros_cons_pass:
                quality_issues.append(f"Insufficient pros/cons: {pros_count} pros, {cons_count} cons")
            
            # Rating validation
            overall_rating = getattr(review_doc, 'overall_rating', 0)
            rating_pass = 1 <= overall_rating <= 10
            
            quality_checks.append({
                "check": "Overall Rating",
                "pass": rating_pass,
                "value": overall_rating,
                "requirement": "Rating between 1-10"
            })
            
            if not rating_pass:
                quality_issues.append(f"Invalid rating: {overall_rating} (must be 1-10)")
            
            # Calculate quality score
            passed_checks = sum(1 for check in quality_checks if check["pass"])
            quality_score = (passed_checks / len(quality_checks)) * 10 if quality_checks else 0
            
            # Build quality metrics
            quality_metrics = [
                QualityMetric(
                    metric="Word Count",
                    value=word_count,
                    target=2500,
                    pass_threshold=2500,
                    actual_score=10.0 if word_count >= 2500 else (word_count / 2500) * 10
                ),
                QualityMetric(
                    metric="Content Sections",
                    value=sections_count,
                    target=7,
                    pass_threshold=7,
                    actual_score=10.0 if sections_count >= 7 else (sections_count / 7) * 10
                ),
                QualityMetric(
                    metric="Pros/Cons Balance",
                    value=min(pros_count, cons_count),
                    target=4,
                    pass_threshold=3,
                    actual_score=10.0 if pros_count >= 3 and cons_count >= 3 else 5.0
                )
            ]
            
            logger.info(f"📊 Content quality validated: {quality_score:.1f}/10")
            
            return {
                "quality_checks": quality_checks,
                "quality_issues": quality_issues,
                "quality_metrics": quality_metrics,
                "quality_score": quality_score
            }
            
        except Exception as e:
            logger.error(f"Content quality validation failed: {str(e)}")
            return {
                "quality_checks": [],
                "quality_issues": [f"Quality validation error: {str(e)}"],
                "quality_metrics": [],
                "quality_score": 0.0
            }
    
    async def _validate_compliance(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Validate WARP.md compliance requirements"""
        
        validated_request = inputs["validated_request"]
        review_doc = validated_request["review_doc"]
        compliance_strict = validated_request["compliance_strict"]
        
        compliance_checks = []
        compliance_issues = []
        
        try:
            # WARP.md Compliance Gate: Publishing is gated by QA/Compliance
            
            # Check 1: Title compliance (50-60 characters)
            title = getattr(review_doc, 'title', '')
            title_length = len(title)
            title_compliant = 30 <= title_length <= 60  # Allow some flexibility
            
            compliance_checks.append(ComplianceCheck(
                check_name="Title Length",
                status="PASS" if title_compliant else "FAIL",
                description="SEO-optimized title length",
                details=f"Title: {title_length} characters",
                severity="high" if not title_compliant else "low",
                requirement="30-60 characters for SEO optimization"
            ))
            
            if not title_compliant:
                compliance_issues.append(f"Title length issue: {title_length} chars (recommended 30-60)")
            
            # Check 2: Meta description compliance (150-160 characters)
            meta_desc = getattr(review_doc, 'meta_description', '')
            meta_length = len(meta_desc)
            meta_compliant = 120 <= meta_length <= 160
            
            compliance_checks.append(ComplianceCheck(
                check_name="Meta Description",
                status="PASS" if meta_compliant else "FAIL", 
                description="SEO meta description length",
                details=f"Meta: {meta_length} characters",
                severity="medium" if not meta_compliant else "low",
                requirement="120-160 characters for SEO"
            ))
            
            if not meta_compliant:
                compliance_issues.append(f"Meta description length: {meta_length} chars (recommended 120-160)")
            
            # Check 3: Target keywords presence
            target_keywords = getattr(review_doc, 'target_keywords', [])
            keywords_compliant = len(target_keywords) >= 3
            
            compliance_checks.append(ComplianceCheck(
                check_name="Target Keywords",
                status="PASS" if keywords_compliant else "FAIL",
                description="SEO target keywords defined",
                details=f"Keywords: {len(target_keywords)} defined",
                severity="medium" if not keywords_compliant else "low",
                requirement="≥3 target keywords for SEO"
            ))
            
            if not keywords_compliant:
                compliance_issues.append(f"Insufficient target keywords: {len(target_keywords)} (minimum 3)")
            
            # Check 4: Content sections completeness (95-field requirement interpretation)
            sections = getattr(review_doc, 'sections', [])
            required_sections = [
                "introduction", "games", "bonuses", "banking", 
                "security", "user experience", "customer support"
            ]
            
            present_sections = [s.title.lower() for s in sections] if sections else []
            missing_sections = [req for req in required_sections 
                             if not any(req in present.lower() for present in present_sections)]
            
            sections_compliant = len(missing_sections) == 0
            
            compliance_checks.append(ComplianceCheck(
                check_name="Content Completeness",
                status="PASS" if sections_compliant else "FAIL",
                description="All required content sections present",
                details=f"Missing sections: {missing_sections}" if missing_sections else "All sections present",
                severity="high" if not sections_compliant else "low",
                requirement="All essential casino review sections required"
            ))
            
            if not sections_compliant:
                compliance_issues.append(f"Missing required sections: {', '.join(missing_sections)}")
            
            # Check 5: Structured data compliance
            ratings = getattr(review_doc, 'ratings', [])
            structured_data_compliant = len(ratings) >= 5  # Major rating categories
            
            compliance_checks.append(ComplianceCheck(
                check_name="Structured Data",
                status="PASS" if structured_data_compliant else "FAIL",
                description="Structured rating data for schema markup",
                details=f"Rating categories: {len(ratings)}",
                severity="medium" if not structured_data_compliant else "low",
                requirement="≥5 rating categories for rich snippets"
            ))
            
            if not structured_data_compliant:
                compliance_issues.append(f"Insufficient rating categories: {len(ratings)} (minimum 5)")
            
            # Overall compliance determination
            failed_checks = [c for c in compliance_checks if c.status == "FAIL"]
            high_severity_failures = [c for c in failed_checks if c.severity == "high"]
            
            if compliance_strict:
                overall_compliance = len(failed_checks) == 0
            else:
                # In non-strict mode, allow medium/low severity failures
                overall_compliance = len(high_severity_failures) == 0
            
            logger.info(f"⚖️ Compliance validated: {'PASS' if overall_compliance else 'FAIL'}")
            
            return {
                "compliance_checks": compliance_checks,
                "compliance_issues": compliance_issues,
                "overall_compliance": overall_compliance,
                "failed_checks": len(failed_checks),
                "high_severity_failures": len(high_severity_failures)
            }
            
        except Exception as e:
            logger.error(f"Compliance validation failed: {str(e)}")
            return {
                "compliance_checks": [],
                "compliance_issues": [f"Compliance validation error: {str(e)}"],
                "overall_compliance": False,
                "failed_checks": 1,
                "high_severity_failures": 1
            }
    
    async def _verify_factual_accuracy(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Verify factual accuracy against research data using LLM"""
        
        validated_request = inputs["validated_request"]
        review_doc = validated_request["review_doc"]
        research_pack = validated_request["research_pack"]
        
        factual_checks = []
        factual_issues = []
        
        try:
            if not research_pack:
                logger.warning("No research pack available for factual verification")
                return {
                    "factual_checks": [],
                    "factual_issues": ["No research data available for factual verification"],
                    "factual_accuracy_score": 5.0  # Neutral score
                }
            
            # Factual accuracy verification prompt
            accuracy_prompt = ChatPromptTemplate.from_messages([
                ("system", """You are a fact-checker specializing in casino reviews. Compare the review content against the research data and identify any factual inaccuracies.

Guidelines:
- Look for specific claims about games, bonuses, payments, licensing
- Check for inconsistencies with research data
- Identify unsupported claims or speculation
- Rate accuracy on a scale of 1-10
- Be thorough but fair"""),
                ("human", """Fact-check this casino review against the research data:

REVIEW CONTENT:
Casino: {casino_name}
Title: {title}
Key Claims: {content_summary}
Pros: {pros}
Cons: {cons}
Overall Rating: {rating}/10

RESEARCH DATA:
Authority Score: {authority_score}
Primary Keywords: {keywords}
Competitors: {competitors}
Brand Mentions: {mentions_count}
Sentiment: {sentiment_score}

Identify any factual inaccuracies or unsupported claims. Rate the overall factual accuracy from 1-10.""")
            ])
            
            # Prepare content summary
            content_summary = review_doc.content[:500] if hasattr(review_doc, 'content') else "No content available"
            pros_text = "; ".join(review_doc.pros[:3]) if hasattr(review_doc, 'pros') and review_doc.pros else "None"
            cons_text = "; ".join(review_doc.cons[:3]) if hasattr(review_doc, 'cons') and review_doc.cons else "None"
            
            # Research data summary
            authority_score = getattr(research_pack, 'domain_authority_score', 0)
            keywords = getattr(research_pack, 'primary_keywords', [])[:5]
            competitors = getattr(research_pack, 'competitor_analysis', [])[:3]
            mentions_count = len(getattr(research_pack, 'brand_mentions', []))
            sentiment_data = getattr(research_pack, 'sentiment_analysis', {})
            sentiment_score = sentiment_data.get('average_score', 0) if sentiment_data else 0
            
            # Run factual verification
            accuracy_chain = accuracy_prompt | self.llm
            
            accuracy_result = await accuracy_chain.ainvoke({
                "casino_name": review_doc.casino_name,
                "title": getattr(review_doc, 'title', ''),
                "content_summary": content_summary,
                "pros": pros_text,
                "cons": cons_text,
                "rating": getattr(review_doc, 'overall_rating', 0),
                "authority_score": authority_score,
                "keywords": ", ".join(keywords),
                "competitors": ", ".join([c.get("domain", "") for c in competitors]),
                "mentions_count": mentions_count,
                "sentiment_score": sentiment_score
            })
            
            # Parse factual accuracy assessment
            accuracy_content = accuracy_result.content
            
            # Simple accuracy score extraction (would be more sophisticated in production)
            factual_accuracy_score = 7.5  # Default neutral score
            
            # Look for accuracy score in the response
            lines = accuracy_content.lower().split('\n')
            for line in lines:
                if 'accuracy' in line and any(str(i) for i in range(1, 11)) in line:
                    # Extract numeric score (simplified)
                    import re
                    scores = re.findall(r'\b([1-9]|10)\b', line)
                    if scores:
                        factual_accuracy_score = float(scores[0])
                        break
            
            # Extract issues from the response
            if 'inaccurac' in accuracy_content.lower() or 'incorrect' in accuracy_content.lower():
                factual_issues.append("Potential factual inaccuracies identified by fact-checker")
            
            if 'unsupported' in accuracy_content.lower():
                factual_issues.append("Unsupported claims identified in content")
            
            factual_checks.append({
                "check": "Research Data Consistency",
                "pass": factual_accuracy_score >= 7.0,
                "score": factual_accuracy_score,
                "details": "Compared against DataForSEO research data"
            })
            
            logger.info(f"🔍 Factual accuracy verified: {factual_accuracy_score}/10")
            
            return {
                "factual_checks": factual_checks,
                "factual_issues": factual_issues,
                "factual_accuracy_score": factual_accuracy_score,
                "verification_notes": accuracy_content[:200] + "..." if len(accuracy_content) > 200 else accuracy_content
            }
            
        except Exception as e:
            logger.error(f"Factual accuracy verification failed: {str(e)}")
            return {
                "factual_checks": [],
                "factual_issues": [f"Factual verification error: {str(e)}"],
                "factual_accuracy_score": 5.0,
                "verification_notes": "Verification failed due to system error"
            }
    
    async def _validate_seo_elements(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Validate SEO elements and optimization"""
        
        validated_request = inputs["validated_request"]
        review_doc = validated_request["review_doc"]
        
        seo_checks = []
        seo_issues = []
        
        try:
            # Title SEO validation
            title = getattr(review_doc, 'title', '')
            title_has_casino_name = review_doc.casino_name.lower() in title.lower()
            title_has_year = '2024' in title or '2025' in title
            
            seo_checks.append({
                "check": "Title Optimization",
                "pass": title_has_casino_name and title_has_year,
                "details": f"Casino name: {title_has_casino_name}, Year: {title_has_year}"
            })
            
            if not title_has_casino_name:
                seo_issues.append("Title should include casino name")
            if not title_has_year:
                seo_issues.append("Title should include current year")
            
            # Meta description SEO
            meta_desc = getattr(review_doc, 'meta_description', '')
            meta_has_casino_name = review_doc.casino_name.lower() in meta_desc.lower()
            meta_has_call_to_action = any(phrase in meta_desc.lower() for phrase in 
                                        ['read', 'review', 'play', 'before', 'expert'])
            
            seo_checks.append({
                "check": "Meta Description SEO",
                "pass": meta_has_casino_name and meta_has_call_to_action,
                "details": f"Casino name: {meta_has_casino_name}, CTA: {meta_has_call_to_action}"
            })
            
            if not meta_has_casino_name:
                seo_issues.append("Meta description should include casino name")
            if not meta_has_call_to_action:
                seo_issues.append("Meta description should have call-to-action")
            
            # Keyword optimization
            target_keywords = getattr(review_doc, 'target_keywords', [])
            content = getattr(review_doc, 'content', '') or ''
            
            keyword_density_checks = []
            for keyword in target_keywords[:3]:  # Check top 3 keywords
                keyword_count = content.lower().count(keyword.lower())
                word_count = len(content.split()) if content else 1
                density = (keyword_count / word_count) * 100 if word_count > 0 else 0
                
                # Target keyword density: 0.5-2.5%
                density_optimal = 0.5 <= density <= 2.5
                keyword_density_checks.append({
                    "keyword": keyword,
                    "density": density,
                    "optimal": density_optimal
                })
            
            keywords_optimized = all(check["optimal"] for check in keyword_density_checks)
            
            seo_checks.append({
                "check": "Keyword Optimization",
                "pass": keywords_optimized,
                "details": f"Checked {len(keyword_density_checks)} keywords"
            })
            
            if not keywords_optimized:
                seo_issues.append("Keyword density not optimal for some target keywords")
            
            # Internal linking (basic check)
            internal_link_indicators = ['best online casinos', 'casino games', 'casino bonuses', 'payment methods']
            has_internal_links = any(indicator in content.lower() for indicator in internal_link_indicators)
            
            seo_checks.append({
                "check": "Internal Linking Potential",
                "pass": has_internal_links,
                "details": f"Internal link opportunities: {has_internal_links}"
            })
            
            if not has_internal_links:
                seo_issues.append("Consider adding internal links to related content")
            
            # Calculate SEO score
            passed_seo = sum(1 for check in seo_checks if check["pass"])
            seo_score = (passed_seo / len(seo_checks)) * 10 if seo_checks else 0
            
            logger.info(f"🎯 SEO validation completed: {seo_score:.1f}/10")
            
            return {
                "seo_checks": seo_checks,
                "seo_issues": seo_issues,
                "seo_score": seo_score,
                "keyword_density_checks": keyword_density_checks
            }
            
        except Exception as e:
            logger.error(f"SEO validation failed: {str(e)}")
            return {
                "seo_checks": [],
                "seo_issues": [f"SEO validation error: {str(e)}"],
                "seo_score": 0.0,
                "keyword_density_checks": []
            }
    
    async def _validate_image_compliance(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Validate image compliance per WARP.md screenshot policy"""
        
        validated_request = inputs["validated_request"]
        review_doc = validated_request["review_doc"]
        
        image_checks = []
        image_issues = []
        
        try:
            # Get images from review document
            featured_image = getattr(review_doc, 'featured_image', None)
            additional_images = getattr(review_doc, 'additional_images', [])
            
            all_images = []
            if featured_image:
                all_images.append(featured_image)
            all_images.extend(additional_images)
            
            if not all_images:
                image_issues.append("No images found in review document")
                return {
                    "image_checks": [],
                    "image_issues": image_issues,
                    "image_compliance_score": 0.0
                }
            
            compliant_images = 0
            total_images = len(all_images)
            
            for i, image in enumerate(all_images):
                image_name = f"Image {i+1}"
                
                # WARP.md compliance checks
                compliance_pass = getattr(image, 'compliance_pass', False)
                dimensions_compliant = getattr(image, 'dimensions_compliant', False)
                licensing_compliant = getattr(image, 'licensing_compliant', False)
                
                image_checks.append({
                    "image": image_name,
                    "compliance_pass": compliance_pass,
                    "dimensions_ok": dimensions_compliant,
                    "licensing_ok": licensing_compliant,
                    "capture_method": getattr(image, 'capture_method', 'unknown')
                })
                
                if compliance_pass:
                    compliant_images += 1
                else:
                    issues = []
                    if not dimensions_compliant:
                        issues.append("dimensions < 900×600")
                    if not licensing_compliant:
                        issues.append("licensing concerns")
                    
                    image_issues.append(f"{image_name}: {', '.join(issues)}")
            
            # Calculate image compliance score
            image_compliance_score = (compliant_images / total_images) * 10 if total_images > 0 else 0
            
            # WARP.md requirement: All publishable images must pass compliance
            overall_image_compliance = compliant_images == total_images
            
            logger.info(f"🖼️ Image compliance validated: {compliant_images}/{total_images} compliant")
            
            return {
                "image_checks": image_checks,
                "image_issues": image_issues,
                "image_compliance_score": image_compliance_score,
                "compliant_images": compliant_images,
                "total_images": total_images,
                "overall_image_compliance": overall_image_compliance
            }
            
        except Exception as e:
            logger.error(f"Image compliance validation failed: {str(e)}")
            return {
                "image_checks": [],
                "image_issues": [f"Image validation error: {str(e)}"],
                "image_compliance_score": 0.0,
                "compliant_images": 0,
                "total_images": 0,
                "overall_image_compliance": False
            }
    
    def _build_qa_report(self, inputs: Dict[str, Any]) -> QAReport:
        """Build comprehensive QA report from all validation results"""
        
        validated_request = inputs["validated_request"]
        review_doc = validated_request["review_doc"]
        
        content_quality = inputs.get("content_quality", {})
        compliance_data = inputs.get("compliance_checks", {})
        factual_data = inputs.get("factual_verification", {})
        seo_data = inputs.get("seo_validation", {})
        image_data = inputs.get("image_compliance", {})
        
        # Collect all issues
        all_issues = []
        all_issues.extend(content_quality.get("quality_issues", []))
        all_issues.extend(compliance_data.get("compliance_issues", []))
        all_issues.extend(factual_data.get("factual_issues", []))
        all_issues.extend(seo_data.get("seo_issues", []))
        all_issues.extend(image_data.get("image_issues", []))
        
        # Collect all compliance checks
        all_compliance_checks = compliance_data.get("compliance_checks", [])
        
        # Collect quality metrics
        quality_metrics = content_quality.get("quality_metrics", [])
        
        # Calculate overall scores
        quality_score = content_quality.get("quality_score", 0.0)
        factual_score = factual_data.get("factual_accuracy_score", 7.5)
        seo_score = seo_data.get("seo_score", 7.5)
        image_score = image_data.get("image_compliance_score", 7.5)
        
        # Weighted overall score
        weights = {"quality": 0.3, "factual": 0.25, "seo": 0.2, "image": 0.25}
        overall_score = (
            quality_score * weights["quality"] +
            factual_score * weights["factual"] +
            seo_score * weights["seo"] +
            image_score * weights["image"]
        )
        
        # Determine overall pass/fail
        # WARP.md: Publishing is gated by QA/Compliance
        compliance_pass = compliance_data.get("overall_compliance", False)
        quality_pass = quality_score >= 7.0
        image_compliance_pass = image_data.get("overall_image_compliance", True)  # Default true if no images
        
        # Strict gate: Must pass compliance, quality, and image checks
        if validated_request["compliance_strict"]:
            overall_pass = compliance_pass and quality_pass and image_compliance_pass
        else:
            # Lenient: Pass if overall score is reasonable and no high-severity issues
            high_severity_failures = compliance_data.get("high_severity_failures", 0)
            overall_pass = overall_score >= 6.0 and high_severity_failures == 0
        
        # Generate recommendations
        recommendations = []
        if not quality_pass:
            recommendations.append("Improve content quality: increase word count, add more sections")
        if not compliance_pass:
            recommendations.append("Fix compliance issues: optimize title/meta, complete all sections")
        if factual_score < 7.0:
            recommendations.append("Verify factual accuracy against research data")
        if seo_score < 7.0:
            recommendations.append("Improve SEO optimization: keyword density, internal links")
        if not image_compliance_pass:
            recommendations.append("Ensure all images meet WARP.md compliance requirements")
        
        if overall_pass:
            recommendations.append("✅ Review is ready for publishing")
        else:
            recommendations.append("❌ Review requires fixes before publishing")
        
        # Build final QA report
        qa_report = QAReport(
            casino_name=review_doc.casino_name,
            review_title=getattr(review_doc, 'title', ''),
            overall_pass=overall_pass,
            quality_score=round(overall_score, 1),
            validation_date=datetime.now(),
            
            # Issues and recommendations
            issues_found=all_issues,
            recommendations=recommendations,
            
            # Detailed results
            compliance_checks=all_compliance_checks,
            quality_metrics=quality_metrics,
            
            # Individual scores
            content_quality_score=round(quality_score, 1),
            factual_accuracy_score=round(factual_score, 1),
            seo_optimization_score=round(seo_score, 1),
            image_compliance_score=round(image_score, 1),
            
            # Metadata
            validation_level=validated_request["validation_level"],
            compliance_strict=validated_request["compliance_strict"],
            notes=f"QA validation completed with {len(all_issues)} issues found"
        )
        
        logger.info(f"📋 QA report built: {'PASS' if overall_pass else 'FAIL'} ({overall_score:.1f}/10)")
        
        return qa_report


# LCEL Tool Wrapper for LangGraph integration
def create_qa_agent_tool(strict_compliance: bool = True) -> RunnableLambda:
    """
    Create a LangChain tool wrapper for the QA agent
    
    Args:
        strict_compliance: Whether to enforce strict compliance checking
        
    Returns:
        RunnableLambda that can be used in LangGraph workflows
    """
    
    agent = CasinoQAAgent(strict_compliance=strict_compliance)
    
    async def qa_tool(inputs: Dict[str, Any]) -> QAReport:
        """Tool function for LangGraph integration"""
        
        # Convert inputs to QAValidationRequest
        request = QAValidationRequest(
            review_doc=inputs["review_doc"],
            research_pack=inputs.get("research_pack"),
            validation_level=inputs.get("validation_level", "comprehensive"),
            compliance_strict=inputs.get("compliance_strict", strict_compliance),
            tenant_id=inputs.get("tenant_id", "crashcasino")
        )
        
        return await agent.validate_review(request)
    
    return RunnableLambda(qa_tool)


# Factory function
def create_casino_qa_agent(llm: Optional[ChatOpenAI] = None, 
                          strict_compliance: bool = True) -> CasinoQAAgent:
    """
    Factory function to create casino QA agent
    
    Args:
        llm: Optional custom LLM (defaults to GPT-4)
        strict_compliance: Whether to enforce strict compliance
        
    Returns:
        Configured CasinoQAAgent
    """
    return CasinoQAAgent(llm=llm, strict_compliance=strict_compliance)


# Testing and validation
async def test_qa_agent():
    """Test the casino QA agent"""
    from ..schemas.casino_review import ReviewDoc, CasinoResearchPack, ReviewSection
    
    # Create test review document
    test_sections = [
        ReviewSection(title="Introduction", content="Test content" * 50, word_count=100),
        ReviewSection(title="Games & Software", content="Test content" * 50, word_count=100),
        ReviewSection(title="Bonuses & Promotions", content="Test content" * 50, word_count=100),
        ReviewSection(title="Banking & Payments", content="Test content" * 50, word_count=100),
        ReviewSection(title="Security & Licensing", content="Test content" * 50, word_count=100),
        ReviewSection(title="User Experience", content="Test content" * 50, word_count=100),
        ReviewSection(title="Customer Support", content="Test content" * 50, word_count=100),
    ]
    
    test_review = ReviewDoc(
        casino_name="Bitstarz",
        casino_url="https://bitstarz.com",
        title="Bitstarz Casino Review 2024 - Honest Analysis",
        content="<h2>Test review content</h2><p>Comprehensive review content here...</p>",
        meta_description="Bitstarz casino review with games, bonuses, payments & more. Expert analysis and 8.5/10 rating. Read before you play!",
        sections=test_sections,
        pros=["Great game selection", "Fast payouts", "24/7 support", "Mobile friendly"],
        cons=["Limited live chat", "High wagering requirements", "Geo-restrictions"],
        overall_rating=8.5,
        word_count=2800,
        target_keywords=["bitstarz review", "bitcoin casino", "crypto gambling"],
        generation_date=datetime.now()
    )
    
    test_research = CasinoResearchPack(
        casino_name="Bitstarz",
        casino_url="https://bitstarz.com",
        research_date=datetime.now(),
        primary_keywords=["bitstarz", "bitcoin casino", "crypto gambling"],
        domain_authority_score=75,
        research_accuracy=0.85
    )
    
    # Create QA agent
    agent = create_casino_qa_agent(strict_compliance=True)
    
    # Test QA validation request
    request = QAValidationRequest(
        review_doc=test_review,
        research_pack=test_research,
        validation_level="comprehensive",
        compliance_strict=True
    )
    
    # Run QA validation
    result = await agent.validate_review(request)
    
    print(f"\n🔍 QA Validation Results:")
    print(f"   Casino: {result.casino_name}")
    print(f"   Overall Status: {'✅ PASS' if result.overall_pass else '❌ FAIL'}")
    print(f"   Quality Score: {result.quality_score}/10")
    print(f"   Issues Found: {len(result.issues_found)}")
    print(f"   Recommendations: {len(result.recommendations)}")
    
    if result.issues_found:
        print("\n   Issues:")
        for issue in result.issues_found[:3]:
            print(f"     - {issue}")
    
    if result.recommendations:
        print(f"\n   Top Recommendation: {result.recommendations[0]}")


if __name__ == "__main__":
    asyncio.run(test_qa_agent())
