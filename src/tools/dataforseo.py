"""
DataForSEO Tool
===============

Casino research and SEO data collection using DataForSEO API.
Per WARP.md: Discovery only - images from DataForSEO CANNOT be published directly.
"""

import asyncio
import aiohttp
import json
import base64
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urlparse
from datetime import datetime
import logging

from ..schemas.casino_review import CasinoResearchPack, SEOPlan

logger = logging.getLogger(__name__)


class DataForSEOConfig:
    """DataForSEO API configuration"""
    def __init__(self, login: str, password: str):
        self.login = login
        self.password = password
        self.base_url = "https://api.dataforseo.com/v3"
        self.timeout = 60
        self.max_retries = 3
        
        # Create basic auth header
        credentials = f"{login}:{password}"
        self.auth_header = base64.b64encode(credentials.encode()).decode()


class DataForSEOClient:
    """
    DataForSEO API client for casino research
    
    Features:
    - Casino SERP analysis and competitor intelligence
    - Keyword research for casino reviews
    - Brand mention monitoring
    - Backlink analysis (for credibility assessment)
    - Image discovery (for reference only - not for publishing)
    
    IMPORTANT: Per WARP.md, images from DataForSEO are for discovery only.
    Publishing requires first-party captures via Firecrawl/CF Browser/Browserless.
    """
    
    def __init__(self, config: DataForSEOConfig):
        self.config = config
        self.session = None
        self._setup_session()
    
    def _setup_session(self):
        """Setup aiohttp session with DataForSEO authentication"""
        timeout = aiohttp.ClientTimeout(total=self.config.timeout)
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            headers={
                "Authorization": f"Basic {self.config.auth_header}",
                "Content-Type": "application/json",
                "User-Agent": "CrashCasino-Research/1.0"
            }
        )
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def research_casino_comprehensive(self, 
                                          casino_name: str, 
                                          casino_url: str,
                                          target_location: str = "United States") -> CasinoResearchPack:
        """
        Comprehensive casino research using multiple DataForSEO endpoints
        
        Args:
            casino_name: Name of the casino to research
            casino_url: Casino website URL
            target_location: Geographic location for SERP analysis
            
        Returns:
            CasinoResearchPack with comprehensive research data
        """
        
        logger.info(f"Starting comprehensive research for {casino_name}")
        
        try:
            # Parallel data collection
            research_tasks = [
                self._get_serp_analysis(casino_name, target_location),
                self._get_competitor_analysis(casino_name, target_location),
                self._get_keyword_research(casino_name),
                self._get_backlink_analysis(casino_url),
                self._get_brand_mentions(casino_name),
                self._discover_images(casino_name)  # Discovery only!
            ]
            
            results = await asyncio.gather(*research_tasks, return_exceptions=True)
            
            # Parse results
            serp_data = results[0] if not isinstance(results[0], Exception) else {}
            competitor_data = results[1] if not isinstance(results[1], Exception) else {}
            keyword_data = results[2] if not isinstance(results[2], Exception) else {}
            backlink_data = results[3] if not isinstance(results[3], Exception) else {}
            mention_data = results[4] if not isinstance(results[4], Exception) else {}
            image_data = results[5] if not isinstance(results[5], Exception) else {}
            
            # Build comprehensive research pack
            research_pack = CasinoResearchPack(
                casino_name=casino_name,
                casino_url=casino_url,
                research_date=datetime.now(),
                
                # SERP Intelligence
                serp_ranking=serp_data.get("rankings", []),
                competitor_analysis=competitor_data.get("competitors", []),
                top_ranking_content=serp_data.get("top_content", []),
                
                # SEO Data
                primary_keywords=keyword_data.get("primary", []),
                long_tail_keywords=keyword_data.get("long_tail", []),
                related_queries=keyword_data.get("related", []),
                search_volume_data=keyword_data.get("volumes", {}),
                
                # Authority & Trust Signals
                backlink_profile=backlink_data.get("profile", {}),
                domain_authority_score=backlink_data.get("authority", 0),
                trust_signals=backlink_data.get("trust_signals", []),
                
                # Brand Intelligence
                brand_mentions=mention_data.get("mentions", []),
                sentiment_analysis=mention_data.get("sentiment", {}),
                
                # Image Discovery (NOT for publishing)
                discovered_images=image_data.get("images", []),
                
                # Metadata
                data_sources=["dataforseo_serp", "dataforseo_keywords", "dataforseo_backlinks"],
                research_accuracy=self._calculate_research_confidence(results),
                notes=f"Comprehensive research via DataForSEO API on {datetime.now().isoformat()}"
            )
            
            logger.info(f"✅ Completed comprehensive research for {casino_name}")
            logger.info(f"   - Found {len(research_pack.primary_keywords)} primary keywords")
            logger.info(f"   - Analyzed {len(research_pack.competitor_analysis)} competitors")
            logger.info(f"   - Discovered {len(research_pack.discovered_images)} reference images")
            
            return research_pack
            
        except Exception as e:
            logger.error(f"Comprehensive research failed for {casino_name}: {str(e)}")
            # Return minimal research pack
            return CasinoResearchPack(
                casino_name=casino_name,
                casino_url=casino_url,
                research_date=datetime.now(),
                notes=f"Research failed: {str(e)}",
                research_accuracy=0.0
            )
    
    async def _get_serp_analysis(self, casino_name: str, location: str) -> Dict:
        """Analyze SERP results for casino-related queries"""
        
        # Key search queries for casino analysis
        queries = [
            f"{casino_name} review",
            f"{casino_name} casino",
            f"{casino_name} bonus",
            f"{casino_name} games",
            f"best {casino_name} alternative"
        ]
        
        serp_results = {"rankings": [], "top_content": []}
        
        for query in queries:
            try:
                result = await self._call_serp_api(query, location)
                if result:
                    serp_results["rankings"].extend(result.get("rankings", []))
                    serp_results["top_content"].extend(result.get("top_results", []))
                
                # Rate limiting
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.warning(f"SERP analysis failed for query '{query}': {str(e)}")
                continue
        
        return serp_results
    
    async def _get_competitor_analysis(self, casino_name: str, location: str) -> Dict:
        """Identify and analyze competitor casinos in SERP"""
        
        try:
            # Search for general casino terms to find competitors
            competitor_queries = [
                "online casino review",
                "best online casinos",
                f"{casino_name} vs",
                "casino comparison"
            ]
            
            competitors = {}
            
            for query in competitor_queries:
                result = await self._call_serp_api(query, location)
                if result:
                    # Extract competitor domains from SERP results
                    for item in result.get("organic_results", []):
                        domain = urlparse(item.get("link", "")).netloc
                        if domain and domain not in competitors:
                            competitors[domain] = {
                                "domain": domain,
                                "titles": [],
                                "descriptions": [],
                                "ranking_positions": []
                            }
                        
                        if domain in competitors:
                            competitors[domain]["titles"].append(item.get("title", ""))
                            competitors[domain]["descriptions"].append(item.get("snippet", ""))
                            competitors[domain]["ranking_positions"].append(item.get("rank_group", 0))
                
                await asyncio.sleep(1)
            
            # Convert to list and limit to top competitors
            competitor_list = list(competitors.values())[:10]
            
            return {"competitors": competitor_list}
            
        except Exception as e:
            logger.error(f"Competitor analysis failed: {str(e)}")
            return {"competitors": []}
    
    async def _get_keyword_research(self, casino_name: str) -> Dict:
        """Research keywords related to the casino"""
        
        try:
            # Seed keywords for expansion
            seed_keywords = [
                casino_name,
                f"{casino_name} casino",
                f"{casino_name} review",
                f"{casino_name} bonus",
                f"{casino_name} games"
            ]
            
            keyword_data = {
                "primary": [],
                "long_tail": [],
                "related": [],
                "volumes": {}
            }
            
            for seed in seed_keywords:
                result = await self._call_keywords_api(seed)
                if result:
                    # Categorize keywords
                    for kw_data in result.get("keywords", []):
                        keyword = kw_data.get("keyword", "")
                        volume = kw_data.get("search_volume", 0)
                        
                        keyword_data["volumes"][keyword] = volume
                        
                        if len(keyword.split()) <= 2:
                            keyword_data["primary"].append(keyword)
                        else:
                            keyword_data["long_tail"].append(keyword)
                
                # Get related keywords
                related = await self._call_related_keywords_api(seed)
                if related:
                    keyword_data["related"].extend(related.get("related", []))
                
                await asyncio.sleep(1)
            
            # Deduplicate and sort by volume
            keyword_data["primary"] = list(set(keyword_data["primary"]))
            keyword_data["long_tail"] = list(set(keyword_data["long_tail"]))
            keyword_data["related"] = list(set(keyword_data["related"]))
            
            return keyword_data
            
        except Exception as e:
            logger.error(f"Keyword research failed: {str(e)}")
            return {"primary": [], "long_tail": [], "related": [], "volumes": {}}
    
    async def _get_backlink_analysis(self, casino_url: str) -> Dict:
        """Analyze casino's backlink profile for authority assessment"""
        
        try:
            result = await self._call_backlinks_api(casino_url)
            
            if result:
                backlinks = result.get("backlinks", [])
                
                # Calculate domain authority score (simplified)
                unique_domains = len(set(link.get("domain", "") for link in backlinks))
                total_backlinks = len(backlinks)
                
                authority_score = min(100, (unique_domains * 0.5) + (total_backlinks * 0.1))
                
                # Extract trust signals
                trust_signals = []
                for link in backlinks[:20]:  # Top 20 backlinks
                    if link.get("domain_rank", 0) > 70:  # High authority domains
                        trust_signals.append({
                            "domain": link.get("domain"),
                            "authority": link.get("domain_rank"),
                            "anchor_text": link.get("anchor_text", "")
                        })
                
                return {
                    "profile": {
                        "total_backlinks": total_backlinks,
                        "unique_domains": unique_domains,
                        "top_backlinks": backlinks[:10]
                    },
                    "authority": authority_score,
                    "trust_signals": trust_signals
                }
            
            return {"profile": {}, "authority": 0, "trust_signals": []}
            
        except Exception as e:
            logger.error(f"Backlink analysis failed: {str(e)}")
            return {"profile": {}, "authority": 0, "trust_signals": []}
    
    async def _get_brand_mentions(self, casino_name: str) -> Dict:
        """Find brand mentions across the web"""
        
        try:
            # Search for brand mentions
            result = await self._call_mentions_api(casino_name)
            
            if result:
                mentions = result.get("mentions", [])
                
                # Basic sentiment analysis (simplified)
                positive_words = ["great", "excellent", "best", "amazing", "fantastic", "recommended"]
                negative_words = ["bad", "terrible", "scam", "awful", "avoid", "horrible"]
                
                sentiment_scores = []
                for mention in mentions:
                    text = mention.get("text", "").lower()
                    positive_count = sum(1 for word in positive_words if word in text)
                    negative_count = sum(1 for word in negative_words if word in text)
                    
                    if positive_count > negative_count:
                        sentiment_scores.append(1)
                    elif negative_count > positive_count:
                        sentiment_scores.append(-1)
                    else:
                        sentiment_scores.append(0)
                
                # Calculate overall sentiment
                if sentiment_scores:
                    avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
                else:
                    avg_sentiment = 0
                
                return {
                    "mentions": mentions,
                    "sentiment": {
                        "average_score": avg_sentiment,
                        "total_mentions": len(mentions),
                        "positive_mentions": sum(1 for s in sentiment_scores if s > 0),
                        "negative_mentions": sum(1 for s in sentiment_scores if s < 0)
                    }
                }
            
            return {"mentions": [], "sentiment": {}}
            
        except Exception as e:
            logger.error(f"Brand mention analysis failed: {str(e)}")
            return {"mentions": [], "sentiment": {}}
    
    async def _discover_images(self, casino_name: str) -> Dict:
        """
        Discover images related to the casino
        
        IMPORTANT: Per WARP.md, these are for DISCOVERY ONLY.
        Images from DataForSEO cannot be published due to licensing.
        Use Firecrawl/CF Browser/Browserless for publishable screenshots.
        """
        
        try:
            result = await self._call_images_api(casino_name)
            
            if result:
                images = result.get("images", [])
                
                # Filter and categorize discovered images
                categorized = {
                    "logos": [],
                    "interfaces": [],
                    "promotions": [],
                    "other": []
                }
                
                for img in images:
                    title = img.get("title", "").lower()
                    alt = img.get("alt", "").lower()
                    
                    if "logo" in title or "logo" in alt:
                        categorized["logos"].append(img)
                    elif any(word in title or word in alt for word in ["interface", "homepage", "game", "casino"]):
                        categorized["interfaces"].append(img)
                    elif any(word in title or word in alt for word in ["bonus", "promotion", "offer"]):
                        categorized["promotions"].append(img)
                    else:
                        categorized["other"].append(img)
                
                logger.info(f"📷 Discovered images for {casino_name}: {len(images)} total")
                logger.warning("⚠️  DataForSEO images are for REFERENCE ONLY - not for publishing")
                
                return {"images": categorized}
            
            return {"images": {}}
            
        except Exception as e:
            logger.error(f"Image discovery failed: {str(e)}")
            return {"images": {}}
    
    # DataForSEO API call methods
    
    async def _call_serp_api(self, query: str, location: str) -> Optional[Dict]:
        """Call DataForSEO SERP API"""
        
        payload = [{
            "language_name": "English",
            "location_name": location,
            "keyword": query,
            "se_domain": "google.com",
            "device": "desktop",
            "os": "windows"
        }]
        
        return await self._make_api_request("serp/google/organic/live/advanced", payload)
    
    async def _call_keywords_api(self, seed_keyword: str) -> Optional[Dict]:
        """Call DataForSEO Keywords API"""
        
        payload = [{
            "keyword": seed_keyword,
            "language_name": "English",
            "location_name": "United States"
        }]
        
        return await self._make_api_request("keywords_data/google/search_volume/live", payload)
    
    async def _call_related_keywords_api(self, seed_keyword: str) -> Optional[Dict]:
        """Get related keywords"""
        
        payload = [{
            "keyword": seed_keyword,
            "language_name": "English",
            "location_name": "United States",
            "limit": 50
        }]
        
        return await self._make_api_request("keywords_data/google/keyword_suggestions/live", payload)
    
    async def _call_backlinks_api(self, target_url: str) -> Optional[Dict]:
        """Call DataForSEO Backlinks API"""
        
        payload = [{
            "target": target_url,
            "limit": 100,
            "order_by": ["rank,desc"]
        }]
        
        return await self._make_api_request("backlinks/backlinks/live", payload)
    
    async def _call_mentions_api(self, brand_name: str) -> Optional[Dict]:
        """Search for brand mentions"""
        
        # Use SERP API to find mentions
        queries = [
            f'"{brand_name}" review',
            f'"{brand_name}" opinion',
            f'"{brand_name}" experience'
        ]
        
        all_mentions = []
        
        for query in queries:
            result = await self._call_serp_api(query, "United States")
            if result:
                organic_results = result.get("organic_results", [])
                for item in organic_results:
                    all_mentions.append({
                        "url": item.get("link", ""),
                        "title": item.get("title", ""),
                        "text": item.get("snippet", ""),
                        "domain": urlparse(item.get("link", "")).netloc
                    })
            
            await asyncio.sleep(1)
        
        return {"mentions": all_mentions}
    
    async def _call_images_api(self, search_term: str) -> Optional[Dict]:
        """Call DataForSEO Images API"""
        
        payload = [{
            "keyword": search_term,
            "language_name": "English",
            "location_name": "United States",
            "device": "desktop",
            "limit": 50
        }]
        
        return await self._make_api_request("serp/google/images/live/advanced", payload)
    
    async def _make_api_request(self, endpoint: str, payload: List[Dict]) -> Optional[Dict]:
        """Make authenticated request to DataForSEO API"""
        
        url = f"{self.config.base_url}/{endpoint}"
        
        for attempt in range(self.config.max_retries):
            try:
                async with self.session.post(url, json=payload) as response:
                    
                    if response.status == 401:
                        raise Exception("DataForSEO authentication failed - check credentials")
                    
                    if response.status == 429:
                        logger.warning("DataForSEO rate limit hit, waiting...")
                        await asyncio.sleep(10)
                        continue
                    
                    if response.status >= 400:
                        error_data = await response.json()
                        raise Exception(f"DataForSEO API error: {error_data}")
                    
                    result = await response.json()
                    
                    if result.get("status_code") == 20000 and result.get("tasks"):
                        task_result = result["tasks"][0].get("result", {})
                        return task_result
                    else:
                        error_message = result.get("status_message", "Unknown error")
                        raise Exception(f"DataForSEO API error: {error_message}")
                        
            except aiohttp.ClientError as e:
                logger.warning(f"DataForSEO request failed (attempt {attempt + 1}): {str(e)}")
                if attempt == self.config.max_retries - 1:
                    raise Exception(f"DataForSEO connection failed after {self.config.max_retries} attempts")
                
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        return None
    
    def _calculate_research_confidence(self, results: List) -> float:
        """Calculate confidence score based on successful data collection"""
        
        successful_results = sum(1 for r in results if not isinstance(r, Exception))
        total_results = len(results)
        
        return (successful_results / total_results) if total_results > 0 else 0.0
    
    async def generate_seo_plan(self, research_pack: CasinoResearchPack) -> SEOPlan:
        """
        Generate SEO optimization plan based on research data
        
        Args:
            research_pack: Completed casino research data
            
        Returns:
            SEO plan with recommendations
        """
        
        try:
            # Extract top keywords for optimization
            primary_kw = research_pack.primary_keywords[:5]  # Top 5 primary
            long_tail_kw = research_pack.long_tail_keywords[:10]  # Top 10 long-tail
            
            # Generate title suggestions
            title_templates = [
                f"{research_pack.casino_name} Review 2024: Honest Casino Analysis",
                f"{research_pack.casino_name} Casino Review - Games, Bonuses & More",
                f"Is {research_pack.casino_name} Legit? Complete 2024 Review"
            ]
            
            # Generate meta descriptions
            meta_descriptions = [
                f"Comprehensive {research_pack.casino_name} review covering games, bonuses, security & more. Read our honest analysis before you play.",
                f"Detailed {research_pack.casino_name} casino review with pros, cons, game selection & bonus offers. Updated 2024.",
                f"Expert {research_pack.casino_name} review: games, payments, licensing & user experience. Everything you need to know."
            ]
            
            # Create structured data suggestions
            structured_data = {
                "@type": "Review",
                "itemReviewed": {
                    "@type": "Organization",
                    "name": research_pack.casino_name,
                    "url": research_pack.casino_url
                },
                "author": {
                    "@type": "Organization",
                    "name": "CrashCasino"
                },
                "reviewRating": {
                    "@type": "Rating",
                    "ratingValue": "4.0",  # To be determined by review content
                    "bestRating": "5.0"
                },
                "publisher": {
                    "@type": "Organization",
                    "name": "CrashCasino"
                }
            }
            
            # Internal linking opportunities
            internal_links = [
                {"anchor": "best online casinos", "target": "/best-online-casinos/"},
                {"anchor": "casino bonuses", "target": "/casino-bonuses/"},
                {"anchor": "casino games", "target": "/casino-games/"},
                {"anchor": "payment methods", "target": "/payment-methods/"}
            ]
            
            seo_plan = SEOPlan(
                target_keywords=primary_kw,
                long_tail_keywords=long_tail_kw,
                title_suggestions=title_templates,
                meta_descriptions=meta_descriptions,
                header_structure={
                    "h1": f"{research_pack.casino_name} Review 2024",
                    "h2": ["Games & Software", "Bonuses & Promotions", "Banking & Security", "User Experience"],
                    "h3": ["Game Selection", "Bonus Terms", "Payment Methods", "Mobile Experience"]
                },
                internal_linking_opportunities=internal_links,
                content_gaps=[],  # To be filled by content analysis
                competitor_insights=research_pack.competitor_analysis[:5],
                structured_data=structured_data,
                estimated_ranking_potential=8.5,  # Based on keyword difficulty
                optimization_priority="high"
            )
            
            logger.info(f"Generated SEO plan for {research_pack.casino_name}")
            logger.info(f"  Target keywords: {len(seo_plan.target_keywords)}")
            logger.info(f"  Long-tail keywords: {len(seo_plan.long_tail_keywords)}")
            
            return seo_plan
            
        except Exception as e:
            logger.error(f"SEO plan generation failed: {str(e)}")
            # Return basic SEO plan
            return SEOPlan(
                target_keywords=[research_pack.casino_name],
                title_suggestions=[f"{research_pack.casino_name} Review"],
                meta_descriptions=[f"{research_pack.casino_name} casino review"],
                notes=f"SEO plan generation failed: {str(e)}"
            )
    
    async def test_connection(self) -> bool:
        """Test DataForSEO API connection"""
        try:
            # Simple test request
            result = await self._make_api_request("serp/google/organic/live/advanced", [{
                "keyword": "test",
                "language_name": "English",
                "location_name": "United States",
                "limit": 1
            }])
            
            if result:
                logger.info("✅ DataForSEO API connection successful")
                return True
            else:
                logger.error("❌ DataForSEO API test failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ DataForSEO API connection failed: {str(e)}")
            return False


# Factory function
def create_dataforseo_client(login: str, password: str) -> DataForSEOClient:
    """
    Factory function to create DataForSEO client
    
    Args:
        login: DataForSEO login
        password: DataForSEO password
        
    Returns:
        Configured DataForSEOClient instance
    """
    config = DataForSEOConfig(login=login, password=password)
    return DataForSEOClient(config)


# Example usage and testing
async def test_dataforseo_research():
    """Test function for DataForSEO casino research"""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Create DataForSEO client
    client = create_dataforseo_client(
        login=os.getenv("DATAFORSEO_LOGIN"),
        password=os.getenv("DATAFORSEO_PASSWORD")
    )
    
    async with client:
        # Test connection
        if await client.test_connection():
            print("✅ DataForSEO connection successful")
            
            # Test comprehensive research
            research_pack = await client.research_casino_comprehensive(
                casino_name="Bitstarz",
                casino_url="https://bitstarz.com"
            )
            
            print(f"\n🔍 Research Results for {research_pack.casino_name}:")
            print(f"   Primary keywords: {len(research_pack.primary_keywords)}")
            print(f"   Competitors analyzed: {len(research_pack.competitor_analysis)}")
            print(f"   Backlinks found: {len(research_pack.backlink_profile.get('top_backlinks', []))}")
            print(f"   Brand mentions: {len(research_pack.brand_mentions)}")
            print(f"   Research confidence: {research_pack.research_accuracy:.1%}")
            
            # Generate SEO plan
            seo_plan = await client.generate_seo_plan(research_pack)
            print(f"\n📊 SEO Plan Generated:")
            print(f"   Target keywords: {seo_plan.target_keywords[:3]}")
            print(f"   Title suggestions: {len(seo_plan.title_suggestions)}")
            print(f"   Ranking potential: {seo_plan.estimated_ranking_potential}/10")
            
        else:
            print("❌ DataForSEO connection failed")


if __name__ == "__main__":
    asyncio.run(test_dataforseo_research())
