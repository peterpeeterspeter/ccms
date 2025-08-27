#!/usr/bin/env python3
"""
🔍 SUPABASE RESEARCH GET TOOL - CLAUDE.md COMPLIANT
==================================================

Single-purpose tool for fetching comprehensive casino research from Supabase.
Follows CLAUDE.md principle: "Tools should do one thing."

This tool ONLY fetches data. For storing, use supabase_research_store_tool.py
"""

import os
import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from langchain.tools import BaseTool

# Import the existing implementation
from .real_supabase_research_tool import RealSupabaseResearchTool

logger = logging.getLogger(__name__)


class SupabaseResearchGetInput(BaseModel):
    """Input schema for Supabase research GET operations"""
    casino_slug: str = Field(description="Casino identifier (e.g., 'viage')")
    locale: str = Field(description="Locale code (e.g., 'en-GB')")
    include_sources: bool = Field(default=True, description="Include source URLs")
    include_serp_intent: bool = Field(default=False, description="Include SERP intent analysis")


class SupabaseResearchGetTool(BaseTool):
    """
    🔍 Single-purpose tool for fetching comprehensive casino research from Supabase
    
    CLAUDE.md compliant: Does one thing (fetch), uses proper tool patterns
    """
    
    name: str = "supabase_research_get"
    description: str = "Fetch comprehensive 95+ field casino research data from Supabase database"
    args_schema: type = SupabaseResearchGetInput
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._internal_tool = RealSupabaseResearchTool()
    
    def _run(
        self,
        casino_slug: str,
        locale: str,
        include_sources: bool = True,
        include_serp_intent: bool = False
    ) -> Dict[str, Any]:
        """
        Fetch comprehensive casino research data from Supabase
        
        Returns:
            Dict containing 95+ field casino intelligence data
        """
        try:
            logger.info(f"🔍 GET: Fetching research data for {casino_slug}/{locale}")
            
            # Use existing implementation
            result = self._internal_tool._run(
                casino_slug=casino_slug,
                locale=locale,
                include_sources=include_sources,
                include_serp_intent=include_serp_intent
            )
            
            logger.info(f"✅ GET: Retrieved {result.get('total_fields', 0)} fields")
            return result
            
        except Exception as e:
            logger.error(f"❌ GET: Failed to fetch research data: {e}")
            return {
                "research_success": False,
                "error_message": str(e),
                "total_fields": 0,
                "research_data": {},
                "sources": []
            }


# Export configured tool instance
supabase_research_get_tool = SupabaseResearchGetTool()