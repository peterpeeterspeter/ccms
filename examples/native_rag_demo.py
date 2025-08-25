"""
Native LangChain Universal RAG Demo
==================================

Demonstrates the native LangChain implementation with real examples.
Shows how to use all the native components and LCEL patterns.
"""

import asyncio
import os
import logging
from pathlib import Path
from typing import List

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add src to path for imports
import sys
sys.path.append(str(Path(__file__).parent.parent / "src"))

from chains.native_universal_rag_lcel import (
    create_native_universal_rag_chain,
    create_native_retrieval_qa_chain,
    create_native_conversational_chain,
    NativeUniversalRAGChain
)

# Native LangChain document processing
from langchain_core.documents import Document
from langchain_community.document_loaders import TextLoader, WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


async def demo_native_rag():
    """Comprehensive demo of the native RAG implementation"""
    
    logger.info("🚀 Starting Native LangChain Universal RAG Demo")
    
    # 1. Create the native chain
    logger.info("📦 Creating Native Universal RAG Chain...")
    
    chain = create_native_universal_rag_chain(
        model_name="gpt-4o-mini",
        temperature=0.1,
        vector_store_type="faiss",
        enable_caching=bool(os.getenv("REDIS_URL")),
        enable_memory=True,
        enable_web_search=bool(os.getenv("TAVILY_API_KEY"))
    )
    
    # 2. Add some sample casino documents
    logger.info("📚 Adding sample documents to vector store...")
    
    sample_documents = [
        Document(
            page_content="""Betway Casino is a well-established online casino licensed by the Malta Gaming Authority (MGA). 
            It offers over 500 slot games from top providers like NetEnt, Microgaming, and Pragmatic Play. 
            The casino provides a welcome bonus of up to $1,000 with reasonable wagering requirements of 30x.
            Payment methods include Visa, Mastercard, PayPal, and Skrill with processing times of 24-48 hours for withdrawals.
            The casino is known for its excellent customer support and mobile-responsive website.""",
            metadata={"source": "betway_review.txt", "casino": "Betway"}
        ),
        Document(
            page_content="""888 Casino is a publicly traded company licensed in Gibraltar and the UK. 
            It features exclusive games from its own 888 Holdings software as well as games from NetEnt and IGT.
            The casino offers a no-deposit bonus of $88 plus a 100% match bonus up to $200 on first deposit.
            It supports multiple currencies including USD, EUR, and GBP. Withdrawal times are typically 1-2 business days.
            The casino has won multiple awards for its software and customer service.""",
            metadata={"source": "888_review.txt", "casino": "888 Casino"}
        ),
        Document(
            page_content="""LeoVegas is a Swedish online casino known as the "King of Mobile Casino". 
            Licensed by the Malta Gaming Authority and UK Gambling Commission.
            It offers over 1,000 games including slots, live casino, and sports betting.
            The welcome package includes up to $1,000 bonus plus 200 free spins across four deposits.
            Popular payment methods include bank transfer, e-wallets, and cryptocurrency options.
            Known for fast withdrawals typically processed within 24 hours.""",
            metadata={"source": "leovegas_review.txt", "casino": "LeoVegas"}
        )
    ]
    
    chain.add_documents(sample_documents)
    
    # 3. Test various query types
    test_queries = [
        "Which casino has the fastest withdrawal times?",
        "Tell me about Betway Casino's game selection and licensing",
        "Compare the welcome bonuses offered by these casinos",
        "What payment methods does 888 Casino accept?",
        "Which casino would you recommend for mobile gaming?"
    ]
    
    logger.info("🔍 Testing various queries...")
    
    for i, query in enumerate(test_queries, 1):
        logger.info(f"\n--- Query {i}: {query} ---")
        
        try:
            # Test synchronous invocation
            result = chain.invoke(query)
            
            if isinstance(result, dict) and "content" in result:
                content = result["content"]
                logger.info(f"✅ Result: {content[:200]}...")
            else:
                logger.info(f"✅ Result: {str(result)[:200]}...")
                
        except Exception as e:
            logger.error(f"❌ Query failed: {str(e)}")
    
    # 4. Test streaming
    logger.info("\n🌊 Testing streaming response...")
    
    try:
        stream_query = "Provide a comprehensive review of Betway Casino"
        logger.info(f"Streaming query: {stream_query}")
        
        for chunk in chain.stream(stream_query):
            if isinstance(chunk, dict) and "content" in chunk:
                print(chunk["content"][:50] + "...", end=" ")
            elif isinstance(chunk, str):
                print(chunk[:50] + "...", end=" ")
        print("\n✅ Streaming completed")
        
    except Exception as e:
        logger.error(f"❌ Streaming failed: {str(e)}")
    
    # 5. Test similarity search
    logger.info("\n🔍 Testing similarity search...")
    
    try:
        similar_docs = chain.similarity_search("mobile casino gaming", k=3)
        logger.info(f"Found {len(similar_docs)} similar documents:")
        
        for i, doc in enumerate(similar_docs, 1):
            logger.info(f"[{i}] {doc.metadata.get('source', 'Unknown')}: {doc.page_content[:100]}...")
            
    except Exception as e:
        logger.error(f"❌ Similarity search failed: {str(e)}")


async def demo_alternative_chains():
    """Demo the alternative native chain implementations"""
    
    logger.info("\n🔧 Testing Alternative Native Chain Implementations")
    
    # 1. Test RetrievalQA Chain
    logger.info("\n📋 Testing Native RetrievalQA Chain...")
    
    try:
        qa_chain = create_native_retrieval_qa_chain(
            vector_store_type="faiss",
            model_name="gpt-4o-mini"
        )
        
        qa_result = qa_chain({"query": "What makes a casino trustworthy?"})
        
        logger.info("✅ RetrievalQA successful!")
        if "result" in qa_result:
            logger.info(f"Answer: {qa_result['result'][:200]}...")
        if "source_documents" in qa_result:
            logger.info(f"Sources: {len(qa_result['source_documents'])} documents")
            
    except Exception as e:
        logger.error(f"❌ RetrievalQA failed: {str(e)}")
    
    # 2. Test ConversationalRetrievalChain
    logger.info("\n💬 Testing Native Conversational Chain...")
    
    try:
        conv_chain = create_native_conversational_chain(
            vector_store_type="faiss", 
            model_name="gpt-4o-mini"
        )
        
        # First conversation turn
        conv_result1 = conv_chain({
            "question": "What are the licensing requirements for online casinos?",
            "chat_history": []
        })
        
        logger.info("✅ First conversation turn successful!")
        if "answer" in conv_result1:
            logger.info(f"Answer 1: {conv_result1['answer'][:200]}...")
        
        # Second conversation turn (with history)
        chat_history = [(
            "What are the licensing requirements for online casinos?",
            conv_result1.get("answer", "")
        )]
        
        conv_result2 = conv_chain({
            "question": "Which of these requirements are most important for players?", 
            "chat_history": chat_history
        })
        
        logger.info("✅ Second conversation turn successful!")
        if "answer" in conv_result2:
            logger.info(f"Answer 2: {conv_result2['answer'][:200]}...")
            
    except Exception as e:
        logger.error(f"❌ Conversational chain failed: {str(e)}")


def demo_document_loading():
    """Demonstrate native LangChain document loading and processing"""
    
    logger.info("\n📄 Demonstrating Native Document Loading...")
    
    # 1. Create sample text file
    sample_text = """
    Casumo Casino Review
    
    Casumo is an award-winning online casino established in 2012. Licensed by the Malta Gaming Authority 
    and the UK Gambling Commission, it offers a safe and secure gaming environment.
    
    Game Selection:
    - Over 2,000 slot games from top providers
    - Live casino games powered by Evolution Gaming
    - Table games including blackjack, roulette, and baccarat
    
    Bonuses:
    - Welcome package: 200% up to $500 + 200 free spins
    - Regular promotions and tournaments
    - VIP loyalty program with exclusive rewards
    
    Payment Methods:
    - Credit/debit cards (Visa, Mastercard)
    - E-wallets (PayPal, Skrill, Neteller)
    - Bank transfers
    - Processing time: 24-72 hours for withdrawals
    
    Customer Support:
    - 24/7 live chat support
    - Email support
    - Comprehensive FAQ section
    """
    
    # Save to file
    sample_file = Path("sample_casino_review.txt")
    sample_file.write_text(sample_text)
    
    try:
        # 2. Load using TextLoader
        logger.info("📖 Loading document with TextLoader...")
        
        loader = TextLoader(str(sample_file))
        documents = loader.load()
        
        logger.info(f"✅ Loaded {len(documents)} document(s)")
        logger.info(f"Content preview: {documents[0].page_content[:200]}...")
        
        # 3. Split document using RecursiveCharacterTextSplitter
        logger.info("✂️ Splitting document with RecursiveCharacterTextSplitter...")
        
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n\n", "\n", " ", ""]
        )
        
        splits = splitter.split_documents(documents)
        
        logger.info(f"✅ Split into {len(splits)} chunks")
        for i, split in enumerate(splits[:3], 1):
            logger.info(f"Chunk {i}: {split.page_content[:100]}...")
        
        # 4. Add to vector store
        logger.info("📚 Adding splits to vector store...")
        
        chain = create_native_universal_rag_chain()
        chain.add_documents(splits)
        
        logger.info("✅ Documents added successfully!")
        
        # 5. Test retrieval
        test_query = "What bonuses does Casumo offer?"
        result = chain.invoke(test_query)
        
        logger.info(f"🔍 Test query result: {str(result)[:200]}...")
        
    except Exception as e:
        logger.error(f"❌ Document processing failed: {str(e)}")
    
    finally:
        # Clean up
        if sample_file.exists():
            sample_file.unlink()
            logger.info("🗑️ Cleaned up sample file")


async def demo_web_loading():
    """Demonstrate web-based document loading"""
    
    logger.info("\n🌐 Demonstrating Web Document Loading...")
    
    try:
        # Load a web page (using a simple, reliable URL)
        logger.info("🔗 Loading web content with WebBaseLoader...")
        
        # Use a simple page that should be accessible
        urls = ["https://httpbin.org/html"]  # Simple HTML test page
        
        loader = WebBaseLoader(urls)
        web_docs = loader.load()
        
        logger.info(f"✅ Loaded {len(web_docs)} web document(s)")
        
        if web_docs:
            logger.info(f"Content preview: {web_docs[0].page_content[:200]}...")
            logger.info(f"Metadata: {web_docs[0].metadata}")
            
            # Add to chain
            chain = create_native_universal_rag_chain()
            chain.add_documents(web_docs)
            
            logger.info("✅ Web documents added to vector store")
        
    except Exception as e:
        logger.error(f"❌ Web loading failed: {str(e)}")


async def main():
    """Run all demos"""
    
    logger.info("🎬 Starting Complete Native LangChain RAG Demo")
    
    # Check for required environment variables
    env_status = {
        "OpenAI API Key": bool(os.getenv("OPENAI_API_KEY")),
        "Redis URL": bool(os.getenv("REDIS_URL")),
        "Tavily API Key": bool(os.getenv("TAVILY_API_KEY"))
    }
    
    logger.info("🔑 Environment Status:")
    for key, status in env_status.items():
        status_icon = "✅" if status else "❌"
        logger.info(f"{status_icon} {key}: {'Available' if status else 'Missing'}")
    
    if not env_status["OpenAI API Key"]:
        logger.error("❌ OpenAI API Key is required. Please set OPENAI_API_KEY environment variable.")
        return
    
    try:
        # Run all demos
        await demo_native_rag()
        await demo_alternative_chains()
        demo_document_loading()
        await demo_web_loading()
        
        logger.info("🎉 All demos completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Demo failed: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())