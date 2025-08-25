"""
🧪 Visual Content Pipeline Tests - PHASE 3
==========================================

Comprehensive test suite for the Visual Content Pipeline system:
- Visual content capture and processing tests
- Screenshot integration tests
- Visual compliance validation tests
- Enhanced workflow integration tests
- Performance and error handling tests

Author: AI Assistant & TaskMaster System
Created: 2025-08-24
Version: 1.0.0
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from typing import Dict, Any, List

# Import components to test
from src.chains.visual_content_pipeline import (
    VisualContentPipeline,
    VisualContentRequest,
    VisualContentResult,
    VisualContentAsset,
    VisualContentType,
    VisualQuality,
    VisualComplianceStatus,
    VisualContentCapture,
    VisualContentProcessor,
    VisualContentValidator,
    create_visual_content_pipeline
)

from src.workflows.enhanced_content_generation_workflow import (
    EnhancedContentGenerationWorkflow,
    EnhancedContentGenerationRequest,
    EnhancedContentGenerationResult,
    create_enhanced_content_generation_workflow
)

from src.schemas.review_doc import TenantConfiguration, MediaAsset, MediaType
from src.chains.qa_compliance_chain import QAValidationLevel


class TestVisualContentTypes:
    """Test visual content type enums and basic schemas"""
    
    def test_visual_content_types(self):
        """Test visual content type enumeration"""
        assert VisualContentType.CASINO_LOBBY == "casino_lobby"
        assert VisualContentType.GAME_SCREENSHOTS == "game_screenshots"
        assert VisualContentType.BONUS_PROMOTIONS == "bonus_promotions"
        assert VisualContentType.MOBILE_INTERFACE == "mobile_interface"
    
    def test_visual_quality_enum(self):
        """Test visual quality enumeration"""
        assert VisualQuality.EXCELLENT == "excellent"
        assert VisualQuality.GOOD == "good"
        assert VisualQuality.ACCEPTABLE == "acceptable"
        assert VisualQuality.POOR == "poor"
        assert VisualQuality.REJECTED == "rejected"
    
    def test_visual_compliance_status(self):
        """Test visual compliance status enumeration"""
        assert VisualComplianceStatus.APPROVED == "approved"
        assert VisualComplianceStatus.REQUIRES_REVIEW == "requires_review"
        assert VisualComplianceStatus.REJECTED == "rejected"


class TestVisualContentRequest:
    """Test visual content request schema"""
    
    def test_visual_content_request_creation(self):
        """Test creating a visual content request"""
        tenant_config = TenantConfiguration(
            tenant_id="test_tenant",
            brand_name="Test Brand",
            locale="en",
            voice_profile="professional"
        )
        
        request = VisualContentRequest(
            casino_name="Test Casino",
            target_urls=["https://example.com", "https://example.com/games"],
            content_types=[VisualContentType.CASINO_LOBBY, VisualContentType.GAME_SCREENSHOTS],
            tenant_config=tenant_config,
            capture_settings={"viewport_width": 1920, "viewport_height": 1080},
            processing_requirements={"quality_threshold": 0.8}
        )
        
        assert request.casino_name == "Test Casino"
        assert len(request.target_urls) == 2
        assert len(request.content_types) == 2
        assert request.tenant_config.tenant_id == "test_tenant"
        assert request.capture_settings["viewport_width"] == 1920


class TestVisualContentAsset:
    """Test visual content asset schema"""
    
    def test_visual_content_asset_creation(self):
        """Test creating a visual content asset"""
        asset = VisualContentAsset(
            asset_id="test_asset_123",
            filename="test_casino_lobby.png",
            content_type=VisualContentType.CASINO_LOBBY,
            original_url="https://example.com",
            storage_url="https://storage.example.com/test_casino_lobby.png",
            quality_score=0.85,
            compliance_status=VisualComplianceStatus.APPROVED,
            alt_text="Test casino main lobby interface",
            caption="Featured games and promotional banners"
        )
        
        assert asset.asset_id == "test_asset_123"
        assert asset.content_type == VisualContentType.CASINO_LOBBY
        assert asset.quality_score == 0.85
        assert asset.compliance_status == VisualComplianceStatus.APPROVED
        assert "lobby" in asset.alt_text
    
    def test_visual_content_asset_defaults(self):
        """Test visual content asset with default values"""
        asset = VisualContentAsset(
            asset_id="test_123",
            filename="test.png",
            content_type=VisualContentType.CASINO_LOBBY,
            original_url="https://example.com",
            storage_url="https://storage.example.com/test.png",
            quality_score=0.7,
            compliance_status=VisualComplianceStatus.APPROVED,
            alt_text="Test image"
        )
        
        assert asset.thumbnail_url is None
        assert asset.caption is None
        assert isinstance(asset.metadata, dict)
        assert isinstance(asset.created_at, datetime)


class TestVisualContentCapture:
    """Test visual content capture functionality"""
    
    @pytest.fixture
    def mock_browserbase_toolkit(self):
        """Mock Browserbase screenshot toolkit"""
        mock_toolkit = Mock()
        mock_toolkit.capture_casino_screenshots.return_value = Mock(
            success=True,
            screenshots=[{
                "url": "https://example.com",
                "success": True,
                "image_data": "mock_image_data"
            }],
            storage_urls=["https://storage.example.com/screenshot.png"],
            metadata={"capture_method": "browserbase", "timestamp": datetime.now().isoformat()}
        )
        return mock_toolkit
    
    @pytest.fixture
    def visual_content_request(self):
        """Sample visual content request"""
        tenant_config = TenantConfiguration(
            tenant_id="test_tenant",
            brand_name="Test Brand",
            locale="en"
        )
        
        return VisualContentRequest(
            casino_name="Test Casino",
            target_urls=["https://example.com"],
            content_types=[VisualContentType.CASINO_LOBBY],
            tenant_config=tenant_config
        )
    
    def test_visual_content_capture_init(self, mock_browserbase_toolkit):
        """Test visual content capture initialization"""
        capture = VisualContentCapture(browserbase_toolkit=mock_browserbase_toolkit)
        
        assert capture.browserbase_toolkit == mock_browserbase_toolkit
        assert capture.primary_service == mock_browserbase_toolkit
    
    def test_capture_casino_screenshots_success(self, mock_browserbase_toolkit, visual_content_request):
        """Test successful casino screenshot capture"""
        capture = VisualContentCapture(browserbase_toolkit=mock_browserbase_toolkit)
        
        results = capture.capture_casino_screenshots(visual_content_request)
        
        assert "screenshots" in results
        assert "metadata" in results
        assert results["metadata"]["casino_name"] == "Test Casino"
        assert results["metadata"]["total_urls"] == 1
        assert len(results["screenshots"]) == 1
        
        # Verify mock was called
        mock_browserbase_toolkit.capture_casino_screenshots.assert_called_once()
    
    def test_capture_casino_screenshots_no_service(self, visual_content_request):
        """Test screenshot capture with no service available"""
        capture = VisualContentCapture()  # No services provided
        
        with pytest.raises(ValueError, match="No screenshot service available"):
            capture.capture_casino_screenshots(visual_content_request)


class TestVisualContentProcessor:
    """Test visual content processor functionality"""
    
    @pytest.fixture
    def mock_llm(self):
        """Mock LLM for visual analysis"""
        mock_llm = Mock()
        mock_llm.invoke.return_value = """{
            "content_type": "casino_lobby",
            "quality": "good",
            "quality_score": 0.8,
            "alt_text": "Casino main lobby with game selection",
            "caption": "Featured slot games and table games",
            "compliance_status": "approved",
            "compliance_notes": "No compliance issues detected",
            "key_features": ["game lobby", "promotional banners", "navigation menu"],
            "technical_quality": {
                "clarity": 0.85,
                "composition": 0.75,
                "relevance": 0.9
            }
        }"""
        return mock_llm
    
    @pytest.fixture
    def visual_content_processor(self, mock_llm):
        """Visual content processor with mock LLM"""
        return VisualContentProcessor(llm=mock_llm)
    
    @pytest.fixture
    def sample_capture_results(self):
        """Sample screenshot capture results"""
        return {
            "screenshots": [
                {
                    "url": "https://example.com",
                    "success": True,
                    "storage_urls": ["https://storage.example.com/screenshot.png"],
                    "metadata": {"timestamp": datetime.now().isoformat()}
                }
            ],
            "metadata": {
                "capture_method": "browserbase",
                "casino_name": "Test Casino"
            }
        }
    
    @pytest.fixture
    def visual_content_request(self):
        """Sample visual content request"""
        tenant_config = TenantConfiguration(
            tenant_id="test_tenant",
            brand_name="Test Brand",
            locale="en"
        )
        
        return VisualContentRequest(
            casino_name="Test Casino",
            target_urls=["https://example.com"],
            content_types=[VisualContentType.CASINO_LOBBY],
            tenant_config=tenant_config
        )
    
    def test_process_visual_assets_success(self, visual_content_processor, sample_capture_results, visual_content_request):
        """Test successful visual asset processing"""
        assets = visual_content_processor.process_visual_assets(sample_capture_results, visual_content_request)
        
        assert len(assets) == 1
        asset = assets[0]
        
        assert isinstance(asset, VisualContentAsset)
        assert asset.content_type == VisualContentType.CASINO_LOBBY
        assert asset.quality_score == 0.8
        assert asset.compliance_status == VisualComplianceStatus.APPROVED
        assert "lobby" in asset.alt_text.lower()
        assert "Test Casino" in asset.filename
    
    def test_process_visual_assets_failed_screenshots(self, visual_content_processor, visual_content_request):
        """Test processing with failed screenshots"""
        failed_capture_results = {
            "screenshots": [
                {
                    "url": "https://example.com",
                    "success": False,
                    "error": "Screenshot capture failed"
                }
            ]
        }
        
        assets = visual_content_processor.process_visual_assets(failed_capture_results, visual_content_request)
        
        assert len(assets) == 0  # No successful screenshots to process
    
    def test_analyze_screenshot_llm_failure(self, visual_content_request):
        """Test screenshot analysis with LLM failure"""
        # Create processor with failing LLM
        failing_llm = Mock()
        failing_llm.invoke.side_effect = Exception("LLM analysis failed")
        
        processor = VisualContentProcessor(llm=failing_llm)
        
        screenshot_data = {
            "url": "https://example.com",
            "success": True,
            "storage_urls": ["https://storage.example.com/test.png"]
        }
        
        analysis = processor._analyze_screenshot(screenshot_data, visual_content_request)
        
        # Should return default analysis on failure
        assert analysis["content_type"] == "casino_lobby"
        assert analysis["quality"] == "acceptable"
        assert analysis["compliance_status"] == "requires_review"
        assert "failed" in analysis["compliance_notes"]


class TestVisualContentValidator:
    """Test visual content validator functionality"""
    
    @pytest.fixture
    def mock_llm(self):
        """Mock LLM for compliance validation"""
        mock_llm = Mock()
        mock_llm.invoke.return_value = """{
            "compliance_approved": true,
            "compliance_score": 0.9,
            "violations": [],
            "recommendations": ["Consider adding more prominent responsible gambling messaging"],
            "jurisdiction_specific": {
                "uk_compliance": true,
                "de_compliance": true,
                "us_compliance": true
            },
            "accessibility_score": 0.85,
            "final_status": "approved"
        }"""
        return mock_llm
    
    @pytest.fixture
    def visual_content_validator(self, mock_llm):
        """Visual content validator with mock LLM"""
        return VisualContentValidator(llm=mock_llm)
    
    @pytest.fixture
    def sample_visual_assets(self):
        """Sample visual content assets"""
        return [
            VisualContentAsset(
                asset_id="test_asset_1",
                filename="test_casino_lobby.png",
                content_type=VisualContentType.CASINO_LOBBY,
                original_url="https://example.com",
                storage_url="https://storage.example.com/test_casino_lobby.png",
                quality_score=0.85,
                compliance_status=VisualComplianceStatus.REQUIRES_REVIEW,
                alt_text="Casino main lobby interface"
            ),
            VisualContentAsset(
                asset_id="test_asset_2",
                filename="test_casino_games.png",
                content_type=VisualContentType.GAME_SCREENSHOTS,
                original_url="https://example.com/games",
                storage_url="https://storage.example.com/test_casino_games.png",
                quality_score=0.78,
                compliance_status=VisualComplianceStatus.REQUIRES_REVIEW,
                alt_text="Casino game selection"
            )
        ]
    
    @pytest.fixture
    def tenant_config(self):
        """Sample tenant configuration"""
        return TenantConfiguration(
            tenant_id="test_tenant",
            brand_name="Test Brand",
            locale="en",
            voice_profile="professional"
        )
    
    def test_validate_visual_assets_success(self, visual_content_validator, sample_visual_assets, tenant_config):
        """Test successful visual asset validation"""
        validation_results = visual_content_validator.validate_visual_assets(sample_visual_assets, tenant_config)
        
        assert validation_results["total_assets"] == 2
        assert validation_results["approved_count"] == 2  # Mock returns approved status
        assert validation_results["requires_review_count"] == 0
        assert validation_results["rejected_count"] == 0
        assert validation_results["overall_compliance_score"] == 0.9
        assert len(validation_results["asset_validations"]) == 2
    
    def test_validate_single_asset_llm_failure(self, sample_visual_assets, tenant_config):
        """Test asset validation with LLM failure"""
        # Create validator with failing LLM
        failing_llm = Mock()
        failing_llm.invoke.side_effect = Exception("Validation failed")
        
        validator = VisualContentValidator(llm=failing_llm)
        
        validation = validator._validate_single_asset(sample_visual_assets[0], tenant_config)
        
        assert validation["compliance_approved"] is False
        assert validation["compliance_score"] == 0.0
        assert "Validation process failed" in validation["violations"]
        assert validation["final_status"] == "requires_review"


class TestVisualContentPipeline:
    """Test complete visual content pipeline"""
    
    @pytest.fixture
    def mock_vector_store(self):
        """Mock vector store"""
        return Mock()
    
    @pytest.fixture
    def mock_llm(self):
        """Mock LLM for pipeline"""
        mock_llm = Mock()
        mock_llm.invoke.return_value = """{
            "content_type": "casino_lobby",
            "quality": "good",
            "quality_score": 0.8,
            "alt_text": "Casino lobby interface",
            "caption": null,
            "compliance_status": "approved",
            "compliance_notes": "No issues detected",
            "key_features": ["games", "promotions"],
            "technical_quality": {"clarity": 0.8, "composition": 0.7, "relevance": 0.9}
        }"""
        return mock_llm
    
    @pytest.fixture
    @patch('src.chains.visual_content_pipeline.VisualContentCapture')
    def visual_content_pipeline(self, mock_capture_class, mock_vector_store, mock_llm):
        """Visual content pipeline with mocked dependencies"""
        # Mock the capture service
        mock_capture = Mock()
        mock_capture.capture_casino_screenshots.return_value = {
            "screenshots": [{
                "url": "https://example.com",
                "success": True,
                "storage_urls": ["https://storage.example.com/test.png"],
                "metadata": {"timestamp": datetime.now().isoformat()}
            }],
            "metadata": {"capture_method": "mock", "casino_name": "Test Casino"}
        }
        mock_capture_class.return_value = mock_capture
        
        return VisualContentPipeline(vector_store=mock_vector_store, llm=mock_llm)
    
    @pytest.fixture
    def sample_visual_request(self):
        """Sample visual content request"""
        tenant_config = TenantConfiguration(
            tenant_id="test_tenant",
            brand_name="Test Brand",
            locale="en"
        )
        
        return VisualContentRequest(
            casino_name="Test Casino",
            target_urls=["https://example.com"],
            content_types=[VisualContentType.CASINO_LOBBY],
            tenant_config=tenant_config
        )
    
    def test_visual_content_pipeline_creation(self, mock_vector_store, mock_llm):
        """Test visual content pipeline creation"""
        pipeline = VisualContentPipeline(vector_store=mock_vector_store, llm=mock_llm)
        
        assert pipeline.vector_store == mock_vector_store
        assert pipeline.llm == mock_llm
        assert hasattr(pipeline, 'chain')
        assert hasattr(pipeline, 'capture_service')
        assert hasattr(pipeline, 'processor')
        assert hasattr(pipeline, 'validator')
    
    def test_process_visual_content_success(self, visual_content_pipeline, sample_visual_request):
        """Test successful visual content processing"""
        result = visual_content_pipeline.process_visual_content(sample_visual_request)
        
        assert isinstance(result, VisualContentResult)
        assert result.success is True
        assert result.casino_name == "Test Casino"
        assert len(result.assets) > 0
        assert result.processing_metadata["total_processed"] > 0
        assert "average_quality" in result.quality_summary
    
    def test_create_visual_content_pipeline_factory(self, mock_vector_store):
        """Test visual content pipeline factory function"""
        pipeline = create_visual_content_pipeline(
            vector_store=mock_vector_store,
            llm_model="gpt-4o",
            temperature=0.1
        )
        
        assert isinstance(pipeline, VisualContentPipeline)
        assert pipeline.vector_store == mock_vector_store


class TestEnhancedContentGenerationWorkflow:
    """Test enhanced content generation workflow with visual integration"""
    
    @pytest.fixture
    def mock_retrieval_system(self):
        """Mock multi-tenant retrieval system"""
        mock_system = Mock()
        mock_system.retrieve.return_value = Mock(
            query_text="test query",
            documents=[Mock(page_content="test content", metadata={})],
            confidence_score=0.8,
            metadata={}
        )
        return mock_system
    
    @pytest.fixture
    def mock_narrative_chain(self):
        """Mock narrative generation chain"""
        mock_chain = Mock()
        mock_chain.generate_narrative.return_value = Mock(
            generated_content="Generated test content for Test Casino",
            review_doc=Mock(
                casino_name="Test Casino",
                content="Test review content"
            ),
            retrieval_context=[],
            generation_metadata={}
        )
        return mock_chain
    
    @pytest.fixture
    def mock_qa_chain(self):
        """Mock QA compliance chain"""
        mock_chain = Mock()
        mock_chain.validate_content.return_value = Mock(
            overall_score=8.5,
            compliance_status=Mock(value="passed"),
            validation_details={},
            recommendations=[]
        )
        return mock_chain
    
    @pytest.fixture
    def mock_visual_pipeline(self):
        """Mock visual content pipeline"""
        mock_pipeline = Mock()
        mock_pipeline.process_visual_content.return_value = VisualContentResult(
            success=True,
            casino_name="Test Casino",
            assets=[
                VisualContentAsset(
                    asset_id="test_asset",
                    filename="test_casino.png",
                    content_type=VisualContentType.CASINO_LOBBY,
                    original_url="https://example.com",
                    storage_url="https://storage.example.com/test_casino.png",
                    quality_score=0.8,
                    compliance_status=VisualComplianceStatus.APPROVED,
                    alt_text="Test casino lobby"
                )
            ],
            compliance_summary={
                "total_assets": 1,
                "approved_count": 1,
                "requires_review_count": 0,
                "rejected_count": 0,
                "overall_compliance_score": 0.8
            }
        )
        return mock_pipeline
    
    @pytest.fixture
    def enhanced_workflow(self, mock_retrieval_system, mock_narrative_chain, mock_qa_chain, mock_visual_pipeline):
        """Enhanced content generation workflow with mocked dependencies"""
        return EnhancedContentGenerationWorkflow(
            retrieval_system=mock_retrieval_system,
            narrative_chain=mock_narrative_chain,
            qa_chain=mock_qa_chain,
            visual_pipeline=mock_visual_pipeline
        )
    
    @pytest.fixture
    def enhanced_request(self):
        """Sample enhanced content generation request"""
        tenant_config = TenantConfiguration(
            tenant_id="test_tenant",
            brand_name="Test Brand",
            locale="en",
            voice_profile="professional"
        )
        
        return EnhancedContentGenerationRequest(
            casino_name="Test Casino",
            tenant_config=tenant_config,
            query_context="comprehensive review with visual content",
            target_urls=["https://example.com"],
            visual_content_types=[VisualContentType.CASINO_LOBBY],
            validation_level=QAValidationLevel.STANDARD,
            auto_publish_threshold=8.0,
            include_visual_content=True,
            visual_compliance_required=True,
            parallel_processing=True
        )
    
    def test_enhanced_workflow_creation(self, enhanced_workflow):
        """Test enhanced workflow creation"""
        assert hasattr(enhanced_workflow, 'retrieval_system')
        assert hasattr(enhanced_workflow, 'narrative_chain')
        assert hasattr(enhanced_workflow, 'qa_chain')
        assert hasattr(enhanced_workflow, 'visual_pipeline')
        assert hasattr(enhanced_workflow, 'workflow_chain')
    
    def test_enhanced_workflow_execution_success(self, enhanced_workflow, enhanced_request):
        """Test successful enhanced workflow execution"""
        result = enhanced_workflow.execute_enhanced_workflow(enhanced_request)
        
        assert isinstance(result, EnhancedContentGenerationResult)
        assert result.success is True
        assert result.visual_assets_count == 1
        assert result.visual_compliance_approved is True
        assert result.publish_approved is True
        assert "visual_content" in result.processing_stages or "visual_content" in str(result.processing_stages)
    
    def test_enhanced_workflow_visual_disabled(self, enhanced_workflow):
        """Test enhanced workflow with visual content disabled"""
        tenant_config = TenantConfiguration(
            tenant_id="test_tenant",
            brand_name="Test Brand",
            locale="en"
        )
        
        request = EnhancedContentGenerationRequest(
            casino_name="Test Casino",
            tenant_config=tenant_config,
            query_context="text-only review",
            include_visual_content=False  # Disable visual content
        )
        
        result = enhanced_workflow.execute_enhanced_workflow(request)
        
        assert isinstance(result, EnhancedContentGenerationResult)
        # Should still succeed even without visual content
        assert result.visual_assets_count == 0


class TestIntegrationScenarios:
    """Test integration scenarios and end-to-end workflows"""
    
    @pytest.fixture
    def full_mock_setup(self):
        """Complete mock setup for integration testing"""
        mocks = {
            'vector_store': Mock(),
            'llm': Mock(),
            'browserbase_toolkit': Mock(),
            'playwright_service': Mock()
        }
        
        # Configure LLM mock
        mocks['llm'].invoke.return_value = """{
            "content_type": "casino_lobby",
            "quality": "excellent",
            "quality_score": 0.9,
            "alt_text": "Premium casino lobby interface",
            "caption": "High-quality game selection and promotions",
            "compliance_status": "approved",
            "compliance_notes": "All compliance requirements met",
            "key_features": ["premium games", "VIP section", "live dealers"],
            "technical_quality": {"clarity": 0.95, "composition": 0.9, "relevance": 0.95}
        }"""
        
        # Configure Browserbase mock
        mocks['browserbase_toolkit'].capture_casino_screenshots.return_value = Mock(
            success=True,
            screenshots=[{
                "url": "https://example.com",
                "success": True,
                "image_data": "mock_premium_screenshot"
            }],
            storage_urls=["https://storage.example.com/premium_casino.png"],
            metadata={"quality": "premium", "timestamp": datetime.now().isoformat()}
        )
        
        return mocks
    
    def test_end_to_end_visual_pipeline(self, full_mock_setup):
        """Test complete end-to-end visual content pipeline"""
        # Create pipeline with mocked dependencies
        with patch('src.chains.visual_content_pipeline.VisualContentCapture') as mock_capture_class:
            mock_capture = Mock()
            mock_capture.capture_casino_screenshots.return_value = {
                "screenshots": [{
                    "url": "https://premium-casino.com",
                    "success": True,
                    "storage_urls": ["https://storage.example.com/premium.png"],
                    "metadata": {"quality": "premium"}
                }],
                "metadata": {"capture_method": "browserbase"}
            }
            mock_capture_class.return_value = mock_capture
            
            pipeline = VisualContentPipeline(
                vector_store=full_mock_setup['vector_store'],
                llm=full_mock_setup['llm']
            )
            
            # Create premium request
            tenant_config = TenantConfiguration(
                tenant_id="premium_tenant",
                brand_name="Premium Casino Guide",
                locale="en",
                voice_profile="premium-professional"
            )
            
            request = VisualContentRequest(
                casino_name="Premium Casino",
                target_urls=["https://premium-casino.com"],
                content_types=[VisualContentType.CASINO_LOBBY, VisualContentType.GAME_SCREENSHOTS],
                tenant_config=tenant_config,
                capture_settings={"viewport_width": 1920, "viewport_height": 1080},
                processing_requirements={"quality_threshold": 0.9}
            )
            
            # Execute pipeline
            result = pipeline.process_visual_content(request)
            
            # Verify results
            assert result.success is True
            assert result.casino_name == "Premium Casino"
            assert len(result.assets) > 0
            assert result.quality_summary["average_quality"] == 0.9
            assert result.compliance_summary["approved_count"] > 0
    
    def test_error_handling_cascade(self):
        """Test error handling throughout the pipeline"""
        # Create pipeline with failing components
        failing_llm = Mock()
        failing_llm.invoke.side_effect = Exception("LLM service unavailable")
        
        pipeline = VisualContentPipeline(llm=failing_llm)
        
        tenant_config = TenantConfiguration(
            tenant_id="test_tenant",
            brand_name="Test Brand",
            locale="en"
        )
        
        request = VisualContentRequest(
            casino_name="Test Casino",
            target_urls=["https://example.com"],
            content_types=[VisualContentType.CASINO_LOBBY],
            tenant_config=tenant_config
        )
        
        # Execute pipeline - should handle errors gracefully
        result = pipeline.process_visual_content(request)
        
        assert isinstance(result, VisualContentResult)
        assert result.success is False
        assert result.error_details is not None
        assert "failed" in result.error_details.lower()


@pytest.mark.performance
class TestPerformanceAndScaling:
    """Performance and scaling tests for visual content pipeline"""
    
    def test_multiple_asset_processing_performance(self):
        """Test performance with multiple visual assets"""
        # This would be expanded with actual performance benchmarks
        # For now, just verify the pipeline can handle multiple assets
        
        mock_llm = Mock()
        mock_llm.invoke.return_value = """{
            "content_type": "casino_lobby",
            "quality": "good",
            "quality_score": 0.8,
            "alt_text": "Casino interface",
            "caption": null,
            "compliance_status": "approved",
            "compliance_notes": "",
            "key_features": [],
            "technical_quality": {"clarity": 0.8, "composition": 0.8, "relevance": 0.8}
        }"""
        
        pipeline = VisualContentPipeline(llm=mock_llm)
        
        # Create request with multiple URLs
        tenant_config = TenantConfiguration(
            tenant_id="perf_test",
            brand_name="Performance Test",
            locale="en"
        )
        
        multiple_urls = [f"https://example.com/page{i}" for i in range(5)]
        
        request = VisualContentRequest(
            casino_name="Performance Test Casino",
            target_urls=multiple_urls,
            content_types=[VisualContentType.CASINO_LOBBY],
            tenant_config=tenant_config
        )
        
        # Mock the capture to return multiple successful screenshots
        with patch.object(pipeline.capture_service, 'capture_casino_screenshots') as mock_capture:
            mock_capture.return_value = {
                "screenshots": [
                    {
                        "url": url,
                        "success": True,
                        "storage_urls": [f"https://storage.example.com/{i}.png"],
                        "metadata": {"index": i}
                    }
                    for i, url in enumerate(multiple_urls)
                ],
                "metadata": {"total_urls": len(multiple_urls)}
            }
            
            result = pipeline.process_visual_content(request)
            
            assert result.success is True
            assert len(result.assets) == len(multiple_urls)
            assert result.processing_metadata["total_processed"] == len(multiple_urls)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])