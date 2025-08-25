"""
🧪 Test Suite: QA & Compliance Chain
Task-014: Comprehensive testing for content quality assurance and compliance validation

Test Coverage:
- Affiliate compliance validation
- Factual accuracy checking
- Brand style consistency
- Content quality assessment
- Human-in-the-loop workflow
- Multi-tenant compliance rules
- Publishing gate validation
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from typing import Dict, Any, List

# Import components under test
from src.chains.qa_compliance_chain import (
    QAComplianceChain,
    QAValidationInput,
    QAValidationOutput,
    QAValidationLevel,
    AffiliateComplianceValidator,
    FactualAccuracyValidator,
    BrandStyleValidator,
    ContentQualityValidator,
    HumanReviewGateway,
    create_qa_compliance_chain
)
from src.schemas.review_doc import (
    ReviewDoc,
    QAReport, 
    QualityScore,
    ComplianceStatus,
    TenantConfiguration,
    MediaAsset,
    MediaType
)
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI


class TestAffiliateComplianceValidator:
    """Test affiliate compliance validation functionality"""
    
    @pytest.fixture
    def sample_tenant_config(self):
        """Create sample tenant configuration"""
        return TenantConfiguration(
            tenant_id="test-tenant",
            brand_name="Test Casino Brand",
            locale="en",
            voice_profile="professional",
            compliance_requirements=["18+ verification", "responsible gambling"]
        )
    
    def test_compliance_validator_initialization(self, sample_tenant_config):
        """Test compliance validator initialization"""
        validator = AffiliateComplianceValidator(sample_tenant_config)
        
        assert validator.tenant_config == sample_tenant_config
        assert isinstance(validator.jurisdiction_rules, dict)
        assert hasattr(validator, 'REQUIRED_DISCLAIMERS')
        assert hasattr(validator, 'PROHIBITED_PATTERNS')
    
    def test_compliance_validation_pass(self, sample_tenant_config):
        """Test compliance validation with compliant content"""
        validator = AffiliateComplianceValidator(sample_tenant_config)
        
        compliant_content = """
        <h1>Casino Review</h1>
        <p>This casino offers great games. Players must be 18+ to play.</p>
        <p>We earn affiliate commissions from this casino.</p>
        <p>Please gamble responsibly and seek help if you have a gambling problem.</p>
        """
        
        result = validator.validate_affiliate_compliance(compliant_content)
        
        assert result["passed"] is True
        assert result["score"] >= 8.0
        assert len(result["missing_disclaimers"]) == 0
        assert len(result["prohibited_content"]) == 0
    
    def test_compliance_validation_fail(self, sample_tenant_config):
        """Test compliance validation with non-compliant content"""
        validator = AffiliateComplianceValidator(sample_tenant_config)
        
        non_compliant_content = """
        <h1>Casino Review</h1>
        <p>This casino guarantees wins for all players!</p>
        <p>Perfect for kids and teens to play.</p>
        <p>You cannot lose with this system.</p>
        """
        
        result = validator.validate_affiliate_compliance(non_compliant_content)
        
        assert result["passed"] is False
        assert result["score"] < 5.0
        assert len(result["missing_disclaimers"]) > 0
        assert len(result["prohibited_content"]) > 0
        assert "guaranteed_wins" in result["prohibited_content"]
        assert "underage_targeting" in result["prohibited_content"]
    
    def test_jurisdiction_specific_rules(self):
        """Test jurisdiction-specific compliance rules"""
        # Test German locale
        de_config = TenantConfiguration(
            tenant_id="test-de",
            locale="de",
            compliance_requirements=["German gambling law"]
        )
        
        validator = AffiliateComplianceValidator(de_config)
        jurisdiction_rules = validator._load_jurisdiction_rules()
        
        # Should load German rules
        if jurisdiction_rules:
            assert "prohibited_terms" in jurisdiction_rules
            assert "required_disclaimers" in jurisdiction_rules


class TestFactualAccuracyValidator:
    """Test factual accuracy validation functionality"""
    
    @pytest.fixture
    def mock_llm(self):
        """Create mock LLM for testing"""
        mock_llm = Mock(spec=ChatOpenAI)
        mock_llm.model_name = "gpt-4o"
        return mock_llm
    
    @pytest.fixture
    def sample_source_documents(self):
        """Create sample source documents"""
        return [
            Document(
                page_content="Betway Casino is licensed by Malta Gaming Authority with license MGA/B2C/145/2007",
                metadata={"source": "official-license-check"}
            ),
            Document(
                page_content="Welcome bonus: 100% up to $500 + 50 free spins",
                metadata={"source": "official-promotion-page"}
            )
        ]
    
    def test_factual_validator_initialization(self, mock_llm):
        """Test factual accuracy validator initialization"""
        validator = FactualAccuracyValidator(mock_llm)
        
        assert validator.llm == mock_llm
        assert hasattr(validator, 'fact_check_chain')
    
    def test_factual_validation_no_sources(self, mock_llm):
        """Test factual validation with no source documents"""
        validator = FactualAccuracyValidator(mock_llm)
        
        content = "This casino offers great games and bonuses."
        result = validator.validate_factual_accuracy(content, [])
        
        assert result["passed"] is False
        assert result["score"] == 0.0
        assert "No source documents provided" in result["errors"][0]
    
    @patch('src.chains.qa_compliance_chain.json.loads')
    def test_factual_validation_with_sources(self, mock_json, mock_llm, sample_source_documents):
        """Test factual validation with source documents"""
        # Mock LLM response
        mock_chain = Mock()
        mock_chain.invoke.return_value = '{"accuracy_score": 8.5, "factual_errors": [], "verified_claims": ["license info"]}'
        
        # Mock JSON parsing
        mock_json.return_value = {
            "accuracy_score": 8.5,
            "factual_errors": [],
            "verified_claims": ["license info"],
            "unverifiable_claims": []
        }
        
        validator = FactualAccuracyValidator(mock_llm)
        validator.fact_check_chain = mock_chain
        
        content = "Betway Casino is licensed by Malta Gaming Authority."
        result = validator.validate_factual_accuracy(content, sample_source_documents)
        
        assert result["passed"] is True
        assert result["score"] == 8.5
        assert len(result["errors"]) == 0
        assert "license info" in result["verified_claims"]


class TestBrandStyleValidator:
    """Test brand style validation functionality"""
    
    @pytest.fixture
    def mock_llm(self):
        """Create mock LLM for testing"""
        mock_llm = Mock(spec=ChatOpenAI)
        mock_llm.model_name = "gpt-4o"
        return mock_llm
    
    @pytest.fixture
    def sample_tenant_config(self):
        """Create sample tenant configuration"""
        return TenantConfiguration(
            tenant_id="test-tenant",
            brand_name="Professional Casino Guide",
            locale="en",
            voice_profile="professional",
            target_demographics=["adults 25-50"],
            content_guidelines="professional, informative, trustworthy"
        )
    
    def test_style_validator_initialization(self, mock_llm):
        """Test style validator initialization"""
        validator = BrandStyleValidator(mock_llm)
        
        assert validator.llm == mock_llm
        assert hasattr(validator, 'style_check_chain')
    
    @patch('src.chains.qa_compliance_chain.json.loads')
    def test_style_validation_pass(self, mock_json, mock_llm, sample_tenant_config):
        """Test style validation with consistent content"""
        # Mock LLM response
        mock_chain = Mock()
        mock_chain.invoke.return_value = '{"style_score": 9.0, "voice_consistency": true}'
        
        # Mock JSON parsing
        mock_json.return_value = {
            "style_score": 9.0,
            "voice_consistency": True,
            "tone_issues": [],
            "brand_alignment": True,
            "guideline_violations": [],
            "prohibited_language_found": [],
            "improvement_suggestions": []
        }
        
        validator = BrandStyleValidator(mock_llm)
        validator.style_check_chain = mock_chain
        
        content = "This comprehensive casino review provides professional analysis of gaming options."
        result = validator.validate_brand_style(content, sample_tenant_config)
        
        assert result["passed"] is True
        assert result["score"] == 9.0
        assert result["voice_consistent"] is True
        assert len(result["issues"]) == 0


class TestContentQualityValidator:
    """Test content quality validation functionality"""
    
    @pytest.fixture
    def mock_llm(self):
        """Create mock LLM for testing"""
        mock_llm = Mock(spec=ChatOpenAI)
        mock_llm.model_name = "gpt-4o"
        return mock_llm
    
    def test_quality_validator_initialization(self, mock_llm):
        """Test quality validator initialization"""
        validator = ContentQualityValidator(mock_llm)
        
        assert validator.llm == mock_llm
        assert hasattr(validator, 'quality_check_chain')
    
    @patch('src.chains.qa_compliance_chain.json.loads')
    def test_quality_validation_pass(self, mock_json, mock_llm):
        """Test quality validation with high-quality content"""
        # Mock LLM response
        mock_chain = Mock()
        mock_chain.invoke.return_value = '{"quality_score": 8.5}'
        
        # Mock JSON parsing
        mock_json.return_value = {
            "quality_score": 8.5,
            "completeness_score": 9.0,
            "readability_score": 8.0,
            "structure_score": 8.5,
            "grammar_score": 9.0,
            "missing_sections": [],
            "quality_issues": [],
            "improvement_areas": [],
            "word_count": 2500,
            "paragraph_count": 15
        }
        
        validator = ContentQualityValidator(mock_llm)
        validator.quality_check_chain = mock_chain
        
        content = "<h1>Casino Review</h1><p>Comprehensive content...</p>" * 50  # Long content
        result = validator.validate_content_quality(content)
        
        assert result["passed"] is True
        assert result["score"] == 8.5
        assert result["word_count"] == 2500
        assert len(result["missing_sections"]) == 0
    
    @patch('src.chains.qa_compliance_chain.json.loads')
    def test_quality_validation_fail(self, mock_json, mock_llm):
        """Test quality validation with low-quality content"""
        # Mock JSON parsing for poor quality
        mock_json.return_value = {
            "quality_score": 4.0,  # Below threshold
            "completeness_score": 3.0,
            "readability_score": 4.0,
            "structure_score": 5.0,
            "grammar_score": 3.0,
            "missing_sections": ["games", "bonuses"],
            "quality_issues": ["poor grammar", "incomplete information"],
            "improvement_areas": ["add missing sections", "improve readability"],
            "word_count": 100,
            "paragraph_count": 2
        }
        
        mock_chain = Mock()
        mock_chain.invoke.return_value = '{"quality_score": 4.0}'
        
        validator = ContentQualityValidator(mock_llm)
        validator.quality_check_chain = mock_chain
        
        content = "<p>Bad casino.</p>"  # Poor content
        result = validator.validate_content_quality(content)
        
        assert result["passed"] is False
        assert result["score"] == 4.0
        assert "games" in result["missing_sections"]
        assert "poor grammar" in result["issues"]


class TestHumanReviewGateway:
    """Test human-in-the-loop review workflow"""
    
    @pytest.fixture
    def sample_review_doc(self):
        """Create sample review document"""
        return ReviewDoc(
            title="Test Casino Review",
            content="<h1>Test Casino</h1><p>Review content...</p>",
            content_type="casino_review",
            tenant_config=TenantConfiguration(
                tenant_id="test",
                brand_name="Test Brand",
                locale="en"
            ),
            tenant_id="test",
            brand="Test Brand",
            locale="en"
        )
    
    def test_human_gateway_initialization(self):
        """Test human review gateway initialization"""
        gateway = HumanReviewGateway()
        
        assert isinstance(gateway.pending_reviews, dict)
        assert len(gateway.pending_reviews) == 0
    
    def test_requires_human_review_premium(self):
        """Test human review requirement for premium content"""
        gateway = HumanReviewGateway()
        
        validation_results = {"compliance": {"score": 9.0}}
        requires_review = gateway.requires_human_review(
            validation_results, 
            QAValidationLevel.PREMIUM
        )
        
        assert requires_review is True
    
    def test_requires_human_review_poor_compliance(self):
        """Test human review requirement for poor compliance"""
        gateway = HumanReviewGateway()
        
        validation_results = {
            "compliance": {"score": 3.0},  # Poor compliance
            "factual": {"score": 8.0},
            "quality": {"score": 8.0}
        }
        requires_review = gateway.requires_human_review(
            validation_results,
            QAValidationLevel.STANDARD
        )
        
        assert requires_review is True
    
    def test_submit_for_human_review(self, sample_review_doc):
        """Test submitting content for human review"""
        gateway = HumanReviewGateway()
        
        validation_results = {"compliance": {"score": 6.0}}
        review_id = gateway.submit_for_human_review(sample_review_doc, validation_results)
        
        assert review_id.startswith("human_review_")
        assert review_id in gateway.pending_reviews
        assert gateway.pending_reviews[review_id]["status"] == "pending"
        assert gateway.pending_reviews[review_id]["review_doc"] == sample_review_doc
    
    def test_get_human_review_status(self, sample_review_doc):
        """Test getting human review status"""
        gateway = HumanReviewGateway()
        
        # Submit review first
        validation_results = {"compliance": {"score": 6.0}}
        review_id = gateway.submit_for_human_review(sample_review_doc, validation_results)
        
        # Get status
        status = gateway.get_human_review_status(review_id)
        assert status["status"] == "pending"
        
        # Test non-existent review
        status = gateway.get_human_review_status("non-existent")
        assert status["status"] == "not_found"


class TestQAComplianceChain:
    """Test the complete QA compliance LCEL chain"""
    
    @pytest.fixture
    def mock_llm(self):
        """Create mock LLM"""
        mock_llm = Mock(spec=ChatOpenAI)
        mock_llm.model_name = "gpt-4o"
        mock_llm.temperature = 0.1
        mock_llm.max_tokens = 2048
        return mock_llm
    
    @pytest.fixture
    def sample_review_doc(self):
        """Create sample review document"""
        return ReviewDoc(
            title="Comprehensive Casino Review",
            content="""
            <h1>Test Casino Review</h1>
            <p>This casino offers excellent gaming opportunities for players aged 18 and above.</p>
            <p>Licensed by Malta Gaming Authority (MGA/B2C/123/2020), this casino provides secure gaming.</p>
            <p>Welcome bonus: 100% up to $500 + 50 free spins on selected slots.</p>
            <p>We earn affiliate commissions from this casino partnership.</p>
            <p>Please gamble responsibly and seek help if you experience gambling problems.</p>
            """,
            content_type="casino_review",
            tenant_config=TenantConfiguration(
                tenant_id="test-casino",
                brand_name="Casino Review Pro",
                locale="en",
                voice_profile="professional",
                compliance_requirements=["18+ verification", "responsible gambling"]
            ),
            tenant_id="test-casino",
            brand="Casino Review Pro",
            locale="en"
        )
    
    @pytest.fixture
    def sample_validation_input(self, sample_review_doc):
        """Create sample validation input"""
        source_docs = [
            Document(
                page_content="Malta Gaming Authority license MGA/B2C/123/2020 verified",
                metadata={"source": "license-verification"}
            ),
            Document(
                page_content="Welcome bonus confirmed: 100% match up to $500",
                metadata={"source": "bonus-terms"}
            )
        ]
        
        return QAValidationInput(
            review_doc=sample_review_doc,
            validation_level=QAValidationLevel.STANDARD,
            source_documents=source_docs,
            brand_guidelines={
                "voice": "professional",
                "prohibited_terms": ["guaranteed", "risk-free"]
            },
            compliance_rules={
                "jurisdiction": "EU",
                "age_requirement": "18+"
            },
            human_reviewer_available=True
        )
    
    def test_chain_initialization(self, mock_llm):
        """Test QA compliance chain initialization"""
        chain = QAComplianceChain(llm=mock_llm)
        
        assert chain.llm == mock_llm
        assert chain.validation_level == QAValidationLevel.STANDARD
        assert isinstance(chain.factual_validator, FactualAccuracyValidator)
        assert isinstance(chain.style_validator, BrandStyleValidator)
        assert isinstance(chain.quality_validator, ContentQualityValidator)
        assert isinstance(chain.human_gateway, HumanReviewGateway)
        assert chain.chain is not None
    
    @patch('src.chains.qa_compliance_chain.json.loads')
    def test_validate_content_success(self, mock_json, mock_llm, sample_validation_input):
        """Test successful content validation"""
        # Mock all JSON parsing to return successful validation
        mock_json.side_effect = [
            # Factual accuracy response
            {
                "accuracy_score": 9.0,
                "factual_errors": [],
                "verified_claims": ["license valid", "bonus accurate"],
                "unverifiable_claims": []
            },
            # Style validation response
            {
                "style_score": 8.5,
                "voice_consistency": True,
                "tone_issues": [],
                "brand_alignment": True,
                "guideline_violations": [],
                "prohibited_language_found": [],
                "improvement_suggestions": []
            },
            # Quality validation response
            {
                "quality_score": 8.0,
                "completeness_score": 8.5,
                "readability_score": 8.0,
                "structure_score": 8.0,
                "grammar_score": 9.0,
                "missing_sections": [],
                "quality_issues": [],
                "improvement_areas": [],
                "word_count": 150,
                "paragraph_count": 5
            }
        ]
        
        # Mock the LLM chain invocations
        with patch.object(mock_llm, '__or__') as mock_or:
            mock_chain = Mock()
            mock_chain.invoke.return_value = '{"accuracy_score": 9.0}'
            mock_or.return_value = mock_chain
            
            chain = QAComplianceChain(llm=mock_llm)
            
            # Mock the LCEL chain execution
            with patch.object(chain.chain, 'invoke') as mock_invoke:
                mock_output = QAValidationOutput(
                    qa_report=QAReport(
                        review_doc_id="Comprehensive Casino Review",
                        overall_quality=QualityScore.GOOD,
                        compliance_status=ComplianceStatus.PASSED,
                        factual_accuracy_score=9.0,
                        brand_voice_consistency=True,
                        qa_timestamp=datetime.now()
                    ),
                    publish_approved=True,
                    validation_score=8.5,
                    detailed_feedback={"test": "feedback"},
                    human_review_required=False,
                    blocking_issues=[],
                    warnings=[],
                    processing_metadata={"test": "metadata"}
                )
                mock_invoke.return_value = mock_output
                
                # Execute validation
                result = chain.validate_content(sample_validation_input)
                
                # Verify results
                assert isinstance(result, QAValidationOutput)
                assert result.publish_approved is True
                assert result.validation_score == 8.5
                assert result.qa_report.overall_quality == QualityScore.GOOD
                assert result.qa_report.compliance_status == ComplianceStatus.PASSED
    
    def test_validate_content_failure(self, mock_llm, sample_validation_input):
        """Test content validation failure handling"""
        chain = QAComplianceChain(llm=mock_llm)
        
        # Make the chain raise an exception
        with patch.object(chain.chain, 'invoke', side_effect=Exception("Validation failed")):
            result = chain.validate_content(sample_validation_input)
            
            # Should return failure result
            assert isinstance(result, QAValidationOutput)
            assert result.publish_approved is False
            assert result.validation_score == 0.0
            assert result.human_review_required is True
            assert len(result.blocking_issues) > 0
            assert "System error" in result.blocking_issues[0]


class TestFactoryFunction:
    """Test the factory function for creating QA compliance chains"""
    
    @patch('src.chains.qa_compliance_chain.ChatOpenAI')
    def test_create_qa_compliance_chain(self, mock_openai_class):
        """Test factory function creates chain correctly"""
        mock_llm_instance = Mock()
        mock_openai_class.return_value = mock_llm_instance
        
        chain = create_qa_compliance_chain(
            llm_model="gpt-4o",
            validation_level=QAValidationLevel.STRICT,
            temperature=0.2
        )
        
        # Verify LLM was created with correct parameters
        mock_openai_class.assert_called_once_with(
            model="gpt-4o",
            temperature=0.2,
            max_tokens=2048
        )
        
        # Verify chain was created
        assert isinstance(chain, QAComplianceChain)
        assert chain.llm == mock_llm_instance
        assert chain.validation_level == QAValidationLevel.STRICT


class TestIntegrationScenarios:
    """Integration tests for complex validation scenarios"""
    
    @pytest.fixture
    def full_integration_setup(self):
        """Set up complete integration test environment"""
        mock_llm = Mock(spec=ChatOpenAI)
        mock_llm.model_name = "gpt-4o"
        
        chain = QAComplianceChain(llm=mock_llm)
        
        return {
            "chain": chain,
            "llm": mock_llm
        }
    
    def test_multi_validation_level_scenarios(self, full_integration_setup):
        """Test different validation levels"""
        chain = full_integration_setup["chain"]
        
        validation_levels = [
            QAValidationLevel.BASIC,
            QAValidationLevel.STANDARD,
            QAValidationLevel.STRICT,
            QAValidationLevel.PREMIUM
        ]
        
        for level in validation_levels:
            # Verify the chain can handle different validation levels
            chain_with_level = QAComplianceChain(
                llm=full_integration_setup["llm"],
                validation_level=level
            )
            assert chain_with_level.validation_level == level
    
    def test_multi_tenant_compliance_scenarios(self):
        """Test different tenant compliance requirements"""
        # Test different jurisdiction configurations
        tenant_configs = [
            TenantConfiguration(
                tenant_id="uk-casino",
                locale="en-GB",
                compliance_requirements=["UK gambling license", "GamCare"]
            ),
            TenantConfiguration(
                tenant_id="de-casino", 
                locale="de-DE",
                compliance_requirements=["German gambling law", "Spielsucht"]
            ),
            TenantConfiguration(
                tenant_id="us-casino",
                locale="en-US",
                compliance_requirements=["State licensing", "21+ requirement"]
            )
        ]
        
        for config in tenant_configs:
            validator = AffiliateComplianceValidator(config)
            # Should create validator without error
            assert validator.tenant_config == config
            
            # Should load appropriate jurisdiction rules
            jurisdiction_rules = validator._load_jurisdiction_rules()
            # Rules may be empty if not configured, but should not error
            assert isinstance(jurisdiction_rules, dict)
    
    def test_complex_content_scenarios(self, full_integration_setup):
        """Test validation with various content complexities"""
        test_scenarios = [
            # Minimal content
            {
                "content": "<p>Casino review.</p>",
                "expected_quality": "poor"
            },
            # Standard content
            {
                "content": "<h1>Casino Review</h1>" + "<p>Content paragraph.</p>" * 20,
                "expected_quality": "acceptable"
            },
            # Comprehensive content
            {
                "content": "<h1>Comprehensive Casino Review</h1>" + "<p>Detailed analysis paragraph.</p>" * 50,
                "expected_quality": "good"
            }
        ]
        
        for scenario in test_scenarios:
            # Create review doc with scenario content
            review_doc = ReviewDoc(
                title="Test Review",
                content=scenario["content"],
                content_type="casino_review",
                tenant_config=TenantConfiguration(
                    tenant_id="test",
                    brand_name="Test",
                    locale="en"
                ),
                tenant_id="test",
                brand="Test",
                locale="en"
            )
            
            # Verify we can create validation input without error
            validation_input = QAValidationInput(review_doc=review_doc)
            assert validation_input.review_doc.content == scenario["content"]


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])