"""
🔄 Research & Ingestion Agent LangGraph Node
Task-007: Implement Planner → Retrieve → Loader pattern for comprehensive content ingestion

Uses LangChain native components:
- LangGraph StateGraph for workflow orchestration
- WebBaseLoader for web content extraction
- RecursiveCharacterTextSplitter for intelligent chunking
- AgenticSupabaseVectorStore for indexing with multi-tenant support
- LCEL chains for data transformation and processing
"""

from typing import Dict, Any, Optional, List, Union
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END
from langchain_community.document_loaders import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document
from pydantic import BaseModel, Field
import asyncio
import logging
from datetime import datetime
from urllib.parse import urlparse, urljoin
import json

# Import our vector store and schemas
from src.integrations.supabase_vector_store import AgenticSupabaseVectorStore
from src.schemas.casino_intelligence_schema import CasinoIntelligence
from src.schemas.review_doc import TenantConfiguration


class ResearchPlan(BaseModel):
    """Research plan with prioritized URLs and extraction strategy"""
    target_urls: List[str] = Field(description="Prioritized URLs to research")
    content_categories: List[str] = Field(description="Types of content to extract")
    extraction_priority: str = Field(description="High/Medium/Low priority level")
    estimated_pages: int = Field(description="Estimated number of pages to process")
    tenant_config: Dict[str, Any] = Field(description="Tenant-specific configuration")


class ContentIngestionState(TypedDict):
    """State for Research & Ingestion workflow"""
    target: str  # Casino name or website
    tenant_id: str
    brand: str
    locale: str
    research_plan: Optional[ResearchPlan]
    raw_documents: List[Document]
    processed_chunks: List[Document]
    indexed_document_ids: List[str]
    current_step: str
    errors: List[str]
    success: bool
    metadata: Dict[str, Any]


class ResearchIngestionAgent:
    """
    LangGraph-based Research & Ingestion Agent
    Implements Planner → Retrieve → Loader pattern with LCEL chains
    """
    
    def __init__(self, tenant_id: str = "crashcasino", brand: str = "default", locale: str = "en"):
        self.tenant_id = tenant_id
        self.brand = brand
        self.locale = locale
        
        # Initialize LLM for planning and analysis
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,  # Low temperature for consistent planning
            max_tokens=2000
        )
        
        # Initialize text splitter with casino-optimized settings
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,  # Optimized for casino content analysis
            chunk_overlap=200,  # Ensure context continuity
            length_function=len,
            separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""]
        )
        
        # Initialize vector store with multi-tenant support
        self.vector_store = AgenticSupabaseVectorStore()
        
        # Create LCEL planning chain
        self.planning_chain = self._create_planning_chain()
        
        # Create LCEL content processing chain
        self.processing_chain = self._create_processing_chain()
        
        # Initialize workflow
        self.workflow = self._create_workflow()
        
        logging.info(f"✅ Research & Ingestion Agent initialized for tenant: {tenant_id}")
    
    def _create_planning_chain(self):
        """Create LCEL chain for research planning"""
        
        planning_prompt = ChatPromptTemplate.from_template("""
You are a research planning specialist for casino intelligence gathering.

Target: {target}
Tenant: {tenant_id} (Brand: {brand}, Locale: {locale})

Create a comprehensive research plan with prioritized URLs and extraction strategy.

Consider these content categories:
- Official casino website and key pages
- Terms & conditions and bonus policies  
- Game portfolio and software providers
- Payment methods and banking info
- License and regulatory information
- Player reviews and ratings (if publicly accessible)

Requirements:
1. Prioritize official sources and authoritative content
2. Focus on content that supports 95-field casino intelligence schema
3. Ensure compliance with tenant-specific requirements
4. Estimate realistic page counts for processing

Respond with a structured plan including target URLs, content categories, priority level, and page estimates.
""")
        
        def parse_planning_output(output: str) -> ResearchPlan:
            """Parse LLM output into structured ResearchPlan"""
            try:
                # Extract structured information from LLM response
                lines = output.strip().split('\n')
                urls = []
                categories = []
                priority = "Medium"
                estimated_pages = 5
                
                for line in lines:
                    if 'http' in line or 'www.' in line:
                        # Extract URLs
                        import re
                        found_urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', line)
                        urls.extend(found_urls)
                    elif any(keyword in line.lower() for keyword in ['terms', 'bonus', 'games', 'payment', 'license', 'reviews']):
                        categories.append(line.strip('- ').strip())
                    elif 'priority:' in line.lower():
                        priority = line.split(':')[1].strip()
                    elif 'pages:' in line.lower():
                        try:
                            estimated_pages = int(re.findall(r'\d+', line)[0])
                        except:
                            estimated_pages = 5
                
                # If no URLs extracted, create reasonable defaults
                if not urls and isinstance(output, str):
                    target_domain = output.lower().replace(' ', '').replace('casino', '')
                    urls = [f"https://{target_domain}.com", f"https://www.{target_domain}.com"]
                
                return ResearchPlan(
                    target_urls=urls[:10],  # Limit to 10 URLs
                    content_categories=categories if categories else ["website_overview", "terms_conditions", "games_portfolio"],
                    extraction_priority=priority,
                    estimated_pages=min(estimated_pages, 20),  # Cap at 20 pages
                    tenant_config={
                        "tenant_id": self.tenant_id,
                        "brand": self.brand,
                        "locale": self.locale
                    }
                )
            except Exception as e:
                logging.warning(f"Planning output parsing failed, using defaults: {e}")
                return ResearchPlan(
                    target_urls=[],
                    content_categories=["website_overview"],
                    extraction_priority="Medium",
                    estimated_pages=3,
                    tenant_config={
                        "tenant_id": self.tenant_id,
                        "brand": self.brand,
                        "locale": self.locale
                    }
                )
        
        return (
            planning_prompt
            | self.llm
            | StrOutputParser()
            | RunnableLambda(parse_planning_output)
        )
    
    def _create_processing_chain(self):
        """Create LCEL chain for content processing and enrichment"""
        
        processing_prompt = ChatPromptTemplate.from_template("""
Analyze and enrich this casino content chunk for structured indexing.

Content: {content}
Source URL: {source_url}
Content Category: {category}
Tenant: {tenant_id}

Extract key information and add structured metadata for:
1. Casino name and brand information
2. Content type and category 
3. Key facts and data points
4. Regulatory and compliance information
5. Financial and gaming details

Return the enriched content with clear structure and factual accuracy.
Focus on information that supports comprehensive casino intelligence gathering.
""")
        
        def enrich_content(inputs: Dict[str, Any]) -> str:
            """Enrich content with LLM analysis"""
            try:
                result = processing_prompt.invoke(inputs) | self.llm | StrOutputParser()
                return result.invoke(inputs)
            except Exception as e:
                logging.warning(f"Content enrichment failed: {e}")
                return inputs.get("content", "")
        
        return RunnableLambda(enrich_content)
    
    def _create_workflow(self) -> StateGraph:
        """Create LangGraph workflow for research and ingestion"""
        
        workflow = StateGraph(ContentIngestionState)
        
        # Add workflow nodes
        workflow.add_node("planner", self._planner_node)
        workflow.add_node("retrieve", self._retrieve_node) 
        workflow.add_node("loader", self._loader_node)
        workflow.add_node("error_handler", self._error_handler_node)
        
        # Set entry point
        workflow.set_entry_point("planner")
        
        # Add state transitions
        workflow.add_edge("planner", "retrieve")
        workflow.add_edge("retrieve", "loader")
        workflow.add_edge("loader", END)
        workflow.add_edge("error_handler", END)
        
        return workflow.compile()
    
    async def _planner_node(self, state: ContentIngestionState) -> ContentIngestionState:
        """
        Planner Node: Create research plan using LCEL planning chain
        """
        try:
            logging.info(f"📋 Planning research for: {state['target']}")
            state["current_step"] = "planning"
            
            # Execute planning chain
            plan = await self.planning_chain.ainvoke({
                "target": state["target"],
                "tenant_id": state["tenant_id"],
                "brand": state["brand"],
                "locale": state["locale"]
            })
            
            state["research_plan"] = plan
            state["metadata"]["plan_created_at"] = datetime.utcnow().isoformat()
            
            logging.info(f"✅ Research plan created with {len(plan.target_urls)} URLs")
            return state
            
        except Exception as e:
            logging.error(f"❌ Planning failed: {e}")
            state["errors"].append(f"Planning failed: {str(e)}")
            state["current_step"] = "error"
            return state
    
    async def _retrieve_node(self, state: ContentIngestionState) -> ContentIngestionState:
        """
        Retrieve Node: Load web content using WebBaseLoader
        """
        try:
            logging.info("🔍 Retrieving web content")
            state["current_step"] = "retrieving"
            
            if not state.get("research_plan") or not state["research_plan"].target_urls:
                raise ValueError("No URLs available for content retrieval")
            
            raw_documents = []
            
            # Process URLs with WebBaseLoader
            for url in state["research_plan"].target_urls[:5]:  # Limit to 5 URLs for performance
                try:
                    logging.info(f"Loading content from: {url}")
                    
                    # Initialize WebBaseLoader with proper configuration
                    loader = WebBaseLoader(
                        web_paths=[url],
                        header_template={
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                        }
                    )
                    
                    # Load documents
                    docs = await asyncio.to_thread(loader.load)
                    
                    # Enrich documents with metadata
                    for doc in docs:
                        doc.metadata.update({
                            "source_url": url,
                            "tenant_id": state["tenant_id"],
                            "brand": state["brand"],
                            "locale": state["locale"],
                            "content_category": self._categorize_content(url),
                            "extracted_at": datetime.utcnow().isoformat(),
                            "extraction_method": "WebBaseLoader"
                        })
                    
                    raw_documents.extend(docs)
                    
                except Exception as url_error:
                    logging.warning(f"Failed to load {url}: {url_error}")
                    state["errors"].append(f"URL load failed {url}: {str(url_error)}")
                    continue
            
            state["raw_documents"] = raw_documents
            logging.info(f"✅ Retrieved {len(raw_documents)} documents")
            return state
            
        except Exception as e:
            logging.error(f"❌ Retrieval failed: {e}")
            state["errors"].append(f"Retrieval failed: {str(e)}")
            state["current_step"] = "error"
            return state
    
    async def _loader_node(self, state: ContentIngestionState) -> ContentIngestionState:
        """
        Loader Node: Process documents and index into vector store
        """
        try:
            logging.info("📦 Processing and loading documents")
            state["current_step"] = "loading"
            
            if not state.get("raw_documents"):
                raise ValueError("No documents available for processing")
            
            processed_chunks = []
            
            # Process each document with text splitting and enrichment
            for doc in state["raw_documents"]:
                try:
                    # Split document into chunks
                    chunks = self.text_splitter.split_documents([doc])
                    
                    # Enrich chunks using processing chain
                    for chunk in chunks:
                        enriched_content = await self.processing_chain.ainvoke({
                            "content": chunk.page_content,
                            "source_url": chunk.metadata.get("source_url", "unknown"),
                            "category": chunk.metadata.get("content_category", "general"),
                            "tenant_id": state["tenant_id"]
                        })
                        
                        # Update chunk with enriched content
                        chunk.page_content = enriched_content
                        chunk.metadata.update({
                            "chunk_id": f"{len(processed_chunks):04d}",
                            "processed_at": datetime.utcnow().isoformat()
                        })
                        
                        processed_chunks.append(chunk)
                        
                except Exception as doc_error:
                    logging.warning(f"Document processing failed: {doc_error}")
                    state["errors"].append(f"Document processing failed: {str(doc_error)}")
                    continue
            
            state["processed_chunks"] = processed_chunks
            
            # Index documents into vector store
            if processed_chunks:
                try:
                    document_ids = await asyncio.to_thread(
                        self.vector_store.add_documents,
                        processed_chunks
                    )
                    state["indexed_document_ids"] = document_ids or []
                    logging.info(f"✅ Indexed {len(processed_chunks)} chunks into vector store")
                    
                except Exception as index_error:
                    logging.error(f"Vector store indexing failed: {index_error}")
                    state["errors"].append(f"Indexing failed: {str(index_error)}")
            
            state["success"] = len(processed_chunks) > 0
            state["metadata"]["total_chunks_processed"] = len(processed_chunks)
            state["metadata"]["completed_at"] = datetime.utcnow().isoformat()
            
            return state
            
        except Exception as e:
            logging.error(f"❌ Loading failed: {e}")
            state["errors"].append(f"Loading failed: {str(e)}")
            state["current_step"] = "error"
            return state
    
    async def _error_handler_node(self, state: ContentIngestionState) -> ContentIngestionState:
        """Error handling node"""
        logging.error(f"🚨 Workflow errors: {state.get('errors', [])}")
        state["success"] = False
        return state
    
    def _categorize_content(self, url: str) -> str:
        """Categorize content based on URL patterns"""
        url_lower = url.lower()
        
        if any(term in url_lower for term in ['terms', 'conditions', 'policy']):
            return "terms_conditions"
        elif any(term in url_lower for term in ['bonus', 'promotion', 'offer']):
            return "bonus_information"
        elif any(term in url_lower for term in ['games', 'casino', 'slots']):
            return "games_portfolio"
        elif any(term in url_lower for term in ['payment', 'banking', 'deposit']):
            return "payment_methods"
        elif any(term in url_lower for term in ['about', 'company', 'license']):
            return "company_information"
        else:
            return "general_content"
    
    async def execute_research_ingestion(
        self, 
        target: str,
        tenant_id: Optional[str] = None,
        brand: Optional[str] = None,
        locale: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute complete research and ingestion workflow
        
        Args:
            target: Casino name or website to research
            tenant_id: Override tenant ID
            brand: Override brand
            locale: Override locale
            
        Returns:
            Dict containing workflow results and metadata
        """
        
        # Initialize state
        state = ContentIngestionState(
            target=target,
            tenant_id=tenant_id or self.tenant_id,
            brand=brand or self.brand,
            locale=locale or self.locale,
            research_plan=None,
            raw_documents=[],
            processed_chunks=[],
            indexed_document_ids=[],
            current_step="initializing",
            errors=[],
            success=False,
            metadata={
                "started_at": datetime.utcnow().isoformat(),
                "agent_version": "1.0.0"
            }
        )
        
        try:
            # Execute workflow
            final_state = await self.workflow.ainvoke(state)
            
            # Return results
            return {
                "success": final_state.get("success", False),
                "target": final_state["target"],
                "documents_processed": len(final_state.get("processed_chunks", [])),
                "documents_indexed": len(final_state.get("indexed_document_ids", [])),
                "research_plan": final_state.get("research_plan"),
                "errors": final_state.get("errors", []),
                "metadata": final_state.get("metadata", {}),
                "tenant_config": {
                    "tenant_id": final_state["tenant_id"],
                    "brand": final_state["brand"],
                    "locale": final_state["locale"]
                }
            }
            
        except Exception as e:
            logging.error(f"❌ Workflow execution failed: {e}")
            return {
                "success": False,
                "target": target,
                "documents_processed": 0,
                "documents_indexed": 0,
                "research_plan": None,
                "errors": [f"Workflow execution failed: {str(e)}"],
                "metadata": state["metadata"],
                "tenant_config": {
                    "tenant_id": tenant_id or self.tenant_id,
                    "brand": brand or self.brand,
                    "locale": locale or self.locale
                }
            }


# Example usage and testing
if __name__ == "__main__":
    import asyncio
    
    async def test_research_ingestion():
        """Test the Research & Ingestion Agent"""
        
        # Initialize agent
        agent = ResearchIngestionAgent(
            tenant_id="crashcasino",
            brand="default", 
            locale="en"
        )
        
        # Test research and ingestion
        result = await agent.execute_research_ingestion(
            target="Betway Casino",
            tenant_id="crashcasino"
        )
        
        print("🔍 Research & Ingestion Results:")
        print("=" * 50)
        print(f"Success: {result['success']}")
        print(f"Target: {result['target']}")
        print(f"Documents Processed: {result['documents_processed']}")
        print(f"Documents Indexed: {result['documents_indexed']}")
        print(f"Errors: {result['errors']}")
        print(f"Tenant Config: {result['tenant_config']}")
        
        if result['research_plan']:
            print(f"URLs Planned: {len(result['research_plan'].target_urls)}")
            print(f"Categories: {result['research_plan'].content_categories}")
    
    # Run test
    asyncio.run(test_research_ingestion())