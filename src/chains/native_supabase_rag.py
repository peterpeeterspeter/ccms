"""
🚀 Native LangChain Supabase RAG Chain
Following official LangChain documentation patterns exactly

Uses native SupabaseVectorStore + SelfQueryRetriever + LCEL chains
"""

import os
from typing import List, Dict, Any, Optional
from langchain_community.vectorstores import SupabaseVectorStore
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.retrievers.self_query.base import SelfQueryRetriever
from langchain.chains.query_constructor.schema import AttributeInfo
from langchain_core.documents import Document
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from supabase.client import create_client


class NativeSupabaseRAGChain:
    """Native LangChain Supabase integration following official patterns"""
    
    def __init__(self):
        self.embeddings = OpenAIEmbeddings()
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
        self.supabase_client = None
        self.vectorstore = None
        self.retriever = None
        self._setup_supabase()
        self._setup_metadata_schema()
        self._create_retriever()
        
    def _setup_supabase(self):
        """Native Supabase setup following LangChain documentation"""
        try:
            # Exact pattern from LangChain docs
            self.supabase_client = create_client(
                os.environ.get("SUPABASE_URL"), 
                os.environ.get("SUPABASE_SERVICE_KEY")
            )
            print("✅ Native Supabase client initialized")
        except Exception as e:
            print(f"⚠️ Supabase setup failed: {e}")
    
    def _setup_metadata_schema(self):
        """Define metadata fields for SelfQueryRetriever"""
        # Native LangChain metadata schema for casino intelligence
        self.metadata_field_info = [
            AttributeInfo(
                name="casino_name",
                description="The name of the casino",
                type="string"
            ),
            AttributeInfo(
                name="license_type", 
                description="Casino license type (e.g., Curacao, Malta, UK)",
                type="string"
            ),
            AttributeInfo(
                name="overall_rating",
                description="Overall casino rating from 1-10",
                type="float"
            ),
            AttributeInfo(
                name="game_count",
                description="Number of games available",
                type="integer"
            ),
            AttributeInfo(
                name="established_year",
                description="Year the casino was established",
                type="integer"
            ),
            AttributeInfo(
                name="payment_methods",
                description="Available payment methods",
                type="string"
            ),
            AttributeInfo(
                name="content_type",
                description="Type of content (review, bonus_info, game_info, etc.)",
                type="string"
            )
        ]
        
    def _create_retriever(self):
        """Create SelfQueryRetriever using native LangChain pattern"""
        if not self.supabase_client:
            print("⚠️ Cannot create retriever without Supabase client")
            return
            
        try:
            # Native LangChain SupabaseVectorStore creation
            self.vectorstore = SupabaseVectorStore(
                client=self.supabase_client,
                embeddings=self.embeddings,
                table_name="documents",
                query_name="match_documents"
            )
            
            # Native SelfQueryRetriever creation
            self.retriever = SelfQueryRetriever.from_llm(
                self.llm,
                self.vectorstore,
                "Casino reviews and gambling information database",
                self.metadata_field_info,
                verbose=True
            )
            print("✅ Native SelfQueryRetriever created")
            
        except Exception as e:
            print(f"⚠️ Retriever creation failed: {e}")
    
    def add_casino_documents(self, casino_data: List[Dict[str, Any]]):
        """Add casino documents using native LangChain pattern"""
        if not self.vectorstore:
            print("⚠️ Vectorstore not available")
            return
            
        # Convert to native LangChain Documents
        documents = []
        for data in casino_data:
            doc = Document(
                page_content=data.get("content", ""),
                metadata={
                    "casino_name": data.get("casino_name"),
                    "license_type": data.get("license_type"),
                    "overall_rating": data.get("overall_rating"),
                    "game_count": data.get("game_count"),
                    "established_year": data.get("established_year"),
                    "payment_methods": data.get("payment_methods"),
                    "content_type": data.get("content_type", "review")
                }
            )
            documents.append(doc)
        
        # Native LangChain document addition
        try:
            self.vectorstore.add_documents(documents)
            print(f"✅ Added {len(documents)} documents to native Supabase vectorstore")
        except Exception as e:
            print(f"❌ Failed to add documents: {e}")
    
    def create_native_rag_chain(self):
        """Create RAG chain using native LangChain patterns"""
        if not self.retriever:
            print("⚠️ Retriever not available - creating basic chain")
            return self._create_fallback_chain()
        
        # Native LangChain RAG prompt
        prompt = ChatPromptTemplate.from_template("""
You are a professional casino reviewer writing engaging narrative reviews.

Use this context from our casino intelligence database:
{context}

Write a comprehensive, flowing narrative review about: {question}

Guidelines:
- Write naturally as a magazine article with engaging paragraphs
- NO bullet points or lists - pure narrative flow
- Integrate the database context naturally into your writing
- Include specific details about games, bonuses, licensing, and user experience
- Make it conversational and authoritative

Write your review:
""")
        
        # Native LCEL chain composition
        native_chain = (
            {
                "context": self.retriever | self._format_docs,
                "question": RunnablePassthrough()
            }
            | prompt
            | self.llm
            | StrOutputParser()
        )
        
        return native_chain
    
    def _create_fallback_chain(self):
        """Fallback chain when Supabase not available"""
        prompt = ChatPromptTemplate.from_template("""
You are a professional casino reviewer.

Write a comprehensive narrative review about: {question}

Write naturally as a magazine article with engaging paragraphs.
""")
        
        return prompt | self.llm | StrOutputParser()
    
    def _format_docs(self, docs: List[Document]) -> str:
        """Native document formatting"""
        return "\n\n".join([
            f"Casino: {doc.metadata.get('casino_name', 'Unknown')}\n"
            f"Rating: {doc.metadata.get('overall_rating', 'N/A')}\n"
            f"License: {doc.metadata.get('license_type', 'N/A')}\n"
            f"Content: {doc.page_content}"
            for doc in docs
        ])
    
    async def generate_review(self, query: str) -> str:
        """Generate review using native chain"""
        chain = self.create_native_rag_chain()
        return await chain.ainvoke(query)
    
    def query_casino_intelligence(self, query: str, filters: Optional[Dict] = None) -> List[Document]:
        """Query casino intelligence using native SelfQueryRetriever"""
        if not self.retriever:
            return []
        
        try:
            # Native SelfQueryRetriever usage
            docs = self.retriever.get_relevant_documents(query)
            return docs
        except Exception as e:
            print(f"Query failed: {e}")
            return []


# Example usage following LangChain docs
if __name__ == "__main__":
    import asyncio
    
    async def test_native_supabase_rag():
        """Test native Supabase RAG following LangChain patterns"""
        
        # Initialize native chain
        rag = NativeSupabaseRAGChain()
        
        # Add sample casino data (native pattern)
        sample_casino_data = [
            {
                "content": "Crashino Casino is a crypto-focused online casino established in 2021. Features over 5,500 games including crash games, slots, and live dealer options. Licensed in Curacao.",
                "casino_name": "Crashino",
                "license_type": "Curacao",
                "overall_rating": 7.8,
                "game_count": 5500,
                "established_year": 2021,
                "payment_methods": "Bitcoin, Ethereum, Visa, Skrill",
                "content_type": "review"
            }
        ]
        
        # Add to native vectorstore
        rag.add_casino_documents(sample_casino_data)
        
        # Test native retrieval
        query = "Tell me about Crashino casino's crash games and overall experience"
        result = await rag.generate_review(query)
        
        print("Native Supabase RAG Result:")
        print("=" * 50)
        print(result)
    
    asyncio.run(test_native_supabase_rag())