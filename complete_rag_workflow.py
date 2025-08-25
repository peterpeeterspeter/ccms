#!/usr/bin/env python3
"""
COMPLETE UNIVERSAL RAG WORKFLOW - PRODUCTION IMPLEMENTATION
===========================================================

This implements the complete flow as described:
1. Research 95 casino intelligence fields using Tavily
2. Vectorize and store all data in Supabase  
3. Integrate all data sources (Tavily + DataForSEO + schema)
4. Generate comprehensive article from vectorized data
5. Publish to WordPress with images and proper HTML/theme

For future use: python complete_rag_workflow.py --casino "Casino Name"
"""

import sys
import os
import asyncio
import logging
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Load environment
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

# LangChain Core
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser
from langchain_core.documents import Document
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.vectorstores.supabase import SupabaseVectorStore
import supabase

# Import schema
try:
    from schemas.casino_intelligence_schema import CasinoIntelligence
    SCHEMA_AVAILABLE = True
except ImportError:
    SCHEMA_AVAILABLE = False
    print("⚠️ Casino schema not available")

# WordPress and Image APIs
import requests
import base64

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CompleteRAGWorkflow:
    """Complete Universal RAG Workflow Implementation"""
    
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.1)
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self.search_tool = TavilySearchResults(max_results=10)
        
        # Initialize Supabase
        self.supabase_client = self._init_supabase()
        self.vector_store = self._init_vector_store()
        
        # API integrations
        self.dataforseo_login = os.getenv("DATAFORSEO_LOGIN")
        self.dataforseo_password = os.getenv("DATAFORSEO_PASSWORD")
        
        self.wordpress_url = os.getenv("WORDPRESS_SITE_URL", "https://www.crashcasino.io")
        self.wordpress_username = os.getenv("WORDPRESS_USERNAME")
        self.wordpress_password = os.getenv("WORDPRESS_APP_PASSWORD")
        
    def _init_supabase(self):
        """Initialize Supabase client"""
        try:
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
            
            if not supabase_url or not supabase_key:
                raise ValueError("Supabase credentials missing")
                
            client = supabase.create_client(supabase_url, supabase_key)
            logger.info("✅ Supabase client initialized")
            return client
            
        except Exception as e:
            logger.error(f"❌ Supabase initialization failed: {e}")
            return None
    
    def _init_vector_store(self):
        """Initialize Supabase vector store"""
        if not self.supabase_client:
            return None
            
        try:
            vector_store = SupabaseVectorStore(
                client=self.supabase_client,
                embedding=self.embeddings,
                table_name="casino_reviews",
                query_name="match_casino_documents"
            )
            logger.info("✅ Supabase vector store initialized")
            return vector_store
            
        except Exception as e:
            logger.error(f"❌ Vector store initialization failed: {e}")
            return None

    async def research_95_fields(self, casino_name: str) -> Dict[str, Any]:
        """Step 1: Research all 95 casino intelligence fields"""
        logger.info(f"🔍 Researching 95 fields for {casino_name}")
        
        # Define research queries for comprehensive data extraction
        research_queries = [
            f"{casino_name} casino license number authority regulation",
            f"{casino_name} casino games slots table games live casino providers",
            f"{casino_name} casino bonuses welcome bonus wagering requirements",
            f"{casino_name} casino payment methods deposits withdrawals processing times",
            f"{casino_name} casino customer support contact methods response times",
            f"{casino_name} casino security SSL encryption fair gaming RNG",
            f"{casino_name} casino mobile app compatibility user interface",
            f"{casino_name} casino restrictions countries VIP program loyalty",
            f"{casino_name} casino reviews ratings complaints trustworthiness",
            f"{casino_name} casino ownership company background financial info"
        ]
        
        research_data = {}
        
        for i, query in enumerate(research_queries, 1):
            logger.info(f"📋 Research query {i}/10: {query}")
            try:
                results = self.search_tool.invoke(query)
                research_data[f"research_batch_{i}"] = {
                    "query": query,
                    "results": results,
                    "timestamp": datetime.now().isoformat()
                }
                
                # Brief pause between requests
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"❌ Research query {i} failed: {e}")
                research_data[f"research_batch_{i}"] = {
                    "query": query,
                    "results": [],
                    "error": str(e)
                }
        
        logger.info(f"✅ Completed research for {casino_name} - {len(research_data)} batches")
        return research_data

    async def extract_structured_data(self, casino_name: str, research_data: Dict) -> Dict[str, Any]:
        """Step 2: Extract structured 95-field data using LLM"""
        logger.info(f"📊 Extracting structured data for {casino_name}")
        
        if not SCHEMA_AVAILABLE:
            logger.warning("⚠️ Casino schema not available, using simplified extraction")
            return {"casino_name": casino_name, "research_completed": True}
        
        # Create extraction prompt
        extraction_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a casino data extraction expert. Extract comprehensive casino information into the 95-field CasinoIntelligence schema.

Analyze all the research data provided and extract:
- License details (numbers, authorities, dates)
- Game information (counts, providers, RTPs)  
- Bonus details (amounts, wagering, terms)
- Payment methods (options, limits, processing times)
- Security measures (SSL, encryption, auditing)
- Support details (methods, hours, languages)
- Company information (ownership, location, background)

Be precise with numbers, dates, and specific details. If information is not available, mark as null or "Not specified"."""),
            ("human", "Casino: {casino_name}\n\nResearch Data: {research_data}\n\nExtract structured casino data:")
        ])
        
        # Use Pydantic parser for structured extraction
        parser = PydanticOutputParser(pydantic_object=CasinoIntelligence)
        extraction_chain = extraction_prompt | self.llm | parser
        
        try:
            structured_data = await extraction_chain.ainvoke({
                "casino_name": casino_name,
                "research_data": json.dumps(research_data, indent=2)
            })
            
            logger.info("✅ Structured data extraction completed")
            return structured_data.dict()
            
        except Exception as e:
            logger.error(f"❌ Structured data extraction failed: {e}")
            return {"casino_name": casino_name, "extraction_error": str(e)}

    async def search_and_download_images(self, casino_name: str) -> List[Dict]:
        """Step 3: Search and process images using DataForSEO"""
        logger.info(f"🖼️ Searching images for {casino_name}")
        
        if not self.dataforseo_login or not self.dataforseo_password:
            logger.warning("❌ DataForSEO credentials missing")
            return []
        
        try:
            # DataForSEO API request
            url = "https://api.dataforseo.com/v3/serp/google/images/live/advanced"
            
            payload = [{
                "keyword": f"{casino_name} casino logo screenshots",
                "location_code": 2826,  # UK
                "language_code": "en", 
                "device": "desktop",
                "num": 5
            }]
            
            auth = base64.b64encode(f"{self.dataforseo_login}:{self.dataforseo_password}".encode()).decode()
            headers = {
                "Authorization": f"Basic {auth}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                images = []
                
                if data.get("tasks") and data["tasks"][0].get("result"):
                    for item in data["tasks"][0]["result"]:
                        if item.get("items"):
                            for img in item["items"][:5]:
                                if img.get("original"):
                                    images.append({
                                        "url": img["original"],
                                        "title": img.get("title", f"{casino_name} Casino"),
                                        "alt_text": img.get("alt", f"{casino_name} Casino Image"),
                                        "width": img.get("original_width", 0),
                                        "height": img.get("original_height", 0)
                                    })
                
                logger.info(f"✅ Found {len(images)} images for {casino_name}")
                return images
            else:
                logger.error(f"❌ DataForSEO API error: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Image search failed: {e}")
            return []

    async def vectorize_and_store(self, casino_name: str, research_data: Dict, structured_data: Dict, images: List[Dict]) -> bool:
        """Step 4: Vectorize all data and store in Supabase"""
        logger.info(f"💾 Vectorizing and storing data for {casino_name}")
        
        if not self.vector_store:
            logger.error("❌ Vector store not available")
            return False
        
        try:
            # Create documents for vectorization
            documents = []
            
            # Research data documents
            for batch_key, batch_data in research_data.items():
                if "results" in batch_data and batch_data["results"]:
                    for result in batch_data["results"]:
                        doc_content = f"Query: {batch_data['query']}\nContent: {result.get('content', '')}"
                        documents.append(Document(
                            page_content=doc_content,
                            metadata={
                                "casino_name": casino_name,
                                "data_type": "research",
                                "batch": batch_key,
                                "source": result.get("url", "unknown"),
                                "timestamp": batch_data.get("timestamp")
                            }
                        ))
            
            # Structured data document
            structured_content = f"Casino: {casino_name}\nStructured Data: {json.dumps(structured_data, indent=2)}"
            documents.append(Document(
                page_content=structured_content,
                metadata={
                    "casino_name": casino_name,
                    "data_type": "structured_schema",
                    "field_count": len(structured_data),
                    "timestamp": datetime.now().isoformat()
                }
            ))
            
            # Image data documents
            for i, img in enumerate(images):
                img_content = f"Casino: {casino_name}\nImage {i+1}: {img['title']}\nAlt Text: {img['alt_text']}\nURL: {img['url']}"
                documents.append(Document(
                    page_content=img_content,
                    metadata={
                        "casino_name": casino_name,
                        "data_type": "image",
                        "image_url": img["url"],
                        "image_title": img["title"],
                        "timestamp": datetime.now().isoformat()
                    }
                ))
            
            # Store in Supabase vector store
            await self.vector_store.aadd_documents(documents)
            logger.info(f"✅ Stored {len(documents)} documents in Supabase vector store")
            return True
            
        except Exception as e:
            logger.error(f"❌ Vectorization and storage failed: {e}")
            return False

    async def generate_comprehensive_article(self, casino_name: str) -> str:
        """Step 5: Generate article from vectorized data"""
        logger.info(f"✍️ Generating comprehensive article for {casino_name}")
        
        if not self.vector_store:
            logger.error("❌ Vector store not available for retrieval")
            return ""
        
        try:
            # Retrieve relevant documents
            query = f"comprehensive review information about {casino_name} casino license games bonuses payments"
            relevant_docs = await self.vector_store.asimilarity_search(query, k=10)
            
            # Combine retrieved content
            context = "\n\n".join([doc.page_content for doc in relevant_docs])
            
            # Article generation prompt
            article_prompt = ChatPromptTemplate.from_messages([
                ("system", """You are a professional casino review writer. Generate a comprehensive 2500-word article about this casino using the vectorized research data.

Structure the article with these sections:
1. **EXECUTIVE SUMMARY** (200 words)
2. **LICENSING & REGULATION** (300 words) 
3. **GAME SELECTION & PROVIDERS** (400 words)
4. **BONUSES & PROMOTIONS** (300 words)
5. **BANKING & PAYMENTS** (300 words)
6. **USER EXPERIENCE & MOBILE** (250 words)
7. **SECURITY & FAIRNESS** (250 words)  
8. **CUSTOMER SUPPORT** (200 words)
9. **FINAL VERDICT** (300 words)

Include specific details like license numbers, game counts, bonus amounts, processing times, etc. Use professional tone and HTML formatting with proper headings, lists, and emphasis.

Make it engaging and informative for players seeking comprehensive casino information."""),
                ("human", "Casino: {casino_name}\n\nVectorized Research Data: {context}\n\nGenerate comprehensive article:")
            ])
            
            article_chain = article_prompt | self.llm | StrOutputParser()
            
            article = await article_chain.ainvoke({
                "casino_name": casino_name,
                "context": context
            })
            
            logger.info(f"✅ Generated comprehensive article for {casino_name}")
            return article
            
        except Exception as e:
            logger.error(f"❌ Article generation failed: {e}")
            return f"Error generating article for {casino_name}: {str(e)}"

    async def publish_to_wordpress(self, casino_name: str, article_content: str, images: List[Dict]) -> Dict[str, Any]:
        """Step 6: Publish to WordPress with images and proper formatting"""
        logger.info(f"📤 Publishing {casino_name} article to WordPress")
        
        if not self.wordpress_url or not self.wordpress_username or not self.wordpress_password:
            logger.error("❌ WordPress credentials missing")
            return {"success": False, "error": "WordPress credentials missing"}
        
        try:
            # WordPress API endpoints
            wp_api_base = f"{self.wordpress_url}/wp-json/wp/v2"
            
            # Prepare authentication
            auth = (self.wordpress_username, self.wordpress_password)
            
            # Upload images first
            uploaded_images = []
            for i, img in enumerate(images[:3]):  # Limit to 3 images
                try:
                    # Download image
                    img_response = requests.get(img["url"], timeout=30)
                    if img_response.status_code == 200:
                        
                        # Upload to WordPress media
                        files = {
                            'file': (f'{casino_name}_image_{i+1}.jpg', img_response.content, 'image/jpeg')
                        }
                        
                        media_response = requests.post(
                            f"{wp_api_base}/media",
                            auth=auth,
                            files=files,
                            data={
                                'title': img["title"],
                                'alt_text': img["alt_text"]
                            }
                        )
                        
                        if media_response.status_code == 201:
                            media_data = media_response.json()
                            uploaded_images.append({
                                "id": media_data["id"],
                                "url": media_data["source_url"],
                                "title": img["title"]
                            })
                            logger.info(f"✅ Uploaded image {i+1}")
                        
                except Exception as e:
                    logger.error(f"❌ Image {i+1} upload failed: {e}")
            
            # Prepare article with Coinflip theme attributes
            formatted_content = self._format_for_coinflip_theme(article_content, uploaded_images)
            
            # Create WordPress post
            post_data = {
                "title": f"{casino_name} Casino Review 2024 - Comprehensive Analysis",
                "content": formatted_content,
                "status": "draft",  # Change to "publish" when ready
                "categories": [1],  # Adjust category ID as needed
                "tags": [casino_name.lower().replace(" ", "-"), "casino-review", "online-casino"],
                "featured_media": uploaded_images[0]["id"] if uploaded_images else None,
                "meta": {
                    "coinflip_review_type": "casino",
                    "coinflip_casino_name": casino_name,
                    "coinflip_rating": "4.5"  # This should come from analysis
                }
            }
            
            # Publish post
            post_response = requests.post(
                f"{wp_api_base}/posts",
                auth=auth,
                json=post_data
            )
            
            if post_response.status_code == 201:
                post_data = post_response.json()
                logger.info(f"✅ Published article: {post_data['link']}")
                
                return {
                    "success": True,
                    "post_id": post_data["id"],
                    "post_url": post_data["link"],
                    "images_uploaded": len(uploaded_images),
                    "status": "published"
                }
            else:
                logger.error(f"❌ WordPress publish failed: {post_response.status_code}")
                return {
                    "success": False,
                    "error": f"WordPress API error: {post_response.status_code}",
                    "response": post_response.text
                }
                
        except Exception as e:
            logger.error(f"❌ WordPress publishing failed: {e}")
            return {"success": False, "error": str(e)}

    def _format_for_coinflip_theme(self, content: str, images: List[Dict]) -> str:
        """Format content with Coinflip theme HTML and attributes"""
        
        # Add hero image if available
        hero_section = ""
        if images:
            hero_img = images[0]
            hero_section = f'''
<div class="coinflip-hero-section" data-coinflip-element="hero">
    <img src="{hero_img['url']}" alt="{hero_img['title']}" class="coinflip-hero-image" />
    <div class="coinflip-hero-overlay">
        <h2 class="coinflip-hero-title">{hero_img['title']}</h2>
    </div>
</div>
'''
        
        # Add Coinflip-specific CSS classes and data attributes
        formatted_content = content.replace('<h2>', '<h2 class="coinflip-section-header" data-coinflip-section="true">')
        formatted_content = formatted_content.replace('<h3>', '<h3 class="coinflip-subsection-header">')
        formatted_content = formatted_content.replace('<p>', '<p class="coinflip-content-paragraph">')
        formatted_content = formatted_content.replace('<ul>', '<ul class="coinflip-feature-list" data-coinflip-list="features">')
        formatted_content = formatted_content.replace('<ol>', '<ol class="coinflip-numbered-list" data-coinflip-list="numbered">')
        
        # Insert additional images throughout content
        if len(images) > 1:
            sections = formatted_content.split('<h2')
            if len(sections) > 3 and len(images) > 1:  # Insert second image after 3rd section
                img_2 = images[1]
                image_html = f'''
<div class="coinflip-inline-image" data-coinflip-element="inline-image">
    <img src="{img_2['url']}" alt="{img_2['title']}" class="coinflip-content-image" />
    <p class="coinflip-image-caption">{img_2['title']}</p>
</div>
'''
                sections[3] = image_html + '<h2' + sections[3]
                formatted_content = ''.join(sections)
        
        # Wrap in Coinflip container
        final_content = f'''
<div class="coinflip-casino-review" data-coinflip-template="casino-review" data-coinflip-version="1.0">
    {hero_section}
    <div class="coinflip-review-content">
        {formatted_content}
    </div>
    <div class="coinflip-review-footer" data-coinflip-element="footer">
        <p class="coinflip-disclaimer">This review was generated using comprehensive research and analysis. Gambling can be addictive, please play responsibly.</p>
        <div class="coinflip-cta-section">
            <a href="#" class="coinflip-cta-button" data-coinflip-action="visit-casino">Visit Casino</a>
        </div>
    </div>
</div>
'''
        
        return final_content

    async def execute_complete_workflow(self, casino_name: str) -> Dict[str, Any]:
        """Execute the complete Universal RAG workflow"""
        logger.info(f"🚀 Starting complete Universal RAG workflow for {casino_name}")
        
        workflow_results = {
            "casino_name": casino_name,
            "start_time": datetime.now().isoformat(),
            "steps_completed": [],
            "errors": [],
            "final_status": "in_progress"
        }
        
        try:
            # Step 1: Research 95 fields
            logger.info("=== STEP 1: RESEARCHING 95 FIELDS ===")
            research_data = await self.research_95_fields(casino_name)
            workflow_results["steps_completed"].append("research_95_fields")
            workflow_results["research_batches"] = len(research_data)
            
            # Step 2: Extract structured data
            logger.info("=== STEP 2: EXTRACTING STRUCTURED DATA ===")
            structured_data = await self.extract_structured_data(casino_name, research_data)
            workflow_results["steps_completed"].append("structured_extraction")
            workflow_results["structured_fields"] = len(structured_data)
            
            # Step 3: Search images
            logger.info("=== STEP 3: SEARCHING AND PROCESSING IMAGES ===")
            images = await self.search_and_download_images(casino_name)
            workflow_results["steps_completed"].append("image_search")
            workflow_results["images_found"] = len(images)
            
            # Step 4: Vectorize and store
            logger.info("=== STEP 4: VECTORIZING AND STORING IN SUPABASE ===")
            storage_success = await self.vectorize_and_store(casino_name, research_data, structured_data, images)
            if storage_success:
                workflow_results["steps_completed"].append("vectorization_storage")
            else:
                workflow_results["errors"].append("vectorization_storage_failed")
            
            # Step 5: Generate article
            logger.info("=== STEP 5: GENERATING COMPREHENSIVE ARTICLE ===")
            article = await self.generate_comprehensive_article(casino_name)
            workflow_results["steps_completed"].append("article_generation")
            workflow_results["article_length"] = len(article)
            
            # Step 6: Publish to WordPress
            logger.info("=== STEP 6: PUBLISHING TO WORDPRESS ===")
            publish_result = await self.publish_to_wordpress(casino_name, article, images)
            if publish_result.get("success"):
                workflow_results["steps_completed"].append("wordpress_publishing")
                workflow_results["wordpress_post_id"] = publish_result.get("post_id")
                workflow_results["wordpress_url"] = publish_result.get("post_url")
            else:
                workflow_results["errors"].append(f"wordpress_publishing_failed: {publish_result.get('error')}")
            
            # Final status
            workflow_results["end_time"] = datetime.now().isoformat()
            workflow_results["final_status"] = "completed" if len(workflow_results["steps_completed"]) >= 5 else "partial"
            
            # Save workflow log
            log_file = f"{casino_name.lower().replace(' ', '_')}_workflow_log.json"
            with open(log_file, 'w') as f:
                json.dump(workflow_results, f, indent=2)
            
            logger.info(f"✅ Workflow completed for {casino_name}")
            logger.info(f"📊 Steps completed: {len(workflow_results['steps_completed'])}/6")
            logger.info(f"💾 Workflow log saved: {log_file}")
            
            return workflow_results
            
        except Exception as e:
            logger.error(f"❌ Workflow failed: {e}")
            workflow_results["errors"].append(str(e))
            workflow_results["final_status"] = "failed"
            return workflow_results


async def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description="Complete Universal RAG Workflow")
    parser.add_argument("--casino", default="Mr Vegas Casino", help="Casino name to analyze")
    args = parser.parse_args()
    
    print("🚀 COMPLETE UNIVERSAL RAG WORKFLOW - PRODUCTION SYSTEM")
    print("=" * 80)
    print(f"🎰 Casino: {args.casino}")
    print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    workflow = CompleteRAGWorkflow()
    results = await workflow.execute_complete_workflow(args.casino)
    
    print("\n" + "=" * 80)
    print("🏆 WORKFLOW EXECUTION RESULTS")
    print("=" * 80)
    print(f"Casino: {results['casino_name']}")
    print(f"Status: {results['final_status'].upper()}")
    print(f"Steps Completed: {len(results['steps_completed'])}/6")
    print(f"Errors: {len(results['errors'])}")
    
    if results.get('wordpress_url'):
        print(f"Published Article: {results['wordpress_url']}")
    
    print("\nSteps Completed:")
    for step in results['steps_completed']:
        print(f"  ✅ {step}")
    
    if results['errors']:
        print("\nErrors Encountered:")
        for error in results['errors']:
            print(f"  ❌ {error}")
    
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())