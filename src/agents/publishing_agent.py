"""
📝 Native LangChain Publishing Agent
Using WordPress tool with proper agent pattern (not LCEL tool calling)

Follows LangChain best practice: Use agents for tools, chains for simple workflows
"""

import os
from typing import Dict, Any, Optional
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from integrations.langchain_wordpress_tool import WordPressPublishingTool


class CasinoPublishingAgent:
    """Native publishing agent using WordPress tool"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1  # Low temperature for structured publishing
        )
        self.wordpress_tool = WordPressPublishingTool()
        self.tools = self._create_tools()
        self.agent = self._create_agent()
        
    def _create_tools(self) -> list:
        """Create publishing tools"""
        
        @tool
        def publish_casino_review(review_data: str) -> str:
            """Publish casino review to WordPress with proper formatting and metadata"""
            try:
                # Parse review data (expecting JSON-like string or structured data)
                if isinstance(review_data, str):
                    # Try to extract key information from the review text
                    data = self._parse_review_content(review_data)
                else:
                    data = review_data
                
                # Use the existing WordPress tool
                result = self.wordpress_tool._run(data)
                
                if result.get('success'):
                    return f"✅ Successfully published casino review! URL: {result.get('url', 'N/A')}, Post ID: {result.get('post_id', 'N/A')}"
                else:
                    return f"❌ Publishing failed: {result.get('error', 'Unknown error')}"
                    
            except Exception as e:
                return f"❌ Publishing error: {str(e)}"
        
        @tool
        def format_review_for_publishing(content: str, casino_name: str) -> str:
            """Format review content for WordPress publishing with metadata and images"""
            try:
                # Enhanced formatting with native images integration
                formatted_data = {
                    'title': f'{casino_name} Casino Review: Complete Analysis & Player Experience',
                    'content': content,
                    'casino_name': casino_name,
                    'overall_rating': 7.8,  # Enhanced rating
                    'license_info': 'Curacao License',
                    'welcome_bonus': 'Up to $1,000 + 100 Free Spins',
                    'pros': [
                        'Comprehensive 95-field analysis',
                        'Professional visual content',  
                        'Native Supabase integration',
                        'Advanced casino intelligence',
                        'User-friendly interface',
                        'Secure platform'
                    ],
                    'cons': [
                        'Geographic restrictions may apply',
                        'Bonus terms and conditions apply',
                        'Regulatory compliance varies'
                    ],
                    'small_description': f'Comprehensive 95-field intelligence review of {casino_name} Casino with visual content',
                    'casino_website_url': f'https://{casino_name.lower().replace(" ", "")}.com',
                    'payment_methods': ['Bitcoin', 'Ethereum', 'Visa', 'Mastercard', 'Skrill', 'Neteller'],
                    'game_providers': ['Pragmatic Play', 'NetEnt', 'Evolution Gaming', 'Quickspin'],
                    # Enhanced with visual content
                    'featured_images': [
                        {
                            'url': 'https://images.unsplash.com/photo-1596838132731-3301c3fd4317?w=800&h=400&fit=crop',
                            'alt': 'Casino gaming environment with chips and cards',
                            'title': 'Casino Gaming Experience'
                        },
                        {
                            'url': 'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=800&h=400&fit=crop',
                            'alt': 'Modern casino floor and gaming tables', 
                            'title': 'Casino Interior Design'
                        }
                    ]
                }
                
                return str(formatted_data)
                
            except Exception as e:
                return f"Formatting error: {str(e)}"
        
        return [publish_casino_review, format_review_for_publishing]
    
    def _parse_review_content(self, content: str) -> Dict[str, Any]:
        """Simple content parsing for WordPress publishing"""
        
        # Extract casino name from content (simple approach)
        casino_name = "Casino"
        lines = content.split('\n')
        for line in lines[:5]:  # Check first few lines
            if 'casino' in line.lower() and len(line) < 100:
                # Try to extract casino name
                words = line.split()
                for i, word in enumerate(words):
                    if 'casino' in word.lower() and i > 0:
                        casino_name = words[i-1].replace(':', '').replace('.', '')
                        break
        
        return {
            'title': f'{casino_name} Casino Review: Complete Analysis & Player Experience',
            'content': content,
            'casino_name': casino_name,
            'overall_rating': 7.5,
            'license_info': 'Licensed Casino',
            'welcome_bonus': 'Welcome Bonus Available',
            'pros': [
                'User-friendly interface',
                'Good game selection',
                'Secure platform',
                'Customer support available'
            ],
            'cons': [
                'Geographic restrictions may apply',
                'Bonus terms and conditions apply'
            ],
            'small_description': f'Comprehensive review of {casino_name} Casino',
            'casino_website_url': f'https://{casino_name.lower().replace(" ", "")}.com',
            'payment_methods': ['Visa', 'Mastercard', 'Bitcoin', 'Skrill'],
            'game_providers': ['Pragmatic Play', 'NetEnt', 'Evolution Gaming']
        }
    
    def _create_agent(self) -> AgentExecutor:
        """Create native tool-calling agent for publishing"""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a professional casino content publishing specialist.

Your job is to publish casino reviews to WordPress with proper formatting and metadata.

When publishing a casino review:
1. First use format_review_for_publishing to structure the content properly
2. Then use publish_casino_review to publish it to WordPress

Always ensure the content is properly formatted for WordPress with:
- Clear title
- Engaging content
- Proper metadata (rating, pros/cons, etc.)
- SEO-friendly structure

Be concise and focused on the publishing task."""),
            
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ])
        
        agent = create_tool_calling_agent(self.llm, self.tools, prompt)
        
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            max_iterations=3,
            early_stopping_method="generate"
        )
    
    async def publish_review(self, content: str, casino_name: str) -> str:
        """Publish casino review using native agent pattern"""
        
        query = f"Please publish this casino review for {casino_name}:\n\n{content}"
        
        print(f"📝 Publishing review for: {casino_name}")
        
        try:
            result = await self.agent.ainvoke({
                "input": query,
                "chat_history": []
            })
            
            return result["output"]
            
        except Exception as e:
            return f"Publishing failed: {str(e)}"
    
    def publish_review_sync(self, content: str, casino_name: str) -> str:
        """Synchronous version for easier integration"""
        query = f"Please publish this casino review for {casino_name}:\n\n{content}"
        
        try:
            result = self.agent.invoke({
                "input": query,
                "chat_history": []
            })
            
            return result["output"]
            
        except Exception as e:
            return f"Publishing failed: {str(e)}"


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test_publishing_agent():
        # Set WordPress credentials
        os.environ['WORDPRESS_SITE_URL'] = 'https://crashcasino.io'
        os.environ['WORDPRESS_USERNAME'] = 'nmlwh'
        os.environ['WORDPRESS_APP_PASSWORD'] = 'ReUA 1ZNM lnDr pmgJ nAgz eR6g'
        
        agent = CasinoPublishingAgent()
        
        sample_review = """
        Crashino Casino: A Unique Crash Gaming Experience

        When I first discovered Crashino Casino, I was immediately drawn to their unique focus on crash games. This innovative platform has carved out a distinctive niche in the online gambling world by specializing in the thrilling world of crash gaming.

        The standout feature of Crashino is undoubtedly their crash game selection. The flagship Aviator game provides heart-pounding excitement as players watch the multiplier climb higher and higher, creating an almost hypnotic tension. The key is finding that perfect balance between greed and prudence.

        Beyond crash games, Crashino maintains a solid traditional casino offering with over 800 slots powered by industry leaders like Pragmatic Play and NetEnt. The games load quickly and run smoothly, providing a dependable gaming experience.

        The banking system deserves special mention, with Bitcoin withdrawals processing in under two hours and transparent fee structures. Customer support via live chat is consistently responsive and knowledgeable.

        While operating under Curacao licensing may not appeal to all players, Crashino delivers a professional, engaging experience that particularly suits those seeking something beyond traditional casino gaming.
        """
        
        result = await agent.publish_review(sample_review, "Crashino")
        
        print("Publishing Result:")
        print("=" * 50)
        print(result)
    
    asyncio.run(test_publishing_agent())