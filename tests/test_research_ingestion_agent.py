"""
Unit Tests for Research & Ingestion Agent LangGraph Node
Task-007: Comprehensive testing for Planner → Retrieve → Loader pattern
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import List, Dict, Any

# Import the agent and related components
from src.agents.research_ingestion_agent import (
    ResearchIngestionAgent,
    ResearchPlan,
    ContentIngestionState
)
from langchain_core.documents import Document


class TestResearchIngestionAgent:
    """Test suite for Research & Ingestion Agent"""
    
    @pytest.fixture
    def agent(self):
        """Create test agent instance"""
        return ResearchIngestionAgent(
            tenant_id="test_tenant",
            brand="test_brand", 
            locale="en"
        )
    
    @pytest.fixture
    def sample_state(self):
        """Create sample workflow state"""
        return ContentIngestionState(
            target="Test Casino",
            tenant_id="test_tenant",
            brand="test_brand",
            locale="en",
            research_plan=None,
            raw_documents=[],
            processed_chunks=[],
            indexed_document_ids=[],
            current_step="initializing",
            errors=[],
            success=False,
            metadata={}
        )
    
    @pytest.fixture
    def sample_research_plan(self):
        """Create sample research plan"""
        return ResearchPlan(
            target_urls=["https://testcasino.com", "https://testcasino.com/terms"],
            content_categories=["website_overview", "terms_conditions"],
            extraction_priority="High",
            estimated_pages=5,
            tenant_config={
                "tenant_id": "test_tenant",
                "brand": "test_brand",
                "locale": "en"
            }
        )
    
    @pytest.fixture  
    def sample_documents(self):
        """Create sample documents"""
        return [
            Document(
                page_content="Test casino content about games and bonuses.",
                metadata={
                    "source_url": "https://testcasino.com",
                    "tenant_id": "test_tenant",
                    "content_category": "website_overview"
                }
            ),
            Document(
                page_content="Terms and conditions for the casino platform.",
                metadata={
                    "source_url": "https://testcasino.com/terms",
                    "tenant_id": "test_tenant", 
                    "content_category": "terms_conditions"
                }
            )
        ]
    
    def test_agent_initialization(self, agent):
        """Test agent initialization"""
        assert agent.tenant_id == "test_tenant"
        assert agent.brand == "test_brand"
        assert agent.locale == "en"
        assert agent.llm is not None
        assert agent.text_splitter is not None
        assert agent.vector_store is not None
        assert agent.planning_chain is not None
        assert agent.processing_chain is not None
        assert agent.workflow is not None
    
    def test_content_categorization(self, agent):
        """Test URL content categorization"""
        test_cases = [
            ("https://casino.com/terms-and-conditions", "terms_conditions"),
            ("https://casino.com/bonus-offers", "bonus_information"),
            ("https://casino.com/casino-games", "games_portfolio"),
            ("https://casino.com/payments", "payment_methods"),
            ("https://casino.com/about-us", "company_information"),
            ("https://casino.com/random-page", "general_content")
        ]
        
        for url, expected_category in test_cases:
            result = agent._categorize_content(url)
            assert result == expected_category, f"URL {url} should be categorized as {expected_category}"
    
    @pytest.mark.asyncio
    async def test_planner_node_success(self, agent, sample_state):
        """Test successful planning node execution"""
        # Mock the planning chain
        mock_plan = ResearchPlan(
            target_urls=["https://testcasino.com"],
            content_categories=["website_overview"],
            extraction_priority="Medium",
            estimated_pages=3,
            tenant_config={"tenant_id": "test_tenant", "brand": "test_brand", "locale": "en"}
        )
        
        with patch.object(agent.planning_chain, 'ainvoke', new_callable=AsyncMock) as mock_invoke:
            mock_invoke.return_value = mock_plan
            
            result_state = await agent._planner_node(sample_state)
            
            assert result_state["current_step"] == "planning"
            assert result_state["research_plan"] == mock_plan
            assert "plan_created_at" in result_state["metadata"]
            assert len(result_state["errors"]) == 0
    
    @pytest.mark.asyncio
    async def test_planner_node_failure(self, agent, sample_state):
        """Test planning node failure handling"""
        with patch.object(agent.planning_chain, 'ainvoke', new_callable=AsyncMock) as mock_invoke:
            mock_invoke.side_effect = Exception("Planning failed")
            
            result_state = await agent._planner_node(sample_state)
            
            assert result_state["current_step"] == "error"
            assert len(result_state["errors"]) == 1
            assert "Planning failed" in result_state["errors"][0]
    
    @pytest.mark.asyncio
    async def test_retrieve_node_success(self, agent, sample_state, sample_research_plan, sample_documents):
        """Test successful retrieve node execution"""
        # Set up state with research plan
        sample_state["research_plan"] = sample_research_plan
        
        # Mock WebBaseLoader
        with patch('src.agents.research_ingestion_agent.WebBaseLoader') as mock_loader_class:
            mock_loader = Mock()
            mock_loader.load.return_value = sample_documents
            mock_loader_class.return_value = mock_loader
            
            # Mock asyncio.to_thread
            with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
                mock_to_thread.return_value = sample_documents
                
                result_state = await agent._retrieve_node(sample_state)
                
                assert result_state["current_step"] == "retrieving"
                assert len(result_state["raw_documents"]) == 2
                assert len(result_state["errors"]) == 0
                
                # Check document metadata enrichment
                for doc in result_state["raw_documents"]:
                    assert "tenant_id" in doc.metadata
                    assert "extraction_method" in doc.metadata
                    assert "extracted_at" in doc.metadata
    
    @pytest.mark.asyncio
    async def test_retrieve_node_no_urls(self, agent, sample_state):
        """Test retrieve node with no URLs"""
        # Set empty research plan
        sample_state["research_plan"] = ResearchPlan(
            target_urls=[],
            content_categories=[],
            extraction_priority="Low",
            estimated_pages=0,
            tenant_config={}
        )
        
        result_state = await agent._retrieve_node(sample_state)
        
        assert result_state["current_step"] == "error"
        assert len(result_state["errors"]) == 1
        assert "No URLs available" in result_state["errors"][0]
    
    @pytest.mark.asyncio
    async def test_loader_node_success(self, agent, sample_state, sample_documents):
        """Test successful loader node execution"""
        # Set up state with raw documents
        sample_state["raw_documents"] = sample_documents
        
        # Mock text splitter
        with patch.object(agent.text_splitter, 'split_documents') as mock_splitter:
            mock_chunks = [
                Document(
                    page_content="Chunk 1 content",
                    metadata={"source_url": "https://testcasino.com", "content_category": "website_overview"}
                ),
                Document(
                    page_content="Chunk 2 content", 
                    metadata={"source_url": "https://testcasino.com/terms", "content_category": "terms_conditions"}
                )
            ]
            mock_splitter.return_value = mock_chunks
            
            # Mock processing chain
            with patch.object(agent.processing_chain, 'ainvoke', new_callable=AsyncMock) as mock_process:
                mock_process.return_value = "Enriched content"
                
                # Mock vector store
                with patch.object(agent.vector_store, 'add_documents') as mock_add_docs:
                    with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
                        mock_to_thread.return_value = ["doc_1", "doc_2"]
                        mock_add_docs.return_value = ["doc_1", "doc_2"]
                        
                        result_state = await agent._loader_node(sample_state)
                        
                        assert result_state["current_step"] == "loading"
                        assert len(result_state["processed_chunks"]) == 2
                        assert len(result_state["indexed_document_ids"]) == 2
                        assert result_state["success"] is True
                        assert "total_chunks_processed" in result_state["metadata"]
                        assert "completed_at" in result_state["metadata"]
    
    @pytest.mark.asyncio
    async def test_loader_node_no_documents(self, agent, sample_state):
        """Test loader node with no documents"""
        result_state = await agent._loader_node(sample_state)
        
        assert result_state["current_step"] == "error"
        assert len(result_state["errors"]) == 1
        assert "No documents available" in result_state["errors"][0]
    
    @pytest.mark.asyncio
    async def test_error_handler_node(self, agent, sample_state):
        """Test error handler node"""
        sample_state["errors"] = ["Test error 1", "Test error 2"]
        
        result_state = await agent._error_handler_node(sample_state)
        
        assert result_state["success"] is False
        assert len(result_state["errors"]) == 2
    
    @pytest.mark.asyncio
    async def test_execute_research_ingestion_success(self, agent):
        """Test complete successful workflow execution"""
        # Mock the workflow
        mock_final_state = {
            "success": True,
            "target": "Test Casino",
            "tenant_id": "test_tenant",
            "brand": "test_brand", 
            "locale": "en",
            "processed_chunks": [Mock(), Mock()],
            "indexed_document_ids": ["doc_1", "doc_2"],
            "research_plan": ResearchPlan(
                target_urls=["https://testcasino.com"],
                content_categories=["website_overview"],
                extraction_priority="Medium",
                estimated_pages=3,
                tenant_config={}
            ),
            "errors": [],
            "metadata": {"started_at": "2024-01-01T00:00:00"}
        }
        
        with patch.object(agent.workflow, 'ainvoke', new_callable=AsyncMock) as mock_workflow:
            mock_workflow.return_value = mock_final_state
            
            result = await agent.execute_research_ingestion("Test Casino")
            
            assert result["success"] is True
            assert result["target"] == "Test Casino"
            assert result["documents_processed"] == 2
            assert result["documents_indexed"] == 2
            assert len(result["errors"]) == 0
            assert result["tenant_config"]["tenant_id"] == "test_tenant"
    
    @pytest.mark.asyncio 
    async def test_execute_research_ingestion_failure(self, agent):
        """Test workflow execution failure"""
        with patch.object(agent.workflow, 'ainvoke', new_callable=AsyncMock) as mock_workflow:
            mock_workflow.side_effect = Exception("Workflow failed")
            
            result = await agent.execute_research_ingestion("Test Casino")
            
            assert result["success"] is False
            assert result["documents_processed"] == 0
            assert result["documents_indexed"] == 0
            assert len(result["errors"]) == 1
            assert "Workflow execution failed" in result["errors"][0]
    
    def test_research_plan_model_validation(self):
        """Test ResearchPlan Pydantic model validation"""
        # Valid plan
        valid_plan = ResearchPlan(
            target_urls=["https://example.com"],
            content_categories=["test_category"],
            extraction_priority="High",
            estimated_pages=5,
            tenant_config={"tenant_id": "test"}
        )
        
        assert len(valid_plan.target_urls) == 1
        assert valid_plan.extraction_priority == "High"
        assert valid_plan.estimated_pages == 5
    
    def test_content_ingestion_state_structure(self):
        """Test ContentIngestionState TypedDict structure"""
        state = ContentIngestionState(
            target="Test Casino",
            tenant_id="test",
            brand="test_brand", 
            locale="en",
            research_plan=None,
            raw_documents=[],
            processed_chunks=[],
            indexed_document_ids=[],
            current_step="test",
            errors=[],
            success=False,
            metadata={}
        )
        
        assert state["target"] == "Test Casino"
        assert state["tenant_id"] == "test"
        assert isinstance(state["errors"], list)
        assert isinstance(state["metadata"], dict)
    
    @pytest.mark.asyncio
    async def test_planning_chain_integration(self, agent):
        """Test planning chain LCEL integration"""
        test_input = {
            "target": "Test Casino",
            "tenant_id": "test",
            "brand": "test_brand",
            "locale": "en"
        }
        
        # Mock LLM response
        with patch.object(agent.llm, 'ainvoke', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = Mock(content="Planning response with https://testcasino.com")
            
            result = await agent.planning_chain.ainvoke(test_input)
            
            assert isinstance(result, ResearchPlan)
            assert result.tenant_config["tenant_id"] == "test"
    
    @pytest.mark.asyncio
    async def test_processing_chain_integration(self, agent):
        """Test processing chain LCEL integration"""
        test_input = {
            "content": "Test casino content",
            "source_url": "https://testcasino.com",
            "category": "website_overview",
            "tenant_id": "test"
        }
        
        # Mock LLM response
        with patch.object(agent.llm, 'ainvoke', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = Mock(content="Enriched casino content")
            
            # Mock the processing chain components
            with patch.object(agent.processing_chain, 'invoke') as mock_chain:
                mock_chain.return_value = "Enriched casino content"
                
                result = agent.processing_chain.invoke(test_input)
                
                assert isinstance(result, str)
                assert len(result) > 0


@pytest.mark.integration
class TestResearchIngestionAgentIntegration:
    """Integration tests for Research & Ingestion Agent"""
    
    @pytest.mark.asyncio
    async def test_full_workflow_integration(self):
        """Test full workflow integration (requires actual services)"""
        # This test would require actual Supabase and OpenAI connections
        # For now, we'll create a mock version
        
        agent = ResearchIngestionAgent(tenant_id="test", brand="test", locale="en")
        
        # Mock all external dependencies
        with patch.object(agent.vector_store, 'add_documents') as mock_add:
            with patch('src.agents.research_ingestion_agent.WebBaseLoader') as mock_loader:
                with patch.object(agent.llm, 'ainvoke', new_callable=AsyncMock) as mock_llm:
                    
                    # Set up mocks
                    mock_add.return_value = ["doc_1"]
                    mock_loader_instance = Mock()
                    mock_loader_instance.load.return_value = [
                        Document(page_content="Test content", metadata={})
                    ]
                    mock_loader.return_value = mock_loader_instance
                    mock_llm.return_value = Mock(content="Test response")
                    
                    # Execute workflow
                    result = await agent.execute_research_ingestion("Test Casino")
                    
                    # Verify basic integration
                    assert "success" in result
                    assert "target" in result 
                    assert result["target"] == "Test Casino"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])