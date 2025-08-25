#!/usr/bin/env python3
"""
🎰 MR VEGAS CASINO - AUTOMATED PRODUCTION PUBLISHING
Based on the successful TrustDice/Ladbrokes scripts that achieved 100% WordPress automation

This script uses the EXACT working configuration that produced live posts:
- Post ID 51371: TrustDice Casino → MT Casino custom post type ✅
- Post ID 51406: Ladbrokes Casino → MT Casino custom post type ✅
"""

import os
import asyncio
import sys
import time
import json
from datetime import datetime

# ✅ CRITICAL: Set WordPress environment variables BEFORE importing the chain
# Using EXACT same variable names and values as the WORKING scripts
os.environ["WORDPRESS_URL"] = "https://www.crashcasino.io"
os.environ["WORDPRESS_USERNAME"] = "nmlwh"
os.environ["WORDPRESS_PASSWORD"] = "q8ZU 4UHD 90vI Ej55 U0Jh yh8c"

print("🔧 WordPress environment variables set (WORKING CONFIGURATION):")
print(f"   WORDPRESS_URL: {os.environ.get('WORDPRESS_URL')}")
print(f"   WORDPRESS_USERNAME: {os.environ.get('WORDPRESS_USERNAME')}")
print(f"   WORDPRESS_PASSWORD: {'*' * len(os.environ.get('WORDPRESS_PASSWORD', ''))}")

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from chains.universal_rag_lcel import create_universal_rag_chain

async def run_mr_vegas_automated_production():
    """Run Mr Vegas analysis using PROVEN WordPress publishing configuration"""
    
    print("🎰 MR VEGAS CASINO - AUTOMATED PRODUCTION PUBLISHING")
    print("=" * 70)
    print("🎯 Target: Mr Vegas Casino → MT Casino WordPress Post")
    print("📝 WordPress Site: https://www.crashcasino.io")
    print("🔐 WordPress: ✅ EXACT working configuration from live posts")
    print("🏗️ Post Type: MT Casino (Custom Post Type)")
    print("🖼️ Images: 6 images per review with automated upload")
    print("📊 Features: 95-field research + DataForSEO + WordPress publishing")
    print()
    
    # Initialize RAG chain with EXACT same configuration as working scripts
    print("🚀 Initializing Universal RAG Chain with PROVEN configuration...")
    rag_chain = create_universal_rag_chain(
        model_name="gpt-4o-mini",
        temperature=0.1,
        enable_comprehensive_web_research=True,
        enable_wordpress_publishing=True,
        enable_dataforseo_images=True,
        enable_web_search=True,
        enable_cache_bypass=False
    )
    
    print("✅ Chain initialized with WORKING WordPress publishing configuration")
    
    # Mr Vegas casino query formatted for MT Casino requirements
    mr_vegas_query = """Create a comprehensive professional Mr Vegas Casino review for MT Casino custom post type.
    
    Cover: licensing and regulation (Malta Gaming Authority), payment methods including e-wallets and bank transfers, 
    games portfolio including 800+ titles from NetEnt and Microgaming, live dealer games from Evolution Gaming,
    welcome bonuses and ongoing promotions, mobile experience and app functionality, customer support quality, 
    security measures and player protection, user experience analysis, pros and cons assessment, 
    and final rating with detailed justification.
    
    Format for WordPress MT Casino post type with proper SEO optimization and structured sections.
    Target 2500+ words with authoritative hyperlinks and MT Casino metadata fields."""
    
    print(f"🔍 Mr Vegas MT Casino Query:")
    print(f"📝 {mr_vegas_query}")
    print("-" * 70)
    
    start_time = time.time()
    
    try:
        # Execute RAG chain with EXACT same input structure as working scripts
        print("⚡ Executing chain with PROVEN WordPress publishing automation...")
        
        # Use the EXACT input structure from successful TrustDice/Ladbrokes scripts
        query_input = {
            "question": mr_vegas_query,
            "publish_to_wordpress": True
        }
        
        response = await rag_chain.ainvoke(query_input)
        
        processing_time = time.time() - start_time
        
        # Display results using same format as working scripts
        print(f"\n⏱️ Processing Time: {processing_time:.2f} seconds")
        print(f"📊 Response Length: {len(response.answer)} characters")
        print(f"🎯 Confidence Score: {response.confidence_score:.3f}")
        print(f"📚 Sources: {len(response.sources)} sources")
        print(f"🖼️ Images: {response.metadata.get('images_found', 0)} found")
        
        # Check Mr Vegas content quality
        mr_vegas_count = response.answer.lower().count('mr vegas')
        print(f"🏷️ Mr Vegas mentions: {mr_vegas_count}")
        
        # Check WordPress publishing result (CRITICAL CHECK)
        wordpress_published = response.metadata.get("wordpress_published", False)
        wordpress_post_id = response.metadata.get("wordpress_post_id", None)
        wordpress_url = response.metadata.get("wordpress_url", None)
        wordpress_post_type = response.metadata.get("wordpress_post_type", None)
        wordpress_error = response.metadata.get("wordpress_error", None)
        
        print(f"\n🌐 WordPress Publishing Results:")
        print(f"   Published: {'✅' if wordpress_published else '❌'}")
        if wordpress_post_id:
            print(f"   Post ID: {wordpress_post_id}")
        if wordpress_url:
            print(f"   Live URL: {wordpress_url}")
        if wordpress_post_type:
            print(f"   Post Type: {wordpress_post_type}")
        if wordpress_error:
            print(f"   Error: {wordpress_error}")
            
        # Check MT Casino specific features (like successful scripts)
        if wordpress_published and wordpress_post_type:
            if 'mt_listing' in str(wordpress_post_type).lower() or '/casino/' in str(wordpress_url):
                print("✅ MT Casino integration successful!")
                print("🎰 Review published as MT Casino custom post type")
            else:
                print("⚠️ Published as regular post, not MT Casino")
        
        # Save comprehensive results (same format as working scripts)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_filename = f'mr_vegas_production_automated_{timestamp}.json'
        
        results_data = {
            "method": "mr_vegas_automated_production",
            "query": mr_vegas_query,
            "processing_time": processing_time,
            "content_length": len(response.answer),
            "confidence_score": response.confidence_score,
            "sources_count": len(response.sources),
            "images_found": response.metadata.get('images_found', 0),
            "mr_vegas_mentions": mr_vegas_count,
            "wordpress_published": wordpress_published,
            "wordpress_post_id": wordpress_post_id,
            "wordpress_url": wordpress_url,
            "wordpress_post_type": wordpress_post_type,
            "wordpress_error": wordpress_error,
            "full_content": response.answer,
            "timestamp": datetime.now().isoformat()
        }
        
        with open(results_filename, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Results saved: {results_filename}")
        
        # Final status report
        if wordpress_published:
            print("\n🎉 AUTOMATED PUBLISHING SUCCESS!")
            print("✅ Mr Vegas Casino review automatically published to WordPress")
            print("✅ MT Casino custom post type integration working")
            print("✅ All automation features operational")
            
            if wordpress_url:
                print(f"🔗 Live at: {wordpress_url}")
        else:
            print("\n❌ AUTOMATED PUBLISHING FAILED")
            if wordpress_error:
                print(f"Error: {wordpress_error}")
            print("Review generated successfully but WordPress publishing needs manual intervention")
        
        return response
        
    except Exception as e:
        print(f"❌ Error during automated production: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

async def main():
    """Main execution function"""
    print("🚀 STARTING MR VEGAS AUTOMATED PRODUCTION...")
    print("Using proven configuration from successful TrustDice/Ladbrokes publications")
    print()
    
    result = await run_mr_vegas_automated_production()
    
    if result:
        print("\n🎊 MR VEGAS AUTOMATED PRODUCTION COMPLETE!")
        
        # Check if it was published successfully
        wordpress_published = result.metadata.get("wordpress_published", False)
        if wordpress_published:
            print("🎰 SUCCESS: Mr Vegas Casino review is now LIVE on crashcasino.io!")
        else:
            print("⚠️ PARTIAL SUCCESS: Review generated but requires manual WordPress publishing")
    else:
        print("\n❌ MR VEGAS AUTOMATED PRODUCTION FAILED")

if __name__ == "__main__":
    asyncio.run(main())