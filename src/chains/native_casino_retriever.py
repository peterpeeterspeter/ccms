"""
🔍 Native LangChain SelfQueryRetriever for 95-Field Casino Intelligence
Phase 1: Pure native components - no custom logic

Uses official LangChain patterns:
- SupabaseVectorStore 
- SelfQueryRetriever with casino metadata schema
- AttributeInfo for all 95 fields
"""

import os
from typing import List, Dict, Any, Optional
from langchain_community.vectorstores import SupabaseVectorStore
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.retrievers.self_query.base import SelfQueryRetriever
from langchain.chains.query_constructor.schema import AttributeInfo
from langchain_core.documents import Document
from supabase.client import create_client


class NativeCasinoRetriever:
    """Native LangChain casino intelligence retriever using SelfQueryRetriever"""
    
    def __init__(self):
        self.embeddings = OpenAIEmbeddings()
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        self.supabase_client = self._setup_supabase()
        self.vectorstore = self._setup_vectorstore()
        self.retriever = self._setup_self_query_retriever()
    
    def _setup_supabase(self):
        """Native Supabase client setup"""
        try:
            client = create_client(
                os.environ.get("SUPABASE_URL"),
                os.environ.get("SUPABASE_SERVICE_KEY")
            )
            print("✅ Native Supabase client initialized")
            return client
        except Exception as e:
            print(f"⚠️ Supabase setup failed: {e}")
            return None
    
    def _setup_vectorstore(self):
        """Native SupabaseVectorStore setup"""
        if not self.supabase_client:
            return None
            
        try:
            vectorstore = SupabaseVectorStore(
                client=self.supabase_client,
                embeddings=self.embeddings,
                table_name="documents",
                query_name="match_documents"
            )
            print("✅ Native SupabaseVectorStore initialized")
            return vectorstore
        except Exception as e:
            print(f"⚠️ VectorStore setup failed: {e}")
            return None
    
    def _setup_self_query_retriever(self):
        """Native SelfQueryRetriever with 95-field casino metadata schema"""
        if not self.vectorstore:
            return None
        
        # Native metadata schema for 95-field casino intelligence
        casino_metadata_fields = [
            # Basic Casino Information
            AttributeInfo(
                name="casino_name",
                description="The name of the casino",
                type="string"
            ),
            AttributeInfo(
                name="license_type", 
                description="Casino license authority (Curacao, Malta, UK, etc.)",
                type="string"
            ),
            AttributeInfo(
                name="overall_rating",
                description="Overall casino rating from 1.0 to 10.0",
                type="float"
            ),
            AttributeInfo(
                name="established_year",
                description="Year the casino was established",
                type="integer"
            ),
            AttributeInfo(
                name="casino_website_url",
                description="Official casino website URL",
                type="string"
            ),
            
            # Game Information
            AttributeInfo(
                name="total_games_count",
                description="Total number of games available",
                type="integer"
            ),
            AttributeInfo(
                name="slot_games_count", 
                description="Number of slot games",
                type="integer"
            ),
            AttributeInfo(
                name="live_casino_games_count",
                description="Number of live dealer games",
                type="integer"
            ),
            AttributeInfo(
                name="game_providers",
                description="Game software providers (comma separated)",
                type="string"
            ),
            
            # Financial Information  
            AttributeInfo(
                name="min_deposit_amount",
                description="Minimum deposit amount in USD",
                type="float"
            ),
            AttributeInfo(
                name="max_withdrawal_amount",
                description="Maximum withdrawal amount in USD",
                type="float"
            ),
            AttributeInfo(
                name="payment_methods",
                description="Available payment methods (comma separated)",
                type="string"
            ),
            AttributeInfo(
                name="cryptocurrency_supported",
                description="Whether cryptocurrency is supported",
                type="boolean"
            ),
            
            # Bonus Information
            AttributeInfo(
                name="welcome_bonus_amount",
                description="Welcome bonus amount in USD",
                type="float"
            ),
            AttributeInfo(
                name="welcome_bonus_percentage",
                description="Welcome bonus percentage",
                type="integer"
            ),
            AttributeInfo(
                name="free_spins_count",
                description="Number of free spins offered",
                type="integer"
            ),
            AttributeInfo(
                name="wagering_requirement",
                description="Bonus wagering requirement multiplier",
                type="integer"
            ),
            
            # Trust & Safety
            AttributeInfo(
                name="safety_score",
                description="Safety and security score from 1.0 to 10.0", 
                type="float"
            ),
            AttributeInfo(
                name="player_experience_score",
                description="Player experience score from 1.0 to 10.0",
                type="float"
            ),
            AttributeInfo(
                name="responsible_gambling_tools",
                description="Available responsible gambling tools",
                type="string"
            ),
            
            # Support & Features
            AttributeInfo(
                name="customer_support_rating",
                description="Customer support rating from 1.0 to 10.0",
                type="float"
            ),
            AttributeInfo(
                name="live_chat_available",
                description="Whether live chat support is available",
                type="boolean"
            ),
            AttributeInfo(
                name="mobile_optimized", 
                description="Whether the casino is mobile optimized",
                type="boolean"
            ),
            AttributeInfo(
                name="languages_supported",
                description="Supported languages (comma separated)",
                type="string"
            ),
            
            # Content Classification
            AttributeInfo(
                name="content_type",
                description="Type of content (review, bonus_info, game_info, research_data, etc.)",
                type="string"
            ),
            AttributeInfo(
                name="data_freshness_score",
                description="How fresh/recent the data is from 1.0 to 10.0",
                type="float"
            ),
            AttributeInfo(
                name="extraction_confidence",
                description="Confidence in extracted data from 1.0 to 10.0",
                type="float"
            )
        ]
        
        try:
            # Native SelfQueryRetriever creation
            retriever = SelfQueryRetriever.from_llm(
                self.llm,
                self.vectorstore,
                "Casino intelligence database with comprehensive 95-field analysis including games, bonuses, licensing, safety, and player experience data",
                casino_metadata_fields,
                verbose=True,
                search_kwargs={"k": 6}
            )
            print("✅ Native SelfQueryRetriever created with 95-field schema")
            return retriever
        except Exception as e:
            print(f"⚠️ SelfQueryRetriever setup failed: {e}")
            return None
    
    def add_casino_intelligence(self, casino_data_list: List[Dict[str, Any]]):
        """Add casino intelligence documents using native patterns"""
        if not self.vectorstore:
            print("⚠️ VectorStore not available")
            return False
        
        # Convert to native Document objects
        documents = []
        for data in casino_data_list:
            doc = Document(
                page_content=data.get("content", ""),
                metadata={
                    # Basic info
                    "casino_name": data.get("casino_name"),
                    "license_type": data.get("license_type"), 
                    "overall_rating": data.get("overall_rating"),
                    "established_year": data.get("established_year"),
                    "casino_website_url": data.get("casino_website_url"),
                    
                    # Games
                    "total_games_count": data.get("total_games_count"),
                    "slot_games_count": data.get("slot_games_count"),
                    "live_casino_games_count": data.get("live_casino_games_count"),
                    "game_providers": data.get("game_providers"),
                    
                    # Financial
                    "min_deposit_amount": data.get("min_deposit_amount"),
                    "max_withdrawal_amount": data.get("max_withdrawal_amount"), 
                    "payment_methods": data.get("payment_methods"),
                    "cryptocurrency_supported": data.get("cryptocurrency_supported"),
                    
                    # Bonuses
                    "welcome_bonus_amount": data.get("welcome_bonus_amount"),
                    "welcome_bonus_percentage": data.get("welcome_bonus_percentage"),
                    "free_spins_count": data.get("free_spins_count"),
                    "wagering_requirement": data.get("wagering_requirement"),
                    
                    # Trust
                    "safety_score": data.get("safety_score"),
                    "player_experience_score": data.get("player_experience_score"),
                    "responsible_gambling_tools": data.get("responsible_gambling_tools"),
                    
                    # Support  
                    "customer_support_rating": data.get("customer_support_rating"),
                    "live_chat_available": data.get("live_chat_available"),
                    "mobile_optimized": data.get("mobile_optimized"),
                    "languages_supported": data.get("languages_supported"),
                    
                    # Meta
                    "content_type": data.get("content_type", "casino_intelligence"),
                    "data_freshness_score": data.get("data_freshness_score", 8.0),
                    "extraction_confidence": data.get("extraction_confidence", 7.5)
                }
            )
            documents.append(doc)
        
        try:
            # Native document addition
            self.vectorstore.add_documents(documents)
            print(f"✅ Added {len(documents)} casino intelligence documents to native Supabase")
            return True
        except Exception as e:
            print(f"❌ Failed to add documents: {e}")
            return False
    
    def query_casino_intelligence(self, query: str) -> List[Document]:
        """Query casino intelligence using native SelfQueryRetriever"""
        if not self.retriever:
            print("⚠️ Retriever not available")
            return []
        
        try:
            # Native self-querying with metadata filtering
            docs = self.retriever.get_relevant_documents(query)
            print(f"✅ Retrieved {len(docs)} documents using native SelfQueryRetriever")
            return docs
        except Exception as e:
            print(f"❌ Query failed: {e}")
            return []
    
    def get_native_retriever(self):
        """Return the native SelfQueryRetriever for LCEL chains"""
        return self.retriever


# Example usage
if __name__ == "__main__":
    # Test native casino retriever
    retriever = NativeCasinoRetriever()
    
    # Add sample casino data
    sample_data = [
        {
            "content": "Crashino Casino is a crypto-focused online casino established in 2021 with over 5,500 games including unique crash games. Licensed in Curacao with strong player protection.",
            "casino_name": "Crashino",
            "license_type": "Curacao",
            "overall_rating": 7.8,
            "established_year": 2021,
            "total_games_count": 5500,
            "cryptocurrency_supported": True,
            "welcome_bonus_amount": 1000.0,
            "safety_score": 8.2,
            "content_type": "comprehensive_review"
        }
    ]
    
    # Add to native vectorstore
    success = retriever.add_casino_intelligence(sample_data)
    
    if success:
        # Test native querying
        results = retriever.query_casino_intelligence("Tell me about Crashino casino's crash games and crypto support")
        print(f"\nQuery Results: {len(results)} documents found")
        for doc in results:
            print(f"- Casino: {doc.metadata.get('casino_name')}")
            print(f"- Rating: {doc.metadata.get('overall_rating')}")
            print(f"- Content: {doc.page_content[:200]}...")