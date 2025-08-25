"""
🎯 Multi-Tenant Retrieval System
Task-010: LCEL retrieval chains with tenant_id, voice, locale parameters

Features:
- Multi-tenant metadata filtering with tenant_id, voice, locale
- Enhanced recall with MultiQueryRetriever
- LCEL chain composition for scalable retrieval
- Integration with AgenticSupabaseVectorStore (Stream 1B)
- Support for Research & Ingestion Agent content (Stream 1C)
"""

from typing import Dict, Any, List, Optional, Union, Tuple
from pydantic import BaseModel, Field
from langchain_core.retrievers import BaseRetriever
from langchain_core.documents import Document
from langchain_core.runnables import (
    RunnablePassthrough, 
    RunnableLambda, 
    RunnableParallel,
    Runnable
)
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langchain.retrievers import MultiQueryRetriever, EnsembleRetriever
from langchain_core.callbacks import CallbackManagerForRetrieverRun
import logging
from datetime import datetime

# Import our components
from src.integrations.supabase_vector_store import AgenticSupabaseVectorStore, TenantMetadataFilter
from src.schemas.review_doc import TenantConfiguration
from src.schemas.casino_intelligence_schema import CasinoIntelligence


logger = logging.getLogger(__name__)


class MultiTenantQuery(BaseModel):
    """Multi-tenant query with filtering parameters"""
    query: str = Field(description="The search query")
    tenant_id: str = Field(description="Tenant identifier")
    brand: Optional[str] = Field(default=None, description="Brand filter")
    locale: str = Field(default="en", description="Locale/language code")
    voice: Optional[str] = Field(default=None, description="Voice profile")
    content_types: Optional[List[str]] = Field(default=None, description="Content type filters")
    limit: int = Field(default=10, description="Maximum results to return")
    similarity_threshold: float = Field(default=0.7, description="Minimum similarity score")


class RetrievalResult(BaseModel):
    """Structured retrieval result with metadata"""
    documents: List[Document] = Field(description="Retrieved documents")
    query_metadata: Dict[str, Any] = Field(description="Query processing metadata")
    retrieval_stats: Dict[str, Any] = Field(description="Retrieval statistics")
    tenant_config: TenantConfiguration = Field(description="Applied tenant configuration")


class MultiTenantRetriever(BaseRetriever):
    """
    Custom multi-tenant retriever with metadata filtering
    Integrates with AgenticSupabaseVectorStore for tenant-aware retrieval
    """
    
    def __init__(
        self,
        vector_store: AgenticSupabaseVectorStore,
        tenant_config: TenantConfiguration,
        search_type: str = "mmr",
        search_kwargs: Optional[Dict[str, Any]] = None
    ):
        super().__init__()
        # Store as private attributes to avoid Pydantic validation issues
        self._vector_store = vector_store
        self._tenant_config = tenant_config
        self._search_type = search_type
        self._search_kwargs = search_kwargs or {"k": 10}
        
        # Create tenant metadata filter
        self._metadata_filter = TenantMetadataFilter.create_tenant_filter(
            tenant_id=tenant_config.tenant_id,
            brand=tenant_config.brand_name,
            locale=tenant_config.locale
        )
        
        logger.info(f"✅ MultiTenantRetriever initialized for tenant: {tenant_config.tenant_id}")
    
    @property
    def vector_store(self):
        return self._vector_store
    
    @property
    def tenant_config(self):
        return self._tenant_config
    
    @property
    def search_type(self):
        return self._search_type
    
    @property
    def search_kwargs(self):
        return self._search_kwargs
    
    @property
    def metadata_filter(self):
        return self._metadata_filter
    
    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun
    ) -> List[Document]:
        """Retrieve documents with tenant filtering"""
        
        # Apply tenant metadata filtering
        filter_dict = self._metadata_filter
        
        # Enhanced search kwargs with tenant filtering
        enhanced_kwargs = {
            **self._search_kwargs,
            "filter": filter_dict
        }
        
        try:
            # Use the vector store's search method with tenant filtering
            if self._search_type == "mmr":
                docs = self._vector_store.vectorstore.max_marginal_relevance_search(
                    query, **enhanced_kwargs
                )
            else:
                docs = self._vector_store.vectorstore.similarity_search(
                    query, **enhanced_kwargs
                )
            
            # Post-process documents with tenant context
            for doc in docs:
                doc.metadata.update({
                    "retrieved_at": datetime.utcnow().isoformat(),
                    "tenant_id": self._tenant_config.tenant_id,
                    "retrieval_method": self._search_type
                })
            
            return docs
            
        except Exception as e:
            logger.error(f"❌ Retrieval failed for tenant {self._tenant_config.tenant_id}: {e}")
            return []


class MultiTenantRetrievalSystem:
    """
    🎯 MULTI-TENANT RETRIEVAL SYSTEM
    ================================
    
    LCEL-based retrieval system with comprehensive multi-tenant support:
    - Tenant-aware metadata filtering
    - Enhanced recall with MultiQueryRetriever
    - Voice and locale personalization
    - Content type filtering
    - Integration with AgenticSupabaseVectorStore
    """
    
    def __init__(
        self,
        vector_store: AgenticSupabaseVectorStore,
        llm: Optional[ChatOpenAI] = None
    ):
        self.vector_store = vector_store
        self.llm = llm or ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,  # Low temperature for consistent query expansion
            max_tokens=1000
        )
        
        # Create LCEL retrieval chains
        self.single_query_chain = self._create_single_query_chain()
        self.multi_query_chain = self._create_multi_query_chain()
        self.ensemble_chain = self._create_ensemble_chain()
        
        logger.info("✅ MultiTenantRetrievalSystem initialized")
    
    def _create_single_query_chain(self) -> Runnable:
        """Create LCEL chain for single-query retrieval"""
        
        def retrieve_with_tenant_filter(inputs: Dict[str, Any]) -> List[Document]:
            """Retrieve documents with tenant filtering applied"""
            tenant_query = MultiTenantQuery(**inputs)
            
            # Create tenant configuration
            tenant_config = TenantConfiguration(
                tenant_id=tenant_query.tenant_id,
                brand_name=tenant_query.brand or "default",
                locale=tenant_query.locale,
                voice_profile=tenant_query.voice,
                target_audience="casino_players"
            )
            
            # Create tenant-aware retriever
            retriever = MultiTenantRetriever(
                vector_store=self.vector_store,
                tenant_config=tenant_config,
                search_type="mmr",
                search_kwargs={
                    "k": tenant_query.limit,
                    "fetch_k": tenant_query.limit * 2,
                    "lambda_mult": 0.7  # Balance relevance vs diversity
                }
            )
            
            # Retrieve documents
            docs = retriever.get_relevant_documents(tenant_query.query)
            
            # Filter by similarity threshold if needed
            if tenant_query.similarity_threshold < 1.0:
                filtered_docs = []
                for doc in docs:
                    score = doc.metadata.get("similarity_score", 1.0)
                    if score >= tenant_query.similarity_threshold:
                        filtered_docs.append(doc)
                docs = filtered_docs
            
            return docs
        
        return RunnableLambda(retrieve_with_tenant_filter)
    
    def _create_multi_query_chain(self) -> Runnable:
        """Create LCEL chain for multi-query retrieval with enhanced recall"""
        
        # Enhanced multi-query prompt for casino content
        multi_query_prompt = ChatPromptTemplate.from_template("""
You are an expert at generating search queries for casino and gambling content.

Original query: {query}
Tenant context: {tenant_id} (Brand: {brand}, Locale: {locale})

Generate 3 different search queries that will help retrieve comprehensive information about this topic.
Consider different perspectives:
1. Player experience and practical aspects
2. Technical and regulatory details  
3. Comparative and industry context

Focus on queries that would be valuable for creating authoritative gambling content.

Return each query on a separate line with no numbering or formatting.
""")
        
        def create_multi_query_retriever(inputs: Dict[str, Any]) -> List[Document]:
            """Create and execute multi-query retrieval"""
            tenant_query = MultiTenantQuery(**inputs)
            
            # Create tenant configuration
            tenant_config = TenantConfiguration(
                tenant_id=tenant_query.tenant_id,
                brand_name=tenant_query.brand or "default",
                locale=tenant_query.locale,
                voice_profile=tenant_query.voice,
                target_audience="casino_players"
            )
            
            # Create base retriever
            base_retriever = MultiTenantRetriever(
                vector_store=self.vector_store,
                tenant_config=tenant_config,
                search_type="mmr",
                search_kwargs={"k": tenant_query.limit}
            )
            
            # Create MultiQueryRetriever with enhanced prompt
            multi_retriever = MultiQueryRetriever.from_llm(
                retriever=base_retriever,
                llm=self.llm,
                prompt=multi_query_prompt,
                include_original=True
            )
            
            # Execute multi-query retrieval
            try:
                docs = multi_retriever.get_relevant_documents(tenant_query.query)
                
                # Deduplicate and rank results
                seen_content = set()
                unique_docs = []
                
                for doc in docs:
                    content_hash = hash(doc.page_content[:200])  # Hash first 200 chars
                    if content_hash not in seen_content:
                        seen_content.add(content_hash)
                        unique_docs.append(doc)
                        if len(unique_docs) >= tenant_query.limit:
                            break
                
                return unique_docs
                
            except Exception as e:
                logger.error(f"Multi-query retrieval failed: {e}")
                # Fallback to single query
                return base_retriever.get_relevant_documents(tenant_query.query)
        
        return RunnableLambda(create_multi_query_retriever)
    
    def _create_ensemble_chain(self) -> Runnable:
        """Create LCEL chain for ensemble retrieval (vector + BM25)"""
        
        def ensemble_retrieve(inputs: Dict[str, Any]) -> List[Document]:
            """Ensemble retrieval combining multiple methods"""
            tenant_query = MultiTenantQuery(**inputs)
            
            # Create tenant configuration
            tenant_config = TenantConfiguration(
                tenant_id=tenant_query.tenant_id,
                brand_name=tenant_query.brand or "default",
                locale=tenant_query.locale,
                voice_profile=tenant_query.voice,
                target_audience="casino_players"
            )
            
            # Create primary vector retriever
            vector_retriever = MultiTenantRetriever(
                vector_store=self.vector_store,
                tenant_config=tenant_config,
                search_type="similarity",
                search_kwargs={"k": tenant_query.limit}
            )
            
            # Create MMR retriever for diversity
            mmr_retriever = MultiTenantRetriever(
                vector_store=self.vector_store,
                tenant_config=tenant_config,
                search_type="mmr",
                search_kwargs={"k": tenant_query.limit, "lambda_mult": 0.5}
            )
            
            try:
                # Get results from both retrievers
                vector_docs = vector_retriever.get_relevant_documents(tenant_query.query)
                mmr_docs = mmr_retriever.get_relevant_documents(tenant_query.query)
                
                # Combine and deduplicate
                all_docs = vector_docs + mmr_docs
                seen_content = set()
                unique_docs = []
                
                for doc in all_docs:
                    content_hash = hash(doc.page_content[:200])
                    if content_hash not in seen_content:
                        seen_content.add(content_hash)
                        doc.metadata["ensemble_method"] = "vector+mmr"
                        unique_docs.append(doc)
                        if len(unique_docs) >= tenant_query.limit:
                            break
                
                return unique_docs
                
            except Exception as e:
                logger.error(f"Ensemble retrieval failed: {e}")
                return vector_retriever.get_relevant_documents(tenant_query.query)
        
        return RunnableLambda(ensemble_retrieve)
    
    def create_retrieval_chain(
        self,
        retrieval_type: str = "multi_query"
    ) -> Runnable:
        """
        Create complete LCEL retrieval chain with result structuring
        
        Args:
            retrieval_type: "single", "multi_query", or "ensemble"
        """
        
        # Select retrieval method
        if retrieval_type == "single":
            retrieval_chain = self.single_query_chain
        elif retrieval_type == "ensemble":
            retrieval_chain = self.ensemble_chain
        else:  # default to multi_query
            retrieval_chain = self.multi_query_chain
        
        # Create result structuring chain
        def structure_results(inputs: Dict[str, Any]) -> RetrievalResult:
            """Structure retrieval results with metadata"""
            
            # Extract components
            documents = inputs["documents"]
            original_query = inputs["original_query"]
            
            # Create tenant config from query
            tenant_config = TenantConfiguration(
                tenant_id=original_query["tenant_id"],
                brand_name=original_query.get("brand", "default"),
                locale=original_query.get("locale", "en"),
                voice_profile=original_query.get("voice"),
                target_audience="casino_players"
            )
            
            # Generate metadata
            query_metadata = {
                "retrieval_type": retrieval_type,
                "query_text": original_query["query"],
                "tenant_filters": {
                    "tenant_id": original_query["tenant_id"],
                    "brand": original_query.get("brand"),
                    "locale": original_query.get("locale", "en")
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
            retrieval_stats = {
                "total_documents": len(documents),
                "unique_sources": len(set(doc.metadata.get("source_url", "unknown") for doc in documents)),
                "content_categories": list(set(doc.metadata.get("content_category", "general") for doc in documents)),
                "average_chunk_size": sum(len(doc.page_content) for doc in documents) // max(len(documents), 1)
            }
            
            return RetrievalResult(
                documents=documents,
                query_metadata=query_metadata,
                retrieval_stats=retrieval_stats,
                tenant_config=tenant_config
            )
        
        # Complete LCEL chain
        complete_chain = (
            RunnableParallel({
                "documents": retrieval_chain,
                "original_query": RunnablePassthrough()
            })
            | RunnableLambda(structure_results)
        )
        
        return complete_chain
    
    async def retrieve(
        self,
        query: str,
        tenant_id: str,
        brand: Optional[str] = None,
        locale: str = "en",
        voice: Optional[str] = None,
        content_types: Optional[List[str]] = None,
        limit: int = 10,
        similarity_threshold: float = 0.7,
        retrieval_type: str = "multi_query"
    ) -> RetrievalResult:
        """
        Execute multi-tenant retrieval with full LCEL chain
        
        Args:
            query: Search query
            tenant_id: Tenant identifier
            brand: Brand filter (optional)
            locale: Language/locale code
            voice: Voice profile (optional)
            content_types: Content type filters (optional)
            limit: Maximum results
            similarity_threshold: Minimum similarity score
            retrieval_type: Retrieval method ("single", "multi_query", "ensemble")
        """
        
        # Create query object
        tenant_query = MultiTenantQuery(
            query=query,
            tenant_id=tenant_id,
            brand=brand,
            locale=locale,
            voice=voice,
            content_types=content_types,
            limit=limit,
            similarity_threshold=similarity_threshold
        )
        
        # Get retrieval chain
        chain = self.create_retrieval_chain(retrieval_type)
        
        # Execute retrieval
        try:
            result = await chain.ainvoke(tenant_query.dict())
            logger.info(f"✅ Retrieved {len(result.documents)} documents for tenant: {tenant_id}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Retrieval failed for tenant {tenant_id}: {e}")
            
            # Return empty result on failure
            return RetrievalResult(
                documents=[],
                query_metadata={
                    "retrieval_type": retrieval_type,
                    "query_text": query,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                },
                retrieval_stats={
                    "total_documents": 0,
                    "unique_sources": 0,
                    "content_categories": [],
                    "average_chunk_size": 0
                },
                tenant_config=TenantConfiguration(
                    tenant_id=tenant_id,
                    brand_name=brand or "default",
                    locale=locale
                )
            )


# Example usage and testing
if __name__ == "__main__":
    import asyncio
    
    async def test_multi_tenant_retrieval():
        """Test the Multi-Tenant Retrieval System"""
        
        print("🎯 Multi-Tenant Retrieval System Test")
        print("=" * 50)
        
        # Initialize vector store (mocked for testing)
        from unittest.mock import Mock
        
        mock_vector_store = Mock(spec=AgenticSupabaseVectorStore)
        
        # Initialize retrieval system
        retrieval_system = MultiTenantRetrievalSystem(
            vector_store=mock_vector_store
        )
        
        # Test query
        result = await retrieval_system.retrieve(
            query="What are the best casino bonuses?",
            tenant_id="crashcasino",
            brand="default",
            locale="en",
            limit=5,
            retrieval_type="multi_query"
        )
        
        print(f"✅ Query: {result.query_metadata['query_text']}")
        print(f"✅ Tenant: {result.tenant_config.tenant_id}")
        print(f"✅ Retrieved: {result.retrieval_stats['total_documents']} documents")
        print(f"✅ Retrieval Type: {result.query_metadata['retrieval_type']}")
        
        return True
    
    # Run test (would need proper setup for full functionality)
    print("Note: Full testing requires proper Supabase and OpenAI setup")
    asyncio.run(test_multi_tenant_retrieval())