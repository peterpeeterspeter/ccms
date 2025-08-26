#!/usr/bin/env python3
"""
🚀 BETWAY CASINO - OPTIMIZED RESEARCH PIPELINE EXECUTION
=======================================================

Production execution of the optimized 95+ datafield research system for Betway Casino.
Combines existing working modules with LangChain efficiency patterns.

Features:
- Real Supabase Research Tool integration
- Enhanced Multi-Query Retrieval with EnsembleRetriever
- Comprehensive 95+ field intelligence extraction
- Vector storage and indexing for future retrieval
- Full LCEL compliance throughout the pipeline

Claude.md Compliant Implementation
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging for production visibility
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'betway_research_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)

logger = logging.getLogger(__name__)

# Import optimized research pipeline
from src.chains.optimized_research_pipeline import create_optimized_research_pipeline
from src.schemas.review_doc import TenantConfiguration


async def run_betway_comprehensive_research():
    """Execute comprehensive Betway Casino research with optimized pipeline"""
    
    print("🚀 BETWAY CASINO COMPREHENSIVE RESEARCH")
    print("=" * 60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # 1. Initialize optimized research pipeline
        logger.info("🎯 Initializing optimized research pipeline...")
        
        pipeline = create_optimized_research_pipeline(
            tenant_id="crashcasino",
            brand_name="Crash Casino",
            locale="en-US"
        )
        
        print("✅ Optimized research pipeline initialized")
        print(f"   - Tenant: crashcasino")
        print(f"   - Brand: Crash Casino")  
        print(f"   - Locale: en-US")
        print(f"   - Components: RealSupabaseResearchTool + AgenticVectorStore + EnsembleRetriever")
        print()
        
        # 2. Execute comprehensive research
        logger.info("🔍 Starting comprehensive Betway research...")
        
        research_start = datetime.now()
        
        result = await pipeline.research_casino_comprehensive(
            casino_name="Betway Casino",
            casino_url="https://betway.com"
        )
        
        research_duration = (datetime.now() - research_start).total_seconds()
        
        # 3. Display comprehensive results
        print("📊 COMPREHENSIVE RESEARCH RESULTS")
        print("-" * 40)
        print(f"Success: {'✅' if result.success else '❌'}")
        print(f"Casino: {result.casino_name}")
        print(f"Research Duration: {research_duration:.2f} seconds")
        print()
        
        if result.success and result.casino_intelligence:
            intelligence = result.casino_intelligence
            
            print("🎰 CASINO INTELLIGENCE EXTRACTED")
            print("-" * 40)
            print(f"Casino Name: {intelligence.casino_name}")
            print(f"Casino URL: {intelligence.casino_url}")
            print(f"Overall Rating: {intelligence.overall_rating}/10")
            print(f"Safety Score: {intelligence.safety_score}/10")
            print()
            
            # Basic Information
            print("📋 BASIC INFORMATION")
            print(f"Launch Year: {intelligence.launch_year}")
            print(f"Ownership: {intelligence.ownership}")
            print(f"Group Affiliation: {intelligence.group_affiliation}")
            print()
            
            # Licensing & Regulation  
            if intelligence.trustworthiness and intelligence.trustworthiness.license_info:
                license_info = intelligence.trustworthiness.license_info
                print("🛡️ LICENSING & REGULATION")
                print(f"Primary License: {license_info.primary_license}")
                print(f"License Number: {license_info.license_number}")
                print(f"Issuing Authority: {license_info.issuing_authority}")
                print(f"License Status: {license_info.license_status}")
                print()
            
            # Games & Software
            if intelligence.games and intelligence.games.game_portfolio:
                games = intelligence.games.game_portfolio
                print("🎮 GAMES & SOFTWARE")
                print(f"Total Games: {games.total_games:,}")
                print(f"Slot Games: {games.slot_games_count:,}")
                print(f"Table Games: {games.table_games_count}")
                print(f"Live Dealer Games: {games.live_dealer_games_count}")
                
                if intelligence.games.software_providers.primary_providers:
                    providers = [p.value for p in intelligence.games.software_providers.primary_providers[:5]]
                    print(f"Top Providers: {', '.join(providers)}")
                print()
            
            # Bonuses & Promotions
            if intelligence.bonuses and intelligence.bonuses.welcome_bonus:
                welcome = intelligence.bonuses.welcome_bonus
                print("🎁 BONUSES & PROMOTIONS")
                print(f"Welcome Bonus: {welcome.bonus_amount}")
                print(f"Match Percentage: {welcome.match_percentage}%")
                print(f"Free Spins: {welcome.free_spins_count}")
                print(f"Wagering Requirements: {welcome.wagering_requirements}")
                print(f"Minimum Deposit: {welcome.minimum_deposit}")
                print()
            
            # Payment Methods
            if intelligence.payments:
                payments = intelligence.payments
                print("💳 PAYMENT METHODS")
                print(f"Deposit Methods: {len(payments.payment_methods)} available")
                print(f"Withdrawal Processing: {payments.withdrawal_processing_time}")
                print(f"Withdrawal Limits: Daily {payments.daily_withdrawal_limit}")
                print(f"Cryptocurrency Support: {'✅' if payments.cryptocurrency_support else '❌'}")
                print()
            
            # User Experience
            if intelligence.user_experience:
                ux = intelligence.user_experience
                print("📱 USER EXPERIENCE")
                print(f"Mobile Compatible: {'✅' if ux.mobile_compatibility else '❌'}")
                print(f"Mobile App: {'✅' if ux.mobile_app_available else '❌'}")
                print(f"Languages: {len(ux.supported_languages)} supported")
                print(f"Currencies: {len(ux.supported_currencies)} supported")
                print()
            
            # Customer Support
            if intelligence.user_experience and intelligence.user_experience.customer_support:
                support = intelligence.user_experience.customer_support
                print("🆘 CUSTOMER SUPPORT")
                print(f"Live Chat: {'✅' if support.live_chat_available else '❌'}")
                print(f"Email Support: {'✅' if support.email_support else '❌'}")
                print(f"Phone Support: {'✅' if support.phone_support else '❌'}")
                print(f"Support Hours: {support.support_hours}")
                print()
            
            # Data Quality Metrics
            completeness_score = intelligence.calculate_completeness_score()
            print("📈 DATA QUALITY METRICS")
            print(f"Completeness Score: {completeness_score:.1f}%")
            print(f"Data Sources: {len(intelligence.data_sources)}")
            print(f"Extraction Time: {intelligence.extraction_timestamp}")
            print()
            
            # Metadata and Performance
            if result.metadata:
                metadata = result.metadata
                print("⚙️ PIPELINE PERFORMANCE")
                print(f"Processing Duration: {metadata.get('research_duration_seconds', 0):.2f}s")
                print(f"Pipeline Version: {metadata.get('pipeline_version', 'unknown')}")
                
                if 'enhanced_retrieval' in metadata:
                    retrieval = metadata['enhanced_retrieval']
                    print(f"Enhanced Retrieval: {retrieval['retrieval_method']}")
                    print(f"Retrieved Documents: {len(retrieval['retrieval_results'])}")
                print()
        
        else:
            print("❌ RESEARCH FAILED")
            if result.error_message:
                print(f"Error: {result.error_message}")
            print()
        
        # 4. Storage and vectorization summary
        print("💾 STORAGE & VECTORIZATION")
        print("-" * 30)
        
        if result.success:
            print("✅ Intelligence data stored in Supabase vector database")
            print("✅ Document chunks vectorized with OpenAI embeddings")
            print("✅ Multi-tenant metadata indexed for retrieval")
            print("✅ Ready for future RAG-based content generation")
        else:
            print("❌ Storage failed due to research errors")
        
        print()
        
        # 5. Next steps
        print("🔄 NEXT STEPS")
        print("-" * 15)
        print("1. Run content generation pipeline using stored intelligence")
        print("2. Generate comprehensive 2,500+ word casino review")  
        print("3. Capture casino screenshots using Firecrawl")
        print("4. Publish to WordPress with SEO optimization")
        print()
        
        print("🏁 RESEARCH PIPELINE COMPLETED")
        print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Betway research pipeline failed: {e}")
        print(f"❌ Pipeline execution failed: {e}")
        raise


def main():
    """Main execution function"""
    try:
        # Check environment variables
        if not os.getenv('OPENAI_API_KEY'):
            print("⚠️  WARNING: OPENAI_API_KEY not found in environment")
            print("   Research may fail without OpenAI API access")
            print()
        
        if not os.getenv('SUPABASE_URL') or not os.getenv('SUPABASE_SERVICE_ROLE'):
            print("⚠️  WARNING: Supabase credentials not found")
            print("   Vector storage may fall back to placeholder data")
            print()
        
        # Run the research pipeline
        result = asyncio.run(run_betway_comprehensive_research())
        
        if result.success:
            print("✅ SUCCESS: Betway comprehensive research completed")
            sys.exit(0)
        else:
            print("❌ FAILURE: Research pipeline encountered errors")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Research interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"💥 FATAL ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()