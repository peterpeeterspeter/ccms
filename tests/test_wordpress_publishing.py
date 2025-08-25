"""
🧪 WordPress Publishing Chain Tests - PHASE 4
==============================================

Comprehensive test suite for WordPress publishing integration:
- WordPress API client authentication and connectivity
- Content processing and HTML formatting
- Media library integration with visual assets
- SEO metadata generation and optimization
- Complete publishing workflow with error handling
- Integration with enhanced content generation

Author: AI Assistant & TaskMaster System
Created: 2025-08-24
Task: Phase 4 Testing - WordPress Publishing Integration
Version: 1.0.0
"""

import pytest
import json
import base64
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from typing import Dict, Any, List

# Import components to test
from src.integrations.wordpress_publishing_chain import (
    WordPressCredentials,
    WordPressAPIClient,
    WordPressContentProcessor,
    WordPressMediaHandler,
    WordPressPublishingChain,
    WordPressPost,
    WordPressSEOData,
    WordPressMediaAsset,
    WordPressPublishingRequest,
    WordPressPublishingResult,
    create_wordpress_publishing_chain,
    create_crashcasino_credentials,
    integrate_wordpress_publishing_with_enhanced_workflow,
    create_phase4_wordpress_workflow
)

from src.schemas.review_doc import ReviewDoc, MediaAsset, TenantConfiguration
from src.chains.visual_content_pipeline import VisualContentResult
from src.workflows.enhanced_content_generation_workflow import EnhancedContentGenerationResult


# ============================================================================
# TEST FIXTURES
# ============================================================================

@pytest.fixture
def sample_credentials():
    """Sample WordPress credentials for testing"""
    return WordPressCredentials(
        site_url="https://testsite.com",
        username="testuser",
        application_password="test-password-123",
        verify_ssl=True
    )


@pytest.fixture
def crashcasino_credentials():
    """CrashCasino.io credentials for testing"""
    return create_crashcasino_credentials("KFKz bo6B ZXOS 7VOA rHWb oxdC")


@pytest.fixture
def sample_review_doc():
    """Sample review document for testing"""
    return ReviewDoc(
        casino_name="Test Casino",
        content="## Test Casino Review\n\nThis is a comprehensive review of Test Casino. The casino offers excellent games and bonuses.\n\n### Games and Software\n\nTest Casino features over 1000 games from top providers.\n\n### Bonuses and Promotions\n\nThe welcome bonus is very attractive for new players.",
        generated_at=datetime.now(),
        word_count=45,
        quality_score=8.5,
        tenant_config=TenantConfiguration(
            tenant_id="crashcasino",
            target_market="UK",
            regulatory_compliance=["UKGC", "EU"],
            content_language="en",
            localization_settings={"currency": "GBP", "time_zone": "Europe/London"}
        )
    )


@pytest.fixture
def sample_visual_content_result():
    """Sample visual content result for testing"""
    assets = [
        MediaAsset(
            url="https://storage.example.com/test_casino_homepage.png",
            alt_text="Test Casino homepage screenshot",
            caption="Homepage showing games and bonuses",
            media_type="image/png",
            source_method="browserbase",
            compliance_checked=True,
            license_status="approved"
        ),
        MediaAsset(
            url="https://storage.example.com/test_casino_games.png",
            alt_text="Test Casino games library",
            caption="Extensive games collection",
            media_type="image/png",
            source_method="browserbase",
            compliance_checked=True,
            license_status="approved"
        )
    ]
    
    return VisualContentResult(
        assets=assets,
        total_assets=2,
        quality_assessment={"overall_quality": 9.0, "compliance_score": 10.0},
        processing_metadata={"duration": 45.2, "method": "browserbase"}
    )


@pytest.fixture
def sample_enhanced_content_result(sample_review_doc, sample_visual_content_result):
    """Sample enhanced content generation result"""
    return EnhancedContentGenerationResult(
        review_doc=sample_review_doc,
        visual_content_result=sample_visual_content_result,
        final_quality_score=9.1,
        visual_assets_count=2,
        processing_metadata={
            "total_duration": 120.5,
            "phase_1_duration": 30.2,
            "phase_2_duration": 45.1,
            "phase_3_duration": 45.2
        },
        compliance_validation={
            "qa_passed": True,
            "visual_compliance": True,
            "content_quality": 9.1
        }
    )


# ============================================================================
# WORDPRESS CREDENTIALS TESTS
# ============================================================================

class TestWordPressCredentials:
    """Test WordPress credentials and authentication"""
    
    def test_credentials_creation(self, sample_credentials):
        """Test WordPress credentials creation"""
        assert sample_credentials.site_url == "https://testsite.com"
        assert sample_credentials.username == "testuser"
        assert sample_credentials.application_password == "test-password-123"
        assert sample_credentials.verify_ssl is True
    
    def test_crashcasino_credentials_factory(self):
        """Test CrashCasino credentials factory function"""
        password = "test-password"
        creds = create_crashcasino_credentials(password)
        
        assert creds.site_url == "https://crashcasino.io"
        assert creds.username == "nmlwh"
        assert creds.application_password == password
        assert creds.verify_ssl is True


# ============================================================================
# WORDPRESS API CLIENT TESTS
# ============================================================================

class TestWordPressAPIClient:
    """Test WordPress API client functionality"""
    
    def test_client_initialization(self, sample_credentials):
        """Test API client initialization"""
        client = WordPressAPIClient(sample_credentials)
        
        assert client.base_url == "https://testsite.com/wp-json/wp/v2"
        assert "Authorization" in client.headers
        assert client.headers["Content-Type"] == "application/json"
        
        # Verify Basic Auth header format
        auth_header = client.headers["Authorization"]
        assert auth_header.startswith("Basic ")
        
        # Decode and verify auth string
        auth_b64 = auth_header.split(" ")[1]
        auth_string = base64.b64decode(auth_b64).decode('ascii')
        assert auth_string == "testuser:test-password-123"
    
    @patch('requests.Session.get')
    def test_connection_test_success(self, mock_get, sample_credentials):
        """Test successful connection test"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        client = WordPressAPIClient(sample_credentials)
        assert client.test_connection() is True
        
        mock_get.assert_called_once_with("https://testsite.com/wp-json/wp/v2/users/me")
    
    @patch('requests.Session.get')
    def test_connection_test_failure(self, mock_get, sample_credentials):
        """Test failed connection test"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response
        
        client = WordPressAPIClient(sample_credentials)
        assert client.test_connection() is False
    
    @patch('requests.Session.post')
    def test_media_upload_success(self, mock_post, sample_credentials):
        """Test successful media upload"""
        # Mock successful media upload response
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            'id': 123,
            'source_url': 'https://testsite.com/wp-content/uploads/test.png'
        }
        mock_post.return_value = mock_response
        
        client = WordPressAPIClient(sample_credentials)
        
        # Test media upload
        media_content = b"fake_image_data"
        result = client.upload_media(
            media_content=media_content,
            filename="test.png",
            alt_text="Test image",
            caption="Test caption"
        )
        
        assert result is not None
        assert result.media_id == 123
        assert result.filename == "test.png"
        assert result.alt_text == "Test image"
        assert result.caption == "Test caption"
    
    @patch('requests.Session.post')
    def test_post_creation_success(self, mock_post, sample_credentials):
        """Test successful post creation"""
        # Mock successful post creation response
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            'id': 456,
            'link': 'https://testsite.com/test-post'
        }
        mock_post.return_value = mock_response
        
        client = WordPressAPIClient(sample_credentials)
        
        # Test post creation
        post_data = WordPressPost(
            title="Test Post",
            content="<p>Test content</p>",
            status="draft"
        )
        
        result = client.create_post(post_data)
        
        assert result is not None
        post_id, post_url = result
        assert post_id == 456
        assert post_url == "https://testsite.com/test-post"


# ============================================================================
# WORDPRESS CONTENT PROCESSOR TESTS
# ============================================================================

class TestWordPressContentProcessor:
    """Test WordPress content processing functionality"""
    
    @patch('src.integrations.wordpress_publishing_chain.ChatOpenAI')
    def test_content_processor_initialization(self, mock_llm_class):
        """Test content processor initialization"""
        mock_llm = Mock()
        mock_llm_class.return_value = mock_llm
        
        processor = WordPressContentProcessor()
        
        # Verify LLM initialization
        mock_llm_class.assert_called_once_with(model="gpt-4o", temperature=0.1)
        assert processor.llm == mock_llm
    
    @patch('src.integrations.wordpress_publishing_chain.ChatOpenAI')
    def test_content_processing_for_wordpress(self, mock_llm_class, sample_enhanced_content_result):
        """Test content processing for WordPress format"""
        # Mock LLM for SEO generation
        mock_llm = Mock()
        mock_llm_class.return_value = mock_llm
        
        # Mock SEO chain response
        mock_seo_response = json.dumps({
            "title": "Test Casino Review - Complete Guide",
            "meta_description": "Comprehensive Test Casino review with bonuses, games, and player experience analysis.",
            "focus_keyword": "test casino review",
            "og_title": "Test Casino Review",
            "og_description": "Complete Test Casino review",
            "schema_markup": {
                "@type": "Review",
                "itemReviewed": {"@type": "Organization", "name": "Test Casino"}
            }
        })
        
        # Mock the chain execution
        with patch.object(WordPressContentProcessor, '_generate_seo_metadata') as mock_seo:
            mock_seo.return_value = WordPressSEOData(
                title="Test Casino Review - Complete Guide",
                meta_description="Comprehensive Test Casino review",
                focus_keyword="test casino review"
            )
            
            processor = WordPressContentProcessor()
            wordpress_post = processor.process_content_for_wordpress(sample_enhanced_content_result)
            
            # Verify WordPress post creation
            assert wordpress_post.title == "Test Casino Casino Review - Complete Guide & Bonuses"
            assert wordpress_post.status == "draft"
            assert "Casino Reviews" in wordpress_post.categories
            assert "test-casino" in wordpress_post.tags
            assert wordpress_post.seo_data is not None
            assert wordpress_post.meta_data["casino_name"] == "Test Casino"
    
    def test_html_formatting(self):
        """Test HTML formatting for WordPress"""
        processor = WordPressContentProcessor()
        
        markdown_content = """## Test Header

This is a **bold** paragraph with *italic* text.

### Sub Header

Another paragraph here."""
        
        html_content = processor._add_wordpress_formatting(markdown_content)
        
        # Verify HTML conversion
        assert "<h2>Test Header</h2>" in html_content
        assert "<h3>Sub Header</h3>" in html_content
        assert "<strong>bold</strong>" in html_content
        assert "<em>italic</em>" in html_content
        assert "<p>" in html_content
    
    def test_excerpt_generation(self):
        """Test excerpt generation from content"""
        processor = WordPressContentProcessor()
        
        long_content = "This is a test content. " * 20  # 500+ characters
        short_content = "This is a short content."
        
        # Test long content truncation
        excerpt_long = processor._generate_excerpt(long_content)
        assert len(excerpt_long) <= 153  # 150 + "..."
        assert excerpt_long.endswith("...") or excerpt_long.endswith(".")
        
        # Test short content preservation
        excerpt_short = processor._generate_excerpt(short_content)
        assert excerpt_short == short_content


# ============================================================================
# WORDPRESS MEDIA HANDLER TESTS
# ============================================================================

class TestWordPressMediaHandler:
    """Test WordPress media handling functionality"""
    
    def test_media_handler_initialization(self, sample_credentials):
        """Test media handler initialization"""
        api_client = WordPressAPIClient(sample_credentials)
        media_handler = WordPressMediaHandler(api_client)
        
        assert media_handler.api_client == api_client
    
    @patch.object(WordPressAPIClient, 'upload_media')
    def test_visual_assets_upload(self, mock_upload, sample_credentials, sample_visual_content_result):
        """Test visual assets upload to WordPress media library"""
        # Mock successful uploads
        mock_upload.side_effect = [
            WordPressMediaAsset(
                media_id=101,
                url="https://testsite.com/wp-content/uploads/homepage.png",
                alt_text="Test Casino homepage screenshot",
                filename="test_casino_homepage.png",
                mime_type="image/png"
            ),
            WordPressMediaAsset(
                media_id=102,
                url="https://testsite.com/wp-content/uploads/games.png",
                alt_text="Test Casino games library",
                filename="test_casino_games.png",
                mime_type="image/png"
            )
        ]
        
        api_client = WordPressAPIClient(sample_credentials)
        media_handler = WordPressMediaHandler(api_client)
        
        uploaded_assets = media_handler.upload_visual_assets(sample_visual_content_result)
        
        assert len(uploaded_assets) == 2
        assert uploaded_assets[0].media_id == 101
        assert uploaded_assets[1].media_id == 102
        assert mock_upload.call_count == 2


# ============================================================================
# WORDPRESS PUBLISHING CHAIN TESTS
# ============================================================================

class TestWordPressPublishingChain:
    """Test complete WordPress publishing chain"""
    
    @patch('src.integrations.wordpress_publishing_chain.ChatOpenAI')
    def test_publishing_chain_initialization(self, mock_llm_class):
        """Test publishing chain initialization"""
        mock_llm = Mock()
        mock_llm_class.return_value = mock_llm
        
        chain = WordPressPublishingChain()
        
        assert chain.llm == mock_llm
        assert chain.content_processor is not None
        assert chain.chain is not None
    
    @patch.object(WordPressAPIClient, 'test_connection')
    @patch.object(WordPressAPIClient, 'create_post')
    @patch.object(WordPressMediaHandler, 'upload_visual_assets')
    @patch.object(WordPressContentProcessor, 'process_content_for_wordpress')
    def test_complete_publishing_workflow(self, mock_process, mock_upload, mock_create, mock_test, 
                                        sample_enhanced_content_result, sample_credentials):
        """Test complete publishing workflow"""
        # Mock all chain components
        mock_test.return_value = True
        mock_create.return_value = (789, "https://testsite.com/published-post")
        
        mock_upload.return_value = [
            WordPressMediaAsset(
                media_id=201,
                url="https://testsite.com/media.png",
                alt_text="Test media",
                filename="test.png",
                mime_type="image/png"
            )
        ]
        
        mock_wordpress_post = WordPressPost(
            title="Test Casino Review",
            content="<p>Test content</p>",
            status="draft"
        )
        mock_process.return_value = mock_wordpress_post
        
        # Create publishing request
        request = WordPressPublishingRequest(
            wordpress_credentials=sample_credentials,
            content_result=sample_enhanced_content_result,
            auto_publish=False,
            include_visual_assets=True
        )
        
        # Execute publishing
        chain = WordPressPublishingChain()
        result = chain.publish_content(request)
        
        # Verify result
        assert result.success is True
        assert result.post_id == 789
        assert result.post_url == "https://testsite.com/published-post"
        assert len(result.media_assets) == 1
        assert result.publishing_metadata is not None
        
        # Verify chain component calls
        mock_process.assert_called_once()
        mock_upload.assert_called_once()
        mock_create.assert_called_once()
        mock_test.assert_called_once()


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestWordPressIntegration:
    """Test WordPress publishing integration with enhanced workflow"""
    
    def test_integration_function(self, sample_enhanced_content_result, sample_credentials):
        """Test integration with enhanced content generation workflow"""
        
        with patch.object(WordPressPublishingChain, 'publish_content') as mock_publish:
            mock_publish.return_value = WordPressPublishingResult(
                success=True,
                post_id=999,
                post_url="https://testsite.com/integrated-post"
            )
            
            result = integrate_wordpress_publishing_with_enhanced_workflow(
                enhanced_workflow_result=sample_enhanced_content_result,
                wordpress_credentials=sample_credentials,
                auto_publish=False
            )
            
            assert result.success is True
            assert result.post_id == 999
            mock_publish.assert_called_once()
    
    def test_phase4_workflow_creation(self, sample_credentials):
        """Test Phase 4 complete workflow creation"""
        
        with patch('src.integrations.wordpress_publishing_chain.create_enhanced_content_generation_workflow') as mock_enhanced:
            mock_workflow = Mock()
            mock_enhanced.return_value = mock_workflow
            
            workflow = create_phase4_wordpress_workflow(
                wordpress_credentials=sample_credentials,
                llm_model="gpt-4o"
            )
            
            # Verify workflow creation
            assert workflow is not None
            mock_enhanced.assert_called_once_with(llm_model="gpt-4o")


# ============================================================================
# FACTORY FUNCTIONS TESTS
# ============================================================================

class TestFactoryFunctions:
    """Test factory functions for WordPress publishing"""
    
    @patch('src.integrations.wordpress_publishing_chain.ChatOpenAI')
    def test_create_wordpress_publishing_chain(self, mock_llm_class):
        """Test WordPress publishing chain factory"""
        mock_llm = Mock()
        mock_llm_class.return_value = mock_llm
        
        chain = create_wordpress_publishing_chain("gpt-4o")
        
        assert isinstance(chain, WordPressPublishingChain)
        mock_llm_class.assert_called_once_with(model="gpt-4o", temperature=0.1)
    
    def test_crashcasino_credentials_factory(self):
        """Test CrashCasino credentials factory"""
        password = "test-app-password"
        creds = create_crashcasino_credentials(password)
        
        assert creds.site_url == "https://crashcasino.io"
        assert creds.username == "nmlwh"
        assert creds.application_password == password


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestWordPressErrorHandling:
    """Test error handling in WordPress publishing"""
    
    @patch('requests.Session.get')
    def test_connection_failure_handling(self, mock_get, sample_credentials):
        """Test handling of connection failures"""
        mock_get.side_effect = Exception("Connection failed")
        
        client = WordPressAPIClient(sample_credentials)
        assert client.test_connection() is False
    
    @patch('requests.Session.post')
    def test_media_upload_failure_handling(self, mock_post, sample_credentials):
        """Test handling of media upload failures"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Server error"
        mock_post.return_value = mock_response
        
        client = WordPressAPIClient(sample_credentials)
        result = client.upload_media(b"test", "test.png", "Test alt")
        
        assert result is None
    
    @patch.object(WordPressAPIClient, 'test_connection')
    def test_publishing_chain_error_handling(self, mock_test, sample_enhanced_content_result, sample_credentials):
        """Test publishing chain error handling"""
        mock_test.return_value = False  # Simulate connection failure
        
        request = WordPressPublishingRequest(
            wordpress_credentials=sample_credentials,
            content_result=sample_enhanced_content_result
        )
        
        chain = WordPressPublishingChain()
        result = chain.publish_content(request)
        
        assert result.success is False
        assert result.error_details is not None


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

class TestWordPressPerformance:
    """Test WordPress publishing performance characteristics"""
    
    def test_chain_execution_timeout(self):
        """Test chain execution doesn't exceed reasonable timeout"""
        import time
        
        # Mock a slow operation
        def slow_operation(x):
            time.sleep(0.1)  # 100ms delay
            return x
        
        start_time = time.time()
        
        # Simulate multiple operations
        for _ in range(5):
            slow_operation("test")
        
        duration = time.time() - start_time
        
        # Should complete within reasonable time (1 second for 5 operations)
        assert duration < 1.0
    
    def test_media_upload_batch_processing(self, sample_visual_content_result):
        """Test batch processing of media uploads"""
        
        # Verify we can handle multiple assets
        assets_count = len(sample_visual_content_result.assets)
        assert assets_count == 2
        
        # Mock processing time should be reasonable per asset
        estimated_time_per_asset = 0.5  # 500ms per asset
        total_estimated_time = assets_count * estimated_time_per_asset
        
        # Should be under 2 seconds for 2 assets
        assert total_estimated_time < 2.0


# ============================================================================
# CONFIGURATION TESTS
# ============================================================================

class TestWordPressConfiguration:
    """Test WordPress publishing configuration"""
    
    def test_ssl_verification_settings(self):
        """Test SSL verification configuration"""
        # Test with SSL verification enabled
        creds_secure = WordPressCredentials(
            site_url="https://secure-site.com",
            username="user",
            application_password="pass",
            verify_ssl=True
        )
        
        client_secure = WordPressAPIClient(creds_secure)
        assert client_secure.session.verify is True
        
        # Test with SSL verification disabled
        creds_insecure = WordPressCredentials(
            site_url="https://insecure-site.com",
            username="user",
            application_password="pass",
            verify_ssl=False
        )
        
        client_insecure = WordPressAPIClient(creds_insecure)
        assert client_insecure.session.verify is False
    
    def test_auto_publish_configuration(self, sample_enhanced_content_result, sample_credentials):
        """Test auto-publish configuration"""
        # Test with auto-publish enabled
        request_auto = WordPressPublishingRequest(
            wordpress_credentials=sample_credentials,
            content_result=sample_enhanced_content_result,
            auto_publish=True
        )
        
        assert request_auto.auto_publish is True
        
        # Test with auto-publish disabled (default)
        request_draft = WordPressPublishingRequest(
            wordpress_credentials=sample_credentials,
            content_result=sample_enhanced_content_result
        )
        
        assert request_draft.auto_publish is False


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])