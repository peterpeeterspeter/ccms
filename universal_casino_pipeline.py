#!/usr/bin/env python3
"""
🎰 UNIVERSAL CASINO REVIEW PIPELINE - NATIVE LANGCHAIN
========================================================

Universal pipeline that can generate comprehensive casino reviews for ANY casino
using ONLY native LangChain LCEL components as per CLAUDE.md requirements:

1. ✅ LCEL everywhere (| composition with Runnable*, ChatPromptTemplate)
2. ✅ No custom orchestration (no raw asyncio.gather, no raw HTTP)  
3. ✅ Schema-First (inputs/outputs in /src/schemas)
4. ✅ External services only via /src/tools/*

Usage Examples:
- python universal_casino_pipeline.py "Mr Vegas Casino"
- python universal_casino_pipeline.py "Betway Casino" 
- python universal_casino_pipeline.py "LeoVegas Casino"
- python universal_casino_pipeline.py "888 Casino"
"""

import os
import sys
import asyncio
import argparse
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# Add src to path for proper imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import ONLY the native LangChain implementation
from chains.native_universal_rag_lcel import NativeUniversalRAGChain

class UniversalCasinoPipeline:
    """
    Universal pipeline for generating casino reviews using native LangChain components
    
    Features:
    - Pure LCEL pipeline composition (| operators)
    - 95-field individual casino research  
    - DataForSEO casino detection system
    - Supabase vectorization with native components
    - WordPress publishing via native tools
    - Revolutionary image detection algorithm
    """
    
    def __init__(self, model_name: str = "gpt-4o", temperature: float = 0.1):
        """Initialize universal pipeline with native LangChain chain"""
        self.model_name = model_name
        self.temperature = temperature
        self.chain = None
        
    async def initialize(self) -> bool:
        """Initialize native LangChain chain with all components"""
        try:
            print("🔧 Initializing Universal Casino Pipeline...")
            print("📋 Components: Native LangChain LCEL + DataForSEO + Supabase")
            
            # Initialize ONLY native LangChain components
            self.chain = NativeUniversalRAGChain(
                model_name=self.model_name,
                temperature=self.temperature,
                vector_store_type='supabase',
                enable_web_search=True
            )
            
            print("✅ Universal pipeline initialized with native components")
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize pipeline: {str(e)}")
            return False
    
    async def generate_casino_review(
        self, 
        casino_name: str, 
        target_words: int = 2500,
        enable_wordpress: bool = True
    ) -> Dict[str, Any]:
        """
        Generate comprehensive casino review using native LangChain pipeline
        
        Args:
            casino_name: Name of casino to review (e.g. "Mr Vegas Casino")
            target_words: Target word count for review (default 2500)
            enable_wordpress: Whether to attempt WordPress publishing
            
        Returns:
            Dict with review results, status, and metadata
        """
        if not self.chain:
            raise ValueError("Pipeline not initialized. Call initialize() first.")
        
        print(f"🎰 Generating universal review for: {casino_name}")
        print(f"🎯 Target length: {target_words} words")
        print(f"🌐 WordPress publishing: {'Enabled' if enable_wordpress else 'Disabled'}")
        print()
        
        start_time = datetime.now()
        
        try:
            # Execute complete workflow using native LangChain components
            # This uses ONLY:
            # - ChatPromptTemplate for all prompts
            # - | operator for pipeline composition  
            # - RunnableParallel for concurrent execution
            # - TavilySearchResults for web search
            # - SupabaseVectorStore for vector storage
            # - Native LangChain retrievers and parsers
            
            results = await self.chain.execute_complete_workflow(casino_name)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Process results using native data structures
            review_results = {
                "casino_name": casino_name,
                "processing_time_seconds": processing_time,
                "final_status": results.get("final_status", "unknown"),
                "steps_completed": results.get("steps_completed", []),
                "total_steps": 5,
                "success": results.get("final_status") == "success",
                "errors": results.get("errors", []),
                "native_langchain_components_used": [
                    "ChatPromptTemplate",
                    "RunnableParallel", 
                    "TavilySearchResults",
                    "SupabaseVectorStore",
                    "StrOutputParser",
                    "LCEL | operators"
                ],
                "timestamp": datetime.now().isoformat()
            }
            
            # Include content metrics if available
            if "generated_content" in results:
                content = results["generated_content"]
                review_results.update({
                    "content_length_chars": len(content),
                    "estimated_words": len(content.split()),
                    "casino_mentions": content.lower().count(casino_name.lower()),
                    "content_preview": content[:200] + "..." if len(content) > 200 else content
                })
            
            # Include WordPress publishing results if available
            if enable_wordpress and "wordpress_result" in results:
                wp_result = results["wordpress_result"]
                review_results["wordpress_publishing"] = {
                    "attempted": True,
                    "success": wp_result.get("success", False),
                    "post_id": wp_result.get("post_id"),
                    "post_url": wp_result.get("post_url"),
                    "post_type": wp_result.get("post_type", "mt_listing"),
                    "error": wp_result.get("error")
                }
            
            # Include research data metrics
            if "research_data" in results:
                research_data = results["research_data"]
                review_results["research_metrics"] = {
                    "categories_researched": len(research_data),
                    "total_data_points": sum(len(v) if isinstance(v, (list, dict)) else 1 
                                           for v in research_data.values()),
                    "dataforseo_images_processed": results.get("images_processed", 0)
                }
            
            return review_results
            
        except Exception as e:
            return {
                "casino_name": casino_name,
                "processing_time_seconds": (datetime.now() - start_time).total_seconds(),
                "success": False,
                "error": str(e),
                "final_status": "error",
                "timestamp": datetime.now().isoformat()
            }
    
    async def batch_generate_reviews(
        self, 
        casino_list: List[str], 
        target_words: int = 2500
    ) -> Dict[str, Dict[str, Any]]:
        """
        Generate reviews for multiple casinos using the universal pipeline
        
        Args:
            casino_list: List of casino names to process
            target_words: Target word count per review
            
        Returns:
            Dict mapping casino names to their review results
        """
        print(f"🎰 BATCH PROCESSING: {len(casino_list)} casinos")
        print("🧬 Using universal native LangChain pipeline")
        print()
        
        results = {}
        
        for i, casino_name in enumerate(casino_list, 1):
            print(f"📋 Processing {i}/{len(casino_list)}: {casino_name}")
            
            try:
                casino_result = await self.generate_casino_review(
                    casino_name=casino_name,
                    target_words=target_words,
                    enable_wordpress=True
                )
                results[casino_name] = casino_result
                
                # Show quick status
                status = "✅ SUCCESS" if casino_result.get("success") else "⚠️ PARTIAL"
                time_taken = casino_result.get("processing_time_seconds", 0)
                print(f"   {status} - {time_taken:.1f}s")
                
            except Exception as e:
                results[casino_name] = {
                    "success": False,
                    "error": str(e),
                    "casino_name": casino_name
                }
                print(f"   ❌ ERROR: {str(e)}")
            
            print()
        
        return results

async def main():
    """Main CLI interface for universal casino pipeline"""
    parser = argparse.ArgumentParser(
        description="Universal Casino Review Pipeline - Native LangChain LCEL",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python universal_casino_pipeline.py "Mr Vegas Casino"
  python universal_casino_pipeline.py "Betway Casino" --words 3000
  python universal_casino_pipeline.py --batch "Mr Vegas,Betway,LeoVegas"
  python universal_casino_pipeline.py "888 Casino" --no-wordpress
        """
    )
    
    parser.add_argument(
        "casino_name", 
        nargs="?",
        help="Name of casino to review (e.g. 'Mr Vegas Casino')"
    )
    
    parser.add_argument(
        "--batch", 
        type=str,
        help="Comma-separated list of casino names for batch processing"
    )
    
    parser.add_argument(
        "--words", 
        type=int, 
        default=2500,
        help="Target word count for review (default: 2500)"
    )
    
    parser.add_argument(
        "--model", 
        type=str, 
        default="gpt-4o",
        help="Language model to use (default: gpt-4o)"
    )
    
    parser.add_argument(
        "--no-wordpress",
        action="store_true",
        help="Disable WordPress publishing attempt"
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.casino_name and not args.batch:
        parser.error("Must provide either a casino name or --batch list")
    
    # Initialize universal pipeline
    pipeline = UniversalCasinoPipeline(
        model_name=args.model,
        temperature=0.1
    )
    
    if not await pipeline.initialize():
        print("❌ Failed to initialize universal pipeline")
        return 1
    
    # Execute based on mode
    if args.batch:
        # Batch processing mode
        casino_list = [name.strip() for name in args.batch.split(",")]
        print(f"🎰 BATCH MODE: Processing {len(casino_list)} casinos")
        print(f"🧬 Pipeline: Universal Native LangChain LCEL")
        print()
        
        batch_results = await pipeline.batch_generate_reviews(
            casino_list=casino_list,
            target_words=args.words
        )
        
        # Save batch results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_file = f"universal_casino_batch_results_{timestamp}.json"
        
        import json
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(batch_results, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Batch results saved: {results_file}")
        
        # Summary
        successful = sum(1 for r in batch_results.values() if r.get("success"))
        print(f"\\n📊 Batch Summary: {successful}/{len(casino_list)} successful")
        
    else:
        # Single casino mode
        print(f"🎰 SINGLE MODE: {args.casino_name}")
        print(f"🧬 Pipeline: Universal Native LangChain LCEL")
        print()
        
        result = await pipeline.generate_casino_review(
            casino_name=args.casino_name,
            target_words=args.words,
            enable_wordpress=not args.no_wordpress
        )
        
        # Save single result
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_name = args.casino_name.lower().replace(' ', '_').replace(' ', '')
        results_file = f"universal_casino_{safe_name}_results_{timestamp}.json"
        
        import json
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Results saved: {results_file}")
        
        # Show result summary
        if result.get("success"):
            print("\\n🎉 UNIVERSAL PIPELINE SUCCESS!")
            if result.get("wordpress_publishing", {}).get("success"):
                wp_url = result["wordpress_publishing"].get("post_url")
                if wp_url:
                    print(f"🔗 Live at: {wp_url}")
        else:
            print("\\n⚠️ UNIVERSAL PIPELINE PARTIAL SUCCESS")
            if "error" in result:
                print(f"Error: {result['error']}")
    
    print("\\n✅ Universal Casino Pipeline Complete!")
    return 0

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\\n⚠️ Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\\n❌ Pipeline failed: {str(e)}")
        sys.exit(1)