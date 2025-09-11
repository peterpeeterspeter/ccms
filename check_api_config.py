#!/usr/bin/env python3
"""
Simple API Configuration Checker

Check what API keys and services you have configured
without trying to import the complex tool orchestrator.
"""

import os
from dotenv import load_dotenv

def main():
    """Check API configuration status"""
    
    print("🔧 Casino Review API Configuration Check")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Check for .env file
    env_file = os.path.join(os.getcwd(), '.env')
    if os.path.exists(env_file):
        print("✅ .env file found")
    else:
        print("⚠️ .env file not found - using system environment variables")
    
    print("\n📋 API Configuration Status:")
    
    # Core required APIs
    required_apis = [
        ("FIRECRAWL_API_KEY", "Firecrawl Screenshot Capture"),
        ("WORDPRESS_SITE_URL", "WordPress Site URL"),
        ("WORDPRESS_USERNAME", "WordPress Username"),
        ("WORDPRESS_APP_PASSWORD", "WordPress App Password"),
    ]
    
    # Optional APIs
    optional_apis = [
        ("DATAFORSEO_LOGIN", "DataForSEO Research Login"),
        ("DATAFORSEO_PASSWORD", "DataForSEO Research Password"),
        ("CF_BROWSER_TOKEN", "Cloudflare Browser Rendering"),
        ("BROWSERLESS_TOKEN", "Browserless Screenshot Service"),
        ("OPENAI_API_KEY", "OpenAI GPT Models"),
        ("ANTHROPIC_API_KEY", "Anthropic Claude Models"),
        ("SUPABASE_URL", "Supabase Database"),
        ("SUPABASE_SERVICE_KEY", "Supabase Service Key"),
        ("LANGCHAIN_API_KEY", "LangSmith Tracing"),
    ]
    
    print("\n🔑 Core Services:")
    configured_core = 0
    for env_var, description in required_apis:
        value = os.getenv(env_var)
        if value:
            status = "✅"
            masked_value = f"{value[:8]}..." if len(value) > 8 else value[:4] + "..."
            configured_core += 1
        else:
            status = "❌"
            masked_value = "NOT CONFIGURED"
        
        print(f"   {status} {description}: {masked_value}")
    
    print(f"\n📊 Core Services: {configured_core}/{len(required_apis)} configured")
    
    print("\n🔧 Optional Services:")
    configured_optional = 0
    for env_var, description in optional_apis:
        value = os.getenv(env_var)
        if value:
            status = "✅"
            masked_value = f"{value[:8]}..." if len(value) > 8 else value[:4] + "..."
            configured_optional += 1
        else:
            status = "⚠️"
            masked_value = "NOT CONFIGURED"
        
        print(f"   {status} {description}: {masked_value}")
    
    print(f"\n📊 Optional Services: {configured_optional}/{len(optional_apis)} configured")
    
    # Check which tools are likely to work
    print("\n🚀 Likely Working Integrations:")
    
    if os.getenv("FIRECRAWL_API_KEY"):
        print("   ✅ Firecrawl Screenshot Capture - Ready")
    else:
        print("   ❌ Firecrawl Screenshot Capture - Missing API key")
    
    if all(os.getenv(var) for var, _ in required_apis if "WORDPRESS" in var):
        print("   ✅ WordPress Publishing - Ready")
    else:
        print("   ❌ WordPress Publishing - Missing credentials")
    
    if os.getenv("DATAFORSEO_LOGIN") and os.getenv("DATAFORSEO_PASSWORD"):
        print("   ✅ DataForSEO Research - Ready")
    else:
        print("   ⚠️ DataForSEO Research - Not configured (optional)")
    
    if os.getenv("CF_BROWSER_TOKEN") or os.getenv("BROWSERLESS_TOKEN"):
        print("   ✅ Fallback Screenshot Services - Available")
    else:
        print("   ⚠️ Fallback Screenshot Services - Not configured (optional)")
    
    if os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_SERVICE_KEY"):
        print("   ✅ Supabase Storage - Ready")
    else:
        print("   ⚠️ Supabase Storage - Not configured (optional)")
    
    # Recommendations
    print("\n💡 Recommendations:")
    
    if configured_core == len(required_apis):
        print("   🎉 All core services configured! You can test the full pipeline.")
        print("   Next: Run 'python test_integrated_pipeline.py' to test with mock data")
    else:
        missing_core = [desc for var, desc in required_apis if not os.getenv(var)]
        print(f"   📝 Configure these core services to enable full testing:")
        for service in missing_core:
            print(f"      - {service}")
    
    if configured_optional > 0:
        print(f"   ✨ {configured_optional} optional services configured for enhanced functionality")
    
    print("\n📄 Configuration Help:")
    print("   - Copy .env.example to .env and fill in your API keys")
    print("   - Refer to WARP.md for service setup instructions")
    print("   - Test individual services with their respective test scripts")
    
    return configured_core == len(required_apis)

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n✅ Configuration looks good!")
        else:
            print("\n⚠️ Some configuration needed")
    except Exception as e:
        print(f"\n❌ Configuration check failed: {str(e)}")
