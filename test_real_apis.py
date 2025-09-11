#!/usr/bin/env python3
"""
Real API Integration Test

Test the actual API integrations (Firecrawl, WordPress, DataForSEO) 
to see which services are working and ready for production use.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import real tool clients
from tools import create_tool_orchestrator, ToolConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_api_connectivity():
    """Test connectivity to all configured APIs"""
    
    print("🔧 Casino Review API Integration Test")
    print("=" * 50)
    
    # Check environment variables
    required_env_vars = [
        "FIRECRAWL_API_KEY",
        "WORDPRESS_SITE_URL", 
        "WORDPRESS_USERNAME",
        "WORDPRESS_APP_PASSWORD"
    ]
    
    optional_env_vars = [
        "DATAFORSEO_LOGIN",
        "DATAFORSEO_PASSWORD",
        "CF_BROWSER_TOKEN",
        "BROWSERLESS_TOKEN"
    ]
    
    print("📋 Environment Configuration:")
    for var in required_env_vars:
        value = os.getenv(var)
        status = "✅" if value else "❌"
        masked_value = f"{value[:8]}..." if value and len(value) > 8 else "NOT SET"
        print(f"   {status} {var}: {masked_value}")
    
    print("\n📋 Optional Configuration:")
    for var in optional_env_vars:
        value = os.getenv(var)
        status = "✅" if value else "⚠️"
        masked_value = f"{value[:8]}..." if value and len(value) > 8 else "NOT SET"
        print(f"   {status} {var}: {masked_value}")
    
    # Check if we have minimum required APIs
    required_missing = [var for var in required_env_vars if not os.getenv(var)]
    if required_missing:
        print(f"\n❌ Missing required environment variables: {', '.join(required_missing)}")
        print("   Please configure these in your .env file")
        return False
    
    print("\n🚀 Testing API Connections...")
    
    try:
        # Create tool orchestrator with real API config
        config = ToolConfig.from_env()
        
        async with await create_tool_orchestrator(config) as tools:
            
            # Test service connectivity
            print("\n📡 Service Health Checks:")
            service_status = tools.get_service_status()
            
            for service, healthy in service_status["service_health"].items():
                status_icon = "✅" if healthy else "❌"
                print(f"   {status_icon} {service.title()}: {'Healthy' if healthy else 'Unavailable'}")
            
            # Count healthy services
            healthy_count = sum(service_status["service_health"].values())
            total_services = len(service_status["service_health"])
            
            print(f"\n📊 Overall Health: {healthy_count}/{total_services} services operational")
            
            if healthy_count == 0:
                print("❌ No services are available - check your API credentials")
                return False
            
            # Test basic operations with real APIs
            test_results = await run_integration_tests(tools, service_status["service_health"])
            
            return test_results
            
    except Exception as e:
        print(f"❌ API integration test failed: {str(e)}")
        logger.error(f"Full error: {e}", exc_info=True)
        return False

async def run_integration_tests(tools, service_health: Dict[str, bool]) -> bool:
    """Run integration tests with available services"""
    
    print("\n🧪 Running Integration Tests...")
    test_results = []
    
    # Test 1: WordPress Connection
    if service_health.get("wordpress"):
        try:
            print("\n1️⃣ Testing WordPress API...")
            
            # Create a test post
            test_post = {
                "title": f"API Test Post - {datetime.now().isoformat()}",
                "content": "<p>This is a test post created by the CCMS API integration test.</p>",
                "status": "draft",  # Don't publish test posts
                "type": "post"
            }
            
            post_result = await tools.wordpress.create_post(test_post)
            
            if post_result and post_result.get("id"):
                print(f"   ✅ WordPress post created: ID {post_result['id']}")
                
                # Clean up test post
                await tools.wordpress.delete_post(post_result["id"], force=True)
                print(f"   🗑️ Test post cleaned up")
                
                test_results.append(("WordPress API", True))
            else:
                print("   ❌ WordPress post creation failed")
                test_results.append(("WordPress API", False))
                
        except Exception as e:
            print(f"   ❌ WordPress test failed: {str(e)}")
            test_results.append(("WordPress API", False))
    else:
        print("\n1️⃣ WordPress API: Skipped (not available)")
        test_results.append(("WordPress API", None))
    
    # Test 2: Firecrawl Screenshot Capture
    if service_health.get("firecrawl"):
        try:
            print("\n2️⃣ Testing Firecrawl Screenshot Capture...")
            
            # Test with a simple, reliable website
            test_url = "https://example.com"
            
            screenshots = await tools.firecrawl.capture_casino_screenshots(test_url)
            
            if screenshots and len(screenshots) > 0:
                print(f"   ✅ Firecrawl captured {len(screenshots)} screenshots")
                for screenshot in screenshots[:2]:  # Show first 2
                    print(f"      - {screenshot.view_type}: {screenshot.width}x{screenshot.height}")
                test_results.append(("Firecrawl Screenshots", True))
            else:
                print("   ❌ Firecrawl screenshot capture failed")
                test_results.append(("Firecrawl Screenshots", False))
                
        except Exception as e:
            print(f"   ❌ Firecrawl test failed: {str(e)}")
            test_results.append(("Firecrawl Screenshots", False))
    else:
        print("\n2️⃣ Firecrawl Screenshots: Skipped (not available)")
        test_results.append(("Firecrawl Screenshots", None))
    
    # Test 3: DataForSEO Research
    if service_health.get("dataforseo"):
        try:
            print("\n3️⃣ Testing DataForSEO Research...")
            
            # Simple research test
            research_pack = await tools.dataforseo.research_casino_comprehensive(
                casino_name="BitStarz",
                casino_url="https://bitstarz.com"
            )
            
            if research_pack and research_pack.casino_name:
                print(f"   ✅ DataForSEO research completed for {research_pack.casino_name}")
                print(f"      - Keywords found: {len(research_pack.primary_keywords)}")
                print(f"      - Research accuracy: {research_pack.research_accuracy:.2f}")
                test_results.append(("DataForSEO Research", True))
            else:
                print("   ❌ DataForSEO research failed")
                test_results.append(("DataForSEO Research", False))
                
        except Exception as e:
            print(f"   ❌ DataForSEO test failed: {str(e)}")
            test_results.append(("DataForSEO Research", False))
    else:
        print("\n3️⃣ DataForSEO Research: Skipped (not available)")
        test_results.append(("DataForSEO Research", None))
    
    # Test 4: Comprehensive Casino Research Flow
    if service_health.get("dataforseo") or service_health.get("firecrawl"):
        try:
            print("\n4️⃣ Testing Comprehensive Research Flow...")
            
            research_result = await tools.comprehensive_casino_research(
                casino_name="Test Casino",
                casino_url="https://example.com"
            )
            
            if research_result:
                print("   ✅ Comprehensive research flow completed")
                print(f"      - Research pack: {'✅' if research_result.get('research_pack') else '❌'}")
                print(f"      - Screenshots: {len(research_result.get('screenshots', []))}")
                test_results.append(("Comprehensive Research", True))
            else:
                print("   ❌ Comprehensive research flow failed")
                test_results.append(("Comprehensive Research", False))
                
        except Exception as e:
            print(f"   ❌ Comprehensive research test failed: {str(e)}")
            test_results.append(("Comprehensive Research", False))
    else:
        print("\n4️⃣ Comprehensive Research: Skipped (no research tools available)")
        test_results.append(("Comprehensive Research", None))
    
    # Summary
    print(f"\n📊 Integration Test Results:")
    print("-" * 40)
    
    passed = 0
    failed = 0
    skipped = 0
    
    for test_name, result in test_results:
        if result is True:
            print(f"✅ {test_name}: PASSED")
            passed += 1
        elif result is False:
            print(f"❌ {test_name}: FAILED")
            failed += 1
        else:
            print(f"⚠️ {test_name}: SKIPPED")
            skipped += 1
    
    print(f"\nSummary: {passed} passed, {failed} failed, {skipped} skipped")
    
    # Overall result
    if passed > 0 and failed == 0:
        print("🎉 All available APIs are working correctly!")
        return True
    elif passed > 0:
        print("⚠️ Some APIs are working, but there are failures to investigate")
        return True
    else:
        print("❌ No APIs are working correctly")
        return False

async def main():
    """Main test runner"""
    try:
        success = await test_api_connectivity()
        
        if success:
            print("\n🚀 Your system is ready for casino review pipeline testing!")
            print("   Next steps:")
            print("   1. Run the integrated pipeline with real APIs:")
            print("      python test_integrated_pipeline_real.py")
            print("   2. Test with a real casino website:")
            print("      python test_real_casino_review.py")
        else:
            print("\n⚠️ Some API configurations need attention")
            print("   Check your .env file and API credentials")
            print("   Refer to .env.example for required variables")
        
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test suite failed: {str(e)}")
        logger.error("Full error:", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())
