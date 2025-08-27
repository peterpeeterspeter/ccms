#!/usr/bin/env python3
"""
🎯 OPTIMIZED 95+ DATAFIELD RESEARCH PIPELINE - LCEL NATIVE
==========================================================

Production-ready research system combining existing modules with LangChain efficiency patterns:
- Real Supabase Research Tool (existing) for data retrieval
- Enhanced Multi-Query Retriever for comprehensive coverage
- EnsembleRetriever (BM25 + Vector) for maximum recall
- RunnableParallel for concurrent processing 
- Agentic Supabase Vector Store for intelligent indexing

Claude.md Compliance:
✅ Pure LCEL composition (|, RunnableParallel, RunnablePassthrough)
✅ Tools via /src/tools/* adapters only
✅ Pydantic v2 schemas for all I/O
✅ No custom orchestration outside LangChain
"""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

# LangChain LCEL core components
from langchain_core.runnables import RunnableParallel, RunnablePassthrough, RunnableLambda
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.retrievers import EnsembleRetriever, MultiQueryRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document

# Production tools (existing)
from ..tools.real_supabase_research_tool import RealSupabaseResearchTool
from ..integrations.supabase_vector_store import AgenticSupabaseVectorStore
from ..schemas.casino_intelligence_schema import CasinoIntelligence
from ..schemas.review_doc import TenantConfiguration

# Import agent components (existing)
from ..agents.research_agent import CasinoResearchAgent
from ..agents.research_ingestion_agent import ResearchIngestionAgent

# Define ResearchOutput schema
class ResearchOutput(BaseModel):
    """Output schema for comprehensive research pipeline"""
    success: bool = Field(description="Whether research was successful")
    casino_name: str = Field(description="Name of the researched casino")
    casino_intelligence: Optional[CasinoIntelligence] = Field(description="Structured 95+ field intelligence")
    error_message: Optional[str] = Field(description="Error message if research failed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Research metadata and metrics")

logger = logging.getLogger(__name__)


class OptimizedResearchPipeline:
    """
    🎯 OPTIMIZED RESEARCH PIPELINE WITH 95+ DATAFIELD INTELLIGENCE
    ==============================================================
    
    Features:
    - RunnableParallel for concurrent web research + database retrieval
    - EnsembleRetriever (BM25 + Vector) for comprehensive data coverage
    - MultiQueryRetriever for query expansion and comprehensive results
    - Real Supabase integration for production data persistence
    - Agentic vector store for intelligent document indexing
    - Pure LCEL composition throughout the pipeline
    """
    
    def __init__(self, tenant_config: TenantConfiguration):
        self.tenant_config = tenant_config
        
        # Initialize LLM with optimal settings for research
        self.llm = ChatOpenAI(
            model="gpt-4o",  # Full model for comprehensive analysis
            temperature=0.1,  # Low temperature for factual accuracy
            max_tokens=4000   # High token limit for detailed analysis
        )
        
        # Initialize embeddings for vector operations
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
        
        # Initialize text splitter optimized for casino content
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,    # Optimal for casino content analysis
            chunk_overlap=300,  # Higher overlap for context preservation
            length_function=len,
            separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""]
        )
        
        # Initialize production tools
        self.supabase_tool = RealSupabaseResearchTool()
        self.research_agent = CasinoResearchAgent()
        self.ingestion_agent = ResearchIngestionAgent(
            tenant_id=tenant_config.tenant_id,
            brand=tenant_config.brand_name,
            locale=tenant_config.locale
        )
        
        # Initialize vector store for intelligent indexing
        try:
            self.vector_store = AgenticSupabaseVectorStore()
        except Exception as e:
            logger.warning(f"⚠️ Vector store initialization failed: {e}")
            self.vector_store = None
        
        # Create the main research chain using LCEL
        self.research_chain = self._create_research_chain()
        
        logger.info(f"✅ Optimized Research Pipeline initialized for {tenant_config.brand_name}")
    
    def _create_research_chain(self):
        """Create optimized LCEL research chain with parallel processing"""
        
        # Research planning prompt
        research_prompt = ChatPromptTemplate.from_template("""
You are an expert casino intelligence researcher analyzing comprehensive data.

Target Casino: {casino_name}
Tenant: {tenant_id} | Brand: {brand} | Locale: {locale}

RESEARCH DATA:
Database Research: {database_research}
Web Research: {web_research} 
Vector Search Results: {vector_results}

TASK: Extract and structure comprehensive 95+ field casino intelligence including:

1. BASIC INFORMATION (8 fields)
   - Casino name, URL, launch year, ownership, group affiliation

2. LICENSING & REGULATION (10 fields) 
   - Primary license, license number, issuing authority, status, regulatory compliance

3. GAMES & SOFTWARE (15 fields)
   - Total games, slots count, table games, live dealer, game providers, RTP info

4. BONUSES & PROMOTIONS (18 fields)
   - Welcome bonus, match percentage, free spins, wagering requirements, terms

5. PAYMENT METHODS (12 fields)
   - Deposit methods, withdrawal methods, processing times, limits, fees

6. USER EXPERIENCE (10 fields)
   - Mobile compatibility, languages, currencies, navigation, design quality

7. CUSTOMER SUPPORT (8 fields)
   - Live chat, email, phone, hours, response times, language support

8. SECURITY & FAIR PLAY (12 fields)
   - SSL encryption, RNG certification, responsible gambling, KYC verification

9. TECHNICAL SPECIFICATIONS (6 fields)
   - Website performance, mobile app, loading times, uptime statistics

10. TERMS & CONDITIONS (6 fields)
    - Key terms, withdrawal conditions, bonus terms, dispute resolution

Extract factual information with source attribution. Focus on accuracy and completeness.
Return structured data that supports comprehensive affiliate content creation.
""")
        
        # Output parser for structured intelligence
        intelligence_parser = PydanticOutputParser(pydantic_object=ResearchOutput)
        
        # Create parallel research execution
        parallel_research = RunnableParallel(
            # Database research using existing Supabase tool
            database_research=RunnableLambda(
                lambda x: self.supabase_tool._run(x["casino_slug"], x["locale"])
            ),
            
            # Web research using existing research agent  
            web_research=RunnableLambda(
                lambda x: self.research_agent.research_casino_sync(
                    x["casino_name"], 
                    x.get("casino_url")
                )
            ),
            
            # Vector search for existing knowledge
            vector_results=RunnableLambda(
                lambda x: self._vector_search_casino(x["casino_name"])
            ),
            
            # Pass through original inputs
            casino_name=RunnablePassthrough.assign(casino_name=lambda x: x["casino_name"]),
            casino_slug=RunnablePassthrough.assign(casino_slug=lambda x: x["casino_slug"]),
            locale=RunnablePassthrough.assign(locale=lambda x: x["locale"]),
            tenant_id=RunnablePassthrough.assign(tenant_id=lambda x: x["tenant_id"]),
            brand=RunnablePassthrough.assign(brand=lambda x: x["brand"])
        )
        
        # Main research chain composition using LCEL
        return (
            # 1. Prepare inputs with tenant context
            RunnablePassthrough.assign(
                tenant_id=lambda x: self.tenant_config.tenant_id,
                brand=lambda x: self.tenant_config.brand_name,
                locale=lambda x: self.tenant_config.locale
            )
            # 2. Execute parallel research
            | parallel_research
            # 3. Analyze and structure intelligence 
            | research_prompt
            | self.llm
            | intelligence_parser
            # 4. Post-process and store results
            | RunnableLambda(self._post_process_intelligence)
        )
    
    def _vector_search_casino(self, casino_name: str) -> List[Document]:
        """Search existing vector knowledge for casino information"""
        if not self.vector_store:
            logger.warning("⚠️ Vector store not available, skipping vector search")
            return []
            
        try:
            # Use tenant-aware similarity search
            results = self.vector_store.similarity_search_with_tenant_filter(
                query=f"{casino_name} casino review information",
                tenant_config=self.tenant_config,
                k=5,
                content_type="casino_intelligence"
            )
            
            logger.info(f"🔍 Vector search found {len(results)} existing documents")
            return results
            
        except Exception as e:
            logger.warning(f"⚠️ Vector search failed: {e}")
            return []
    
    async def _enhanced_retrieval_research(self, casino_name: str) -> Dict[str, Any]:
        """Perform enhanced retrieval using EnsembleRetriever for maximum coverage"""
        if not self.vector_store:
            logger.info("ℹ️ Vector store not available, skipping enhanced retrieval")
            return {"retrieval_results": [], "retrieval_method": "not_available"}
            
        try:
            # Create BM25 retriever from existing documents
            existing_docs = self.vector_store.similarity_search_with_tenant_filter(
                query=casino_name,
                tenant_config=self.tenant_config,
                k=20  # Get more docs for BM25
            )
            
            if existing_docs:
                # Create BM25 retriever
                bm25_retriever = BM25Retriever.from_documents(existing_docs)
                bm25_retriever.k = 5
                
                # Create vector retriever
                vector_retriever = self.vector_store.create_tenant_aware_retriever(
                    tenant_config=self.tenant_config,
                    search_type="mmr",  # Use MMR for diversity
                    k=5
                )
                
                # Create ensemble retriever
                ensemble_retriever = EnsembleRetriever(
                    retrievers=[bm25_retriever, vector_retriever],
                    weights=[0.4, 0.6]  # Favor vector search slightly
                )
                
                # Create multi-query retriever for query expansion
                multi_query_retriever = MultiQueryRetriever.from_llm(
                    retriever=ensemble_retriever,
                    llm=ChatOpenAI(model="gpt-4o-mini", temperature=0),
                    include_original=True
                )
                
                # Execute enhanced retrieval
                query = f"comprehensive casino intelligence about {casino_name}"
                results = await multi_query_retriever.ainvoke(query)
                
                logger.info(f"✅ Enhanced retrieval returned {len(results)} comprehensive results")
                return {"retrieval_results": results, "retrieval_method": "ensemble_multi_query"}
            
            else:
                logger.info("ℹ️ No existing documents, skipping enhanced retrieval")
                return {"retrieval_results": [], "retrieval_method": "none"}
                
        except Exception as e:
            logger.warning(f"⚠️ Enhanced retrieval failed: {e}")
            return {"retrieval_results": [], "retrieval_method": "failed"}
    
    def _post_process_intelligence(self, intelligence: ResearchOutput) -> ResearchOutput:
        """Post-process intelligence and store in vector database"""
        try:
            # Store intelligence in vector database for future retrieval
            if intelligence.casino_intelligence and self.vector_store:
                self.vector_store.add_casino_intelligence_documents(
                    casino_intelligence=[intelligence.casino_intelligence],
                    tenant_config=self.tenant_config
                )
                logger.info("✅ Intelligence stored in vector database")
            elif not self.vector_store:
                logger.warning("⚠️ Vector store not available, skipping storage")
            
            # Add processing metadata
            intelligence.metadata.update({
                "processed_at": datetime.utcnow().isoformat(),
                "processing_method": "optimized_pipeline",
                "tenant_id": self.tenant_config.tenant_id,
                "completeness_score": intelligence.casino_intelligence.calculate_completeness_score() if intelligence.casino_intelligence else 0
            })
            
            return intelligence
            
        except Exception as e:
            logger.error(f"❌ Post-processing failed: {e}")
            return intelligence
    
    async def research_casino_comprehensive(
        self,
        casino_name: str,
        casino_url: Optional[str] = None
    ) -> ResearchOutput:
        """
        Execute comprehensive 95+ datafield casino research
        
        Args:
            casino_name: Name of the casino to research
            casino_url: Optional official casino URL
            
        Returns:
            Comprehensive ResearchOutput with 95+ structured fields
        """
        try:
            logger.info(f"🎯 Starting comprehensive research: {casino_name}")
            
            # Prepare research inputs
            research_input = {
                "casino_name": casino_name,
                "casino_slug": casino_name.lower().replace(" ", "_").replace("casino", "").strip("_"),
                "casino_url": casino_url,
                "locale": self.tenant_config.locale
            }
            
            # Execute the optimized research chain
            start_time = datetime.utcnow()
            
            # Run main research chain
            result = await self.research_chain.ainvoke(research_input)
            
            # Run enhanced retrieval in parallel for additional context
            enhanced_retrieval = await self._enhanced_retrieval_research(casino_name)
            
            # Add retrieval results to metadata
            result.metadata.update({
                "enhanced_retrieval": enhanced_retrieval,
                "research_duration_seconds": (datetime.utcnow() - start_time).total_seconds(),
                "pipeline_version": "optimized_v1.0"
            })
            
            logger.info(f"✅ Comprehensive research completed in {result.metadata['research_duration_seconds']:.2f}s")
            logger.info(f"📊 Completeness: {result.metadata.get('completeness_score', 0):.1f}%")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Comprehensive research failed: {e}")
            
            # Return error result
            return ResearchOutput(
                success=False,
                casino_name=casino_name,
                error_message=str(e),
                metadata={
                    "error_occurred_at": datetime.utcnow().isoformat(),
                    "pipeline_version": "optimized_v1.0"
                }
            )
    
    def research_casino_sync(
        self,
        casino_name: str,
        casino_url: Optional[str] = None
    ) -> ResearchOutput:
        """Synchronous version for easier integration"""
        import asyncio
        return asyncio.run(self.research_casino_comprehensive(casino_name, casino_url))


# Utility function for creating configured pipeline
def create_optimized_research_pipeline(
    tenant_id: str = "crashcasino",
    brand_name: str = "Crash Casino", 
    locale: str = "en-US"
) -> OptimizedResearchPipeline:
    """Create configured optimized research pipeline"""
    
    tenant_config = TenantConfiguration(
        tenant_id=tenant_id,
        brand_name=brand_name,
        locale=locale,
        voice_profile="professional",
        target_audience="casino_players"
    )
    
    return OptimizedResearchPipeline(tenant_config)


# Production integration example
if __name__ == "__main__":
    import asyncio
    
    async def test_optimized_pipeline():
        """Test the optimized research pipeline"""
        
        # Create pipeline
        pipeline = create_optimized_research_pipeline(
            tenant_id="crashcasino",
            brand_name="Crash Casino",
            locale="en-US"
        )
        
        # Test comprehensive research
        result = await pipeline.research_casino_comprehensive(
            casino_name="Betway Casino",
            casino_url="https://betway.com"
        )
        
        print("🎯 OPTIMIZED RESEARCH PIPELINE RESULTS")
        print("=" * 50)
        print(f"Success: {result.success}")
        print(f"Casino: {result.casino_name}")
        print(f"Completeness: {result.metadata.get('completeness_score', 0):.1f}%")
        print(f"Duration: {result.metadata.get('research_duration_seconds', 0):.2f}s")
        
        if result.casino_intelligence:
            print(f"Intelligence Fields: {len(result.casino_intelligence.model_fields)}")
            print(f"Data Sources: {len(result.casino_intelligence.data_sources)}")
        
        if result.error_message:
            print(f"Error: {result.error_message}")
    
    # Run test
    asyncio.run(test_optimized_pipeline())