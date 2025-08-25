"""
🤖 Native LangChain Casino Research Agent  
Phase 1: Replace custom agent logic with create_tool_calling_agent

Uses official LangChain agent patterns:
- create_tool_calling_agent for native agent creation
- AgentExecutor for execution
- Native tool integration
- ChatPromptTemplate for agent prompts
"""

from typing import List, Dict, Any, Optional
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from tools.native_casino_research_tools import NATIVE_CASINO_RESEARCH_TOOLS


class NativeCasinoResearchAgent:
    """Native LangChain casino research agent using create_tool_calling_agent"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini", 
            temperature=0.3,
            max_tokens=2000
        )
        self.tools = NATIVE_CASINO_RESEARCH_TOOLS
        self.agent_executor = self._create_native_agent()
    
    def _create_native_agent(self) -> AgentExecutor:
        """Create native agent using create_tool_calling_agent"""
        
        # Native agent prompt following LangChain patterns
        agent_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a professional casino research specialist using native LangChain tools.

Your mission is to conduct comprehensive casino research using the available tools systematically:

1. **search_casino_information** - Get general casino overview and basic details
2. **load_casino_website_content** - Extract official casino information from their website  
3. **search_casino_reviews_and_ratings** - Find player reviews and ratings from multiple sources
4. **research_casino_games_portfolio** - Research available games and software providers
5. **research_casino_bonuses_and_promotions** - Investigate bonus offers and promotions
6. **extract_casino_intelligence_data** - Extract structured data from gathered research

RESEARCH STRATEGY:
- Always start with general casino information search
- Load official website content if URL is provided
- Gather reviews and ratings for credibility assessment
- Research specific areas (games, bonuses) for comprehensive coverage  
- Extract and structure all findings for analysis

IMPORTANT: Use tools systematically and provide detailed, factual information that can be used for writing comprehensive casino reviews. Focus on accuracy and completeness."""),
            
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])
        
        # Native agent creation
        agent = create_tool_calling_agent(
            llm=self.llm,
            tools=self.tools, 
            prompt=agent_prompt
        )
        
        # Native executor with proper configuration
        agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            max_iterations=6,  # Allow sufficient iterations for comprehensive research
            early_stopping_method="generate",
            handle_parsing_errors=True
        )
        
        print("✅ Native casino research agent created with create_tool_calling_agent")
        return agent_executor
    
    async def research_casino_comprehensive(
        self, 
        casino_name: str, 
        casino_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Conduct comprehensive casino research using native agent"""
        
        # Build research request
        research_request = f"Conduct comprehensive research on {casino_name} casino"
        if casino_url:
            research_request += f" with official website at {casino_url}"
        
        research_request += """

Please use all available research tools systematically:
1. Search for general casino information and overview
2. Load official website content (if URL provided) 
3. Find player reviews and ratings from multiple sources
4. Research the casino's games portfolio and software providers
5. Investigate bonus offers and promotional details
6. Extract structured intelligence data from all gathered research

Provide comprehensive findings that can be used for writing detailed casino reviews."""

        try:
            print(f"🔍 Starting comprehensive research for: {casino_name}")
            
            # Execute native agent
            result = await self.agent_executor.ainvoke({
                "input": research_request,
                "chat_history": []
            })
            
            return {
                "success": True,
                "casino_name": casino_name,
                "research_output": result["output"],
                "research_length": len(result["output"]),
                "tools_used": "Native LangChain tools via create_tool_calling_agent"
            }
            
        except Exception as e:
            return {
                "success": False,
                "casino_name": casino_name,
                "error": str(e),
                "research_output": f"Research failed: {e}"
            }
    
    def research_casino_sync(
        self, 
        casino_name: str, 
        casino_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Synchronous version for easier integration"""
        
        research_request = f"Research {casino_name} casino comprehensively"
        if casino_url:
            research_request += f" using official website {casino_url}"
        
        try:
            result = self.agent_executor.invoke({
                "input": research_request,
                "chat_history": []
            })
            
            return {
                "success": True, 
                "casino_name": casino_name,
                "research_output": result["output"],
                "research_length": len(result["output"])
            }
            
        except Exception as e:
            return {
                "success": False,
                "casino_name": casino_name, 
                "error": str(e),
                "research_output": f"Research failed: {e}"
            }
    
    def get_available_tools(self) -> List[str]:
        """Get list of available native tools"""
        return [tool.name for tool in self.tools]


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test_native_research_agent():
        """Test the native casino research agent"""
        
        print("🤖 Testing Native Casino Research Agent")
        print("=" * 50)
        
        # Initialize native agent
        agent = NativeCasinoResearchAgent()
        
        print(f"Available tools: {agent.get_available_tools()}")
        print()
        
        # Test comprehensive research
        result = await agent.research_casino_comprehensive(
            casino_name="Crashino",
            casino_url="https://crashino.com" 
        )
        
        print("🎯 RESEARCH RESULTS:")
        print("=" * 40)
        
        if result["success"]:
            print(f"✅ Research completed successfully")
            print(f"📊 Data length: {result['research_length']} characters")  
            print(f"🔧 Tools: {result['tools_used']}")
            print()
            print("📝 RESEARCH PREVIEW (first 800 characters):")
            print("-" * 40)
            print(result["research_output"][:800] + "...")
            print("-" * 40)
        else:
            print(f"❌ Research failed: {result['error']}")
    
    # Run test
    asyncio.run(test_native_research_agent())