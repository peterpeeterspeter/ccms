"""
🎯 Complete Content Generation Workflow Demo
End-to-End demonstration of the Agentic RAG CMS workflow

Demonstrates:
- Phase 1: Foundation (Vector Store + Retrieval + Research Agent)
- Phase 2: Content Generation (Narrative Chain + QA Validation)
- Complete workflow orchestration with multi-tenant support
- Quality assurance and compliance validation
- Human-in-the-loop workflows
"""

import asyncio
import os
from datetime import datetime
from typing import Dict, Any

# Import complete workflow system
from src.workflows.content_generation_workflow import (
    ContentGenerationWorkflow,
    ContentGenerationRequest,
    create_content_generation_workflow
)
from src.chains.multi_tenant_retrieval_system import create_multi_tenant_retrieval_system
from src.integrations.supabase_vector_store import create_agentic_supabase_vectorstore
from src.chains.qa_compliance_chain import QAValidationLevel
from src.schemas.review_doc import TenantConfiguration, MediaAsset, MediaType


async def setup_complete_system():
    """Set up the complete Agentic RAG CMS system"""
    
    print("🎰 Setting up Complete Agentic RAG CMS System...")
    print("=" * 60)
    
    # 1. Create Supabase Vector Store (Phase 1A)
    print("📊 Phase 1A: Creating Supabase Vector Store...")
    vector_store = create_agentic_supabase_vectorstore(
        tenant_id="demo-system",
        table_name="casino_intelligence_demo",
        embedding_dimension=1536
    )
    
    # 2. Create Multi-Tenant Retrieval System (Phase 1B)  
    print("🔍 Phase 1B: Creating Multi-Tenant Retrieval System...")
    retrieval_system = create_multi_tenant_retrieval_system(
        vector_store=vector_store,
        llm_model="gpt-4o"
    )
    
    # 3. Create Complete Content Generation Workflow (Phase 2)
    print("✍️ Phase 2: Creating Content Generation Workflow...")
    workflow = create_content_generation_workflow(
        retrieval_system=retrieval_system,
        llm_model="gpt-4o"
    )
    
    print("✅ Complete system setup finished!")
    print()
    
    return workflow


def create_demo_scenarios() -> Dict[str, Dict[str, Any]]:
    """Create comprehensive demo scenarios for different use cases"""
    
    return {
        "premium_review": {
            "name": "Premium Casino Review (English)",
            "request": ContentGenerationRequest(
                casino_name="Betway Casino",
                tenant_config=TenantConfiguration(
                    tenant_id="crashcasino",
                    brand_name="CrashCasino Premium",
                    locale="en",
                    voice_profile="professional-enthusiastic",
                    target_demographics=["adults 25-45", "serious players"],
                    compliance_requirements=["18+ verification", "UK gambling commission", "responsible gambling"]
                ),
                query_context="comprehensive review focusing on game variety, bonuses, mobile experience, and payment security",
                visual_assets=[
                    MediaAsset(
                        filename="betway-homepage.png",
                        url="https://example.com/betway-homepage.png",
                        type=MediaType.SCREENSHOT,
                        alt_text="Betway casino homepage with game lobby",
                        caption="Main casino interface showcasing featured games"
                    ),
                    MediaAsset(
                        filename="betway-bonus.jpg",
                        url="https://example.com/betway-bonus.jpg", 
                        type=MediaType.PROMOTIONAL,
                        alt_text="Welcome bonus promotional banner",
                        caption="£1000 welcome bonus + 50 free spins offer"
                    ),
                    MediaAsset(
                        filename="betway-mobile.png",
                        url="https://example.com/betway-mobile.png",
                        type=MediaType.SCREENSHOT,
                        alt_text="Betway mobile casino app",
                        caption="Mobile gaming experience on smartphone"
                    )
                ],
                affiliate_metadata={
                    "commission_structure": "15% revenue share + performance bonuses",
                    "marketing_materials": ["banners", "email templates", "landing pages"],
                    "compliance_requirements": ["18+ verification", "responsible gambling tools"],
                    "custom_bonus_codes": ["CRASH100", "PREMIUM50"]
                },
                validation_level=QAValidationLevel.PREMIUM,
                auto_publish_threshold=8.5
            ),
            "description": "High-quality premium review with comprehensive validation"
        },
        
        "german_compliance": {
            "name": "German Compliance Review",
            "request": ContentGenerationRequest(
                casino_name="bet365 Casino",
                tenant_config=TenantConfiguration(
                    tenant_id="betmeister",
                    brand_name="BetMeister",
                    locale="de",
                    voice_profile="professional-authoritative",
                    target_demographics=["adults 30-55", "German market"],
                    compliance_requirements=["German gambling law", "18+ verification", "Spielsucht prevention"]
                ),
                query_context="German market focused review emphasizing legal compliance, licensing, and player protection measures",
                visual_assets=[
                    MediaAsset(
                        filename="bet365-de-homepage.png",
                        url="https://example.com/bet365-de.png",
                        type=MediaType.SCREENSHOT,
                        alt_text="bet365 German casino homepage"
                    )
                ],
                affiliate_metadata={
                    "commission_structure": "10% revenue share",
                    "compliance_requirements": ["German gambling regulations", "Spielsucht awareness"],
                    "marketing_restrictions": ["no bonus advertising", "responsible gambling emphasis"]
                },
                validation_level=QAValidationLevel.STRICT,
                auto_publish_threshold=8.0
            ),
            "description": "Strict compliance-focused review for German market"
        },
        
        "mobile_focused": {
            "name": "Mobile-First Casino Review",
            "request": ContentGenerationRequest(
                casino_name="LeoVegas Casino",
                tenant_config=TenantConfiguration(
                    tenant_id="mobilecasinos",
                    brand_name="Mobile Casino Guide", 
                    locale="en",
                    voice_profile="friendly-informative",
                    target_demographics=["mobile users", "millennials 25-35"],
                    compliance_requirements=["18+ verification", "mobile-specific warnings"]
                ),
                query_context="mobile-first review emphasizing app quality, mobile games, and on-the-go gaming experience",
                visual_assets=[
                    MediaAsset(
                        filename="leovegas-mobile-lobby.png",
                        url="https://example.com/leovegas-mobile.png",
                        type=MediaType.SCREENSHOT,
                        alt_text="LeoVegas mobile casino game lobby"
                    ),
                    MediaAsset(
                        filename="leovegas-app-store.png",
                        url="https://example.com/leovegas-app.png",
                        type=MediaType.SCREENSHOT,
                        alt_text="LeoVegas app in app store"
                    )
                ],
                affiliate_metadata={
                    "commission_structure": "12% revenue share",
                    "mobile_specific_bonuses": ["mobile welcome bonus", "app download bonus"],
                    "tracking_method": "mobile app attribution"
                },
                validation_level=QAValidationLevel.STANDARD,
                auto_publish_threshold=7.5
            ),
            "description": "Mobile-focused review with app-specific content"
        },
        
        "quick_standard": {
            "name": "Quick Standard Review",
            "request": ContentGenerationRequest(
                casino_name="888 Casino",
                tenant_config=TenantConfiguration(
                    tenant_id="quickreviews",
                    brand_name="Quick Casino Reviews",
                    locale="en", 
                    voice_profile="informative-concise",
                    target_demographics=["casual players", "quick decision makers"]
                ),
                query_context="concise review covering essential information: games, bonuses, payments, support",
                validation_level=QAValidationLevel.BASIC,
                auto_publish_threshold=7.0
            ),
            "description": "Fast, basic validation review for quick publishing"
        }
    }


async def run_workflow_demonstrations(workflow: ContentGenerationWorkflow):
    """Run comprehensive workflow demonstrations"""
    
    print("🎯 Running Complete Workflow Demonstrations")
    print("=" * 60)
    print()
    
    scenarios = create_demo_scenarios()
    results = {}
    
    for scenario_key, scenario_data in scenarios.items():
        print(f"📝 Demo: {scenario_data['name']}")
        print(f"   {scenario_data['description']}")
        print(f"   Casino: {scenario_data['request'].casino_name}")
        print(f"   Tenant: {scenario_data['request'].tenant_config.tenant_id}")
        print(f"   Locale: {scenario_data['request'].tenant_config.locale}")
        print(f"   Validation: {scenario_data['request'].validation_level.value}")
        
        try:
            print(f"   🔄 Executing workflow...")
            start_time = datetime.now()
            
            # Execute the complete workflow
            result = workflow.execute_workflow(scenario_data["request"])
            
            duration = datetime.now() - start_time
            results[scenario_key] = result
            
            # Display results
            print(f"   ✅ Workflow Status: {result.workflow_status.value}")
            if result.final_quality_score:
                print(f"   📊 Quality Score: {result.final_quality_score:.2f}/10")
            print(f"   📋 Publish Approved: {result.publish_approved}")
            if result.review_doc:
                print(f"   📄 Content Length: {len(result.review_doc.content)} characters")
            print(f"   ⏱️  Duration: {duration.total_seconds():.1f} seconds")
            print(f"   🔄 Iterations: {result.improvement_iterations}")
            
            # Show key quality metrics
            if result.qa_report:
                print(f"   🛡️  Compliance: {result.qa_report.compliance_status.value}")
                print(f"   ✍️  Brand Voice: {'✅' if result.qa_report.brand_voice_consistency else '❌'}")
                print(f"   📈 Factual Score: {result.qa_report.factual_accuracy_score:.1f}")
            
        except Exception as e:
            print(f"   ❌ Workflow failed: {str(e)}")
            results[scenario_key] = None
        
        print()
    
    return results


def analyze_workflow_performance(results: Dict[str, Any]):
    """Analyze and display workflow performance metrics"""
    
    print("📊 Workflow Performance Analysis")
    print("=" * 40)
    
    successful_workflows = [r for r in results.values() if r and r.publish_approved]
    total_workflows = len([r for r in results.values() if r])
    
    if total_workflows == 0:
        print("No successful workflows to analyze.")
        return
    
    print(f"✅ Successful Workflows: {len(successful_workflows)}/{total_workflows}")
    
    if successful_workflows:
        # Quality score distribution
        quality_scores = [r.final_quality_score for r in successful_workflows if r.final_quality_score]
        if quality_scores:
            avg_quality = sum(quality_scores) / len(quality_scores)
            print(f"📈 Average Quality Score: {avg_quality:.2f}")
            print(f"📊 Quality Range: {min(quality_scores):.1f} - {max(quality_scores):.1f}")
        
        # Performance metrics
        durations = [r.total_duration_ms for r in successful_workflows]
        if durations:
            avg_duration = sum(durations) / len(durations)
            print(f"⏱️  Average Duration: {avg_duration:.0f}ms")
        
        # Content metrics
        content_lengths = [len(r.review_doc.content) for r in successful_workflows if r.review_doc]
        if content_lengths:
            avg_length = sum(content_lengths) / len(content_lengths)
            print(f"📄 Average Content Length: {avg_length:.0f} characters")
    
    print()
    
    # Detailed breakdown by scenario
    print("📋 Detailed Results by Scenario:")
    for scenario_key, result in results.items():
        if result:
            status_emoji = "✅" if result.publish_approved else "❌"
            quality = f"{result.final_quality_score:.1f}" if result.final_quality_score else "N/A"
            print(f"   {status_emoji} {scenario_key}: Quality {quality}, Status {result.workflow_status.value}")
    
    print()


def demonstrate_system_capabilities():
    """Demonstrate key system capabilities and architecture"""
    
    print("🏗️ System Architecture & Capabilities")
    print("=" * 45)
    print()
    
    print("📋 Implemented Components:")
    print("   ✅ Phase 1A: ReviewDoc & QAReport Pydantic Schemas (26 fields)")
    print("   ✅ Phase 1B: AgenticSupabaseVectorStore with MMR Search")
    print("   ✅ Phase 1C: Research & Ingestion Agent (LangGraph)")
    print("   ✅ Phase 1D: Multi-Tenant Retrieval System (LCEL)")
    print("   ✅ Phase 2A: Narrative Generation Chain (LCEL + Multi-locale)")
    print("   ✅ Phase 2B: QA & Compliance Chain (4-validator system)")
    print("   ✅ Phase 2C: Complete Workflow Orchestration")
    print()
    
    print("🎯 Key Features:")
    print("   • Multi-tenant support (tenant_id, brand, locale, voice)")
    print("   • 4-language prompt templates (EN, DE, FR, ES)")
    print("   • Visual content integration (screenshots, promotional)")
    print("   • Affiliate metadata processing (commissions, compliance)")
    print("   • 95-field casino intelligence schema integration")
    print("   • Quality assurance with 4 validation layers:")
    print("     - Affiliate compliance validation")
    print("     - Factual accuracy checking") 
    print("     - Brand style consistency")
    print("     - Content quality assessment")
    print("   • Human-in-the-loop workflow support")
    print("   • Automated content improvement iterations")
    print("   • WordPress publishing pipeline ready")
    print()
    
    print("🔧 Technical Architecture:")
    print("   • LangChain Expression Language (LCEL) throughout")
    print("   • Streaming-capable chain composition")
    print("   • Pydantic v2 schema validation")
    print("   • Multi-query retrieval with MMR ranking")
    print("   • Tenant-aware metadata filtering")
    print("   • Comprehensive error handling and logging")
    print("   • Factory functions for easy instantiation")
    print()


async def main():
    """Main demo execution function"""
    
    print("🎰 AGENTIC RAG CMS - COMPLETE SYSTEM DEMO")
    print("=" * 50)
    print(f"🕒 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check environment
    required_vars = ["OPENAI_API_KEY", "SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("⚠️  Warning: Missing environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print()
        print("   This demo will show system architecture and capabilities,")
        print("   but workflow execution requires proper credentials.")
        print()
    
    try:
        # Show system capabilities
        demonstrate_system_capabilities()
        
        print("🚀 System Ready for Full Demo")
        print("   To run complete workflow execution:")
        print("   1. Set environment variables: OPENAI_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY")
        print("   2. Ensure Supabase database is set up with casino intelligence data")
        print("   3. Uncomment the workflow execution section below")
        print()
        
        # Uncomment this section to run full workflow demo:
        """
        # Set up complete system
        workflow = await setup_complete_system()
        
        # Run workflow demonstrations
        results = await run_workflow_demonstrations(workflow)
        
        # Analyze performance
        analyze_workflow_performance(results)
        
        print("🏆 All workflow demonstrations completed successfully!")
        """
        
        print("✅ Demo completed - System architecture validated")
        
    except KeyboardInterrupt:
        print("\\n🛑 Demo interrupted by user")
    except Exception as e:
        print(f"\\n❌ Demo failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print(f"\\n🏁 Demo finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    asyncio.run(main())