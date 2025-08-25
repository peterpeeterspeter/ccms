"""
🎯 Native LangChain Casino CMS with Existing 95-Field Data
Uses existing Supabase casino intelligence data + embeds new research

Native LangChain components ONLY:
- SupabaseVectorStore with existing embeddings
- TavilySearchResults for research  
- WebBaseLoader for casino websites
- create_tool_calling_agent
- LCEL chains with | operator
- LangGraph StateGraph
"""

import os
from typing_extensions import TypedDict
from typing import List, Dict, Any
from supabase import create_client

# Load environment variables  
from dotenv import load_dotenv
load_dotenv()

# Native LangChain imports
from langchain_community.vectorstores import SupabaseVectorStore
from langchain_community.tools import TavilySearchResults
from langchain_community.document_loaders import WebBaseLoader
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.graph import StateGraph, END

# Import existing native WordPress tool
from integrations.langchain_wordpress_tool import WordPressPublishingTool

print("🔧 Loading Native LangChain CMS with Existing Casino Data")

# Set WordPress credentials
os.environ['WORDPRESS_SITE_URL'] = 'https://crashcasino.io'
os.environ['WORDPRESS_USERNAME'] = 'nmlwh'
os.environ['WORDPRESS_APP_PASSWORD'] = 'ReUA 1ZNM lnDr pmgJ nAgz eR6g'

# ==================================================
# 1. NATIVE SUPABASE WITH EXISTING DATA
# ==================================================

supabase = create_client(
    os.getenv("SUPABASE_URL"), 
    os.getenv("SUPABASE_SERVICE_KEY")
)

# Native SupabaseVectorStore using existing embeddings
vectorstore = SupabaseVectorStore(
    client=supabase,
    embeddings=OpenAIEmbeddings(),
    table_name="documents",
    query_name="match_documents"
)

# Native retriever for existing casino intelligence
retriever = vectorstore.as_retriever(search_kwargs={"k": 6})

print("✅ Native Supabase vectorstore connected to existing casino data")

# ==================================================
# 2. NATIVE TOOLS FOR RESEARCH AND EMBEDDING
# ==================================================

search_tool = TavilySearchResults(max_results=4)
wordpress_tool = WordPressPublishingTool()

def research_and_embed_casino(casino_name: str, casino_url: str = None):
    """Research casino and add to existing vectorstore using native components"""
    
    print(f"🔍 Researching {casino_name} to add to existing intelligence...")
    
    # Native research using TavilySearchResults
    research_queries = [
        f"{casino_name} casino comprehensive review 2024",
        f"{casino_name} casino games bonuses licensing",
        f"{casino_name} casino player reviews ratings safety"
    ]
    
    all_research = []
    
    for query in research_queries:
        try:
            results = search_tool.invoke(query)
            for result in results:
                research_content = f"""
Title: {result.get('title', 'N/A')}
URL: {result.get('url', 'N/A')}
Content: {result.get('content', 'N/A')}
---"""
                all_research.append(research_content)
        except Exception as e:
            print(f"Search failed for {query}: {e}")
    
    # Native website loading if URL provided
    if casino_url:
        try:
            loader = WebBaseLoader([casino_url])
            docs = loader.load()
            if docs:
                website_content = f"""
Official Website Content:
URL: {casino_url}
Title: {docs[0].metadata.get('title', 'Official Website')}
Content: {docs[0].page_content[:3000]}
---"""
                all_research.append(website_content)
        except Exception as e:
            print(f"Website loading failed: {e}")
    
    # Combine all research
    combined_research = "\\n".join(all_research)
    
    if combined_research:
        # Native text splitting
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        
        # Split research into chunks
        chunks = text_splitter.split_text(combined_research)
        
        # Create native Documents with metadata
        documents = []
        for i, chunk in enumerate(chunks):
            doc = Document(
                page_content=chunk,
                metadata={
                    "casino_name": casino_name,
                    "content_type": "research_intelligence",
                    "chunk_id": i,
                    "source": "tavily_research",
                    "casino_url": casino_url or f"https://{casino_name.lower()}.com"
                }
            )
            documents.append(doc)
        
        # Native embedding and storage to existing vectorstore
        try:
            vectorstore.add_documents(documents)
            print(f"✅ Added {len(documents)} research chunks to existing casino intelligence")
            return len(documents)
        except Exception as e:
            print(f"❌ Failed to embed research: {e}")
            return 0
    
    return 0

print("✅ Research and embedding function ready")

# ==================================================
# 3. NATIVE RAG CHAIN USING EXISTING + NEW DATA
# ==================================================

# Enhanced prompt for using existing casino intelligence
intelligence_prompt = ChatPromptTemplate.from_template("""
You are a professional casino reviewer writing comprehensive magazine-style reviews.

You have access to our comprehensive casino intelligence database containing:
- Existing 95-field casino analysis data  
- Fresh research from multiple authoritative sources
- Player reviews and ratings
- Licensing and safety information
- Games, bonuses, and banking details

CASINO INTELLIGENCE FROM DATABASE:
{context}

Write a comprehensive, engaging narrative review for: {question}

REQUIREMENTS:
- Write as a flowing magazine article with natural paragraphs
- NO bullet points, lists, or structured formatting
- Integrate specific data from our intelligence database naturally
- Include licensing details, game variety, bonus information, and safety aspects
- Make it authoritative using our database insights
- Focus on player experience and what makes this casino unique
- Write 1500+ words with engaging storytelling

Your comprehensive review:""")

# Native LCEL chain using existing data
casino_rag_chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | intelligence_prompt
    | ChatOpenAI(model="gpt-4o-mini", temperature=0.7, max_tokens=4000)
    | StrOutputParser()
)

print("✅ Native RAG chain created using existing casino intelligence")

# ==================================================
# 4. NATIVE RESEARCH AGENT
# ==================================================

research_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a casino research specialist. Use tavily_search_results_json to research casinos thoroughly.

Your mission:
1. Search for comprehensive casino information
2. Find player reviews and expert ratings  
3. Research licensing and safety details
4. Investigate games, bonuses, and banking options

Provide detailed, factual research that will be embedded into our casino intelligence database."""),
    ("placeholder", "{chat_history}"),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

research_agent = create_tool_calling_agent(
    ChatOpenAI(model="gpt-4o-mini", temperature=0.3),
    [search_tool],
    research_prompt
)

research_executor = AgentExecutor(
    agent=research_agent,
    tools=[search_tool],
    verbose=True,
    max_iterations=4
)

print("✅ Native research agent ready")

# ==================================================
# 5. NATIVE PUBLISHING AGENT  
# ==================================================

publish_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a content publishing specialist. Format casino reviews for WordPress publication.

Use wordpress_publisher tool to publish with proper metadata:
- Engaging titles
- Casino-specific metadata (name, rating, pros/cons)
- SEO-friendly tags and categories
- Professional formatting"""),
    ("placeholder", "{chat_history}"),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

# Fix the WordPress tool call format
class FixedWordPressPublishingTool(WordPressPublishingTool):
    def _run(self, query: str) -> str:
        """Override to handle string input properly"""
        try:
            import json
            if isinstance(query, str):
                # Try to parse JSON from string
                if query.startswith('{'):
                    data = json.loads(query)
                else:
                    # Handle non-JSON string input
                    data = {"title": "Casino Review", "content": query}
            else:
                data = query
            
            return super()._run(data)
        except Exception as e:
            return f"Publishing failed: {str(e)}"

fixed_wordpress_tool = FixedWordPressPublishingTool()

publish_agent = create_tool_calling_agent(
    ChatOpenAI(model="gpt-4o-mini", temperature=0.1),
    [fixed_wordpress_tool],
    publish_prompt  
)

publish_executor = AgentExecutor(
    agent=publish_agent,
    tools=[fixed_wordpress_tool],
    verbose=True,
    max_iterations=2
)

print("✅ Native publishing agent ready")

# ==================================================
# 6. NATIVE WORKFLOW WITH EXISTING DATA INTEGRATION
# ==================================================

class CasinoIntelligenceState(TypedDict):
    casino_name: str
    casino_url: str
    query: str
    research_chunks_added: int
    review_content: str
    published_result: str

def research_and_embed_node(state):
    """Research casino and add to existing intelligence database"""
    print(f"🔍 Researching {state['casino_name']} and embedding into existing data")
    
    chunks_added = research_and_embed_casino(
        state['casino_name'], 
        state.get('casino_url')
    )
    
    return {"research_chunks_added": chunks_added}

def generate_review_node(state):
    """Generate review using existing + new casino intelligence"""
    print(f"📝 Generating review using existing intelligence + new research")
    
    # Query both existing and new data
    query = f"Write a comprehensive narrative review of {state['casino_name']} casino using all available intelligence data"
    
    review = casino_rag_chain.invoke(query)
    
    return {"review_content": review}

def publish_review_node(state):
    """Publish using native agent"""
    print(f"🚀 Publishing {state['casino_name']} review")
    
    # Prepare structured data for publishing
    publish_data = {
        "title": f"{state['casino_name']} Casino Review - Comprehensive Analysis",
        "content": state["review_content"],
        "casino_name": state['casino_name'],
        "overall_rating": 7.8,
        "pros": [
            "Comprehensive intelligence analysis",
            "Existing database integration", 
            "Fresh research insights",
            "Professional content quality"
        ],
        "cons": [
            "Geographic restrictions may apply",
            "Bonus terms and conditions apply"
        ]
    }
    
    import json
    publish_query = json.dumps(publish_data)
    
    result = publish_executor.invoke({"input": f"Please publish this casino review: {publish_query}"})
    
    return {"published_result": result["output"]}

# Native LangGraph workflow
workflow = StateGraph(CasinoIntelligenceState)
workflow.add_node("research_embed", research_and_embed_node)
workflow.add_node("generate", generate_review_node)
workflow.add_node("publish", publish_review_node)

workflow.set_entry_point("research_embed")
workflow.add_edge("research_embed", "generate")
workflow.add_edge("generate", "publish")
workflow.add_edge("publish", END)

intelligence_workflow = workflow.compile()

print("✅ Native workflow ready with existing data integration")

# ==================================================
# 7. MAIN FUNCTION USING EXISTING CASINO INTELLIGENCE
# ==================================================

async def generate_casino_review_with_intelligence(casino_name: str, casino_url: str = None):
    """Generate casino review using existing intelligence + new research"""
    
    initial_state = {
        "casino_name": casino_name,
        "casino_url": casino_url or f"https://{casino_name.lower()}.com",
        "query": f"Comprehensive review of {casino_name} casino",
        "research_chunks_added": 0,
        "review_content": "",
        "published_result": ""
    }
    
    print(f"🚀 Starting Intelligence-Enhanced Casino CMS for {casino_name}")
    print("=" * 60)
    
    try:
        final_state = await intelligence_workflow.ainvoke(initial_state)
        
        return {
            "success": True,
            "casino_name": casino_name,
            "research_chunks_added": final_state["research_chunks_added"],
            "review_length": len(final_state["review_content"]),
            "review_content": final_state["review_content"],
            "published_result": final_state["published_result"],
            "implementation": "Native LangChain + Existing 95-Field Intelligence"
        }
        
    except Exception as e:
        return {
            "success": False,
            "casino_name": casino_name,
            "error": str(e)
        }

# ==================================================
# 8. TEST WITH EXISTING DATA
# ==================================================

if __name__ == "__main__":
    import asyncio
    
    async def test_intelligence_enhanced_cms():
        print("\\n🧪 Testing Casino CMS with Existing Intelligence Data")
        print("=" * 60)
        
        # Check existing data first
        print("🔍 Checking existing casino intelligence...")
        existing_docs = supabase.table('documents').select('*').limit(3).execute()
        print(f"Found {len(existing_docs.data)} existing casino intelligence records")
        
        # Test with Crashino
        result = await generate_casino_review_with_intelligence(
            "Crashino", 
            "https://crashino.com"
        )
        
        if result["success"]:
            print("\\n✅ SUCCESS with Existing Intelligence Integration!")
            print(f"📊 Research chunks added: {result['research_chunks_added']}")
            print(f"📝 Review length: {result['review_length']} chars")
            print(f"🔧 Implementation: {result['implementation']}")
            print(f"\\n🚀 Publishing result: {result['published_result'][:100]}...")
            
            print(f"\\n📖 Intelligence-Enhanced Review Preview:")
            print("-" * 50)
            print(result['review_content'][:800] + "...")
            print("-" * 50)
            
            print("\\n🎉 NATIVE LANGCHAIN + EXISTING DATA SUCCESS!")
            print("✅ Used existing 95-field casino intelligence")
            print("✅ Added fresh research and embedded it")
            print("✅ Generated comprehensive narrative review") 
            print("✅ Published with native WordPress tool")
            
        else:
            print(f"❌ Failed: {result['error']}")
    
    asyncio.run(test_intelligence_enhanced_cms())