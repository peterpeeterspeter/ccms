#!/usr/bin/env python3
"""
🏗️ NATIVE LANGCHAIN WordPress Chain Integration
Proper Runnable chain integration with WordPress tool
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Union

from langchain_core.runnables import (
    Runnable, RunnableLambda, RunnablePassthrough, 
    RunnableBranch, RunnableParallel
)
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser
from langchain_core.tools import BaseTool

from .langchain_wordpress_tool import (
    WordPressPublishingTool, WordPressPostSchema, CasinoReviewSchema,
    get_wordpress_prompt_template, wordpress_parser
)

logger = logging.getLogger(__name__)

class WordPressChainIntegration:
    """🏗️ Native LangChain WordPress Chain Integration"""
    
    def __init__(self, wordpress_tool: Optional[WordPressPublishingTool] = None):
        self.wordpress_tool = wordpress_tool or WordPressPublishingTool()
        self.casino_parser = PydanticOutputParser(pydantic_object=CasinoReviewSchema)
        self.standard_parser = PydanticOutputParser(pydantic_object=WordPressPostSchema)
    
    def create_wordpress_publishing_chain(
        self, 
        llm, 
        enable_casino_detection: bool = True
    ) -> Runnable:
        """Create a complete WordPress publishing chain using proper LangChain patterns"""
        
        # Step 1: Content Analysis and Preparation
        content_analyzer = RunnableParallel({
            "original_content": RunnablePassthrough(),
            "content_type": RunnableLambda(self._detect_content_type),
            "structured_data": RunnableLambda(self._extract_structured_data)
        })
        
        # Step 2: Content Processing Branch
        content_processor = RunnableBranch(
            # Casino content processing
            (
                lambda x: x.get("content_type") == "casino_review" and enable_casino_detection,
                self._create_casino_processing_chain(llm)
            ),
            # Standard content processing
            self._create_standard_processing_chain(llm)
        )
        
        # Step 3: WordPress Publishing
        publisher = RunnableLambda(self._execute_wordpress_publishing)
        
        # Combine into full chain
        chain = (
            content_analyzer
            | content_processor
            | publisher
        )
        
        return chain
    
    def _create_casino_processing_chain(self, llm) -> Runnable:
        """Create specialized chain for casino content"""
        
        # Casino content enhancement prompt
        casino_prompt = ChatPromptTemplate.from_template("""
You are a casino review expert. Process the following content into a structured casino review.

Original Content: {original_content}
Structured Data: {structured_data}

Extract and format:
1. Casino name and key details
2. Overall rating (0-10)
3. Licensing information
4. Welcome bonus details
5. Pros and cons lists
6. Payment methods and game providers
7. CoinFlip theme fields (small_description, casino_features, bonus_message, casino_website_url)

{format_instructions}

Generate a comprehensive, SEO-optimized casino review with all required fields.
""")
        
        # Casino processing pipeline
        casino_chain = (
            RunnableParallel({
                "original_content": lambda x: x["original_content"],
                "structured_data": lambda x: x.get("structured_data", {}),
                "format_instructions": lambda x: self.casino_parser.get_format_instructions()
            })
            | casino_prompt
            | llm
            | self.casino_parser
            | RunnableLambda(self._convert_casino_to_wordpress_format)
        )
        
        return casino_chain
    
    def _create_standard_processing_chain(self, llm) -> Runnable:
        """Create standard content processing chain"""
        
        # Standard content enhancement prompt
        standard_prompt = ChatPromptTemplate.from_template("""
You are a WordPress content expert. Process the following content into a well-formatted WordPress post.

Content: {original_content}
Additional Data: {structured_data}

Create:
1. SEO-optimized title
2. Clean HTML content with proper formatting
3. Relevant categories and tags
4. Compelling excerpt/meta description
5. Any custom fields that would be useful

{format_instructions}

Make the content engaging, well-structured, and WordPress-ready.
""")
        
        # Standard processing pipeline
        standard_chain = (
            RunnableParallel({
                "original_content": lambda x: x["original_content"],
                "structured_data": lambda x: x.get("structured_data", {}),
                "format_instructions": lambda x: self.standard_parser.get_format_instructions()
            })
            | standard_prompt
            | llm
            | self.standard_parser
        )
        
        return standard_chain
    
    def _detect_content_type(self, inputs: Dict[str, Any]) -> str:
        """Detect the type of content for proper processing"""
        
        content = str(inputs)
        content_lower = content.lower()
        
        # Casino content indicators
        casino_indicators = [
            'casino', 'gambling', 'slots', 'poker', 'blackjack', 'roulette',
            'bonus', 'wagering', 'license', 'mga', 'ukgc', 'curacao',
            'welcome bonus', 'free spins', 'deposit', 'withdrawal'
        ]
        
        casino_score = sum(1 for indicator in casino_indicators if indicator in content_lower)
        
        if casino_score >= 3:
            return "casino_review"
        else:
            return "standard_post"
    
    def _extract_structured_data(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Extract any structured data from inputs"""
        
        if isinstance(inputs, dict):
            structured_data = {}
            
            # Look for common structured data keys
            structured_keys = [
                'structured_metadata', 'metadata', 'casino_data',
                'coinflip_fields', 'custom_fields', 'additional_info'
            ]
            
            for key in structured_keys:
                if key in inputs:
                    if isinstance(inputs[key], dict):
                        structured_data.update(inputs[key])
                    else:
                        structured_data[key] = inputs[key]
            
            return structured_data
        
        return {}
    
    def _convert_casino_to_wordpress_format(self, casino_data: CasinoReviewSchema) -> Dict[str, Any]:
        """Convert CasinoReviewSchema to WordPress tool format"""
        
        wordpress_data = {
            "title": casino_data.title,
            "content": casino_data.content,
            "casino_name": casino_data.casino_name,
            "overall_rating": casino_data.overall_rating,
            "license_info": casino_data.license_info,
            "welcome_bonus": casino_data.welcome_bonus,
            "pros": casino_data.pros,
            "cons": casino_data.cons,
            "payment_methods": casino_data.payment_methods,
            "game_providers": casino_data.game_providers,
            "small_description": casino_data.small_description,
            "casino_features": casino_data.casino_features,
            "bonus_message": casino_data.bonus_message,
            "casino_website_url": casino_data.casino_website_url
        }
        
        # Remove None values
        wordpress_data = {k: v for k, v in wordpress_data.items() if v is not None}
        
        return wordpress_data
    
    async def _execute_wordpress_publishing(self, processed_data: Union[Dict[str, Any], WordPressPostSchema]) -> Dict[str, Any]:
        """Execute WordPress publishing using the native tool"""
        
        try:
            # Convert Pydantic model to dict if needed
            if hasattr(processed_data, 'dict'):
                publish_data = processed_data.dict()
            else:
                publish_data = processed_data
            
            # Use the WordPress tool
            result = await self.wordpress_tool._arun(publish_data)
            
            logger.info(f"✅ WordPress publishing completed: {result.get('success', False)}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ WordPress publishing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "tool": "wordpress_chain_integration"
            }
    
    def create_simple_publish_chain(self) -> Runnable:
        """Create a simple publishing chain for direct content"""
        
        return RunnableLambda(self._execute_wordpress_publishing)
    
    def create_content_enhancement_chain(self, llm) -> Runnable:
        """Create a chain that enhances content before publishing"""
        
        enhancement_prompt = ChatPromptTemplate.from_template("""
Enhance the following content for WordPress publishing:

Content: {content}

Improvements to make:
1. Add proper HTML formatting
2. Create an engaging title if missing
3. Add relevant categories and tags
4. Create a compelling excerpt
5. Clean up any formatting issues

Return the enhanced content in a structured format suitable for WordPress.
""")
        
        chain = (
            enhancement_prompt
            | llm
            | StrOutputParser()
            | RunnableLambda(lambda x: {"content": x, "title": "Enhanced Content"})
            | RunnableLambda(self._execute_wordpress_publishing)
        )
        
        return chain

# Factory functions for easy integration
def create_wordpress_publishing_chain(
    llm,
    wordpress_tool: Optional[WordPressPublishingTool] = None,
    enable_casino_detection: bool = True
) -> Runnable:
    """Factory function to create WordPress publishing chain"""
    
    integration = WordPressChainIntegration(wordpress_tool)
    return integration.create_wordpress_publishing_chain(llm, enable_casino_detection)

def create_simple_wordpress_chain(
    wordpress_tool: Optional[WordPressPublishingTool] = None
) -> Runnable:
    """Factory function to create simple WordPress publishing chain"""
    
    integration = WordPressChainIntegration(wordpress_tool)
    return integration.create_simple_publish_chain()

# Example usage and testing
async def test_wordpress_chain_integration():
    """Test the WordPress chain integration"""
    
    try:
        from langchain_openai import ChatOpenAI
        
        # Initialize components
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
        wordpress_tool = WordPressPublishingTool()
        
        # Create the chain
        wordpress_chain = create_wordpress_publishing_chain(llm, wordpress_tool)
        
        # Test with casino content
        casino_content = {
            "original_content": """
            Napoleon Games Casino Review
            
            Napoleon Games Casino is a prominent online gaming platform licensed by the Belgian Gaming Commission.
            The casino offers over 1,000 games including slots, table games, and live dealer options.
            
            Pros:
            - Licensed and regulated
            - Fast withdrawals
            - Mobile optimized
            - Live chat support
            
            Cons:
            - Limited to Belgium
            - High wagering requirements
            
            Overall Rating: 8.5/10
            """,
            "structured_metadata": {
                "casino_name": "Napoleon Games",
                "coinflip_fields": {
                    "small_description": "Premium Belgian casino with 500+ games",
                    "bonus_message": "Get €100 + 50 Free Spins Today!",
                    "casino_website_url": "https://napoleon-games.be"
                }
            }
        }
        
        # Execute the chain
        print("🚀 Testing WordPress chain integration...")
        result = await wordpress_chain.ainvoke(casino_content)
        
        print("✅ Chain execution completed:")
        print(f"   Success: {result.get('success', False)}")
        print(f"   Post ID: {result.get('post_id', 'N/A')}")
        print(f"   URL: {result.get('url', 'N/A')}")
        
        return result
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # Run the test
    result = asyncio.run(test_wordpress_chain_integration())
    
    if result and result.get('success'):
        print("\n🎉 WordPress chain integration test passed!")
    else:
        print("\n💥 WordPress chain integration test failed!")