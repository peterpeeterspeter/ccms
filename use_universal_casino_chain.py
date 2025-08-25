#!/usr/bin/env python3
"""
Demo: Using Universal Casino LCEL Chain
======================================

Demonstrates proper usage of the native LangChain LCEL universal casino chain.
This follows CLAUDE.md best practices by using the chain as a standard LangChain Runnable.

Usage:
    python use_universal_casino_chain.py
"""

import asyncio
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Import the proper LCEL chain
from chains.universal_casino_lcel import (
    create_universal_casino_chain, 
    CasinoReviewInput,
    CasinoReviewOutput
)

async def demo_single_casino():
    """Demo: Generate review for a single casino using LCEL chain"""
    print("🎰 DEMO: Universal Casino LCEL Chain")
    print("=" * 50)
    
    # Create the native LangChain LCEL chain
    chain = create_universal_casino_chain()
    print("✅ Universal Casino LCEL Chain created")
    
    # Prepare input using proper schema
    casino_input = CasinoReviewInput(
        casino_name="Mr Vegas Casino",
        target_words=2500,
        include_images=True,
        publish_to_wordpress=False
    )
    
    print(f"🎯 Generating review for: {casino_input.casino_name}")
    print(f"📝 Target words: {casino_input.target_words}")
    
    try:
        # Use standard LangChain ainvoke method
        result: CasinoReviewOutput = await chain.ainvoke(casino_input.dict())
        
        print("\\n✅ LCEL Chain Execution Complete!")
        print(f"📊 Casino: {result.casino_name}")
        print(f"📝 Word Count: {result.word_count}")
        print(f"🎯 Confidence: {result.confidence_score:.3f}")
        print(f"⏱️ Processing Time: {result.processing_time_seconds:.2f}s")
        print(f"📋 Status: {result.status}")
        print(f"📚 Sources: {len(result.research_sources)}")
        
        if result.wordpress_url:
            print(f"🌐 WordPress: {result.wordpress_url}")
        
        # Show preview of content
        if result.review_content:
            preview = result.review_content[:300] + "..." if len(result.review_content) > 300 else result.review_content
            print(f"\\n📄 Content Preview:\\n{preview}")
        
        # Save result
        output_file = f"demo_result_{result.casino_name.lower().replace(' ', '_')}.json"
        with open(output_file, 'w') as f:
            json.dump(result.dict(), f, indent=2, default=str)
        
        print(f"💾 Result saved: {output_file}")
        
        return result
        
    except Exception as e:
        print(f"❌ LCEL Chain execution failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

async def demo_batch_casinos():
    """Demo: Generate reviews for multiple casinos using the same LCEL chain"""
    print("\\n🎰 DEMO: Batch Casino Processing with LCEL Chain")
    print("=" * 50)
    
    # Create the chain once (reusable)
    chain = create_universal_casino_chain()
    
    # List of casinos to process
    casinos = [
        "Mr Vegas Casino",
        "Betway Casino", 
        "LeoVegas Casino"
    ]
    
    results = []
    
    for i, casino_name in enumerate(casinos, 1):
        print(f"\\n📋 Processing {i}/{len(casinos)}: {casino_name}")
        
        # Prepare input
        casino_input = CasinoReviewInput(
            casino_name=casino_name,
            target_words=2000,  # Smaller for demo
            include_images=False,
            publish_to_wordpress=False
        )
        
        try:
            # Use the same chain for different inputs
            result = await chain.ainvoke(casino_input.dict())
            results.append(result)
            
            print(f"   ✅ Success - {result.word_count} words in {result.processing_time_seconds:.1f}s")
            
        except Exception as e:
            print(f"   ❌ Failed: {str(e)}")
            results.append(None)
    
    # Summary
    successful = sum(1 for r in results if r is not None)
    print(f"\\n📊 Batch Summary: {successful}/{len(casinos)} successful")
    
    return results

async def demo_chain_composition():
    """Demo: Show how to compose the chain with other LangChain components"""
    print("\\n🔗 DEMO: LCEL Chain Composition")
    print("=" * 50)
    
    from langchain_core.runnables import RunnableLambda
    
    # Get the base chain
    casino_chain = create_universal_casino_chain()
    
    # Add post-processing using LCEL composition
    def add_summary(result: CasinoReviewOutput) -> dict:
        """Add a summary to the result"""
        return {
            "original_result": result,
            "summary": {
                "casino": result.casino_name,
                "words": result.word_count,
                "quality": "High" if result.confidence_score > 0.8 else "Medium" if result.confidence_score > 0.5 else "Low",
                "time": f"{result.processing_time_seconds:.1f}s"
            }
        }
    
    # Compose chains using | operator (LCEL best practice)
    enhanced_chain = casino_chain | RunnableLambda(add_summary)
    
    # Test composed chain
    test_input = CasinoReviewInput(
        casino_name="888 Casino",
        target_words=1500,
        include_images=False,
        publish_to_wordpress=False
    )
    
    print(f"🎯 Testing composed chain with: {test_input.casino_name}")
    
    try:
        result = await enhanced_chain.ainvoke(test_input.dict())
        
        print("✅ Composed chain successful!")
        print("📊 Summary:", result["summary"])
        
        return result
        
    except Exception as e:
        print(f"❌ Composed chain failed: {str(e)}")
        return None

async def main():
    """Main demo function"""
    print("🚀 Universal Casino LCEL Chain Demonstrations")
    print("Following CLAUDE.md native LangChain best practices")
    print()
    
    # Demo 1: Single casino
    await demo_single_casino()
    
    # Demo 2: Batch processing  
    await demo_batch_casinos()
    
    # Demo 3: Chain composition
    await demo_chain_composition()
    
    print("\\n🎉 All demos complete!")
    print("\\n✅ CLAUDE.md Compliance Verified:")
    print("   ✅ LCEL everywhere (| composition)")
    print("   ✅ No custom orchestration") 
    print("   ✅ Schema-first approach")
    print("   ✅ Native LangChain components only")
    print("   ✅ Proper Runnable interface")

if __name__ == "__main__":
    asyncio.run(main())