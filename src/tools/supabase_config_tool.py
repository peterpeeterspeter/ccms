#!/usr/bin/env python3
"""
🗃️ Supabase Configuration Tool - Claude.md Compliant
==================================================

LangChain BaseTool for fetching tenant configuration from Supabase.
Implements config hierarchy: tenant_overrides > tenant_defaults > global_defaults

Claude.md Compliance:
✅ All external I/O via /src/tools/* adapters  
✅ No ad-hoc HTTP inside chains
✅ BaseTool implementation for LCEL integration
"""

import json
import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from langchain.tools import BaseTool

logger = logging.getLogger(__name__)

class SupabaseConfigInput(BaseModel):
    """Input schema for Supabase config tool"""
    tenant_slug: str = Field(description="Tenant identifier (e.g., 'crashcasino')")
    casino_slug: str = Field(description="Casino identifier (e.g., 'viage')")
    locale: str = Field(description="Locale code (e.g., 'en-GB')")
    chains: Optional[list] = Field(default=None, description="Specific chains to fetch config for")

class SupabaseConfigTool(BaseTool):
    """
    🗃️ LangChain tool for fetching merged tenant configuration from Supabase
    
    Config hierarchy (highest precedence wins):
    1. tenant_overrides (per casino/chain)
    2. tenant_defaults (per tenant/chain)  
    3. global_defaults (per chain)
    """
    
    name: str = "supabase_config"
    description: str = "Fetch merged tenant configuration from Supabase following config hierarchy"
    args_schema: type = SupabaseConfigInput
    
    def _run(
        self,
        tenant_slug: str,
        casino_slug: str,
        locale: str,
        chains: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Fetch and merge configuration following hierarchy
        
        Args:
            tenant_slug: Tenant identifier
            casino_slug: Casino identifier  
            locale: Locale code
            chains: Specific chains to fetch (default: all)
            
        Returns:
            Merged configuration dictionary with tenant_id included
        """
        try:
            logger.info(f"🗃️ Fetching config: {tenant_slug}/{casino_slug}/{locale}")
            
            # TODO: Replace with actual Supabase client
            # For now, simulate the config resolution
            
            # 1. Get tenant info
            tenant_info = self._get_tenant_info(tenant_slug)
            if not tenant_info:
                raise ValueError(f"Tenant '{tenant_slug}' not found")
            
            # 2. Get global defaults
            global_config = self._get_global_defaults(chains)
            
            # 3. Get tenant defaults
            tenant_config = self._get_tenant_defaults(tenant_info["id"], chains)
            
            # 4. Get tenant overrides for this casino
            override_config = self._get_tenant_overrides(tenant_info["id"], casino_slug, chains)
            
            # 5. Merge configurations (override > tenant > global)
            merged_config = self._merge_configs(global_config, tenant_config, override_config)
            
            # 6. Add tenant info to config
            merged_config["tenant_info"] = tenant_info
            merged_config["locale"] = locale
            
            logger.info(f"✅ Config resolved for {len(merged_config)} chains")
            
            return {
                "config_success": True,
                "tenant_id": tenant_info["id"],
                "tenant_slug": tenant_slug,
                "casino_slug": casino_slug,
                "locale": locale,
                "config": merged_config
            }
            
        except Exception as e:
            logger.error(f"❌ Config resolution failed: {e}")
            return {
                "config_success": False,
                "error": str(e),
                "config": {}
            }
    
    def _get_tenant_info(self, tenant_slug: str) -> Optional[Dict[str, Any]]:
        """Get tenant information"""
        # TODO: SELECT id, slug, name, brand_voice, locales, feature_flags FROM tenants WHERE slug = %s
        
        # Simulated tenant data for CrashCasino
        if tenant_slug == "crashcasino":
            return {
                "id": "550e8400-e29b-41d4-a716-446655440000",  # UUID
                "slug": "crashcasino",
                "name": "CrashCasino.io",
                "brand_voice": {
                    "tone": "crypto-savvy, punchy",
                    "style": "direct, no-nonsense",
                    "disclaimers": "prominent"
                },
                "locales": ["en-GB", "en-US"],
                "feature_flags": {
                    "use_faq_schema": True,
                    "use_itemlist": True,
                    "geo_proxy": True
                }
            }
        return None
    
    def _get_global_defaults(self, chains: Optional[list] = None) -> Dict[str, Dict]:
        """Get global default configs"""
        # TODO: SELECT chain, config FROM global_defaults WHERE chain = ANY(%s) OR %s IS NULL
        
        global_defaults = {
            "compliance": {
                "retries": {"attempts": 3, "backoff": "exponential", "base_ms": 400},
                "fail_fast": True,
                "required_checks": ["license", "wagering", "age_disclaimer", "rg_links"]
            },
            "media": {
                "screenshot": {"viewport": "1440x900", "wait_for": [".bonus-banner"], "timeout": 30000},
                "resize": {"variants": [{"w": 1280}, {"w": 800}, {"w": 400}]},
                "retries": {"attempts": 3, "backoff": "exponential", "base_ms": 500}
            },
            "seo": {
                "title_max_length": 60,
                "meta_description_max_length": 158,
                "inject_secondary_keywords": True,
                "schema_types": ["Review", "FAQPage"]
            },
            "content": {
                "target_word_count": 2500,
                "include_comparison_tables": True,
                "include_pros_cons": True
            },
            "research": {
                "max_sources": 10,
                "fact_verification_threshold": 0.8
            },
            "publish": {
                "default_status": "draft",
                "retries": {"attempts": 5, "backoff": "exponential", "base_ms": 1000}
            }
        }
        
        if chains:
            return {chain: global_defaults.get(chain, {}) for chain in chains}
        return global_defaults
    
    def _get_tenant_defaults(self, tenant_id: str, chains: Optional[list] = None) -> Dict[str, Dict]:
        """Get tenant-specific defaults"""
        # TODO: SELECT chain, config FROM tenant_defaults WHERE tenant_id = %s AND (chain = ANY(%s) OR %s IS NULL)
        
        # Simulated tenant defaults for CrashCasino
        tenant_defaults = {
            "seo": {
                "title_pattern": "{casino} Review {year} – {bonus}",
                "h1_pattern": "{casino} Review {year}: Complete Guide",
                "meta_max_len": 158,
                "inject_secondary_keywords": True,
                "internal_link_blocks": [
                    {"title": "Best Crypto Casinos 2025", "target_slug": "best-crypto-casinos"},
                    {"title": "Bitcoin Casinos", "target_slug": "bitcoin-casinos"}
                ]
            },
            "content": {
                "author_name": "Peter Peeters",
                "include_crypto_section": True,
                "include_mobile_section": True
            }
        }
        
        if chains:
            return {chain: tenant_defaults.get(chain, {}) for chain in chains}
        return tenant_defaults
    
    def _get_tenant_overrides(self, tenant_id: str, casino_slug: str, chains: Optional[list] = None) -> Dict[str, Dict]:
        """Get casino-specific overrides"""
        # TODO: SELECT chain, config FROM tenant_overrides WHERE tenant_id = %s AND casino_slug = %s AND (chain = ANY(%s) OR %s IS NULL)
        
        # Simulated overrides for specific casinos
        overrides = {}
        if casino_slug == "viage":
            overrides = {
                "seo": {
                    "primary_kw": "Viage Casino Review 2025",
                    "secondary_kws": ["Viage Casino bonus", "Viage withdrawal time", "is Viage legit"]
                },
                "content": {
                    "focus_areas": ["cryptocurrency", "live_dealer", "mobile_gaming"]
                }
            }
        
        if chains:
            return {chain: overrides.get(chain, {}) for chain in chains}
        return overrides
    
    def _merge_configs(self, global_cfg: Dict, tenant_cfg: Dict, override_cfg: Dict) -> Dict:
        """Merge configurations with proper precedence"""
        merged = {}
        
        # Get all unique chain names
        all_chains = set(global_cfg.keys()) | set(tenant_cfg.keys()) | set(override_cfg.keys())
        
        for chain in all_chains:
            chain_config = {}
            
            # Start with global defaults
            if chain in global_cfg:
                chain_config.update(global_cfg[chain])
            
            # Override with tenant defaults
            if chain in tenant_cfg:
                chain_config.update(tenant_cfg[chain])
            
            # Override with casino-specific settings
            if chain in override_cfg:
                chain_config.update(override_cfg[chain])
            
            merged[chain] = chain_config
        
        return merged

    async def _arun(
        self,
        tenant_slug: str,
        casino_slug: str,
        locale: str,
        chains: Optional[list] = None
    ) -> Dict[str, Any]:
        """Async version of the tool"""
        return self._run(tenant_slug, casino_slug, locale, chains)

# Create tool instance for easy import
supabase_config_tool = SupabaseConfigTool()