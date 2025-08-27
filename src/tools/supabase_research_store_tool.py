#!/usr/bin/env python3
"""
💾 SUPABASE RESEARCH STORE TOOL - CLAUDE.md COMPLIANT
====================================================

Single-purpose tool for storing comprehensive casino research to Supabase.
Follows CLAUDE.md principle: "Tools should do one thing."

This tool ONLY stores data. For fetching, use supabase_research_get_tool.py
"""

import os
import logging
import time
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from langchain.tools import BaseTool
from supabase import create_client, Client

logger = logging.getLogger(__name__)


class SupabaseResearchStoreInput(BaseModel):
    """Input schema for Supabase research STORE operations"""
    casino_slug: str = Field(description="Casino identifier (e.g., 'viage')")
    locale: str = Field(description="Locale code (e.g., 'en-GB')")
    research_data: Dict[str, Any] = Field(description="Comprehensive research data to store")
    tenant_id: str = Field(description="Tenant identifier")


class SupabaseResearchStoreTool(BaseTool):
    """
    💾 Single-purpose tool for storing comprehensive casino research to Supabase
    
    CLAUDE.md compliant: Does one thing (store), uses proper tool patterns
    """
    
    name: str = "supabase_research_store"
    description: str = "Store comprehensive 95+ field casino research data to Supabase database"
    args_schema: type = SupabaseResearchStoreInput
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._supabase_client: Optional[Client] = None
    
    def _get_supabase_client(self) -> Client:
        """Get or create Supabase client"""
        if self._supabase_client is None:
            url = os.getenv('SUPABASE_URL')
            service_key = os.getenv('SUPABASE_SERVICE_ROLE')
            
            if not url or not service_key:
                raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE environment variables")
            
            self._supabase_client = create_client(url, service_key)
        
        return self._supabase_client
    
    def _run(
        self,
        casino_slug: str,
        locale: str,
        research_data: Dict[str, Any],
        tenant_id: str
    ) -> Dict[str, Any]:
        """
        Store comprehensive casino research data to Supabase
        
        Returns:
            Dict containing storage result metadata
        """
        try:
            logger.info(f"💾 STORE: Storing research data for {casino_slug}/{locale}")
            
            supabase = self._get_supabase_client()
            
            # Prepare storage record
            storage_record = {
                "casino_slug": casino_slug,
                "locale": locale,
                "tenant_id": tenant_id,
                "research_data": research_data,
                "field_count": len([k for k, v in research_data.items() if v is not None]) if isinstance(research_data, dict) else 0,
                "stored_at": time.time(),
                "data_version": "v1.0_comprehensive"
            }
            
            # Store to casino_research table
            result = supabase.table("casino_research").upsert(storage_record).execute()
            
            logger.info(f"✅ STORE: Stored {storage_record['field_count']} fields to Supabase")
            
            return {
                "storage_success": True,
                "stored_fields": storage_record["field_count"],
                "storage_timestamp": storage_record["stored_at"],
                "record_id": result.data[0].get("id") if result.data else None
            }
            
        except Exception as e:
            logger.error(f"❌ STORE: Failed to store research data: {e}")
            return {
                "storage_success": False,
                "error_message": str(e),
                "stored_fields": 0,
                "storage_timestamp": time.time()
            }


# Export configured tool instance
supabase_research_store_tool = SupabaseResearchStoreTool()