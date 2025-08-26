#!/usr/bin/env python3
"""
🧪 Test Real Supabase Integration
================================

Test the production Supabase tools to ensure they work with the actual database.
"""

import os
import logging
from dotenv import load_dotenv
from src.tools.real_supabase_config_tool import real_supabase_config_tool

# Load production environment
load_dotenv('.env.production')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_supabase_config_tool():
    """Test the real Supabase config tool"""
    
    logger.info("🧪 Testing Real Supabase Config Tool")
    logger.info("=" * 50)
    
    # Test config resolution
    result = real_supabase_config_tool._run(
        tenant_slug="crashcasino",
        casino_slug="viage",
        locale="en-GB"
    )
    
    logger.info(f"📋 Config Resolution Result:")
    logger.info(f"   Success: {'✅' if result['config_success'] else '❌'}")
    logger.info(f"   Tenant: {result.get('tenant_slug', 'N/A')}")
    logger.info(f"   Casino: {result.get('casino_slug', 'N/A')}")
    logger.info(f"   Chains: {len(result.get('config', {}))}")
    
    config = result.get('config', {})
    if config:
        logger.info(f"\n📊 Available Chains:")
        for chain_name, chain_config in config.items():
            if isinstance(chain_config, dict):
                logger.info(f"   ✅ {chain_name}: {len(chain_config)} settings")
            else:
                logger.info(f"   ℹ️  {chain_name}: {type(chain_config).__name__}")
    
    return result['config_success']

def test_database_connectivity():
    """Test basic database connectivity"""
    
    logger.info("\n🔗 Testing Database Connectivity")
    logger.info("=" * 50)
    
    url = os.getenv('SUPABASE_URL')
    service_key = os.getenv('SUPABASE_SERVICE_ROLE')
    
    if not url or not service_key:
        logger.error("❌ Missing Supabase credentials")
        return False
    
    logger.info(f"🔗 URL: {url}")
    logger.info(f"🔑 Service Key: {'*' * 20}...{service_key[-10:]}")
    
    try:
        from supabase import create_client
        supabase = create_client(url, service_key)
        
        # Try a simple operation - list tables
        result = supabase.table('information_schema.tables').select('table_name').limit(1).execute()
        logger.info("✅ Database connectivity successful")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database connectivity failed: {e}")
        return False

def main():
    """Run all tests"""
    
    logger.info("🎰 CCMS Real Supabase Integration Test")
    logger.info("=" * 60)
    
    # Test 1: Database connectivity
    connectivity_ok = test_database_connectivity()
    
    # Test 2: Config tool
    config_tool_ok = test_supabase_config_tool()
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("🏁 Test Results Summary")
    logger.info("=" * 60)
    logger.info(f"Database Connectivity: {'✅ PASS' if connectivity_ok else '❌ FAIL'}")
    logger.info(f"Config Tool:          {'✅ PASS' if config_tool_ok else '❌ FAIL'}")
    
    if connectivity_ok and config_tool_ok:
        logger.info("\n🎊 All tests passed! Supabase integration is working.")
        logger.info("🚀 Ready to run: python cli.py run --tenant=crashcasino --casino=viage --dry-run")
    else:
        logger.info("\n⚠️  Some tests failed. Check the logs above for details.")
        logger.info("💡 The system will fall back to simulated data if needed.")
    
    return connectivity_ok and config_tool_ok

if __name__ == "__main__":
    main()