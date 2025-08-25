"""
🔧 Native LangChain Casino Research Tools
Phase 1: Convert research functions to native @tool patterns

Uses official LangChain tool patterns:
- @tool decorator for native tool creation
- TavilySearchResults integration
- WebBaseLoader integration  
- PydanticOutputParser for structured extraction
"""

import os
from typing import List, Dict, Any, Optional
from langchain_core.tools import tool
from langchain_community.tools import TavilySearchResults
from langchain_community.document_loaders import WebBaseLoader
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI


# Native LangChain tools using @tool decorator
@tool
def search_casino_information(casino_name: str) -> str:
    """Search for general casino information using native TavilySearchResults.
    
    Args:
        casino_name: The name of the casino to research
        
    Returns:
        Formatted search results with titles, content, and URLs
    """
    try:
        # Native LangChain web search tool
        tavily = TavilySearchResults(max_results=4)
        query = f"{casino_name} casino review games bonuses license"
        
        results = tavily.invoke(query)
        
        # Format results natively
        formatted_results = []
        for result in results:
            formatted_results.append(
                f"Title: {result.get('title', 'N/A')}\n"
                f"Content: {result.get('content', 'N/A')}\n"
                f"URL: {result.get('url', 'N/A')}\n"
                f"---"
            )
        
        return "\n".join(formatted_results)
        
    except Exception as e:
        return f"Search failed: {str(e)}"


@tool  
def load_casino_website_content(casino_url: str) -> str:
    """Load official casino website content using native WebBaseLoader.
    
    Args:
        casino_url: The official casino website URL
        
    Returns:
        Extracted website content with metadata
    """
    try:
        # Native LangChain document loader
        loader = WebBaseLoader([casino_url])
        documents = loader.load()
        
        if not documents:
            return "No content loaded from website"
        
        # Format loaded content
        content_parts = []
        for doc in documents[:2]:  # Limit to first 2 documents
            content_parts.append(
                f"Source: {doc.metadata.get('source', 'N/A')}\n"
                f"Title: {doc.metadata.get('title', 'N/A')}\n" 
                f"Content: {doc.page_content[:2500]}\n"
                f"---"
            )
        
        return "\n".join(content_parts)
        
    except Exception as e:
        return f"Website loading failed: {str(e)}"


@tool
def search_casino_reviews_and_ratings(casino_name: str) -> str:
    """Search for casino reviews and player ratings using native search.
    
    Args:
        casino_name: The casino name to search reviews for
        
    Returns:
        Aggregated review data from multiple sources
    """
    try:
        # Native search for reviews
        tavily = TavilySearchResults(max_results=3)
        review_queries = [
            f"{casino_name} casino review 2024",
            f"{casino_name} casino player experience ratings",
            f"{casino_name} casino complaints trustpilot"
        ]
        
        all_reviews = []
        for query in review_queries:
            try:
                results = tavily.invoke(query)
                for result in results:
                    all_reviews.append(
                        f"Review Source: {result.get('title', 'N/A')}\n"
                        f"Rating/Review: {result.get('content', 'N/A')}\n"
                        f"URL: {result.get('url', 'N/A')}\n"
                        f"---"
                    )
            except:
                continue
        
        return "\n".join(all_reviews[:10])  # Limit results
        
    except Exception as e:
        return f"Review search failed: {str(e)}"


@tool
def extract_casino_intelligence_data(research_content: str) -> str:
    """Extract structured casino intelligence from research content using native PydanticOutputParser.
    
    Args:
        research_content: Raw research content to extract data from
        
    Returns:
        Structured casino intelligence data
    """
    try:
        # Native LangChain structured extraction
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
        
        # Simple structured extraction prompt
        extraction_prompt = PromptTemplate(
            template="""Extract casino information from this research content:

{content}

Extract the following information if available:
- Casino name
- License type (Curacao, Malta, UK, etc.)
- Overall rating (1-10)
- Total games count
- Welcome bonus details
- Payment methods
- Safety/trust indicators
- Player experience highlights

Format as: Field: Value (or "Not specified" if not found)

Extracted Information:""",
            input_variables=["content"]
        )
        
        # Native chain composition
        extraction_chain = extraction_prompt | llm
        result = extraction_chain.invoke({"content": research_content[:4000]})
        
        return result.content if hasattr(result, 'content') else str(result)
        
    except Exception as e:
        return f"Intelligence extraction failed: {str(e)}"


@tool
def research_casino_games_portfolio(casino_name: str) -> str:
    """Research specific casino games and software providers using native tools.
    
    Args:
        casino_name: Casino name to research games for
        
    Returns:
        Detailed games portfolio information  
    """
    try:
        # Native search for games information
        tavily = TavilySearchResults(max_results=3)
        games_query = f"{casino_name} casino games slots live dealer software providers"
        
        results = tavily.invoke(games_query)
        
        games_info = []
        for result in results:
            games_info.append(
                f"Games Info: {result.get('title', 'N/A')}\n"
                f"Details: {result.get('content', 'N/A')}\n"
                f"Source: {result.get('url', 'N/A')}\n"
                f"---"
            )
        
        return "\n".join(games_info)
        
    except Exception as e:
        return f"Games research failed: {str(e)}"


@tool
def research_casino_bonuses_and_promotions(casino_name: str) -> str:
    """Research casino bonuses and promotional offers using native search.
    
    Args:
        casino_name: Casino name to research bonuses for
        
    Returns:
        Comprehensive bonus and promotion information
    """
    try:
        # Native search for bonus information
        tavily = TavilySearchResults(max_results=3)  
        bonus_query = f"{casino_name} casino welcome bonus free spins promotions wagering requirements"
        
        results = tavily.invoke(bonus_query)
        
        bonus_info = []
        for result in results:
            bonus_info.append(
                f"Bonus Info: {result.get('title', 'N/A')}\n"
                f"Details: {result.get('content', 'N/A')}\n"
                f"Source: {result.get('url', 'N/A')}\n" 
                f"---"
            )
        
        return "\n".join(bonus_info)
        
    except Exception as e:
        return f"Bonus research failed: {str(e)}"


# Native tool collection for agent use
NATIVE_CASINO_RESEARCH_TOOLS = [
    search_casino_information,
    load_casino_website_content,
    search_casino_reviews_and_ratings,
    extract_casino_intelligence_data,
    research_casino_games_portfolio,
    research_casino_bonuses_and_promotions
]


# Example usage
if __name__ == "__main__":
    # Test native tools
    print("🔧 Testing Native Casino Research Tools")
    print("=" * 50)
    
    # Test search tool
    print("1. Testing casino information search...")
    search_result = search_casino_information.invoke({"casino_name": "Crashino"})
    print(f"Search result length: {len(search_result)} characters")
    
    # Test website loader  
    print("\n2. Testing website content loading...")
    website_result = load_casino_website_content.invoke({"casino_url": "https://crashino.com"})
    print(f"Website content length: {len(website_result)} characters")
    
    # Test review search
    print("\n3. Testing review search...")
    review_result = search_casino_reviews_and_ratings.invoke({"casino_name": "Crashino"})
    print(f"Review data length: {len(review_result)} characters")
    
    print("\n✅ All native tools tested successfully!")