"""
Casino Research Agent
=====================

LangChain LCEL-based agent for comprehensive casino research using DataForSEO.
Follows WARP.md: deterministic contracts, tool adapters only, Pydantic v2 schemas.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import PydanticOutputParser

from ..schemas.casino_review import CasinoResearchPack, SEOPlan, CasinoResearchRequest
from ..tools import ToolOrchestrator
from ..prompts.research_prompts import (
    CASINO_RESEARCH_SYSTEM_PROMPT,
    CASINO_ANALYSIS_PROMPT,
    SEO_PLANNING_PROMPT
)

logger = logging.getLogger(__name__)


class CasinoResearchAgent:
    """
    Casino Research Agent using LCEL composition
    
    Responsibilities:
    - Comprehensive casino data collection via DataForSEO
    - Competitor analysis and market positioning
    - Keyword research and SEO opportunity identification
    - Authority assessment via backlink analysis
    - Brand sentiment analysis
    
    Input: CasinoResearchRequest
    Output: CasinoResearchPack
    """
    
    def __init__(self, 
                 llm: Optional[ChatOpenAI] = None,
                 tool_orchestrator: Optional[ToolOrchestrator] = None):
        self.llm = llm or ChatOpenAI(
            model="gpt-4",
            temperature=0.1,  # Low temperature for factual research
            max_tokens=2000
        )
        self.tools = tool_orchestrator
        self.research_chain = self._build_research_chain()
    
    def _build_research_chain(self):
        """Build the LCEL research chain"""
        
        # Research prompt
        research_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a professional casino research analyst. Analyze casino data comprehensively and provide structured insights."),
            ("human", "Analyze this casino: {casino_name} at {casino_url}. Focus on market position, SEO opportunities, and competitive landscape.")
        ])
        
        # Build the LCEL chain
        chain = (
            RunnablePassthrough.assign(
                # Step 1: Validate and enrich input
                validated_input=RunnableLambda(self._validate_research_request)
            )
            | RunnablePassthrough.assign(
                # Step 2: Perform comprehensive data collection
                raw_research_data=RunnableLambda(self._collect_research_data)
            )
            | RunnablePassthrough.assign(
                # Step 3: Analyze and structure research findings
                analysis_results=RunnableLambda(self._analyze_research_data)
            )
            | RunnablePassthrough.assign(
                # Step 4: Generate SEO strategy
                seo_plan=RunnableLambda(self._generate_seo_strategy)
            )
            | RunnableLambda(self._build_research_pack)
        )
        
        return chain
    
    async def research_casino(self, request: CasinoResearchRequest) -> CasinoResearchPack:
        """
        Main entry point for casino research
        
        Args:
            request: Casino research request with casino details
            
        Returns:
            Comprehensive CasinoResearchPack
        """
        try:
            logger.info(f"🔍 Starting casino research for {request.casino_name}")
            
            # Execute the research chain
            result = await self.research_chain.ainvoke({
                "casino_name": request.casino_name,
                "casino_url": request.casino_url,
                "target_keywords": request.target_keywords or [],
                "competitor_analysis": request.competitor_analysis,
                "depth": request.research_depth,
                "tenant_id": request.tenant_id
            })
            
            logger.info(f"✅ Research completed for {request.casino_name}")
            logger.info(f"   - Keywords found: {len(result.primary_keywords)}")
            logger.info(f"   - Competitors analyzed: {len(result.competitor_analysis)}")
            logger.info(f"   - Research accuracy: {result.research_accuracy:.1%}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Casino research failed for {request.casino_name}: {str(e)}")
            # Return minimal research pack with error info
            return CasinoResearchPack(
                casino_name=request.casino_name,
                casino_url=request.casino_url,
                research_date=datetime.now(),
                notes=f"Research failed: {str(e)}",
                research_accuracy=0.0
            )
    
    def _validate_research_request(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and enrich the research request"""
        
        casino_name = inputs.get("casino_name", "").strip()
        casino_url = inputs.get("casino_url", "").strip()
        
        if not casino_name or not casino_url:
            raise ValueError("Casino name and URL are required for research")
        
        # Normalize and validate URL
        if not casino_url.startswith(("http://", "https://")):
            casino_url = f"https://{casino_url}"
        
        # Set defaults
        validated = {
            "casino_name": casino_name,
            "casino_url": casino_url,
            "target_keywords": inputs.get("target_keywords", []),
            "competitor_analysis": inputs.get("competitor_analysis", True),
            "depth": inputs.get("depth", "comprehensive"),
            "tenant_id": inputs.get("tenant_id", "crashcasino")
        }
        
        logger.info(f"✅ Research request validated for {casino_name}")
        return validated
    
    async def _collect_research_data(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Collect raw research data using DataForSEO"""
        
        if not self.tools:
            raise Exception("Tool orchestrator not available for data collection")
        
        casino_name = inputs["validated_input"]["casino_name"]
        casino_url = inputs["validated_input"]["casino_url"]
        
        try:
            # Use tool orchestrator for comprehensive research
            research_results = await self.tools.comprehensive_casino_research(
                casino_name=casino_name,
                casino_url=casino_url
            )
            
            # Extract the research pack (DataForSEO results)
            research_pack = research_results.get("research_pack")
            if not research_pack:
                raise Exception("No research data returned from DataForSEO")
            
            logger.info(f"📊 Raw research data collected for {casino_name}")
            return {"dataforseo_results": research_pack}
            
        except Exception as e:
            logger.error(f"Data collection failed: {str(e)}")
            return {"dataforseo_results": None, "error": str(e)}
    
    async def _analyze_research_data(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze raw research data using LLM"""
        
        raw_data = inputs.get("raw_research_data", {})
        dataforseo_results = raw_data.get("dataforseo_results")
        
        if not dataforseo_results:
            logger.warning("No raw research data available for analysis")
            return {"analysis": {}, "insights": []}
        
        # Prepare analysis prompt
        analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a casino industry research analyst. Analyze the provided casino research data and extract key insights, competitive positioning, and strategic recommendations.
            
Focus on:
1. Market position and competitive landscape
2. SEO opportunities and keyword gaps
3. Authority signals and trust indicators
4. Brand sentiment and reputation analysis
5. Strategic recommendations

Provide structured, actionable insights."""),
            ("human", """Analyze this casino research data:

Casino: {casino_name}
Primary Keywords: {primary_keywords}
Competitors: {competitors}
Authority Score: {authority_score}
Brand Mentions: {brand_mentions}
Sentiment Score: {sentiment_score}

Provide key insights and strategic recommendations.""")
        ])
        
        try:
            # Extract key data points
            primary_keywords = getattr(dataforseo_results, 'primary_keywords', [])[:10]
            competitors = getattr(dataforseo_results, 'competitor_analysis', [])[:5]
            authority_score = getattr(dataforseo_results, 'domain_authority_score', 0)
            brand_mentions = len(getattr(dataforseo_results, 'brand_mentions', []))
            sentiment = getattr(dataforseo_results, 'sentiment_analysis', {})
            sentiment_score = sentiment.get('average_score', 0)
            
            # Run analysis
            analysis_chain = analysis_prompt | self.llm
            
            analysis_result = await analysis_chain.ainvoke({
                "casino_name": inputs["validated_input"]["casino_name"],
                "primary_keywords": ", ".join(primary_keywords),
                "competitors": ", ".join([c.get("domain", "") for c in competitors]),
                "authority_score": authority_score,
                "brand_mentions": brand_mentions,
                "sentiment_score": sentiment_score
            })
            
            logger.info("🔍 Research data analysis completed")
            
            return {
                "analysis": analysis_result.content,
                "insights": [
                    f"Authority Score: {authority_score}/100",
                    f"Brand Mentions: {brand_mentions}",
                    f"Sentiment Score: {sentiment_score:.2f}",
                    f"Primary Keywords: {len(primary_keywords)}",
                    f"Competitors Identified: {len(competitors)}"
                ]
            }
            
        except Exception as e:
            logger.error(f"Research data analysis failed: {str(e)}")
            return {"analysis": {}, "insights": [], "error": str(e)}
    
    async def _generate_seo_strategy(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Generate SEO strategy using DataForSEO results"""
        
        raw_data = inputs.get("raw_research_data", {})
        dataforseo_results = raw_data.get("dataforseo_results")
        
        if not dataforseo_results:
            logger.warning("No research data available for SEO strategy")
            return {"seo_plan": None}
        
        try:
            # Use DataForSEO client to generate SEO plan
            seo_plan = await self.tools.dataforseo.generate_seo_plan(dataforseo_results)
            
            logger.info("📈 SEO strategy generated")
            return {"seo_plan": seo_plan}
            
        except Exception as e:
            logger.error(f"SEO strategy generation failed: {str(e)}")
            return {"seo_plan": None, "error": str(e)}
    
    def _build_research_pack(self, inputs: Dict[str, Any]) -> CasinoResearchPack:
        """Build final CasinoResearchPack from all collected data"""
        
        validated_input = inputs["validated_input"]
        raw_data = inputs.get("raw_research_data", {})
        analysis = inputs.get("analysis_results", {})
        seo_data = inputs.get("seo_plan", {})
        
        # Get the original DataForSEO results
        dataforseo_results = raw_data.get("dataforseo_results")
        
        if dataforseo_results:
            # Use the comprehensive DataForSEO results as base
            research_pack = dataforseo_results
            
            # Enhance with analysis results
            if analysis.get("analysis"):
                research_pack.notes = f"{research_pack.notes}\n\nAnalysis: {analysis['analysis']}"
            
            # Add SEO plan if available
            seo_plan = seo_data.get("seo_plan")
            if seo_plan:
                research_pack.seo_recommendations = {
                    "target_keywords": seo_plan.target_keywords,
                    "content_strategy": seo_plan.title_suggestions,
                    "optimization_priority": seo_plan.optimization_priority
                }
            
        else:
            # Create minimal research pack if DataForSEO failed
            research_pack = CasinoResearchPack(
                casino_name=validated_input["casino_name"],
                casino_url=validated_input["casino_url"],
                research_date=datetime.now(),
                notes="Research completed with limited data due to API issues",
                research_accuracy=0.3  # Low accuracy due to missing data
            )
        
        # Add metadata
        research_pack.research_method = "dataforseo_comprehensive"
        research_pack.analysis_insights = analysis.get("insights", [])
        
        logger.info(f"📋 Research pack built for {research_pack.casino_name}")
        
        return research_pack


# LCEL Tool Wrapper for LangGraph integration
def create_research_agent_tool(tool_orchestrator: ToolOrchestrator) -> RunnableLambda:
    """
    Create a LangChain tool wrapper for the research agent
    
    Args:
        tool_orchestrator: Configured tool orchestrator
        
    Returns:
        RunnableLambda that can be used in LangGraph workflows
    """
    
    agent = CasinoResearchAgent(tool_orchestrator=tool_orchestrator)
    
    async def research_tool(inputs: Dict[str, Any]) -> CasinoResearchPack:
        """Tool function for LangGraph integration"""
        
        # Convert inputs to CasinoResearchRequest
        request = CasinoResearchRequest(
            casino_name=inputs["casino_name"],
            casino_url=inputs["casino_url"],
            target_keywords=inputs.get("target_keywords", []),
            competitor_analysis=inputs.get("competitor_analysis", True),
            research_depth=inputs.get("research_depth", "comprehensive"),
            tenant_id=inputs.get("tenant_id", "crashcasino")
        )
        
        return await agent.research_casino(request)
    
    return RunnableLambda(research_tool)


# Factory function
def create_casino_research_agent(tool_orchestrator: ToolOrchestrator, 
                                llm: Optional[ChatOpenAI] = None) -> CasinoResearchAgent:
    """
    Factory function to create casino research agent
    
    Args:
        tool_orchestrator: Configured tool orchestrator
        llm: Optional custom LLM (defaults to GPT-4)
        
    Returns:
        Configured CasinoResearchAgent
    """
    return CasinoResearchAgent(llm=llm, tool_orchestrator=tool_orchestrator)


# Testing and validation
async def test_research_agent():
    """Test the casino research agent"""
    import os
    from dotenv import load_dotenv
    from ..tools import create_tool_orchestrator
    
    load_dotenv()
    
    # Create tool orchestrator
    async with await create_tool_orchestrator() as tools:
        
        # Create research agent
        agent = create_casino_research_agent(tools)
        
        # Test research request
        request = CasinoResearchRequest(
            casino_name="Bitstarz",
            casino_url="https://bitstarz.com",
            target_keywords=["bitstarz review", "bitcoin casino"],
            competitor_analysis=True,
            research_depth="comprehensive"
        )
        
        # Execute research
        result = await agent.research_casino(request)
        
        print(f"\n🎯 Research Results for {result.casino_name}:")
        print(f"   Research Date: {result.research_date}")
        print(f"   Primary Keywords: {len(result.primary_keywords)}")
        print(f"   Competitors: {len(result.competitor_analysis)}")
        print(f"   Authority Score: {result.domain_authority_score}")
        print(f"   Research Accuracy: {result.research_accuracy:.1%}")
        print(f"   Data Sources: {result.data_sources}")
        
        if hasattr(result, 'seo_recommendations') and result.seo_recommendations:
            print(f"   SEO Keywords: {result.seo_recommendations.get('target_keywords', [])[:3]}")


if __name__ == "__main__":
    asyncio.run(test_research_agent())
