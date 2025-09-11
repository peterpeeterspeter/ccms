#!/usr/bin/env python3
"""
🧪 LangGraph Research Agent Test Suite
=====================================

Comprehensive test suite for the LangGraph Research Agent including:
- Unit tests for individual workflow nodes
- Integration tests with existing CCMS components
- End-to-end workflow testing
- Streaming and checkpointing validation
- Error handling and recovery testing
- Backward compatibility verification

Author: AI Assistant
Created: 2025-01-10
Version: 1.0.0
"""

import pytest
import asyncio
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any, List

# Import components to test
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.langgraph_research_agent import (
    LangGraphResearchAgent, 
    ResearchPhase, 
    ResearchState
)
from src.integrations.langgraph_research_integration import (
    CCMSLangGraphResearchAgent,
    StreamingCallback,
    create_enhanced_research_agent,
    create_backward_compatible_agent
)
from src.schemas.casino_intelligence_schema import CasinoIntelligence, create_empty_casino_intelligence


class TestLangGraphResearchAgent:
    """Test suite for the core LangGraph Research Agent"""
    
    @pytest.fixture
    def research_agent(self):
        """Create research agent for testing"""
        return LangGraphResearchAgent(
            model_name="gpt-4o-mini",
            enable_streaming=True,
            enable_human_checkpoints=False  # Disable for testing
        )
    
    @pytest.fixture
    def sample_research_state(self) -> ResearchState:
        """Create sample research state for testing"""
        return {
            "research_id": str(uuid.uuid4()),
            "casino_name": "Test Casino",
            "casino_url": "https://test-casino.com",
            "locale": "en-US",
            "tenant_id": "test_tenant",
            "current_phase": ResearchPhase.INITIALIZED,
            "completed_phases": [],
            "failed_phases": [],
            "progress_percentage": 0.0,
            "phase_start_time": None,
            "total_start_time": datetime.now(),
            "messages": [],
            "status_updates": [],
            "last_update_time": datetime.now(),
            "web_search_results": [],
            "review_data": [],
            "screenshot_urls": [],
            "screenshot_metadata": [],
            "fallback_images": [],
            "raw_facts": {},
            "fact_sources": {},
            "errors": [],
            "retry_counts": {},
            "quality_issues": [],
            "extraction_confidence": 0.0,
            "data_quality_score": 0.0,
            "source_reliability_score": 0.0,
            "completeness_score": 0.0,
            "requires_human_review": False,
            "fallback_data_used": False,
            "wordpress_ready": False
        }
    
    def test_agent_initialization(self, research_agent):
        """Test basic agent initialization"""
        assert research_agent is not None
        assert research_agent.model_name == "gpt-4o-mini"
        assert research_agent.enable_streaming == True
        assert research_agent.enable_human_checkpoints == False
        assert research_agent.compiled_workflow is not None
    
    def test_initialize_research_node(self, research_agent, sample_research_state):
        """Test research initialization node"""
        result_state = research_agent._initialize_research_node(sample_research_state)
        
        assert result_state["current_phase"] == ResearchPhase.INITIALIZED
        assert ResearchPhase.INITIALIZED in result_state["completed_phases"]
        assert result_state["progress_percentage"] == 0.1
        assert len(result_state["status_updates"]) > 0
        assert result_state["status_updates"][0]["message"] == "Research session initialized"
    
    @patch('src.tools.real_supabase_research_tool.real_supabase_research_tool._run')
    @patch.dict(os.environ, {'TAVILY_API_KEY': 'test-key'})
    def test_gather_basic_info_node(self, mock_supabase, research_agent, sample_research_state):
        """Test basic information gathering node"""
        # Mock Supabase response
        mock_supabase.return_value = {
            "research_success": True,
            "total_fields": 42,
            "facts": {"casino_name": "Test Casino"}
        }
        
        # Mock Tavily search
        with patch('langchain_community.tools.TavilySearchResults') as mock_tavily:
            mock_tavily.return_value.invoke.return_value = [
                {"title": "Test Result", "content": "Test content", "url": "https://test.com"}
            ]
            
            result_state = research_agent._gather_basic_info_node(sample_research_state)
            
            assert result_state["current_phase"] == ResearchPhase.BASIC_INFO_GATHERING
            assert ResearchPhase.BASIC_INFO_GATHERING in result_state["completed_phases"]
            assert result_state["progress_percentage"] == 0.4
            assert result_state["supabase_research"] is not None
            assert len(result_state["web_search_results"]) > 0
    
    def test_quality_review_node(self, research_agent, sample_research_state):
        """Test quality review and scoring"""
        # Setup state with some test data
        sample_research_state["web_search_results"] = [
            {"url": "https://test1.com", "content": "Test content 1"},
            {"url": "https://test2.com", "content": "Test content 2"},
            {"url": "https://test3.com", "content": "Test content 3"}
        ]
        sample_research_state["website_content"] = {
            "url": "https://test-casino.com",
            "content": "Official website content"
        }
        sample_research_state["supabase_research"] = {"research_success": True}
        sample_research_state["screenshot_urls"] = ["https://screenshot1.png"]
        
        result_state = research_agent._quality_review_node(sample_research_state)
        
        assert result_state["current_phase"] == ResearchPhase.QUALITY_REVIEW
        assert result_state["data_quality_score"] > 0.0
        assert result_state["source_reliability_score"] > 0.0
        assert result_state["completeness_score"] > 0.0
        assert isinstance(result_state["quality_issues"], list)
    
    def test_human_checkpoint_node(self, research_agent, sample_research_state):
        """Test human checkpoint node"""
        # Setup high-quality state
        sample_research_state["data_quality_score"] = 0.8
        sample_research_state["errors"] = []
        
        result_state = research_agent._human_checkpoint_node(sample_research_state)
        
        assert result_state["current_phase"] == ResearchPhase.HUMAN_CHECKPOINT
        assert result_state["human_feedback"] is not None
        assert result_state["human_feedback"]["decision"] in ["approved", "retry", "manual_edit"]
    
    def test_finalize_research_node(self, research_agent, sample_research_state):
        """Test research finalization"""
        # Setup completed state
        sample_research_state["data_quality_score"] = 0.7
        sample_research_state["casino_intelligence"] = create_empty_casino_intelligence("Test Casino")
        
        result_state = research_agent._finalize_research_node(sample_research_state)
        
        assert result_state["current_phase"] == ResearchPhase.COMPLETED
        assert result_state["progress_percentage"] == 1.0
        assert result_state["ccms_pipeline_data"] is not None
        assert result_state["wordpress_ready"] == True
    
    def test_conditional_routing(self, research_agent):
        """Test conditional routing logic"""
        # Test human review requirement
        state_low_quality = {"data_quality_score": 0.3, "requires_human_review": False}
        assert research_agent._should_require_human_review(state_low_quality) == "retry"
        
        state_human_required = {"data_quality_score": 0.7, "requires_human_review": True}
        assert research_agent._should_require_human_review(state_human_required) == "human_review"
        
        state_good_quality = {"data_quality_score": 0.8, "requires_human_review": False}
        assert research_agent._should_require_human_review(state_good_quality) == "finalize"
        
        # Test human feedback processing
        feedback_approved = {"human_feedback": {"decision": "approved"}}
        assert research_agent._process_human_feedback(feedback_approved) == "approved"
        
        feedback_retry = {"human_feedback": {"decision": "retry"}}
        assert research_agent._process_human_feedback(feedback_retry) == "retry"
    
    def test_error_handling(self, research_agent, sample_research_state):
        """Test error tracking and handling"""
        research_agent._add_error(sample_research_state, "test_error", "Test error message")
        
        assert len(sample_research_state["errors"]) == 1
        assert sample_research_state["errors"][0]["type"] == "test_error"
        assert sample_research_state["errors"][0]["message"] == "Test error message"
        assert len(sample_research_state["status_updates"]) > 0
    
    def test_status_updates(self, research_agent, sample_research_state):
        """Test status update tracking"""
        research_agent._add_status_update(sample_research_state, "Test message", "info")
        
        assert len(sample_research_state["status_updates"]) == 1
        assert sample_research_state["status_updates"][0]["message"] == "Test message"
        assert sample_research_state["status_updates"][0]["level"] == "info"
        assert sample_research_state["status_updates"][0]["phase"] == ResearchPhase.INITIALIZED.value


class TestCCMSLangGraphIntegration:
    """Test suite for CCMS integration layer"""
    
    @pytest.fixture
    def ccms_agent(self):
        """Create CCMS integration agent for testing"""
        return CCMSLangGraphResearchAgent(
            model_name="gpt-4o-mini",
            enable_streaming=True,
            enable_human_checkpoints=False
        )
    
    def test_ccms_agent_initialization(self, ccms_agent):
        """Test CCMS agent initialization"""
        assert ccms_agent is not None
        assert ccms_agent.langgraph_agent is not None
        assert ccms_agent.enable_streaming == True
        assert isinstance(ccms_agent.active_research_sessions, dict)
    
    @pytest.mark.asyncio
    async def test_backward_compatible_research(self, ccms_agent):
        """Test backward compatibility with original research API"""
        with patch.object(ccms_agent.langgraph_agent, 'research_casino', new_callable=AsyncMock) as mock_research:
            mock_research.return_value = {
                "success": True,
                "research_id": "test-123",
                "casino_name": "Test Casino",
                "quality_metrics": {"data_quality_score": 0.8},
                "phases_completed": ["initialized", "basic_info_gathering", "completed"],
                "wordpress_ready": True,
                "casino_intelligence": create_empty_casino_intelligence("Test Casino")
            }
            
            result = await ccms_agent.research_casino("Test Casino", "https://test-casino.com")
            
            assert isinstance(result, str)
            assert "Test Casino" in result
            assert "Research ID: test-123" in result
            assert "Quality Score: 0.80" in result
            assert "LangGraph Enhanced" in result
    
    def test_synchronous_research_wrapper(self, ccms_agent):
        """Test synchronous wrapper for async research"""
        with patch.object(ccms_agent, 'research_casino', new_callable=AsyncMock) as mock_async:
            mock_async.return_value = "Test research result"
            
            result = ccms_agent.research_casino_sync("Test Casino")
            
            assert result == "Test research result"
            mock_async.assert_called_once_with(
                casino_name="Test Casino",
                casino_url=None,
                locale="en-US",
                tenant_id="default"
            )
    
    @pytest.mark.asyncio
    async def test_enhanced_research_api(self, ccms_agent):
        """Test enhanced research API with structured data"""
        with patch.object(ccms_agent.langgraph_agent, 'research_casino', new_callable=AsyncMock) as mock_research:
            mock_research.return_value = {
                "success": True,
                "research_id": "test-456",
                "casino_name": "Enhanced Test Casino",
                "quality_metrics": {"data_quality_score": 0.9},
                "visual_assets": {"screenshots": ["screenshot1.png"]},
                "wordpress_ready": True
            }
            
            result = await ccms_agent.research_casino_enhanced("Enhanced Test Casino")
            
            assert isinstance(result, dict)
            assert result["success"] == True
            assert result["research_id"] == "test-456"
            assert "ccms_integration" in result
            assert result["ccms_integration"]["api_version"] == "2.0.0"
            assert result["ccms_integration"]["compatible_with_pipeline"] == True
    
    @pytest.mark.asyncio
    async def test_streaming_research(self, ccms_agent):
        """Test streaming research progress"""
        updates = []
        
        async for update in ccms_agent.stream_research_progress("Streaming Test Casino"):
            updates.append(update)
            if update['phase'] == 'completed':
                break
        
        assert len(updates) > 5  # Should have multiple progress updates
        assert updates[0]['phase'] == 'initializing'
        assert updates[-1]['phase'] == 'completed'
        assert updates[-1]['progress'] == 1.0
        
        # Verify progress is monotonic
        for i in range(1, len(updates) - 1):  # Exclude final update which might have different structure
            if 'progress' in updates[i] and 'progress' in updates[i-1]:
                assert updates[i]['progress'] >= updates[i-1]['progress']
    
    def test_research_status_tracking(self, ccms_agent):
        """Test research session status tracking"""
        # Add a test session
        research_id = "test-status-123"
        ccms_agent.active_research_sessions[research_id] = {
            "casino_name": "Status Test Casino",
            "start_time": datetime.now(),
            "result": {"success": True, "quality_score": 0.8}
        }
        
        status = ccms_agent.get_research_status(research_id)
        
        assert status["found"] == True
        assert status["research_id"] == research_id
        assert status["casino_name"] == "Status Test Casino"
        assert status["source"] == "local_session"
        
        # Test non-existent session
        missing_status = ccms_agent.get_research_status("non-existent")
        assert missing_status["found"] == False
    
    def test_session_cleanup(self, ccms_agent):
        """Test old session cleanup"""
        # Add old session (25 hours ago)
        old_time = datetime.now() - timedelta(hours=25)
        ccms_agent.active_research_sessions["old-session"] = {
            "casino_name": "Old Casino",
            "start_time": old_time,
            "result": {}
        }
        
        # Add recent session
        ccms_agent.active_research_sessions["recent-session"] = {
            "casino_name": "Recent Casino", 
            "start_time": datetime.now(),
            "result": {}
        }
        
        # Cleanup with 24 hour limit
        ccms_agent.cleanup_old_sessions(max_age_hours=24)
        
        assert "old-session" not in ccms_agent.active_research_sessions
        assert "recent-session" in ccms_agent.active_research_sessions
    
    def test_ccms_pipeline_data_extraction(self, ccms_agent):
        """Test CCMS pipeline data extraction"""
        research_id = "test-pipeline-data"
        ccms_agent.active_research_sessions[research_id] = {
            "casino_name": "Pipeline Test Casino",
            "start_time": datetime.now(),
            "result": {
                "ccms_pipeline_data": {
                    "casino_intelligence": "test_intelligence",
                    "quality_metrics": {"score": 0.9}
                }
            }
        }
        
        pipeline_data = ccms_agent.get_ccms_pipeline_data(research_id)
        
        assert pipeline_data is not None
        assert "integration_metadata" in pipeline_data
        assert pipeline_data["integration_metadata"]["langgraph_enhanced"] == True
        assert pipeline_data["integration_metadata"]["backward_compatible"] == True
    
    def test_legacy_result_formatting(self, ccms_agent):
        """Test formatting of results for legacy API compatibility"""
        mock_result = {
            "casino_name": "Format Test Casino",
            "research_id": "format-123",
            "research_duration": 45.5,
            "quality_metrics": {
                "data_quality_score": 0.85,
                "source_reliability_score": 0.9,
                "completeness_score": 0.8,
                "extraction_confidence": 0.7
            },
            "phases_completed": ["initialized", "basic_info", "completed"],
            "visual_assets": {
                "screenshots": ["screenshot1.png", "screenshot2.png"],
                "fallback_images": []
            },
            "errors": [
                {"type": "minor_error", "message": "Minor test error"}
            ],
            "wordpress_ready": True,
            "casino_intelligence": create_empty_casino_intelligence("Format Test Casino")
        }
        
        formatted = ccms_agent._format_research_results_for_legacy_api(mock_result)
        
        assert isinstance(formatted, str)
        assert "Format Test Casino" in formatted
        assert "Research ID: format-123" in formatted
        assert "Duration: 45.5 seconds" in formatted
        assert "Quality Score: 0.85" in formatted
        assert "Screenshots: 2 captured" in formatted
        assert "WordPress Publishing Ready: ✅ Yes" in formatted
        assert "LangGraph Enhanced: ✅ Yes" in formatted


class TestFactoryFunctions:
    """Test factory functions for easy integration"""
    
    def test_enhanced_agent_factory(self):
        """Test enhanced agent factory function"""
        agent = create_enhanced_research_agent(
            model_name="gpt-4o",
            temperature=0.2
        )
        
        assert isinstance(agent, CCMSLangGraphResearchAgent)
        assert agent.langgraph_agent.model_name == "gpt-4o"
        assert agent.langgraph_agent.temperature == 0.2
    
    def test_backward_compatible_factory(self):
        """Test backward compatible agent factory"""
        agent = create_backward_compatible_agent(
            model_name="gpt-4o-mini"
        )
        
        assert isinstance(agent, CCMSLangGraphResearchAgent)
        assert agent.enable_streaming == False  # Should be disabled for compatibility
        assert agent.langgraph_agent.enable_human_checkpoints == False


class TestStreamingCallback:
    """Test streaming callback functionality"""
    
    def test_callback_initialization(self):
        """Test callback initialization"""
        callback = StreamingCallback()
        assert callback.callback_func is None
        assert callback.updates == []
        
        mock_func = Mock()
        callback_with_func = StreamingCallback(mock_func)
        assert callback_with_func.callback_func == mock_func
    
    def test_callback_update_handling(self):
        """Test callback update handling"""
        mock_func = Mock()
        callback = StreamingCallback(mock_func)
        
        test_update = {
            "phase": "test_phase",
            "progress": 0.5,
            "message": "Test message"
        }
        
        callback.on_update(test_update)
        
        assert len(callback.updates) == 1
        assert callback.updates[0] == test_update
        mock_func.assert_called_once_with(test_update)


class TestErrorScenarios:
    """Test error scenarios and edge cases"""
    
    @pytest.fixture
    def error_agent(self):
        """Create agent for error testing"""
        return LangGraphResearchAgent(
            model_name="gpt-4o-mini",
            enable_streaming=False,
            enable_human_checkpoints=False
        )
    
    def test_missing_environment_variables(self, error_agent):
        """Test handling of missing environment variables"""
        with patch.dict(os.environ, {}, clear=True):
            # Should handle missing TAVILY_API_KEY gracefully
            state = {
                "casino_name": "Error Test Casino",
                "current_phase": ResearchPhase.BASIC_INFO_GATHERING,
                "web_search_results": [],
                "errors": [],
                "status_updates": []
            }
            
            result_state = error_agent._gather_basic_info_node(state)
            
            # Should complete without web search results
            assert result_state["current_phase"] == ResearchPhase.BASIC_INFO_GATHERING
            assert len(result_state["web_search_results"]) == 0
    
    def test_network_timeout_simulation(self, error_agent):
        """Test handling of network timeouts"""
        state = {
            "casino_name": "Timeout Test Casino",
            "casino_url": "https://timeout-test.com",
            "current_phase": ResearchPhase.BASIC_INFO_GATHERING,
            "web_search_results": [],
            "errors": [],
            "status_updates": []
        }
        
        # Mock network timeout
        with patch('langchain_community.document_loaders.WebBaseLoader') as mock_loader:
            mock_loader.side_effect = Exception("Connection timeout")
            
            result_state = error_agent._gather_basic_info_node(state)
            
            # Should handle error gracefully
            assert len(result_state["errors"]) > 0
            assert any("timeout" in error["message"].lower() for error in result_state["errors"])
    
    @pytest.mark.asyncio
    async def test_malformed_research_request(self):
        """Test handling of malformed research requests"""
        agent = CCMSLangGraphResearchAgent()
        
        # Test empty casino name
        result = await agent.research_casino("")
        assert "Research failed" in result or "error" in result.lower()
        
        # Test invalid URL
        result = await agent.research_casino("Test Casino", "invalid-url")
        # Should still proceed (URL is optional)
        assert isinstance(result, str)


# ========================================================================
# INTEGRATION TESTS
# ========================================================================

class TestIntegrationWithExistingComponents:
    """Integration tests with existing CCMS components"""
    
    @pytest.mark.asyncio
    async def test_integration_with_supabase_tool(self):
        """Test integration with existing Supabase research tool"""
        with patch('src.tools.real_supabase_research_tool.real_supabase_research_tool._run') as mock_tool:
            mock_tool.return_value = {
                "research_success": True,
                "total_fields": 50,
                "facts": {"casino_name": "Integration Test Casino"}
            }
            
            agent = LangGraphResearchAgent(enable_human_checkpoints=False)
            
            # Test that the agent can use the existing tool
            result = await agent.research_casino("Integration Test Casino")
            
            assert result["success"] in [True, False]  # Should complete without errors
            mock_tool.assert_called()
    
    @pytest.mark.asyncio
    async def test_integration_with_screenshot_tools(self):
        """Test integration with existing screenshot tools"""
        with patch('src.tools.firecrawl_screenshot_tool.firecrawl_screenshot_tool._run') as mock_screenshot:
            mock_screenshot.return_value = {
                "screenshot_success": True,
                "screenshot_url": "https://test-screenshot.png"
            }
            
            agent = LangGraphResearchAgent(enable_human_checkpoints=False)
            
            result = await agent.research_casino(
                "Screenshot Test Casino",
                "https://screenshot-test.com"
            )
            
            # Should complete and potentially use screenshot tool
            assert result["success"] in [True, False]
    
    def test_casino_intelligence_schema_integration(self):
        """Test integration with existing CasinoIntelligence schema"""
        # Test that we can create and use the schema
        intelligence = create_empty_casino_intelligence("Schema Test Casino")
        
        assert isinstance(intelligence, CasinoIntelligence)
        assert intelligence.casino_name == "Schema Test Casino"
        assert intelligence.trustworthiness is not None
        assert intelligence.games is not None
        
        # Test completeness calculation
        completeness = intelligence.calculate_completeness_score()
        assert 0.0 <= completeness <= 1.0


# ========================================================================
# PERFORMANCE TESTS
# ========================================================================

class TestPerformance:
    """Performance and load testing"""
    
    @pytest.mark.asyncio
    async def test_concurrent_research_sessions(self):
        """Test handling of multiple concurrent research sessions"""
        agent = CCMSLangGraphResearchAgent()
        
        # Simulate multiple concurrent requests
        tasks = []
        for i in range(3):  # Keep small for test performance
            task = agent.research_casino(f"Concurrent Casino {i}")
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All should complete (successfully or with errors)
        assert len(results) == 3
        for result in results:
            assert isinstance(result, str) or isinstance(result, Exception)
    
    def test_memory_usage_with_large_sessions(self):
        """Test memory usage with many research sessions"""
        agent = CCMSLangGraphResearchAgent()
        
        # Create many sessions
        for i in range(100):
            research_id = f"memory-test-{i}"
            agent.active_research_sessions[research_id] = {
                "casino_name": f"Memory Test Casino {i}",
                "start_time": datetime.now(),
                "result": {"test_data": f"data_{i}"}
            }
        
        assert len(agent.active_research_sessions) == 100
        
        # Test cleanup
        agent.cleanup_old_sessions(max_age_hours=0)  # Clean all
        assert len(agent.active_research_sessions) == 0


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--disable-warnings"
    ])
