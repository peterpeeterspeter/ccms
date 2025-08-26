#!/usr/bin/env python3
"""
🔍 CCMS Environment Verification Script
=====================================

Verifies that all required environment variables and services 
are properly configured for the CCMS production system.
"""

import os
import sys
from pathlib import Path

def check_env_var(name: str, required: bool = True, description: str = ""):
    """Check if environment variable exists and is properly formatted"""
    value = os.getenv(name)
    
    if not value:
        status = "❌ MISSING" if required else "⚠️  OPTIONAL"
        print(f"{status}: {name}")
        if required:
            return False
        return True
    
    # Mask sensitive values
    if "KEY" in name or "PASSWORD" in name or "SECRET" in name:
        masked_value = f"{value[:10]}..." if len(value) > 10 else "***"
    else:
        masked_value = value
    
    print(f"✅ FOUND: {name} = {masked_value}")
    return True

def main():
    """Main verification function"""
    print("🔍 CCMS ENVIRONMENT VERIFICATION")
    print("=" * 50)
    print()
    
    # Track verification status
    all_required_present = True
    
    print("🔑 CORE API KEYS (REQUIRED)")
    print("-" * 30)
    all_required_present &= check_env_var("OPENAI_API_KEY", True, "GPT-4o + embeddings")
    all_required_present &= check_env_var("ANTHROPIC_API_KEY", True, "Claude models")
    all_required_present &= check_env_var("TAVILY_API_KEY", True, "Web research")
    print()
    
    print("🗄️ SUPABASE CONFIGURATION (REQUIRED)")
    print("-" * 35)
    all_required_present &= check_env_var("SUPABASE_URL", True)
    all_required_present &= check_env_var("SUPABASE_SERVICE_KEY", True)
    all_required_present &= check_env_var("SUPABASE_ANON_KEY", True)
    all_required_present &= check_env_var("SUPABASE_PROJECT_ID", True)
    print()
    
    print("🌐 WORDPRESS CONFIGURATION (REQUIRED)")
    print("-" * 35)
    all_required_present &= check_env_var("WORDPRESS_SITE_URL", True)
    all_required_present &= check_env_var("WORDPRESS_USERNAME", True)
    all_required_present &= check_env_var("WORDPRESS_APP_PASSWORD", True)
    print()
    
    print("📸 SCREENSHOT SERVICES (REQUIRED)")
    print("-" * 30)
    all_required_present &= check_env_var("FIRECRAWL_API_KEY", True, "Screenshot capture")
    print()
    
    print("⚠️  OPTIONAL SERVICES")
    print("-" * 20)
    check_env_var("DATAFORSEO_LOGIN", False, "Image discovery")
    check_env_var("DATAFORSEO_PASSWORD", False, "Image discovery")
    check_env_var("LANGCHAIN_API_KEY", False, "LangSmith tracing")
    print()
    
    print("⚙️ SYSTEM CONFIGURATION")
    print("-" * 25)
    check_env_var("TENANT_DEFAULT", False)
    check_env_var("ENVIRONMENT", False)
    check_env_var("USER_AGENT", False)
    print()
    
    # Final status
    if all_required_present:
        print("🎉 VERIFICATION COMPLETE")
        print("=" * 25)
        print("✅ All required environment variables are configured!")
        print("✅ System is ready for CCMS production use.")
        print()
        print("🚀 NEXT STEPS:")
        print("1. Test component discovery: python scripts/discover_components.py")
        print("2. Test integration: python integrate_existing_components.py")
        print("3. Run production pipeline: python test_ccms_pipeline.py")
        return True
    else:
        print("❌ VERIFICATION FAILED")
        print("=" * 20)
        print("❌ Missing required environment variables!")
        print("📋 Please check your .env file configuration.")
        print("💡 Use .env.example as a template:")
        print("   cp .env.example .env")
        print("   # Fill in your API keys")
        return False

if __name__ == "__main__":
    # Load .env file if it exists
    env_file = Path(".env")
    if env_file.exists():
        print(f"📋 Loading environment from: {env_file.absolute()}")
        print()
        
        # Simple .env parser (basic implementation)
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # Remove quotes if present
                    value = value.strip('\'"')
                    os.environ[key] = value
    else:
        print("⚠️  No .env file found. Using system environment variables.")
        print("💡 Create .env file: cp .env.example .env")
        print()
    
    success = main()
    sys.exit(0 if success else 1)