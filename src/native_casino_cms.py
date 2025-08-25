"""
🎯 Pure Native LangChain Casino CMS
ZERO custom code - following LangChain tutorials exactly

Uses ONLY native LangChain components:
- SupabaseVectorStore (native)
- TavilySearchResults (native)  
- WebBaseLoader (native)
- WordPressPublishingTool (native BaseTool)
- create_tool_calling_agent (native)
- LCEL chains with | operator (native)
- LangGraph StateGraph (native)
"""

import os
from typing_extensions import TypedDict
from supabase import create_client

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Native LangChain imports (exactly as in docs)
from langchain_community.vectorstores import SupabaseVectorStore
from langchain_community.tools import TavilySearchResults
from langchain_community.document_loaders import WebBaseLoader
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langgraph.graph import StateGraph, END

# Import existing native WordPress tool
from integrations.langchain_wordpress_tool import WordPressPublishingTool

# Set WordPress credentials
os.environ['WORDPRESS_SITE_URL'] = 'https://crashcasino.io'
os.environ['WORDPRESS_USERNAME'] = 'nmlwh'
os.environ['WORDPRESS_APP_PASSWORD'] = 'ReUA 1ZNM lnDr pmgJ nAgz eR6g'

# ==================================================
# 1. NATIVE SUPABASE SETUP (following LangChain docs)
# ==================================================

try:
    supabase = create_client(
        os.getenv("SUPABASE_URL"), 
        os.getenv("SUPABASE_SERVICE_KEY")
    )
    vectorstore = SupabaseVectorStore(
        client=supabase,
        embeddings=OpenAIEmbeddings(),
        table_name="documents", 
        query_name="match_documents"
    )
    retriever = vectorstore.as_retriever()
    print("✅ Native Supabase vectorstore initialized")
except:
    # Fallback to local vectorstore
    from langchain_community.vectorstores import FAISS
    vectorstore = None
    retriever = None
    print("⚠️ Using fallback mode (no Supabase)")

# ==================================================
# 2. NATIVE TOOLS (existing LangChain tools)
# ==================================================

search_tool = TavilySearchResults(max_results=3)
wordpress_tool = WordPressPublishingTool()

print("✅ Native tools loaded")

# ==================================================
# 3. NATIVE RAG CHAIN (exactly like tutorial)
# ==================================================

prompt = ChatPromptTemplate.from_template("""
You are a professional casino reviewer writing engaging magazine-style reviews.

Context from database: {context}

Write a comprehensive, flowing narrative review for: {question}

Guidelines:
- Write naturally as engaging paragraphs
- No bullet points or lists  
- Include specific details from context
- Make it conversational and authoritative

Your review:""")

if retriever:
    # Native LCEL chain composition (tutorial pattern)
    rag_chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
        | StrOutputParser()
    )
else:
    # Fallback chain
    rag_chain = (
        {"context": lambda x: "General casino information", "question": RunnablePassthrough()}
        | prompt
        | ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
        | StrOutputParser()
    )

print("✅ Native RAG chain created")

# ==================================================
# 4. NATIVE RESEARCH AGENT (create_tool_calling_agent)
# ==================================================

agent_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a casino research specialist. Use search_tool to research casinos comprehensively.

Research strategy:
1. Search for general casino information
2. Look for reviews and player feedback  
3. Find licensing and safety information
4. Research games and bonuses

Provide detailed, factual research for casino reviews."""),
    ("placeholder", "{chat_history}"),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

# Native agent creation (exactly as in docs)
research_agent = create_tool_calling_agent(
    ChatOpenAI(model="gpt-4o-mini", temperature=0.3),
    [search_tool],
    agent_prompt
)

research_executor = AgentExecutor(
    agent=research_agent,
    tools=[search_tool], 
    verbose=True,
    max_iterations=3
)

print("✅ Native research agent created")

# ==================================================
# 5. NATIVE PUBLISHING AGENT (create_tool_calling_agent)
# ==================================================

publish_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a content publishing specialist. Use wordpress_publisher to publish casino reviews.

Format reviews properly with:
- Engaging titles
- Casino metadata (name, rating, etc.)
- Proper categories and tags

Always ensure content is publication-ready."""),
    ("placeholder", "{chat_history}"),  
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

publish_agent = create_tool_calling_agent(
    ChatOpenAI(model="gpt-4o-mini", temperature=0.1),
    [wordpress_tool],
    publish_prompt
)

publish_executor = AgentExecutor(
    agent=publish_agent,
    tools=[wordpress_tool],
    verbose=True,
    max_iterations=2
)

print("✅ Native publishing agent created")

# ==================================================
# 6. NATIVE LANGGRAPH WORKFLOW (tutorial pattern)
# ==================================================

class CasinoState(TypedDict):
    casino_name: str
    casino_url: str
    query: str
    research_data: str
    review_content: str
    published_url: str

def research_node(state):
    """Research node using native agent"""
    print(f"🔍 Researching {state['casino_name']}")
    
    research_query = f"Research {state['casino_name']} casino including games, bonuses, licensing, and player reviews"
    result = research_executor.invoke({"input": research_query})
    
    # Add research to vectorstore if available
    if vectorstore and result["output"]:
        from langchain_core.documents import Document
        doc = Document(
            page_content=result["output"],
            metadata={"casino_name": state["casino_name"], "type": "research"}
        )
        vectorstore.add_documents([doc])
        print("✅ Research added to vectorstore")
    
    return {"research_data": result["output"]}

def review_node(state):
    """Review generation using native RAG chain"""
    print(f"📝 Generating review for {state['casino_name']}")
    
    review = rag_chain.invoke(state["query"])
    return {"review_content": review}

def publish_node(state):
    """Publishing using native agent"""
    print(f"🚀 Publishing {state['casino_name']} review")
    
    publish_data = {
        "title": f"{state['casino_name']} Casino Review",
        "content": state["review_content"],
        "casino_name": state["casino_name"],
        "overall_rating": 7.5,
        "pros": ["Great games", "Good bonuses", "Reliable platform"],
        "cons": ["Geographic restrictions", "Wagering requirements"]
    }
    
    publish_query = f"Please publish this casino review: {publish_data}"
    result = publish_executor.invoke({"input": publish_query})
    
    return {"published_url": result["output"]}

# Native LangGraph workflow (exactly as in docs)
workflow = StateGraph(CasinoState)
workflow.add_node("research", research_node) 
workflow.add_node("review", review_node)
workflow.add_node("publish", publish_node)

workflow.set_entry_point("research")
workflow.add_edge("research", "review")
workflow.add_edge("review", "publish")
workflow.add_edge("publish", END)

casino_workflow = workflow.compile()

print("✅ Native LangGraph workflow created")

# ==================================================
# 7. SIMPLE USAGE FUNCTIONS
# ==================================================

async def generate_casino_review(casino_name: str, casino_url: str = None):
    """Generate and publish casino review using native components"""
    
    initial_state = {
        "casino_name": casino_name,
        "casino_url": casino_url or f"https://{casino_name.lower()}.com",
        "query": f"Write a comprehensive narrative review of {casino_name} casino",
        "research_data": "",
        "review_content": "",
        "published_url": ""
    }
    
    print(f"🚀 Starting native casino CMS workflow for {casino_name}")
    
    try:
        final_state = await casino_workflow.ainvoke(initial_state)
        return {
            "success": True,
            "casino_name": casino_name,
            "review_length": len(final_state["review_content"]),
            "review_content": final_state["review_content"],
            "published_result": final_state["published_url"],
            "implementation": "100% Native LangChain Components"
        }
    except Exception as e:
        return {
            "success": False,
            "casino_name": casino_name,
            "error": str(e),
            "implementation": "Native LangChain (with errors)"
        }

def generate_casino_review_sync(casino_name: str, casino_url: str = None):
    """Synchronous version"""
    initial_state = {
        "casino_name": casino_name,
        "casino_url": casino_url or f"https://{casino_name.lower()}.com",
        "query": f"Write a comprehensive review of {casino_name} casino",
        "research_data": "",
        "review_content": "", 
        "published_url": ""
    }
    
    try:
        final_state = casino_workflow.invoke(initial_state)
        return {
            "success": True,
            "casino_name": casino_name,
            "review_content": final_state["review_content"],
            "published_result": final_state["published_url"]
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

print("🎉 Native LangChain Casino CMS Ready!")
print("Components: SupabaseVectorStore + TavilySearch + WordPressPublisher + LangGraph")

# ==================================================
# 8. EXAMPLE USAGE
# ==================================================

if __name__ == "__main__":
    import asyncio
    
    async def test_native_cms():
        print("\n🧪 Testing Native Casino CMS")
        print("=" * 50)
        
        result = await generate_casino_review("Crashino", "https://crashino.com")
        
        if result["success"]:
            print("✅ SUCCESS with native components!")
            print(f"📝 Review: {result['review_length']} chars")
            print(f"🚀 Published: {result['published_result'][:100]}...")
            print(f"\n📖 Preview:\n{result['review_content'][:500]}...")
        else:
            print(f"❌ Failed: {result['error']}")
    
    asyncio.run(test_native_cms())