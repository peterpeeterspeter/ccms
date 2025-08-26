#!/usr/bin/env python3
"""
🧪 CCMS Pipeline Test Suite
==========================

Test the complete native LangChain pipeline end-to-end.
"""

import pytest
import logging
from unittest.mock import patch, MagicMock

from ccms_pipeline import (
    ccms_pipeline, CCMSInput, CCMSResult, ComplianceError,
    run_ccms_pipeline
)

# Configure test logging
logging.basicConfig(level=logging.INFO)

class TestCCMSPipeline:
    
    def test_pipeline_input_schema(self):
        """Test CCMSInput schema validation"""
        input_data = CCMSInput(
            tenant_slug="crashcasino",
            casino_slug="viage",
            locale="en-GB"
        )
        
        assert input_data.tenant_slug == "crashcasino"
        assert input_data.casino_slug == "viage"
        assert input_data.locale == "en-GB"
        assert input_data.dry_run == False
        assert input_data.skip_compliance == False
        assert len(input_data.run_id) == 36  # UUID4 length
    
    def test_pipeline_result_schema(self):
        """Test CCMSResult schema validation"""
        result = CCMSResult(
            run_id="test-123",
            success=True,
            tenant_slug="crashcasino",
            casino_slug="viage", 
            locale="en-GB"
        )
        
        assert result.run_id == "test-123"
        assert result.success == True
        assert result.tenant_slug == "crashcasino"
        assert result.published_url == ""
        assert result.compliance_score == 0.0
        assert result.total_duration_ms == 0
        assert len(result.events) == 0
    
    @patch('ccms_pipeline.supabase_config_tool')
    @patch('ccms_pipeline.supabase_research_tool')
    @patch('ccms_pipeline.wordpress_enhanced_publisher')
    def test_dry_run_pipeline(self, mock_wp, mock_research, mock_config):
        """Test pipeline execution in dry-run mode"""
        
        # Mock config tool
        mock_config._run.return_value = {
            "config_success": True,
            "tenant_id": "test-tenant-id",
            "config": {
                "tenant_info": {
                    "name": "CrashCasino.io",
                    "brand_voice": {"tone": "crypto-savvy"}
                },
                "compliance": {"fail_fast": True},
                "publish": {"default_status": "draft"},
                "content": {"author_name": "Test Author"}
            }
        }
        
        # Mock research tool
        mock_research._run.return_value = {
            "research_success": True,
            "research_data": {
                "facts": {
                    "casino_name": "Viage Casino",
                    "license": {"primary": "Malta Gaming Authority", "license_number": "MGA/B2C/123"},
                    "games": {"total_games": 2500, "slots": 2000},
                    "welcome_bonus": {"amount": "€1,000", "wagering_requirement": "35x", "min_deposit": "€20", "validity": "30 days"},
                    "payments": {"deposit_methods": ["Bitcoin", "Visa"]},
                    "user_experience": {"customer_support": {"hours": "24/7"}}
                },
                "serp_intent": {"primary_kw": "Viage Casino review"},
                "secondary_keywords": ["viage casino bonus"]
            }
        }
        
        # Execute pipeline in dry-run mode
        result = run_ccms_pipeline(
            tenant_slug="crashcasino",
            casino_slug="viage",
            locale="en-GB",
            dry_run=True
        )
        
        # Assertions
        assert result.success == True
        assert result.tenant_slug == "crashcasino"
        assert result.casino_slug == "viage"
        assert result.wordpress_post_id == 99999  # Dry run mock ID
        assert "dry-run" in result.published_url
        assert result.total_duration_ms > 0
        assert len(result.events) > 0
        
        # Verify tools were called
        mock_config._run.assert_called_once()
        mock_research._run.assert_called_once()
        # WordPress should NOT be called in dry run
        mock_wp._run.assert_not_called()
    
    @patch('ccms_pipeline.supabase_config_tool')
    @patch('ccms_pipeline.supabase_research_tool')
    def test_compliance_failure_blocking(self, mock_research, mock_config):
        """Test that compliance failures block the pipeline"""
        
        # Mock config
        mock_config._run.return_value = {
            "config_success": True,
            "tenant_id": "test-tenant-id",
            "config": {
                "tenant_info": {"name": "Test", "brand_voice": {"tone": "test"}},
                "compliance": {"fail_fast": True}
            }
        }
        
        # Mock research with missing license info to trigger compliance failure
        mock_research._run.return_value = {
            "research_success": True,
            "research_data": {
                "facts": {
                    "casino_name": "Test Casino",
                    # Missing license info should trigger compliance error
                },
                "serp_intent": {"primary_kw": "test casino review"},
                "secondary_keywords": []
            }
        }
        
        # Execute pipeline - should fail at compliance gate
        result = run_ccms_pipeline(
            tenant_slug="crashcasino",
            casino_slug="test",
            locale="en-GB"
        )
        
        # Should fail due to compliance
        assert result.success == False
        assert "Compliance check failed" in result.error
    
    @patch('ccms_pipeline.supabase_config_tool')
    @patch('ccms_pipeline.supabase_research_tool')
    def test_compliance_skip_flag(self, mock_research, mock_config):
        """Test that --skip-compliance bypasses blocking compliance errors"""
        
        # Mock config
        mock_config._run.return_value = {
            "config_success": True,
            "tenant_id": "test-tenant-id",
            "config": {
                "tenant_info": {"name": "Test", "brand_voice": {"tone": "test"}},
                "compliance": {"fail_fast": True},
                "publish": {"default_status": "draft"}
            }
        }
        
        # Mock research with missing license info
        mock_research._run.return_value = {
            "research_success": True,
            "research_data": {
                "facts": {"casino_name": "Test Casino"},
                "serp_intent": {"primary_kw": "test casino review"},
                "secondary_keywords": []
            }
        }
        
        # Execute with compliance skip - should succeed
        result = run_ccms_pipeline(
            tenant_slug="crashcasino",
            casino_slug="test",
            locale="en-GB",
            dry_run=True,
            skip_compliance=True
        )
        
        # Should succeed despite compliance issues
        assert result.success == True
        assert result.wordpress_post_id == 99999  # Dry run ID
        
    def test_pipeline_lcel_composition(self):
        """Test that the pipeline is properly composed with LCEL"""
        from langchain_core.runnables import Runnable
        
        # Verify pipeline is a Runnable
        assert isinstance(ccms_pipeline, Runnable)
        
        # Verify we can get the pipeline steps
        # The pipeline should be a sequence of operations
        assert hasattr(ccms_pipeline, 'first')
        assert hasattr(ccms_pipeline, 'last')
    
    def test_compliance_error_exception(self):
        """Test ComplianceError exception behavior"""
        error = ComplianceError("Test compliance failure")
        
        assert str(error) == "Test compliance failure"
        assert isinstance(error, Exception)

if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])