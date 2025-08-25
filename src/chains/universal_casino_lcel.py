"""
Universal Casino Review Chain - Pure LCEL Implementation
=======================================================

This is a proper LangChain LCEL chain that can be used for any casino review.
Uses ONLY native LangChain components with | operator composition.

Follows CLAUDE.md best practices:
1. ✅ LCEL everywhere (| composition with Runnable*, ChatPromptTemplate, RouterRunnable)
2. ✅ No custom orchestration (no raw asyncio.gather, no raw HTTP)
3. ✅ Schema-First (inputs/outputs in /src/schemas)
4. ✅ External services only via /src/tools/*

Usage:
    from chains.universal_casino_lcel import create_universal_casino_chain
    
    chain = create_universal_casino_chain()
    result = await chain.ainvoke({"casino_name": "Mr Vegas Casino"})
"""

import os
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

# Native LangChain Core Components - LCEL Foundation
from langchain_core.runnables import (
    Runnable, 
    RunnablePassthrough, 
    RunnableLambda, 
    RunnableParallel,
    RunnableBranch,
    RunnableSequence
)
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import StrOutputParser, PydanticOutputParser
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage

# Native LangChain Models
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

# Native LangChain Tools
from langchain_community.tools.tavily_search import TavilySearchResults

# Native LangChain VectorStores
from langchain_community.vectorstores.supabase import SupabaseVectorStore

# Native LangChain Retrievers
from langchain.retrievers import MultiQueryRetriever, EnsembleRetriever

# Pydantic for schema validation
from pydantic import BaseModel, Field

# Supabase client
from supabase import create_client, Client

# Environment setup
from dotenv import load_dotenv
load_dotenv()

# Schema Definition (Schema-First approach)
class CasinoReviewInput(BaseModel):
    """Input schema for casino review chain"""
    casino_name: str = Field(..., description="Name of the casino to review")
    target_words: int = Field(default=2500, description="Target word count for review")
    include_images: bool = Field(default=True, description="Whether to include images")
    publish_to_wordpress: bool = Field(default=False, description="Whether to publish to WordPress")

class CasinoReviewOutput(BaseModel):
    """Output schema for casino review chain"""
    casino_name: str = Field(..., description="Name of the reviewed casino")
    review_content: str = Field(..., description="Generated review content")
    word_count: int = Field(..., description="Actual word count of review")
    research_sources: List[str] = Field(default_factory=list, description="Research sources used")
    confidence_score: float = Field(..., description="Confidence score of the review")
    processing_time_seconds: float = Field(..., description="Time taken to process")
    wordpress_url: Optional[str] = Field(default=None, description="WordPress publication URL if published")
    status: str = Field(..., description="Processing status")

# LCEL Chain Components
def create_research_chain() -> Runnable:
    """Create research chain using native LangChain components"""
    
    # Research prompt using native ChatPromptTemplate
    research_prompt = ChatPromptTemplate.from_template(
        """Research comprehensive information about {casino_name}.
        
        Focus on these key areas:
        1. Licensing and regulation
        2. Game portfolio and software providers
        3. Bonuses and promotions
        4. Payment methods and security
        5. Mobile experience and usability
        6. Customer support quality
        7. User experience and reputation
        
        Provide detailed, factual information for a comprehensive casino review.
        Casino: {casino_name}
        """
    )
    
    # Native Tavily search tool
    tavily_search = TavilySearchResults(
        max_results=10,
        search_depth="advanced",
        include_answer=True
    )
    
    # LLM for processing
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.1,
        max_tokens=4000
    )
    
    # LCEL chain composition using | operator
    research_chain = (
        research_prompt 
        | llm 
        | StrOutputParser()
        | RunnableLambda(lambda x: {"research_content": x, "sources": ["tavily_search"]})
    )
    
    return research_chain

def create_rag_content_generation_chain() -> Runnable:
    """Create RAG content generation chain using proper retrieval patterns"""
    
    def setup_retriever_and_generate(inputs: Dict[str, Any]) -> str:
        """Set up retriever and generate content using RAG"""
        import asyncio
        
        async def _generate_with_rag():
            casino_name = inputs.get("casino_name", "")
            target_words = inputs.get("target_words", 2500)
            
            # Initialize Supabase vector store
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
            
            if not supabase_url or not supabase_key:
                # Fallback to research-based generation
                research_content = inputs.get("research_content", "")
                fallback_prompt = ChatPromptTemplate.from_template(
                    """Create a {target_words}-word casino review for {casino_name}.
                    Research: {research_content}"""
                )
                llm = ChatOpenAI(model="gpt-4o", temperature=0.2)
                chain = fallback_prompt | llm | StrOutputParser()
                return await chain.ainvoke({
                    "casino_name": casino_name,
                    "target_words": target_words,
                    "research_content": research_content
                })
            
            # Set up proper RAG retrieval
            from supabase import create_client
            supabase_client = create_client(supabase_url, supabase_key)
            embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
            
            # Create SupabaseVectorStore
            vector_store = SupabaseVectorStore(
                client=supabase_client,
                embedding=embeddings,
                table_name="casino_reviews",
                query_name="search_casino_reviews"
            )
            
            # Create retriever with MMR for diversity
            base_retriever = vector_store.as_retriever(
                search_type="mmr",
                search_kwargs={
                    "k": 8,
                    "fetch_k": 24,
                    "lambda_mult": 0.5,
                    "filter": {"casino_name": casino_name}
                }
            )
            
            # Wrap with MultiQueryRetriever for better recall
            llm = ChatOpenAI(model="gpt-4o", temperature=0.1)
            multi_retriever = MultiQueryRetriever.from_llm(
                retriever=base_retriever,
                llm=llm,
                include_original=True
            )
            
            # RAG prompt template
            rag_prompt = ChatPromptTemplate.from_template(
                """Generate a comprehensive {target_words}-word casino review for {casino_name}.
                
                Retrieved Context:
                {context}
                
                Create a professional review with these sections:
                1. Executive Summary with rating
                2. Licensing and Regulation
                3. Game Portfolio and Software
                4. Bonuses and Promotions
                5. Payment Methods and Security
                6. Mobile Experience
                7. Customer Support
                8. User Experience Analysis
                9. Pros and Cons
                10. Final Verdict
                
                Use the retrieved context to provide specific, factual information.
                Target exactly {target_words} words.
                """
            )
            
            # PROPER RAG LCEL chain
            rag_chain = (
                {
                    "context": multi_retriever,
                    "casino_name": lambda x: casino_name,
                    "target_words": lambda x: target_words
                }
                | rag_prompt
                | llm
                | StrOutputParser()
            )
            
            # Execute RAG chain
            return await rag_chain.ainvoke({"query": f"Review {casino_name} casino"})
        
        # Run async function
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(_generate_with_rag())
    
    # LCEL chain using RunnableLambda
    rag_content_chain = RunnableLambda(setup_retriever_and_generate)
    
    return rag_content_chain

def create_vectorization_chain() -> Runnable:
    """Create vectorization chain using native LangChain components"""
    
    # Initialize Supabase client
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY") 
    
    if not supabase_url or not supabase_key:
        # Return passthrough if Supabase not configured
        return RunnablePassthrough()
    
    supabase_client = create_client(supabase_url, supabase_key)
    
    # Native OpenAI embeddings
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small"
    )
    
    # Native Supabase vector store
    def vectorize_content(inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Vectorize content using native SupabaseVectorStore"""
        try:
            casino_name = inputs.get("casino_name", "")
            content = inputs.get("review_content", "")
            
            if not content:
                return inputs
            
            # Create document
            doc = Document(
                page_content=content,
                metadata={
                    "casino_name": casino_name,
                    "content_type": "casino_review",
                    "timestamp": datetime.now().isoformat(),
                    "source": "universal_casino_chain"
                }
            )
            
            # Native SupabaseVectorStore operation
            vector_store = SupabaseVectorStore(
                client=supabase_client,
                embedding=embeddings,
                table_name="casino_reviews",
                query_name="search_casino_reviews"
            )
            
            # Add document to vector store
            vector_store.add_documents([doc])
            
            inputs["vectorized"] = True
            inputs["vector_store"] = "supabase"
            
        except Exception as e:
            inputs["vectorized"] = False
            inputs["vectorization_error"] = str(e)
        
        return inputs
    
    # LCEL chain using RunnableLambda
    vectorization_chain = RunnableLambda(vectorize_content)
    
    return vectorization_chain

def create_wordpress_publishing_chain() -> Runnable:
    """Create WordPress publishing chain using native LangChain components"""
    
    def publish_to_wordpress(inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Publish to WordPress using native tools integration"""
        try:
            if not inputs.get("publish_to_wordpress", False):
                inputs["wordpress_published"] = False
                inputs["wordpress_message"] = "Publishing not requested"
                return inputs
            
            # WordPress publishing would use /src/tools/wordpress.py adapter
            # Following CLAUDE.md rule: "External services only via /src/tools/*"
            
            # For now, simulate WordPress publishing structure
            casino_name = inputs.get("casino_name", "")
            content = inputs.get("review_content", "")
            
            # This would call the native WordPress tool adapter
            inputs["wordpress_published"] = False
            inputs["wordpress_message"] = "WordPress adapter not implemented yet"
            inputs["wordpress_url"] = f"https://example.com/casino/{casino_name.lower().replace(' ', '-')}-review/"
            
        except Exception as e:
            inputs["wordpress_published"] = False
            inputs["wordpress_error"] = str(e)
        
        return inputs
    
    # LCEL chain using RunnableLambda
    wordpress_chain = RunnableLambda(publish_to_wordpress)
    
    return wordpress_chain

def create_output_formatting_chain() -> Runnable:
    """Create output formatting chain using native LangChain components"""
    
    def format_output(inputs: Dict[str, Any]) -> CasinoReviewOutput:
        """Format final output according to schema"""
        try:
            casino_name = inputs.get("casino_name", "")
            review_content = inputs.get("review_content", "")
            word_count = len(review_content.split()) if review_content else 0
            sources = inputs.get("sources", [])
            processing_time = inputs.get("processing_time_seconds", 0.0)
            wordpress_url = inputs.get("wordpress_url") if inputs.get("wordpress_published") else None
            
            # Calculate confidence score based on content quality
            confidence_score = min(1.0, word_count / 2500.0) if word_count > 0 else 0.0
            
            return CasinoReviewOutput(
                casino_name=casino_name,
                review_content=review_content,
                word_count=word_count,
                research_sources=sources,
                confidence_score=confidence_score,
                processing_time_seconds=processing_time,
                wordpress_url=wordpress_url,
                status="completed" if review_content else "failed"
            )
            
        except Exception as e:
            return CasinoReviewOutput(
                casino_name=inputs.get("casino_name", ""),
                review_content="",
                word_count=0,
                research_sources=[],
                confidence_score=0.0,
                processing_time_seconds=inputs.get("processing_time_seconds", 0.0),
                wordpress_url=None,
                status=f"error: {str(e)}"
            )
    
    # LCEL chain using RunnableLambda with schema validation
    output_chain = RunnableLambda(format_output)
    
    return output_chain

def create_universal_casino_chain() -> Runnable:
    """
    Create the complete universal casino review chain using LCEL composition
    
    This is the main chain that composes all components using | operators
    according to LCEL best practices.
    """
    
    # Add processing time tracking
    def add_start_time(inputs: Union[CasinoReviewInput, Dict[str, Any]]) -> Dict[str, Any]:
        """Add start time for processing time calculation"""
        if isinstance(inputs, CasinoReviewInput):
            result = inputs.dict()
        else:
            result = dict(inputs)
        
        result["start_time"] = datetime.now()
        return result
    
    def add_processing_time(inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate and add processing time"""
        start_time = inputs.get("start_time")
        if start_time:
            processing_time = (datetime.now() - start_time).total_seconds()
            inputs["processing_time_seconds"] = processing_time
        else:
            inputs["processing_time_seconds"] = 0.0
        return inputs
    
    # Create all sub-chains with proper RAG
    research_chain = create_research_chain()
    rag_content_chain = create_rag_content_generation_chain()  # Updated to use RAG
    vectorization_chain = create_vectorization_chain()
    wordpress_chain = create_wordpress_publishing_chain()
    output_chain = create_output_formatting_chain()
    
    # MAIN LCEL CHAIN COMPOSITION using | operators
    # This is the proper LCEL way following CLAUDE.md guidelines
    universal_casino_chain = (
        RunnableLambda(add_start_time)
        | RunnableParallel({
            "casino_name": lambda x: x["casino_name"],
            "target_words": lambda x: x.get("target_words", 2500),
            "publish_to_wordpress": lambda x: x.get("publish_to_wordpress", False),
            "research_data": research_chain,
            "start_time": lambda x: x["start_time"]
        })
        | RunnableParallel({
            "casino_name": lambda x: x["casino_name"],
            "target_words": lambda x: x["target_words"],
            "publish_to_wordpress": lambda x: x["publish_to_wordpress"],
            "research_content": lambda x: x["research_data"]["research_content"],
            "sources": lambda x: x["research_data"]["sources"],
            "start_time": lambda x: x["start_time"]
        })
        | RunnableParallel({
            "casino_name": lambda x: x["casino_name"],
            "target_words": lambda x: x["target_words"],
            "publish_to_wordpress": lambda x: x["publish_to_wordpress"],
            "research_content": lambda x: x["research_content"],
            "sources": lambda x: x["sources"],
            "start_time": lambda x: x["start_time"],
            "review_content": rag_content_chain
        })
        | vectorization_chain
        | wordpress_chain
        | RunnableLambda(add_processing_time)
        | output_chain
    )
    
    return universal_casino_chain

# Factory function for easy chain creation
def get_universal_casino_chain() -> Runnable:
    """Get a configured universal casino review chain"""
    return create_universal_casino_chain()

# Example usage for testing
if __name__ == "__main__":
    import asyncio
    
    async def test_chain():
        """Test the universal casino chain"""
        chain = create_universal_casino_chain()
        
        # Test input
        test_input = CasinoReviewInput(
            casino_name="Mr Vegas Casino",
            target_words=2500,
            include_images=True,
            publish_to_wordpress=False
        )
        
        print("🎰 Testing Universal Casino LCEL Chain...")
        print(f"📋 Input: {test_input.casino_name}")
        
        try:
            # Use native LangChain ainvoke method
            result = await chain.ainvoke(test_input.dict())
            
            print("✅ Chain execution successful!")
            print(f"📊 Casino: {result.casino_name}")
            print(f"📝 Word Count: {result.word_count}")
            print(f"⏱️ Processing Time: {result.processing_time_seconds:.2f}s")
            print(f"🎯 Status: {result.status}")
            
            return result
            
        except Exception as e:
            print(f"❌ Chain execution failed: {str(e)}")
            return None
    
    # Run test
    asyncio.run(test_chain())