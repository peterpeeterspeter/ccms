#!/usr/bin/env python3
"""
🔧 DEBUG: Supabase Vector Store Issues
=====================================

This script helps debug Supabase vector store problems:
1. Test connection to Supabase
2. Check table schema and structure  
3. Check existing data and dimensions
4. Test basic retrieval operations
5. Fix common issues

Usage:
    python debug_supabase.py
"""

import os
import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def debug_supabase_connection():
    """Test basic Supabase connection and configuration"""
    print("🔧 SUPABASE CONNECTION DEBUG")
    print("=" * 40)
    
    # Check environment variables
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    print(f"🌐 SUPABASE_URL: {'✅ Set' if supabase_url else '❌ Missing'}")
    print(f"🔑 SUPABASE_SERVICE_KEY: {'✅ Set' if supabase_key else '❌ Missing'}")
    
    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase environment variables")
        return False
    
    try:
        # Test basic Supabase connection
        from supabase import create_client
        supabase_client = create_client(supabase_url, supabase_key)
        
        print("✅ Supabase client created successfully")
        
        # Check if we can make a basic request
        tables_response = supabase_client.table("casino_reviews").select("*").limit(1).execute()
        print(f"✅ Basic table access works: {len(tables_response.data) if tables_response.data else 0} rows found")
        
        return True
        
    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")
        return False

async def debug_vector_store_setup():
    """Debug vector store setup and embedding dimensions"""
    print("\n🎯 VECTOR STORE SETUP DEBUG")
    print("=" * 40)
    
    try:
        from langchain_openai import OpenAIEmbeddings
        from langchain_community.vectorstores.supabase import SupabaseVectorStore
        from supabase import create_client
        
        # Initialize components
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        print("✅ OpenAI embeddings initialized")
        
        # Test embedding dimensions
        test_text = "This is a test embedding"
        test_embedding = embeddings.embed_query(test_text)
        print(f"✅ Embedding dimension: {len(test_embedding)} (should be 1536 for text-embedding-3-small)")
        
        # Create Supabase client
        supabase_client = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_KEY")
        )
        
        # Create SupabaseVectorStore using documents table (has embeddings)
        documents_check = supabase_client.table("documents").select("embedding").limit(1).execute()
        if documents_check.data and documents_check.data[0].get('embedding'):
            print("✅ Using documents table (has embeddings)")
            vector_store = SupabaseVectorStore(
                client=supabase_client,
                embedding=embeddings,
                table_name="documents"
            )
        else:
            print("⚠️ Using casino_reviews table (no custom query)")
            vector_store = SupabaseVectorStore(
                client=supabase_client,
                embedding=embeddings,
                table_name="casino_reviews"
            )
        print("✅ SupabaseVectorStore created successfully")
        
        return vector_store, embeddings
        
    except Exception as e:
        print(f"❌ Vector store setup failed: {e}")
        import traceback
        traceback.print_exc()
        return None, None

async def debug_table_schema():
    """Check Supabase table schema and existing data"""
    print("\n📊 TABLE SCHEMA DEBUG")
    print("=" * 40)
    
    try:
        from supabase import create_client
        
        supabase_client = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_KEY")
        )
        
        # Check if casino_reviews table exists and has data
        try:
            response = supabase_client.table("casino_reviews").select("*").limit(5).execute()
            print(f"📋 casino_reviews table: {len(response.data)} rows found")
            
            if response.data:
                print("📄 Sample row structure:")
                for key in response.data[0].keys():
                    print(f"   - {key}")
                    
                # Check if embedding column exists and has correct dimensions
                first_row = response.data[0]
                if 'embedding' in first_row and first_row['embedding']:
                    embedding_len = len(first_row['embedding']) if isinstance(first_row['embedding'], list) else 0
                    print(f"🎯 Embedding dimension in table: {embedding_len}")
                else:
                    print("⚠️ No embedding data found in existing rows")
            
        except Exception as e:
            print(f"❌ Error accessing casino_reviews table: {e}")
        
        # Check for documents table (old schema)
        try:
            response = supabase_client.table("documents").select("*").limit(5).execute()
            print(f"📋 documents table: {len(response.data)} rows found")
            
            if response.data:
                print("📄 Documents table sample structure:")
                for key in response.data[0].keys():
                    print(f"   - {key}")
        except Exception as e:
            print(f"ℹ️ documents table not accessible (this is okay): {e}")
            
    except Exception as e:
        print(f"❌ Table schema check failed: {e}")

async def test_basic_retrieval():
    """Test basic retrieval operations"""
    print("\n🔍 RETRIEVAL TEST")
    print("=" * 40)
    
    vector_store, embeddings = await debug_vector_store_setup()
    
    if not vector_store:
        print("❌ Cannot test retrieval - vector store not available")
        return
    
    try:
        # Test basic similarity search
        print("🔍 Testing basic similarity search...")
        results = vector_store.similarity_search("Mr Vegas Casino", k=3)
        print(f"✅ Basic search returned {len(results)} results")
        
        for i, doc in enumerate(results):
            print(f"   {i+1}. Content preview: {doc.page_content[:100]}...")
            print(f"      Metadata: {doc.metadata}")
            
    except Exception as e:
        print(f"❌ Basic retrieval failed: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        # Test retriever with filter
        print("\n🎯 Testing retriever with casino filter...")
        retriever = vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={
                "k": 3,
                "filter": {"casino_name": "Mr Vegas Casino"}
            }
        )
        
        results = retriever.get_relevant_documents("casino review")
        print(f"✅ Filtered search returned {len(results)} results")
        
    except Exception as e:
        print(f"❌ Filtered retrieval failed: {e}")
        import traceback
        traceback.print_exc()

async def suggest_fixes():
    """Suggest fixes for common Supabase issues"""
    print("\n🛠️ SUGGESTED FIXES")
    print("=" * 40)
    
    print("Based on the error 'Number of columns in X and Y must be the same', try:")
    print()
    print("1. 🗃️ Check if casino_reviews table exists:")
    print("   - Go to Supabase dashboard > Table Editor")
    print("   - Look for 'casino_reviews' table")
    print("   - If missing, create it with proper schema")
    print()
    print("2. 📐 Check embedding dimensions:")
    print("   - Table should have 'embedding' column of type 'vector(1536)'")
    print("   - All embeddings must be exactly 1536 dimensions")
    print()
    print("3. 🔧 Create proper RPC function:")
    print("   SQL to run in Supabase SQL Editor:")
    print("""
CREATE OR REPLACE FUNCTION match_casino_reviews(
  query_embedding vector(1536),
  match_threshold float DEFAULT 0.78,
  match_count int DEFAULT 10
)
RETURNS TABLE (
  id bigint,
  content text,
  metadata jsonb,
  embedding vector(1536),
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    cr.id,
    cr.content,
    cr.metadata,
    cr.embedding,
    1 - (cr.embedding <=> query_embedding) AS similarity
  FROM casino_reviews cr
  WHERE 1 - (cr.embedding <=> query_embedding) > match_threshold
  ORDER BY similarity DESC
  LIMIT match_count;
END;
$$;
""")
    print()
    print("4. 🔄 Clear and re-create table if needed:")
    print("   - DROP TABLE IF EXISTS casino_reviews;")
    print("   - Re-run vectorization to populate fresh data")

async def main():
    """Main debug execution"""
    print("🚀 SUPABASE DEBUG DIAGNOSTICS")
    print("=" * 50)
    
    # Test connection
    connection_ok = await debug_supabase_connection()
    
    if not connection_ok:
        print("\n❌ Fix connection issues first before continuing")
        return
    
    # Test vector store setup
    await debug_vector_store_setup()
    
    # Check table schema
    await debug_table_schema()
    
    # Test retrieval
    await test_basic_retrieval()
    
    # Suggest fixes
    await suggest_fixes()
    
    print("\n✅ SUPABASE DEBUG COMPLETE")
    print("Review the output above to identify and fix issues")

if __name__ == "__main__":
    asyncio.run(main())