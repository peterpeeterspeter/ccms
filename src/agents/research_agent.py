"""
🔍 Native LangChain Research Agent
Using built-in tools and agent patterns (not custom web research)

Follows LangChain best practice: Use agents for tools, chains for simple workflows
"""

import os
from typing import List, Dict, Any, Optional
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_community.tools import TavilySearchResults
from langchain_community.document_loaders import WebBaseLoader


class CasinoResearchAgent:
    """Native research agent using built-in LangChain tools"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3
        )
        self.tools = self._create_tools()
        self.agent = self._create_agent()
        
    def _create_tools(self) -> List:
        """Create native LangChain tools for casino research"""
        
        @tool
        def search_casino_info(query: str) -> str:
            """Search for general casino information using web search"""
            try:
                search = TavilySearchResults(max_results=3)
                results = search.invoke(query)
                
                # Format results simply
                formatted = []
                for result in results:
                    formatted.append(f"Title: {result.get('title', 'N/A')}")
                    formatted.append(f"Content: {result.get('content', 'N/A')}")
                    formatted.append(f"URL: {result.get('url', 'N/A')}")
                    formatted.append("---")
                
                return "\n".join(formatted)
            except Exception as e:
                return f"Search failed: {str(e)}"
        
        @tool
        def load_casino_website(url: str) -> str:
            """Load and extract content from casino website"""
            try:
                loader = WebBaseLoader([url])
                docs = loader.load()
                
                # Simple content extraction
                content = []
                for doc in docs[:2]:  # Limit to first 2 documents
                    content.append(f"URL: {doc.metadata.get('source', 'N/A')}")
                    content.append(f"Content: {doc.page_content[:2000]}...")  # First 2000 chars
                    content.append("---")
                
                return "\n".join(content)
            except Exception as e:
                return f"Website loading failed: {str(e)}"
        
        @tool
        def search_casino_reviews(casino_name: str) -> str:
            """Search for casino reviews and user feedback"""
            try:
                search = TavilySearchResults(max_results=3)
                query = f"{casino_name} casino review user experience feedback"
                results = search.invoke(query)
                
                # Format review results
                reviews = []
                for result in results:
                    reviews.append(f"Review Source: {result.get('title', 'N/A')}")
                    reviews.append(f"Review: {result.get('content', 'N/A')}")
                    reviews.append(f"URL: {result.get('url', 'N/A')}")
                    reviews.append("---")
                
                return "\n".join(reviews)
            except Exception as e:
                return f"Review search failed: {str(e)}"
        
        return [search_casino_info, load_casino_website, search_casino_reviews]
    
    def _create_agent(self) -> AgentExecutor:
        """Create native tool-calling agent"""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a professional casino research specialist. 

Your job is to gather comprehensive information about casinos using the available tools.

When researching a casino:
1. Use search_casino_info to get general information
2. Use load_casino_website to get official casino details (if URL provided)
3. Use search_casino_reviews to find user feedback and reviews

Provide detailed, factual information that can be used for writing casino reviews.
Focus on: games, bonuses, payment methods, customer support, licensing, user experience.

Always use the tools to gather current information rather than relying on existing knowledge."""),
            
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ])
        
        agent = create_tool_calling_agent(self.llm, self.tools, prompt)
        
        return AgentExecutor(
            agent=agent, 
            tools=self.tools, 
            verbose=True,
            max_iterations=5,
            early_stopping_method="generate"
        )
    
    async def research_casino(self, casino_name: str, casino_url: Optional[str] = None) -> str:
        """Research casino using native agent pattern"""
        
        # Build research query
        query_parts = [f"Research {casino_name} casino comprehensively"]
        
        if casino_url:
            query_parts.append(f"Official website: {casino_url}")
        
        query = ". ".join(query_parts)
        
        print(f"🔍 Researching: {casino_name}")
        
        try:
            result = await self.agent.ainvoke({
                "input": query,
                "chat_history": []
            })
            
            return result["output"]
            
        except Exception as e:
            return f"Research failed: {str(e)}"
    
    def research_casino_sync(self, casino_name: str, casino_url: Optional[str] = None) -> str:
        """Synchronous version for easier integration"""
        query_parts = [f"Research {casino_name} casino comprehensively"]
        
        if casino_url:
            query_parts.append(f"Official website: {casino_url}")
        
        query = ". ".join(query_parts)
        
        try:
            result = self.agent.invoke({
                "input": query,
                "chat_history": []
            })
            
            return result["output"]
            
        except Exception as e:
            return f"Research failed: {str(e)}"


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test_research_agent():
        agent = CasinoResearchAgent()
        
        # Test research
        result = await agent.research_casino(
            "Crashino Casino",
            "https://crashino.com"
        )
        
        print("Research Result:")
        print("=" * 50)
        print(result)
    
    asyncio.run(test_research_agent())