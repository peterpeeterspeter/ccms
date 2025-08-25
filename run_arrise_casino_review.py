#!/usr/bin/env python3
"""
Complete pipeline test: Generate comprehensive Arrise Casino review with images and taxonomies
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

async def run_comprehensive_arrise_review():
    """Run complete pipeline for Arrise Casino review with all features enabled"""
    
    print("🎰 COMPLETE PIPELINE: Arrise Casino Review Generation")
    print("=" * 70)
    print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎯 Target: 2500+ words with images, taxonomies, and CoinFlip integration")
    print()
    
    try:
        # Import the Universal RAG Chain
        from chains.universal_rag_lcel import UniversalRAGChain
        
        print("✅ Universal RAG Chain imported successfully")
        
        # Initialize with ALL features enabled for comprehensive review
        chain = UniversalRAGChain(
            model_name="gpt-4o-mini",
            temperature=0.1,
            
            # Core publishing features
            enable_wordpress_publishing=True,
            enable_web_search=True,
            enable_comprehensive_web_research=True,
            enable_dataforseo_images=True,
            
            # Content enhancement features
            enable_prompt_optimization=True,
            enable_enhanced_confidence=True,
            enable_template_system_v2=True,
            enable_contextual_retrieval=True,
            
            # Additional features
            enable_fti_processing=True,
            enable_security=True,
            enable_profiling=True,
            enable_browserbase_screenshots=True,
            enable_hyperlink_generation=True
        )
        
        print("🚀 Universal RAG Chain initialized with ALL features:")
        print(f"   📝 Native WordPress Publishing: {chain.wordpress_tool is not None}")
        print(f"   🔗 WordPress Chain Available: {chain.wordpress_chain is not None}")
        print(f"   🌐 Web Research: {chain.enable_web_search}")
        print(f"   🖼️ Image Integration: {chain.enable_dataforseo_images}")
        print(f"   📸 Screenshot Capture: {chain.enable_browserbase_screenshots}")
        print(f"   🧠 Advanced Prompts: {chain.enable_prompt_optimization}")
        print(f"   📊 Enhanced Confidence: {chain.enable_enhanced_confidence}")
        print()
        
        # Comprehensive review query
        review_query = """Write a comprehensive 2500+ word review of Arrise Casino. Include:

CONTENT REQUIREMENTS:
- Executive summary with key highlights
- Detailed licensing and security analysis
- Complete game portfolio review (slots, table games, live casino)
- Software providers and game quality assessment
- Welcome bonus and promotions analysis
- Banking and payment methods evaluation
- Mobile experience and usability review
- Customer support quality assessment
- Detailed pros and cons analysis
- Geographic restrictions and availability
- Final verdict with professional rating out of 10

COINFLIP THEME REQUIREMENTS:
- Small description for subtitle
- List of casino features for About section
- Clear pros and cons for single page display
- Bonus message for call-to-action
- Official casino website URL

TECHNICAL REQUIREMENTS:
- Professional tone with expert analysis
- Include specific details about RTPs, wagering requirements, processing times
- Add relevant statistics and comparisons
- Ensure content is SEO-optimized
- Include images where relevant
- Target 2500+ words minimum

Focus on providing comprehensive, actionable information for players considering Arrise Casino."""

        # Input configuration for comprehensive review
        review_input = {
            "question": review_query,
            "publish_to_wordpress": True,
            "casino_name": "Arrise Casino",
            "target_word_count": 2500,
            "include_images": True,
            "enable_taxonomies": True
        }
        
        print("📝 Review Configuration:")
        print(f"   🎰 Casino: {review_input['casino_name']}")
        print(f"   📏 Target Length: {review_input['target_word_count']} words")
        print(f"   🖼️ Include Images: {review_input['include_images']}")
        print(f"   📋 WordPress Publishing: {review_input['publish_to_wordpress']}")
        print()
        
        print("🚀 Executing Complete Pipeline...")
        print("⏳ This may take 2-3 minutes for comprehensive research and content generation...")
        print()
        
        # Execute the complete pipeline
        start_time = datetime.now()
        result = await chain.ainvoke(review_input)
        end_time = datetime.now()
        
        processing_time = (end_time - start_time).total_seconds()
        
        print("📊 PIPELINE EXECUTION RESULTS")
        print("=" * 50)
        print(f"⏱️ Total Processing Time: {processing_time:.2f} seconds")
        print(f"📝 Content Length: {len(result.answer):,} characters")
        print(f"📏 Estimated Word Count: {len(result.answer.split()):,} words")
        print(f"🔗 Sources Found: {len(result.sources)}")
        print(f"📊 Confidence Score: {result.confidence_score:.3f}")
        print()
        
        # WordPress Publishing Results
        wp_published = result.metadata.get('wordpress_published', False)
        print("🌐 WORDPRESS PUBLISHING RESULTS")
        print("=" * 40)
        
        if wp_published:
            print("✅ WordPress Publishing: SUCCESS")
            print(f"   🆔 Post ID: {result.metadata.get('wordpress_post_id', 'N/A')}")
            print(f"   🔗 Live URL: {result.metadata.get('wordpress_url', 'N/A')}")
            print(f"   ✏️ Edit URL: {result.metadata.get('wordpress_edit_url', 'N/A')}")
            print(f"   📋 Categories: {len(result.metadata.get('wordpress_categories', []))} applied")
            print(f"   🏷️ Tags: {len(result.metadata.get('wordpress_tags', []))} applied")
            print(f"   📊 Custom Fields: {result.metadata.get('wordpress_custom_fields_count', 0)} created")
            print(f"   📝 Title: {result.metadata.get('wordpress_title', 'N/A')}")
        else:
            print("❌ WordPress Publishing: FAILED")
            print(f"   🚨 Error: {result.metadata.get('wordpress_error', 'Unknown error')}")
        
        print()
        
        # Content Analysis
        print("📄 CONTENT ANALYSIS")
        print("=" * 30)
        
        content_preview = result.answer[:500] if len(result.answer) > 500 else result.answer
        print(f"Content Preview (first 500 chars):\n{content_preview}...")
        print()
        
        # Check for HTML formatting
        has_html = '<h1>' in result.answer or '<h2>' in result.answer or '<p>' in result.answer
        print(f"🔧 HTML Formatting: {'✅ Detected' if has_html else '❌ Missing'}")
        
        # Check for raw answer format (should be cleaned)
        has_raw_format = 'answer="' in result.answer
        print(f"🧹 Content Cleaning: {'❌ Raw format detected' if has_raw_format else '✅ Clean HTML'}")
        
        # Check for CoinFlip indicators
        has_coinflip = 'coinflip-casino-data' in result.answer or 'mt-casino-listing' in result.answer
        print(f"🎰 CoinFlip Integration: {'✅ Embedded' if has_coinflip else '❌ Missing'}")
        
        print()
        
        # Source Analysis
        if result.sources:
            print("🔗 RESEARCH SOURCES")
            print("=" * 25)
            for i, source in enumerate(result.sources[:5], 1):  # Show first 5 sources
                title = source.get('title', 'No title')
                url = source.get('url', 'No URL')
                source_type = source.get('type', 'unknown')
                print(f"   {i}. [{source_type}] {title}")
                print(f"      🔗 {url}")
            
            if len(result.sources) > 5:
                print(f"   ... and {len(result.sources) - 5} more sources")
            print()
        
        # Metadata Summary
        print("📊 METADATA SUMMARY")
        print("=" * 25)
        
        metadata_keys = [
            'contextual_retrieval_used', 'template_system_v2_used', 
            'dataforseo_images_used', 'web_research_count',
            'processing_time_ms', 'token_usage'
        ]
        
        for key in metadata_keys:
            if key in result.metadata:
                value = result.metadata[key]
                print(f"   {key.replace('_', ' ').title()}: {value}")
        
        print()
        
        # Success Summary
        word_count = len(result.answer.split())
        target_met = word_count >= 2500
        
        print("🎉 EXECUTION SUMMARY")
        print("=" * 30)
        print(f"✅ Pipeline Execution: SUCCESS")
        print(f"📏 Word Count Target: {'✅ MET' if target_met else '❌ MISSED'} ({word_count:,}/2,500)")
        print(f"📝 WordPress Publishing: {'✅ SUCCESS' if wp_published else '❌ FAILED'}")
        print(f"🧹 Content Processing: {'✅ CLEAN' if not has_raw_format else '❌ NEEDS FIXING'}")
        print(f"🎰 CoinFlip Integration: {'✅ ACTIVE' if has_coinflip else '❌ INACTIVE'}")
        
        if wp_published and result.metadata.get('wordpress_url'):
            print(f"\n🚀 LIVE REVIEW URL: {result.metadata['wordpress_url']}")
        
        # Save detailed results to file
        output_file = f"arrise_casino_review_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# Arrise Casino Review - Complete Pipeline Results\n\n")
            f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Processing Time**: {processing_time:.2f} seconds\n")
            f.write(f"**Word Count**: {word_count:,} words\n")
            f.write(f"**Sources**: {len(result.sources)}\n")
            f.write(f"**Confidence**: {result.confidence_score:.3f}\n\n")
            
            if wp_published:
                f.write(f"**Published**: {result.metadata.get('wordpress_url', 'N/A')}\n")
                f.write(f"**Post ID**: {result.metadata.get('wordpress_post_id', 'N/A')}\n\n")
            
            f.write(f"## Generated Content\n\n{result.answer}\n\n")
            
            f.write(f"## Sources Used\n\n")
            for i, source in enumerate(result.sources, 1):
                f.write(f"{i}. **{source.get('title', 'No title')}**\n")
                f.write(f"   - URL: {source.get('url', 'No URL')}\n")
                f.write(f"   - Type: {source.get('type', 'unknown')}\n\n")
            
            f.write(f"## Metadata\n\n")
            for key, value in result.metadata.items():
                f.write(f"- **{key}**: {value}\n")
        
        print(f"\n📄 Detailed results saved to: {output_file}")
        
        return {
            "success": True,
            "word_count": word_count,
            "wordpress_published": wp_published,
            "wordpress_url": result.metadata.get('wordpress_url'),
            "processing_time": processing_time,
            "content_clean": not has_raw_format,
            "coinflip_integrated": has_coinflip,
            "sources_count": len(result.sources),
            "confidence_score": result.confidence_score
        }
        
    except Exception as e:
        print(f"❌ Pipeline execution failed: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e)
        }

if __name__ == "__main__":
    print("🎰 Arrise Casino Complete Pipeline Test")
    print("Starting comprehensive review generation with all features...")
    print()
    
    result = asyncio.run(run_comprehensive_arrise_review())
    
    if result["success"]:
        print(f"\n🎉 PIPELINE COMPLETED SUCCESSFULLY!")
        print(f"📊 Generated {result['word_count']:,} words")
        if result["wordpress_published"]:
            print(f"🔗 Live at: {result['wordpress_url']}")
        print(f"⏱️ Total time: {result['processing_time']:.2f}s")
    else:
        print(f"\n💥 PIPELINE FAILED: {result['error']}")
        sys.exit(1)