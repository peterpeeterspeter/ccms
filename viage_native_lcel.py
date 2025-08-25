"""
🎯 Viage Casino - Pure Native LangChain LCEL
CLAUDE.md Compliant: LCEL chains + native tools only
"""

import os
from dotenv import load_dotenv
load_dotenv()

# Pure native LangChain imports
from langchain_community.vectorstores import SupabaseVectorStore
from langchain_community.tools import TavilySearchResults
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from langchain_core.output_parsers import StrOutputParser
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.documents import Document
from supabase import create_client
import sys
sys.path.append('src')
from integrations.langchain_wordpress_tool import WordPressPublishingTool

print("🚀 Viage Casino - Pure Native LangChain LCEL")

# Native connections
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

# Native vectorstore
vectorstore = SupabaseVectorStore(
    client=supabase,
    embedding=OpenAIEmbeddings(),
    table_name="documents",
    query_name="match_documents"
)

# Native tools
tavily_tool = TavilySearchResults(max_results=5)
wordpress_tool = WordPressPublishingTool()

# Native retriever for existing data
casino_retriever = vectorstore.as_retriever(search_kwargs={"k": 10})

# === 1. RESEARCH CHAIN ===
research_prompt = ChatPromptTemplate.from_messages([
    ("system", "Research Viage Casino comprehensively. Find licensing, games, bonuses, banking, reviews."),
    ("human", "{input}")
])

research_agent = create_tool_calling_agent(
    ChatOpenAI(model="gpt-4o-mini"),
    [tavily_tool],
    research_prompt
)

research_executor = AgentExecutor(
    agent=research_agent,
    tools=[tavily_tool],
    max_iterations=3,
    verbose=True
)

# === 2. REVIEW GENERATION CHAIN ===
review_prompt = ChatPromptTemplate.from_template("""
Write comprehensive 2500+ word narrative review of Viage Casino.

Casino Intelligence Database:
{context}

Fresh Research:
{research}

Write flowing paragraphs (NO bullet points) covering:
- Casino overview and licensing
- Game selection and providers  
- Bonuses and promotions
- Banking and withdrawals
- Security and support
- Mobile experience
- Final verdict

Casino: {casino_name}

Your comprehensive narrative review:""")

# Native LCEL review chain
review_chain = (
    RunnableParallel({
        "context": casino_retriever,
        "research": lambda x: research_executor.invoke({"input": f"Research {x} casino comprehensive analysis"}),
        "casino_name": RunnablePassthrough()
    })
    | review_prompt
    | ChatOpenAI(model="gpt-4o", temperature=0.7, max_tokens=4000)
    | StrOutputParser()
)

# === 3. PUBLISHING CHAIN ===
publish_prompt = ChatPromptTemplate.from_messages([
    ("system", "Publish casino review with proper WordPress formatting and taxonomies."),
    ("human", "Publish this Viage Casino review: {content}")
])

publish_agent = create_tool_calling_agent(
    ChatOpenAI(model="gpt-4o-mini"),
    [wordpress_tool],
    publish_prompt
)

publish_executor = AgentExecutor(
    agent=publish_agent,
    tools=[wordpress_tool],
    max_iterations=2,
    verbose=True
)

# === 4. COMPLETE LCEL PIPELINE ===
viage_pipeline = (
    RunnablePassthrough()
    | review_chain
    | (lambda review: {
        "title": "Viage Casino Review 2024 - Comprehensive Expert Analysis",
        "content": review,
        "casino_name": "Viage",
        "overall_rating": 8.4,
        "pros": ["Licensed operation", "Game variety", "Multiple payment methods"],
        "cons": ["Geographic restrictions", "Wagering requirements"],
        "categories": ["Casino Reviews", "Expert Analysis"],
        "tags": ["Viage Casino", "Casino Review 2024", "Expert Analysis"]
    })
    | publish_executor
)

# Execute native pipeline
if __name__ == "__main__":
    print("\n🎯 Executing Native LangChain Pipeline for Viage Casino")
    print("=" * 60)
    
    try:
        result = viage_pipeline.invoke("Viage")
        print(f"✅ Pipeline complete: {result}")
    except Exception as e:
        print(f"❌ Pipeline failed: {e}")