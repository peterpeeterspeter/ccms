"""
🔗 Native LangChain Casino RAG Chain
Phase 1: Pure LCEL chain with native SelfQueryRetriever integration

Uses official LangChain patterns:
- Native LCEL chain composition (retriever | prompt | model | parser)
- SelfQueryRetriever for 95-field casino intelligence
- ChatPromptTemplate for prompts
- RunnablePassthrough for data flow
"""

from typing import List, Dict, Any, Optional
from langchain_core.runnables import RunnablePassthrough, RunnableLambda, RunnableParallel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI
from chains.native_casino_retriever import NativeCasinoRetriever


class NativeCasinoRAGChain:
    """Native LangChain RAG chain using SelfQueryRetriever and LCEL"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
            max_tokens=3000
        )
        self.casino_retriever = NativeCasinoRetriever()
        self.native_retriever = self.casino_retriever.get_native_retriever()
        self.rag_chain = self._create_native_rag_chain()
    
    def _create_native_rag_chain(self):
        """Create pure native LCEL RAG chain"""
        
        if not self.native_retriever:
            print("⚠️ Native retriever not available - creating fallback chain")
            return self._create_fallback_chain()
        
        # Native casino review prompt
        casino_prompt = ChatPromptTemplate.from_template("""
You are a professional casino reviewer writing comprehensive, engaging magazine-style reviews.

You have access to our comprehensive casino intelligence database with 95-field analysis including:
- Casino licensing and safety information
- Complete games portfolio and software providers  
- Bonus structures and promotional offers
- Payment methods and financial details
- Player experience metrics and ratings
- Customer support and features

CASINO INTELLIGENCE CONTEXT:
{context}

USER QUERY: {question}

Write a comprehensive, flowing narrative casino review that:

1. **NARRATIVE FLOW**: Write naturally as an engaging magazine article with smooth paragraph transitions
2. **NO BULLET POINTS**: Use pure narrative prose - avoid any lists, bullet points, or structured formatting
3. **INTELLIGENCE INTEGRATION**: Seamlessly weave specific data from our casino intelligence database into the narrative
4. **COMPREHENSIVE COVERAGE**: Address games, bonuses, licensing, safety, user experience, and unique features
5. **AUTHORITATIVE TONE**: Write with confidence based on our extensive database analysis
6. **ENGAGING STYLE**: Make it conversational and interesting while maintaining professionalism

Focus on telling the complete story of what it's like to experience this casino, using our intelligence data to provide specific, credible details throughout the narrative.

Your comprehensive review:""")
        
        # Pure native LCEL chain composition
        native_rag_chain = (
            {
                "context": self.native_retriever | RunnableLambda(self._format_casino_context),
                "question": RunnablePassthrough()
            }
            | casino_prompt
            | self.llm  
            | StrOutputParser()
        )
        
        print("✅ Native LCEL RAG chain created with SelfQueryRetriever")
        return native_rag_chain
    
    def _create_fallback_chain(self):
        """Fallback chain when native retriever unavailable"""
        
        fallback_prompt = ChatPromptTemplate.from_template("""
You are a professional casino reviewer.

Write a comprehensive narrative review about: {question}

Focus on creating engaging, magazine-style content with natural paragraph flow.
""")
        
        return (
            RunnablePassthrough()
            | RunnableLambda(lambda x: {"question": x})
            | fallback_prompt
            | self.llm
            | StrOutputParser()
        )
    
    def _format_casino_context(self, docs: List[Document]) -> str:
        """Format casino intelligence context from retrieved documents"""
        if not docs:
            return "No casino intelligence data available."
        
        context_parts = []
        
        for doc in docs:
            # Extract key intelligence fields from metadata
            metadata = doc.metadata
            casino_name = metadata.get('casino_name', 'Unknown Casino')
            
            # Build structured context from 95-field data
            intelligence_summary = []
            
            # Basic Info
            if metadata.get('license_type'):
                intelligence_summary.append(f"Licensed: {metadata['license_type']}")
            if metadata.get('overall_rating'):
                intelligence_summary.append(f"Overall Rating: {metadata['overall_rating']}/10")
            if metadata.get('established_year'):
                intelligence_summary.append(f"Established: {metadata['established_year']}")
            
            # Games & Features
            if metadata.get('total_games_count'):
                intelligence_summary.append(f"Games: {metadata['total_games_count']} total")
            if metadata.get('game_providers'):
                intelligence_summary.append(f"Providers: {metadata['game_providers']}")
            if metadata.get('cryptocurrency_supported'):
                intelligence_summary.append(f"Crypto: {'Supported' if metadata['cryptocurrency_supported'] else 'Not supported'}")
            
            # Financial
            if metadata.get('welcome_bonus_amount'):
                intelligence_summary.append(f"Welcome Bonus: ${metadata['welcome_bonus_amount']}")
            if metadata.get('payment_methods'):
                intelligence_summary.append(f"Payment Methods: {metadata['payment_methods']}")
            
            # Trust & Safety
            if metadata.get('safety_score'):
                intelligence_summary.append(f"Safety Score: {metadata['safety_score']}/10")
            if metadata.get('customer_support_rating'):
                intelligence_summary.append(f"Support Rating: {metadata['customer_support_rating']}/10")
            
            # Meta info
            if metadata.get('content_type'):
                intelligence_summary.append(f"Data Type: {metadata['content_type']}")
            
            context_entry = f"""
CASINO: {casino_name}
INTELLIGENCE DATA: {' | '.join(intelligence_summary)}
CONTENT: {doc.page_content}
---"""
            
            context_parts.append(context_entry)
        
        return "\n".join(context_parts)
    
    def add_casino_intelligence_data(self, casino_data_list: List[Dict[str, Any]]) -> bool:
        """Add casino intelligence to native vectorstore"""
        return self.casino_retriever.add_casino_intelligence(casino_data_list)
    
    async def generate_casino_review(self, query: str) -> str:
        """Generate casino review using native RAG chain"""
        try:
            print(f"📝 Generating casino review using native LCEL RAG chain")
            result = await self.rag_chain.ainvoke(query)
            print(f"✅ Generated {len(result)} characters using native components")
            return result
        except Exception as e:
            print(f"❌ Native RAG generation failed: {e}")
            return f"Review generation failed: {e}"
    
    def generate_casino_review_sync(self, query: str) -> str:
        """Synchronous version for easier integration"""
        try:
            result = self.rag_chain.invoke(query)
            return result
        except Exception as e:
            return f"Review generation failed: {e}"
    
    def query_casino_intelligence_directly(self, query: str) -> List[Document]:
        """Direct access to native SelfQueryRetriever for testing"""
        return self.casino_retriever.query_casino_intelligence(query)


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test_native_casino_rag():
        """Test native casino RAG chain"""
        
        print("🔗 Testing Native Casino RAG Chain")
        print("=" * 50)
        
        # Initialize native RAG
        rag_chain = NativeCasinoRAGChain()
        
        # Add sample casino intelligence data
        sample_data = [
            {
                "content": "Crashino Casino is a cryptocurrency-focused online casino that launched in 2021. The platform specializes in crash games alongside a comprehensive selection of traditional casino games. With over 5,500 games from top providers like Pragmatic Play and Evolution Gaming, Crashino offers a diverse gaming experience. The casino operates under a Curacao license and has gained recognition for its innovative approach to crypto gambling.",
                "casino_name": "Crashino",
                "license_type": "Curacao",
                "overall_rating": 7.8,
                "established_year": 2021,
                "casino_website_url": "https://crashino.com",
                "total_games_count": 5500,
                "slot_games_count": 4000,
                "live_casino_games_count": 200,
                "game_providers": "Pragmatic Play, Evolution Gaming, NetEnt, Quickspin",
                "min_deposit_amount": 10.0,
                "max_withdrawal_amount": 10000.0,
                "payment_methods": "Bitcoin, Ethereum, Litecoin, Visa, Mastercard, Skrill",
                "cryptocurrency_supported": True,
                "welcome_bonus_amount": 1000.0,
                "welcome_bonus_percentage": 100,
                "free_spins_count": 100,
                "wagering_requirement": 35,
                "safety_score": 8.2,
                "player_experience_score": 7.9,
                "customer_support_rating": 8.5,
                "live_chat_available": True,
                "mobile_optimized": True,
                "content_type": "comprehensive_analysis",
                "data_freshness_score": 9.0,
                "extraction_confidence": 8.8
            }
        ]
        
        # Add to native vectorstore
        success = rag_chain.add_casino_intelligence_data(sample_data)
        print(f"Data added to native vectorstore: {success}")
        
        if success:
            # Test native RAG generation
            query = "Write a comprehensive review of Crashino Casino focusing on their crash games specialization, cryptocurrency support, and overall player experience"
            
            result = await rag_chain.generate_casino_review(query)
            
            print("\n🎯 NATIVE RAG RESULT:")
            print("=" * 40)
            print(f"Length: {len(result)} characters")
            
            # Check for narrative style
            bullet_count = sum(result.count(indicator) for indicator in ['•', '- ', '* ', '1. ', '2. '])
            print(f"Bullet points found: {bullet_count}")
            print(f"Style: {'NARRATIVE' if bullet_count < 5 else 'STRUCTURED'}")
            
            print("\n📖 REVIEW PREVIEW:")
            print("-" * 40) 
            print(result[:1000] + "...")
            print("-" * 40)
    
    # Run test
    asyncio.run(test_native_casino_rag())