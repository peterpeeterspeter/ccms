"""
Unit Tests for Multi-Tenant Retrieval System
Task-010: LCEL retrieval chains with tenant filtering and enhanced recall
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import List, Dict, Any

from src.chains.multi_tenant_retrieval_system import (
    MultiTenantRetrievalSystem,
    MultiTenantRetriever,
    MultiTenantQuery,
    RetrievalResult
)
from src.integrations.supabase_vector_store import AgenticSupabaseVectorStore
from src.schemas.review_doc import TenantConfiguration
from langchain_core.documents import Document


class TestMultiTenantQuery:
    """Test MultiTenantQuery Pydantic model"""
    
    def test_multi_tenant_query_creation(self):
        """Test MultiTenantQuery model creation and validation"""
        query = MultiTenantQuery(
            query="What are the best casino bonuses?",
            tenant_id="crashcasino",
            brand="default",
            locale="en",
            voice="professional",
            content_types=["bonus_information", "terms_conditions"],
            limit=10,
            similarity_threshold=0.8
        )
        
        assert query.query == "What are the best casino bonuses?"
        assert query.tenant_id == "crashcasino"
        assert query.brand == "default"
        assert query.locale == "en"
        assert query.voice == "professional"
        assert query.content_types == ["bonus_information", "terms_conditions"]
        assert query.limit == 10
        assert query.similarity_threshold == 0.8
    
    def test_multi_tenant_query_defaults(self):
        """Test MultiTenantQuery with default values"""
        query = MultiTenantQuery(
            query="Test query",
            tenant_id="test_tenant"
        )
        
        assert query.locale == "en"
        assert query.limit == 10
        assert query.similarity_threshold == 0.7
        assert query.brand is None
        assert query.voice is None
        assert query.content_types is None


class TestMultiTenantRetriever:
    """Test MultiTenantRetriever functionality"""
    
    @pytest.fixture
    def mock_vector_store(self):
        """Create mock vector store"""
        mock_store = Mock(spec=AgenticSupabaseVectorStore)
        mock_vectorstore = Mock()
        mock_store.vectorstore = mock_vectorstore
        return mock_store
    
    @pytest.fixture
    def tenant_config(self):
        """Create test tenant configuration"""
        return TenantConfiguration(
            tenant_id="test_tenant",
            brand_name="test_brand",
            locale="en",
            voice_profile="professional",
            target_audience="casino_players"
        )
    
    @pytest.fixture
    def sample_documents(self):
        """Create sample documents for testing"""
        return [
            Document(
                page_content="Casino bonuses are promotional offers...",
                metadata={
                    "source_url": "https://casino.com/bonuses",
                    "tenant_id": "test_tenant",
                    "content_category": "bonus_information"
                }
            ),
            Document(
                page_content="Terms and conditions apply to all offers...",
                metadata={
                    "source_url": "https://casino.com/terms",
                    "tenant_id": "test_tenant", 
                    "content_category": "terms_conditions"
                }
            )
        ]
    
    def test_multi_tenant_retriever_initialization(self, mock_vector_store, tenant_config):
        """Test MultiTenantRetriever initialization"""
        retriever = MultiTenantRetriever(
            vector_store=mock_vector_store,
            tenant_config=tenant_config,
            search_type="mmr",
            search_kwargs={"k": 5}
        )
        
        assert retriever.vector_store == mock_vector_store
        assert retriever.tenant_config == tenant_config
        assert retriever.search_type == "mmr"
        assert retriever.search_kwargs == {"k": 5}
        assert retriever.metadata_filter["tenant_id"] == "test_tenant"
    
    def test_get_relevant_documents_mmr(self, mock_vector_store, tenant_config, sample_documents):
        """Test MMR document retrieval"""
        # Mock MMR search
        mock_vector_store.vectorstore.max_marginal_relevance_search.return_value = sample_documents
        
        retriever = MultiTenantRetriever(
            vector_store=mock_vector_store,
            tenant_config=tenant_config,
            search_type="mmr"
        )
        
        docs = retriever._get_relevant_documents("test query", run_manager=Mock())
        
        assert len(docs) == 2
        assert all(doc.metadata.get("tenant_id") == "test_tenant" for doc in docs)
        assert all("retrieved_at" in doc.metadata for doc in docs)
        assert all(doc.metadata.get("retrieval_method") == "mmr" for doc in docs)
    
    def test_get_relevant_documents_similarity(self, mock_vector_store, tenant_config, sample_documents):
        """Test similarity search retrieval"""
        # Mock similarity search
        mock_vector_store.vectorstore.similarity_search.return_value = sample_documents
        
        retriever = MultiTenantRetriever(
            vector_store=mock_vector_store,
            tenant_config=tenant_config,
            search_type="similarity"
        )
        
        docs = retriever._get_relevant_documents("test query", run_manager=Mock())
        
        assert len(docs) == 2
        assert all(doc.metadata.get("retrieval_method") == "similarity" for doc in docs)
        
        # Verify similarity_search was called with tenant filtering
        mock_vector_store.vectorstore.similarity_search.assert_called_once()
    
    def test_get_relevant_documents_error_handling(self, mock_vector_store, tenant_config):
        """Test error handling in document retrieval"""
        # Mock vector store to raise exception
        mock_vector_store.vectorstore.max_marginal_relevance_search.side_effect = Exception("Search failed")
        
        retriever = MultiTenantRetriever(
            vector_store=mock_vector_store,
            tenant_config=tenant_config
        )
        
        docs = retriever._get_relevant_documents("test query", run_manager=Mock())
        
        assert docs == []  # Should return empty list on error


class TestMultiTenantRetrievalSystem:
    """Test MultiTenantRetrievalSystem main class"""
    
    @pytest.fixture
    def mock_vector_store(self):
        """Create mock vector store"""
        mock_store = Mock(spec=AgenticSupabaseVectorStore)
        return mock_store
    
    @pytest.fixture
    def mock_llm(self):
        """Create mock LLM"""
        mock_llm = Mock()
        mock_llm.ainvoke = AsyncMock(return_value=Mock(content="Alternative query 1\nAlternative query 2\nAlternative query 3"))
        return mock_llm
    
    @pytest.fixture
    def retrieval_system(self, mock_vector_store, mock_llm):
        """Create test retrieval system"""
        return MultiTenantRetrievalSystem(
            vector_store=mock_vector_store,
            llm=mock_llm
        )
    
    @pytest.fixture
    def sample_documents(self):
        """Create sample documents"""
        return [
            Document(
                page_content="Welcome bonus: 100% up to $500",
                metadata={
                    "source_url": "https://casino.com/bonuses",
                    "tenant_id": "crashcasino",
                    "content_category": "bonus_information"
                }
            ),
            Document(
                page_content="Wagering requirements: 35x bonus amount", 
                metadata={
                    "source_url": "https://casino.com/terms",
                    "tenant_id": "crashcasino",
                    "content_category": "terms_conditions"
                }
            )
        ]
    
    def test_system_initialization(self, mock_vector_store, mock_llm):
        """Test system initialization"""
        system = MultiTenantRetrievalSystem(
            vector_store=mock_vector_store,
            llm=mock_llm
        )
        
        assert system.vector_store == mock_vector_store
        assert system.llm == mock_llm
        assert system.single_query_chain is not None
        assert system.multi_query_chain is not None
        assert system.ensemble_chain is not None
    
    @pytest.mark.asyncio
    async def test_single_query_retrieval(self, retrieval_system, sample_documents):
        """Test single query retrieval"""
        # Mock the retriever to return sample documents
        with patch.object(retrieval_system, '_create_single_query_chain') as mock_chain:
            mock_runnable = AsyncMock()
            mock_runnable.ainvoke.return_value = sample_documents
            mock_chain.return_value = mock_runnable
            
            # Reinitialize with mocked chain
            retrieval_system.single_query_chain = mock_runnable
            
            result = await retrieval_system.retrieve(
                query="casino bonuses",
                tenant_id="crashcasino",
                brand="default",
                locale="en",
                retrieval_type="single"
            )
            
            assert isinstance(result, RetrievalResult)
            assert result.query_metadata["query_text"] == "casino bonuses"
            assert result.tenant_config.tenant_id == "crashcasino"
    
    @pytest.mark.asyncio
    async def test_multi_query_retrieval(self, retrieval_system, sample_documents):
        """Test multi-query retrieval"""
        with patch.object(retrieval_system, '_create_multi_query_chain') as mock_chain:
            mock_runnable = AsyncMock()
            mock_runnable.ainvoke.return_value = sample_documents
            mock_chain.return_value = mock_runnable
            
            # Reinitialize with mocked chain
            retrieval_system.multi_query_chain = mock_runnable
            
            result = await retrieval_system.retrieve(
                query="best casino games",
                tenant_id="crashcasino",
                retrieval_type="multi_query"
            )
            
            assert isinstance(result, RetrievalResult)
            assert result.query_metadata["retrieval_type"] == "multi_query"
    
    @pytest.mark.asyncio
    async def test_ensemble_retrieval(self, retrieval_system, sample_documents):
        """Test ensemble retrieval"""
        with patch.object(retrieval_system, '_create_ensemble_chain') as mock_chain:
            mock_runnable = AsyncMock()
            mock_runnable.ainvoke.return_value = sample_documents
            mock_chain.return_value = mock_runnable
            
            # Reinitialize with mocked chain
            retrieval_system.ensemble_chain = mock_runnable
            
            result = await retrieval_system.retrieve(
                query="casino payment methods",
                tenant_id="crashcasino",
                retrieval_type="ensemble"
            )
            
            assert isinstance(result, RetrievalResult)
            assert result.query_metadata["retrieval_type"] == "ensemble"
    
    @pytest.mark.asyncio
    async def test_retrieval_with_filters(self, retrieval_system, sample_documents):
        """Test retrieval with various filters"""
        with patch.object(retrieval_system, '_create_multi_query_chain') as mock_chain:
            mock_runnable = AsyncMock()
            mock_runnable.ainvoke.return_value = sample_documents
            mock_chain.return_value = mock_runnable
            
            retrieval_system.multi_query_chain = mock_runnable
            
            result = await retrieval_system.retrieve(
                query="mobile casino apps",
                tenant_id="betway_tenant",
                brand="betway",
                locale="nl",
                voice="friendly",
                content_types=["games_portfolio", "mobile_features"],
                limit=15,
                similarity_threshold=0.85
            )
            
            assert result.tenant_config.tenant_id == "betway_tenant"
            assert result.tenant_config.brand_name == "betway"
            assert result.tenant_config.locale == "nl"
            assert result.query_metadata["tenant_filters"]["brand"] == "betway"
            assert result.query_metadata["tenant_filters"]["locale"] == "nl"
    
    @pytest.mark.asyncio
    async def test_retrieval_error_handling(self, retrieval_system):
        """Test error handling in retrieval"""
        # Mock chain to raise exception
        with patch.object(retrieval_system, '_create_multi_query_chain') as mock_chain:
            mock_runnable = AsyncMock()
            mock_runnable.ainvoke.side_effect = Exception("Retrieval failed")
            mock_chain.return_value = mock_runnable
            
            retrieval_system.multi_query_chain = mock_runnable
            
            result = await retrieval_system.retrieve(
                query="test query",
                tenant_id="test_tenant"
            )
            
            assert isinstance(result, RetrievalResult)
            assert len(result.documents) == 0
            assert "error" in result.query_metadata
            assert result.retrieval_stats["total_documents"] == 0
    
    def test_create_retrieval_chain_types(self, retrieval_system):
        """Test creation of different retrieval chain types"""
        # Test single query chain
        single_chain = retrieval_system.create_retrieval_chain("single")
        assert single_chain is not None
        
        # Test multi-query chain
        multi_chain = retrieval_system.create_retrieval_chain("multi_query")
        assert multi_chain is not None
        
        # Test ensemble chain
        ensemble_chain = retrieval_system.create_retrieval_chain("ensemble")
        assert ensemble_chain is not None
        
        # Test default (should be multi_query)
        default_chain = retrieval_system.create_retrieval_chain()
        assert default_chain is not None


class TestRetrievalResult:
    """Test RetrievalResult model"""
    
    def test_retrieval_result_creation(self):
        """Test RetrievalResult model creation"""
        documents = [
            Document(page_content="Test content", metadata={"test": "metadata"})
        ]
        
        tenant_config = TenantConfiguration(
            tenant_id="test_tenant",
            brand_name="test_brand",
            locale="en"
        )
        
        result = RetrievalResult(
            documents=documents,
            query_metadata={"query": "test", "retrieval_type": "single"},
            retrieval_stats={"total_documents": 1, "unique_sources": 1},
            tenant_config=tenant_config
        )
        
        assert len(result.documents) == 1
        assert result.query_metadata["query"] == "test"
        assert result.retrieval_stats["total_documents"] == 1
        assert result.tenant_config.tenant_id == "test_tenant"


class TestLCELIntegration:
    """Test LCEL chain integration"""
    
    @pytest.mark.asyncio
    async def test_runnable_interface(self, mock_vector_store, mock_llm):
        """Test that chains properly implement Runnable interface"""
        system = MultiTenantRetrievalSystem(
            vector_store=mock_vector_store,
            llm=mock_llm
        )
        
        # Test that chains have invoke and ainvoke methods
        chain = system.create_retrieval_chain("single")
        
        # Should have invoke method (synchronous)
        assert hasattr(chain, 'invoke')
        
        # Should have ainvoke method (asynchronous)
        assert hasattr(chain, 'ainvoke')
    
    def test_chain_composition(self, mock_vector_store, mock_llm):
        """Test LCEL chain composition with RunnableParallel and RunnableLambda"""
        system = MultiTenantRetrievalSystem(
            vector_store=mock_vector_store,
            llm=mock_llm
        )
        
        # Verify chain components exist
        assert system.single_query_chain is not None
        assert system.multi_query_chain is not None  
        assert system.ensemble_chain is not None
        
        # Test chain creation returns valid Runnable
        chain = system.create_retrieval_chain()
        assert hasattr(chain, 'invoke')


@pytest.mark.integration
class TestMultiTenantRetrievalIntegration:
    """Integration tests for Multi-Tenant Retrieval System"""
    
    @pytest.mark.asyncio
    async def test_full_workflow_integration(self):
        """Test full workflow integration (mocked)"""
        # Mock all dependencies
        mock_vector_store = Mock(spec=AgenticSupabaseVectorStore)
        mock_vectorstore = Mock()
        mock_vector_store.vectorstore = mock_vectorstore
        
        # Mock retrieval results
        sample_docs = [
            Document(
                page_content="Comprehensive casino review content",
                metadata={
                    "source_url": "https://casino.com/review",
                    "tenant_id": "integration_test",
                    "content_category": "casino_review"
                }
            )
        ]
        mock_vectorstore.max_marginal_relevance_search.return_value = sample_docs
        
        # Create system
        system = MultiTenantRetrievalSystem(vector_store=mock_vector_store)
        
        # Test retrieval
        result = await system.retrieve(
            query="comprehensive casino analysis",
            tenant_id="integration_test",
            brand="test_brand",
            locale="en",
            limit=5
        )
        
        # Verify integration
        assert isinstance(result, RetrievalResult)
        assert result.tenant_config.tenant_id == "integration_test"
        assert len(result.query_metadata) > 0
        assert len(result.retrieval_stats) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])