"""
🧪 Test Suite: Narrative Generation LCEL Chain
Task-012: Comprehensive testing for world-class narrative generation

Test Coverage:
- Multi-locale prompt template loading
- LCEL chain execution with retrieval integration
- Visual content and affiliate metadata processing
- Multi-tenant scenario validation
- ReviewDoc output validation
- Error handling and edge cases
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from pathlib import Path
import tempfile
import os

# Import components under test
from src.chains.narrative_generation_lcel import (
    NarrativeGenerationChain,
    NarrativeGenerationInput,
    NarrativeGenerationOutput,
    NarrativePromptLoader,
    VisualContentProcessor,
    AffiliateMetadataProcessor,
    create_narrative_generation_chain
)
from src.chains.multi_tenant_retrieval_system import (
    MultiTenantRetrievalSystem,
    MultiTenantQuery,
    RetrievalResult
)
from src.schemas.review_doc import (
    ReviewDoc, 
    TenantConfiguration, 
    MediaAsset, 
    MediaType,
    PublishingStatus
)
from src.schemas.casino_intelligence_schema import CasinoIntelligence
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI


class TestNarrativePromptLoader:
    """Test prompt template loading functionality"""
    
    def test_load_english_prompt_template(self):
        """Test loading English prompt template"""
        loader = NarrativePromptLoader()
        
        # Test default English template
        prompt = loader.load_prompt_template("en")
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "world-class casino reviewer" in prompt.lower()
        assert "{images}" in prompt
    
    def test_load_german_prompt_template(self):
        """Test loading German prompt template"""
        loader = NarrativePromptLoader()
        
        prompt = loader.load_prompt_template("de")
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "erstklassiger casino-rezensent" in prompt.lower()
        assert "{images}" in prompt
    
    def test_fallback_to_english(self):
        """Test fallback to English for missing locale"""
        loader = NarrativePromptLoader()
        
        # Test non-existent locale falls back to English
        prompt = loader.load_prompt_template("xx")
        english_prompt = loader.load_prompt_template("en")
        assert prompt == english_prompt
    
    def test_get_available_locales(self):
        """Test getting list of available locales"""
        loader = NarrativePromptLoader()
        
        locales = loader.get_available_locales()
        assert isinstance(locales, list)
        assert "en" in locales
        assert "de" in locales
        assert "fr" in locales
        assert "es" in locales
    
    def test_template_caching(self):
        """Test that templates are cached after first load"""
        loader = NarrativePromptLoader()
        
        # Load template twice
        prompt1 = loader.load_prompt_template("en")
        prompt2 = loader.load_prompt_template("en")
        
        assert prompt1 == prompt2
        assert "en" in loader._cache


class TestVisualContentProcessor:
    """Test visual content processing functionality"""
    
    def test_format_visual_context_empty(self):
        """Test formatting with no visual assets"""
        result = VisualContentProcessor.format_visual_context([])
        assert result == "No visual content available."
    
    def test_format_visual_context_with_assets(self):
        """Test formatting with visual assets"""
        assets = [
            MediaAsset(
                filename="casino-homepage.png",
                url="https://example.com/homepage.png",
                type=MediaType.SCREENSHOT,
                alt_text="Casino homepage",
                caption="Main casino interface"
            ),
            MediaAsset(
                filename="bonus-banner.jpg",
                url="https://example.com/banner.jpg",
                type=MediaType.PROMOTIONAL,
                alt_text="Welcome bonus",
                caption="50% welcome bonus offer"
            )
        ]
        
        result = VisualContentProcessor.format_visual_context(assets)
        assert "Screenshot: casino-homepage.png (Casino homepage) - Main casino interface" in result
        assert "Promotional: bonus-banner.jpg (Welcome bonus) - 50% welcome bonus offer" in result
    
    def test_extract_visual_metadata(self):
        """Test extracting metadata from visual assets"""
        assets = [
            MediaAsset(
                filename="screenshot1.png",
                url="https://example.com/screenshot1.png",
                type=MediaType.SCREENSHOT
            ),
            MediaAsset(
                filename="promo1.jpg",
                url="https://example.com/promo1.jpg",
                type=MediaType.PROMOTIONAL
            )
        ]
        
        metadata = VisualContentProcessor.extract_visual_metadata(assets)
        
        assert metadata["total_images"] == 2
        assert "screenshot" in metadata["image_types"]
        assert "promotional" in metadata["image_types"]
        assert metadata["has_screenshots"] is True
        assert metadata["has_promotional"] is True
        assert isinstance(metadata["visual_context"], str)


class TestAffiliateMetadataProcessor:
    """Test affiliate metadata processing functionality"""
    
    def test_format_affiliate_context_empty(self):
        """Test formatting with no affiliate metadata"""
        result = AffiliateMetadataProcessor.format_affiliate_context(None)
        assert result == "No affiliate-specific metadata available."
        
        result = AffiliateMetadataProcessor.format_affiliate_context({})
        assert result == "Standard affiliate terms apply."
    
    def test_format_affiliate_context_with_data(self):
        """Test formatting with affiliate metadata"""
        metadata = {
            "commission_structure": "10% revenue share",
            "marketing_materials": ["banners", "email templates"],
            "compliance_requirements": ["18+ age verification", "responsible gambling"]
        }
        
        result = AffiliateMetadataProcessor.format_affiliate_context(metadata)
        
        assert "Commission: 10% revenue share" in result
        assert "Marketing materials: banners, email templates" in result
        assert "Compliance: 18+ age verification, responsible gambling" in result


class TestNarrativeGenerationChain:
    """Test the complete narrative generation LCEL chain"""
    
    @pytest.fixture
    def mock_retrieval_system(self):
        """Create mock retrieval system"""
        mock_system = Mock(spec=MultiTenantRetrievalSystem)
        
        # Mock retrieval result
        mock_documents = [
            Document(
                page_content="Test casino offers great games and bonuses",
                metadata={"source": "test-source-1", "relevance": 0.9}
            ),
            Document(
                page_content="Licensed by Malta Gaming Authority, license ID: MGA/B2C/123/2020",
                metadata={"source": "test-source-2", "relevance": 0.85}
            )
        ]
        
        mock_result = RetrievalResult(
            documents=mock_documents,
            confidence_score=0.87,
            context_metadata={"total_retrieved": 2},
            retrieval_timestamp=datetime.now()
        )
        
        mock_system.retrieve_with_context.return_value = mock_result
        return mock_system
    
    @pytest.fixture
    def mock_llm(self):
        """Create mock LLM"""
        mock_llm = Mock(spec=ChatOpenAI)
        mock_llm.model_name = "gpt-4o"
        mock_llm.temperature = 0.7
        mock_llm.max_tokens = 4096
        return mock_llm
    
    @pytest.fixture
    def sample_input(self):
        """Create sample input data"""
        tenant_config = TenantConfiguration(
            tenant_id="test-tenant",
            brand_name="Test Casino Brand",
            locale="en",
            voice_profile="professional",
            target_demographics=["adults 25-45"]
        )
        
        visual_assets = [
            MediaAsset(
                filename="casino-lobby.png",
                url="https://example.com/lobby.png",
                type=MediaType.SCREENSHOT,
                alt_text="Casino game lobby"
            )
        ]
        
        affiliate_metadata = {
            "commission_structure": "15% revenue share",
            "compliance_requirements": ["18+ verification"]
        }
        
        return NarrativeGenerationInput(
            casino_name="Test Casino",
            tenant_config=tenant_config,
            query_context="comprehensive review with bonuses and games",
            visual_assets=visual_assets,
            affiliate_metadata=affiliate_metadata
        )
    
    def test_chain_initialization(self, mock_retrieval_system, mock_llm):
        """Test chain initialization"""
        chain = NarrativeGenerationChain(
            retrieval_system=mock_retrieval_system,
            llm=mock_llm
        )
        
        assert chain.retrieval_system == mock_retrieval_system
        assert chain.llm == mock_llm
        assert chain.chain is not None
        assert isinstance(chain.prompt_loader, NarrativePromptLoader)
    
    @patch('src.chains.narrative_generation_lcel.ChatPromptTemplate')
    @patch('src.chains.narrative_generation_lcel.StrOutputParser')
    def test_generate_narrative_success(self, mock_parser, mock_prompt, 
                                      mock_retrieval_system, mock_llm, sample_input):
        """Test successful narrative generation"""
        # Mock the LLM generation
        mock_generated_content = """
        <h1>Test Casino Review</h1>
        <p>Test Casino offers an exceptional gaming experience with great games and bonuses. 
        Licensed by Malta Gaming Authority (MGA/B2C/123/2020), this casino provides a safe 
        and secure environment for players.</p>
        <p>Players must be 18+ and practice responsible gambling.</p>
        """
        
        # Mock the chain components
        mock_chain_instance = Mock()
        mock_chain_instance.invoke.return_value = mock_generated_content
        mock_prompt.from_template.return_value = Mock()
        
        # Create a mock for the complete chain pipeline
        with patch.object(mock_llm, '__or__', return_value=mock_chain_instance):
            chain = NarrativeGenerationChain(
                retrieval_system=mock_retrieval_system,
                llm=mock_llm
            )
            
            # Mock the LCEL chain execution
            with patch.object(chain.chain, 'invoke') as mock_invoke:
                mock_output = NarrativeGenerationOutput(
                    generated_content=mock_generated_content,
                    review_doc=ReviewDoc(
                        title="Test Casino Review",
                        content=mock_generated_content,
                        content_type="casino_review",
                        tenant_config=sample_input.tenant_config,
                        tenant_id=sample_input.tenant_config.tenant_id,
                        brand=sample_input.tenant_config.brand_name,
                        locale=sample_input.tenant_config.locale
                    ),
                    retrieval_context=[],
                    generation_metadata={"test": "metadata"}
                )
                mock_invoke.return_value = mock_output
                
                # Execute the chain
                result = chain.generate_narrative(sample_input)
                
                # Verify results
                assert isinstance(result, NarrativeGenerationOutput)
                assert result.generated_content == mock_generated_content
                assert isinstance(result.review_doc, ReviewDoc)
                assert result.review_doc.title == "Test Casino Review"
                assert result.review_doc.tenant_id == sample_input.tenant_config.tenant_id
    
    def test_get_available_locales(self, mock_retrieval_system, mock_llm):
        """Test getting available locales"""
        chain = NarrativeGenerationChain(
            retrieval_system=mock_retrieval_system,
            llm=mock_llm
        )
        
        locales = chain.get_available_locales()
        assert isinstance(locales, list)
        assert len(locales) >= 4  # en, de, fr, es
    
    def test_generate_narrative_error_handling(self, mock_retrieval_system, mock_llm, sample_input):
        """Test error handling in narrative generation"""
        # Make retrieval system raise an exception
        mock_retrieval_system.retrieve_with_context.side_effect = Exception("Retrieval failed")
        
        chain = NarrativeGenerationChain(
            retrieval_system=mock_retrieval_system,
            llm=mock_llm
        )
        
        # Should raise the exception
        with pytest.raises(Exception, match="Retrieval failed"):
            chain.generate_narrative(sample_input)


class TestFactoryFunction:
    """Test the factory function for creating narrative generation chains"""
    
    @patch('src.chains.narrative_generation_lcel.ChatOpenAI')
    def test_create_narrative_generation_chain(self, mock_openai_class):
        """Test factory function creates chain correctly"""
        mock_retrieval_system = Mock(spec=MultiTenantRetrievalSystem)
        mock_llm_instance = Mock()
        mock_openai_class.return_value = mock_llm_instance
        
        chain = create_narrative_generation_chain(
            retrieval_system=mock_retrieval_system,
            llm_model="gpt-4o",
            temperature=0.8
        )
        
        # Verify LLM was created with correct parameters
        mock_openai_class.assert_called_once_with(
            model="gpt-4o",
            temperature=0.8,
            max_tokens=4096
        )
        
        # Verify chain was created
        assert isinstance(chain, NarrativeGenerationChain)
        assert chain.retrieval_system == mock_retrieval_system
        assert chain.llm == mock_llm_instance


class TestIntegrationScenarios:
    """Integration tests for complex multi-tenant scenarios"""
    
    @pytest.fixture
    def full_integration_setup(self):
        """Set up complete integration test environment"""
        # This would typically use test databases and real components
        # For now, we'll use mocks but structure for real integration
        
        mock_retrieval_system = Mock(spec=MultiTenantRetrievalSystem)
        mock_llm = Mock(spec=ChatOpenAI)
        
        # Create chain
        chain = NarrativeGenerationChain(
            retrieval_system=mock_retrieval_system,
            llm=mock_llm
        )
        
        return {
            "chain": chain,
            "retrieval_system": mock_retrieval_system,
            "llm": mock_llm
        }
    
    def test_multi_locale_generation(self, full_integration_setup):
        """Test generation across multiple locales"""
        chain = full_integration_setup["chain"]
        
        # Test different locales
        locales = ["en", "de", "fr", "es"]
        
        for locale in locales:
            tenant_config = TenantConfiguration(
                tenant_id=f"test-tenant-{locale}",
                brand_name=f"Test Brand {locale.upper()}",
                locale=locale,
                voice_profile="professional"
            )
            
            input_data = NarrativeGenerationInput(
                casino_name="Multi Casino",
                tenant_config=tenant_config,
                query_context="test review"
            )
            
            # Verify prompt loader can handle the locale
            prompt = chain.prompt_loader.load_prompt_template(locale)
            assert isinstance(prompt, str)
            assert len(prompt) > 0
    
    def test_visual_content_integration(self, full_integration_setup):
        """Test integration with various visual content types"""
        chain = full_integration_setup["chain"]
        
        # Create diverse visual assets
        visual_assets = [
            MediaAsset(filename="homepage.png", url="https://example.com/homepage.png", type=MediaType.SCREENSHOT),
            MediaAsset(filename="bonus.jpg", url="https://example.com/bonus.jpg", type=MediaType.PROMOTIONAL),
            MediaAsset(filename="games.png", url="https://example.com/games.png", type=MediaType.SCREENSHOT),
            MediaAsset(filename="mobile.png", url="https://example.com/mobile.png", type=MediaType.SCREENSHOT)
        ]
        
        # Process visual metadata
        visual_metadata = VisualContentProcessor.extract_visual_metadata(visual_assets)
        
        assert visual_metadata["total_images"] == 4
        assert visual_metadata["has_screenshots"] is True
        assert visual_metadata["has_promotional"] is True
        assert len(visual_metadata["image_types"]) == 2
    
    def test_affiliate_metadata_scenarios(self, full_integration_setup):
        """Test various affiliate metadata scenarios"""
        test_scenarios = [
            # Standard affiliate
            {
                "commission_structure": "10% revenue share",
                "marketing_materials": ["banners", "text links"],
                "compliance_requirements": ["18+ verification"]
            },
            # Premium affiliate  
            {
                "commission_structure": "15% revenue share + bonuses",
                "marketing_materials": ["banners", "email templates", "landing pages"],
                "compliance_requirements": ["18+ verification", "KYC", "responsible gambling"]
            },
            # Minimal affiliate
            {
                "commission_structure": "5% revenue share"
            }
        ]
        
        for scenario in test_scenarios:
            context = AffiliateMetadataProcessor.format_affiliate_context(scenario)
            assert isinstance(context, str)
            assert len(context) > 0


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])