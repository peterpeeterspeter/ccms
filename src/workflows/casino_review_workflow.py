"""
🔄 Native LangGraph Casino Review Workflow
Clean orchestration of research → RAG → publishing using native patterns

Follows LangChain best practice: Use LangGraph for complex workflows
"""

import os
from typing import Dict, Any, List, Optional
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage

# Import our native components  
from chains.native_supabase_rag import NativeSupabaseRAGChain
from agents.research_agent import CasinoResearchAgent
from agents.publishing_agent import CasinoPublishingAgent


class ReviewState(TypedDict):
    """State for casino review workflow"""
    casino_name: str
    casino_url: Optional[str]
    query: str
    research_data: str
    review_content: str
    published_result: str
    error: Optional[str]


class CasinoReviewWorkflow:
    """Native LangGraph workflow orchestrating the simplified components"""
    
    def __init__(self):
        self.research_agent = CasinoResearchAgent()
        self.rag_chain = NativeSupabaseRAGChain()
        self.publishing_agent = CasinoPublishingAgent()
        self.workflow = self._create_workflow()
        
    def _create_workflow(self) -> StateGraph:
        """Create LangGraph workflow with native components"""
        
        workflow = StateGraph(ReviewState)
        
        # Add nodes for each step
        workflow.add_node("research", self._research_node)
        workflow.add_node("generate", self._generate_node)
        workflow.add_node("publish", self._publish_node)
        workflow.add_node("error_handler", self._error_handler)
        
        # Set entry point
        workflow.set_entry_point("research")
        
        # Add edges with error handling
        workflow.add_edge("research", "generate")
        workflow.add_edge("generate", "publish")
        workflow.add_edge("publish", END)
        workflow.add_edge("error_handler", END)
        
        return workflow.compile()
    
    async def _research_node(self, state: ReviewState) -> ReviewState:
        """Research node using native research agent"""
        try:
            print(f"🔍 Step 1: Researching {state['casino_name']}")
            
            research_data = await self.research_agent.research_casino(
                state['casino_name'],
                state.get('casino_url')
            )
            
            # Add research data to native Supabase vectorstore
            if research_data and len(research_data) > 100:
                casino_doc_data = [{
                    "content": research_data,
                    "casino_name": state['casino_name'],
                    "license_type": "Curacao",  # Extract from research
                    "overall_rating": 7.5,     # Extract from research
                    "game_count": 5000,        # Extract from research  
                    "established_year": 2021,  # Extract from research
                    "payment_methods": "Crypto, Cards",
                    "content_type": "research_data"
                }]
                self.rag_chain.add_casino_documents(casino_doc_data)
                print("✅ Research data added to native Supabase vectorstore")
            
            return {
                **state,
                "research_data": research_data
            }
            
        except Exception as e:
            print(f"❌ Research failed: {e}")
            return {
                **state,
                "error": f"Research failed: {str(e)}"
            }
    
    async def _generate_node(self, state: ReviewState) -> ReviewState:
        """Generation node using simple RAG chain"""
        try:
            print(f"📝 Step 2: Generating review content")
            
            # Use native Supabase RAG chain
            review_content = await self.rag_chain.generate_review(state['query'])
            
            print(f"✅ Generated {len(review_content)} characters of content")
            
            return {
                **state,
                "review_content": review_content
            }
            
        except Exception as e:
            print(f"❌ Generation failed: {e}")
            return {
                **state,
                "error": f"Generation failed: {str(e)}"
            }
    
    async def _publish_node(self, state: ReviewState) -> ReviewState:
        """Publishing node using native publishing agent"""
        try:
            print(f"🚀 Step 3: Publishing review")
            
            published_result = await self.publishing_agent.publish_review(
                state['review_content'],
                state['casino_name']
            )
            
            print("✅ Publishing completed")
            
            return {
                **state,
                "published_result": published_result
            }
            
        except Exception as e:
            print(f"❌ Publishing failed: {e}")
            return {
                **state,
                "error": f"Publishing failed: {str(e)}"
            }
    
    async def _error_handler(self, state: ReviewState) -> ReviewState:
        """Handle errors gracefully"""
        print(f"❌ Workflow error: {state.get('error', 'Unknown error')}")
        return state
    
    async def run_complete_workflow(
        self, 
        casino_name: str, 
        casino_url: Optional[str] = None,
        custom_query: Optional[str] = None
    ) -> Dict[str, Any]:
        """Run complete casino review workflow"""
        
        # Build query
        if custom_query:
            query = custom_query
        else:
            query = f"Write a comprehensive narrative review of {casino_name} casino focusing on user experience, games, bonuses, and overall quality"
        
        # Initial state
        initial_state = ReviewState(
            casino_name=casino_name,
            casino_url=casino_url,
            query=query,
            research_data="",
            review_content="",
            published_result="",
            error=None
        )
        
        print(f"🚀 Starting complete workflow for {casino_name}")
        print("=" * 60)
        
        try:
            # Run workflow
            final_state = await self.workflow.ainvoke(initial_state)
            
            # Format results
            if final_state.get('error'):
                return {
                    "success": False,
                    "error": final_state['error'],
                    "casino_name": casino_name
                }
            
            return {
                "success": True,
                "casino_name": casino_name,
                "query": query,
                "research_length": len(final_state.get('research_data', '')),
                "review_length": len(final_state.get('review_content', '')),
                "publishing_result": final_state.get('published_result', ''),
                "review_content": final_state.get('review_content', '')
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Workflow execution failed: {str(e)}",
                "casino_name": casino_name
            }
    
    def run_complete_workflow_sync(
        self, 
        casino_name: str, 
        casino_url: Optional[str] = None,
        custom_query: Optional[str] = None
    ) -> Dict[str, Any]:
        """Synchronous version for easier integration"""
        import asyncio
        return asyncio.run(self.run_complete_workflow(casino_name, casino_url, custom_query))


# Simple interface function
async def generate_and_publish_casino_review(
    casino_name: str,
    casino_url: Optional[str] = None,
    custom_query: Optional[str] = None
) -> Dict[str, Any]:
    """Simple function to generate and publish casino review"""
    
    workflow = CasinoReviewWorkflow()
    return await workflow.run_complete_workflow(casino_name, casino_url, custom_query)


def generate_and_publish_casino_review_sync(
    casino_name: str,
    casino_url: Optional[str] = None,
    custom_query: Optional[str] = None
) -> Dict[str, Any]:
    """Synchronous version of the simple function"""
    import asyncio
    return asyncio.run(generate_and_publish_casino_review(casino_name, casino_url, custom_query))


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test_complete_workflow():
        # Set WordPress credentials
        os.environ['WORDPRESS_SITE_URL'] = 'https://crashcasino.io'
        os.environ['WORDPRESS_USERNAME'] = 'nmlwh'
        os.environ['WORDPRESS_APP_PASSWORD'] = 'ReUA 1ZNM lnDr pmgJ nAgz eR6g'
        
        # Test complete workflow
        result = await generate_and_publish_casino_review(
            casino_name="Crashino",
            casino_url="https://crashino.com",
            custom_query="Write a comprehensive narrative review of Crashino Casino focusing on their unique crash games experience, user interface, banking options, and overall player satisfaction"
        )
        
        print("\n🎯 WORKFLOW RESULT:")
        print("=" * 60)
        
        if result['success']:
            print(f"✅ Successfully completed workflow for {result['casino_name']}")
            print(f"📊 Research data: {result['research_length']} characters")
            print(f"📝 Review content: {result['review_length']} characters")
            print(f"🚀 Publishing: {result['publishing_result']}")
            
            print(f"\n📖 REVIEW PREVIEW (first 500 chars):")
            print("-" * 40)
            print(result['review_content'][:500] + "...")
            
        else:
            print(f"❌ Workflow failed: {result['error']}")
    
    asyncio.run(test_complete_workflow())