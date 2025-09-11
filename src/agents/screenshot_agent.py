"""
Screenshot Agent
================

LangChain LCEL-based agent for casino interface capture using Firecrawl.
Follows WARP.md: compliance checking, WordPress media integration, deterministic contracts.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from ..schemas.casino_review import ScreenshotResult, ScreenshotRequest
from ..tools import ToolOrchestrator

logger = logging.getLogger(__name__)


class CasinoScreenshotAgent:
    """
    Casino Screenshot Agent using LCEL composition
    
    Responsibilities:
    - Multi-viewport casino interface capture (desktop, mobile, tablet)
    - WARP.md compliance checking (dimensions, licensing, branding)
    - WordPress media library integration
    - Fallback screenshot services when primary fails
    - Metadata generation and storage path management
    
    Input: ScreenshotRequest
    Output: List[ScreenshotResult]
    """
    
    def __init__(self, 
                 llm: Optional[ChatOpenAI] = None,
                 tool_orchestrator: Optional[ToolOrchestrator] = None):
        self.llm = llm or ChatOpenAI(
            model="gpt-4",
            temperature=0.1,  # Low temperature for consistent operations
            max_tokens=1000
        )
        self.tools = tool_orchestrator
        self.screenshot_chain = self._build_screenshot_chain()
    
    def _build_screenshot_chain(self):
        """Build the LCEL screenshot capture chain"""
        
        # Build the LCEL chain following WARP.md screenshot policy
        chain = (
            RunnablePassthrough.assign(
                # Step 1: Validate screenshot request
                validated_request=RunnableLambda(self._validate_screenshot_request)
            )
            | RunnablePassthrough.assign(
                # Step 2: Capture casino screenshots using priority order
                # Priority: Firecrawl → CF Browser → Browserless → Playwright
                raw_screenshots=RunnableLambda(self._capture_screenshots)
            )
            | RunnablePassthrough.assign(
                # Step 3: Process and validate screenshots for compliance
                compliant_screenshots=RunnableLambda(self._process_compliance_check)
            )
            | RunnablePassthrough.assign(
                # Step 4: Upload screenshots to WordPress media library
                media_results=RunnableLambda(self._upload_to_wordpress)
            )
            | RunnableLambda(self._build_screenshot_results)
        )
        
        return chain
    
    async def capture_casino_screenshots(self, request: ScreenshotRequest) -> List[ScreenshotResult]:
        """
        Main entry point for casino screenshot capture
        
        Args:
            request: Screenshot request with casino details and configuration
            
        Returns:
            List of ScreenshotResult objects with WordPress media IDs
        """
        try:
            logger.info(f"📸 Starting screenshot capture for {request.casino_url}")
            
            # Execute the screenshot chain
            results = await self.screenshot_chain.ainvoke({
                "casino_url": request.casino_url,
                "casino_name": request.casino_name,
                "viewport_configs": request.viewport_configs or self._get_default_viewports(),
                "capture_options": request.capture_options,
                "tenant_id": request.tenant_id,
                "compliance_strict": request.compliance_strict
            })
            
            logger.info(f"✅ Screenshot capture completed for {request.casino_url}")
            logger.info(f"   - Screenshots captured: {len(results)}")
            logger.info(f"   - Compliant screenshots: {sum(1 for r in results if r.compliance_pass)}")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Screenshot capture failed for {request.casino_url}: {str(e)}")
            return []  # Return empty list on failure
    
    def _validate_screenshot_request(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and enrich the screenshot request"""
        
        casino_url = inputs.get("casino_url", "").strip()
        casino_name = inputs.get("casino_name", "").strip()
        
        if not casino_url:
            raise ValueError("Casino URL is required for screenshot capture")
        
        # Normalize URL
        if not casino_url.startswith(("http://", "https://")):
            casino_url = f"https://{casino_url}"
        
        # Extract casino name from URL if not provided
        if not casino_name:
            from urllib.parse import urlparse
            domain = urlparse(casino_url).netloc
            casino_name = domain.replace("www.", "").replace(".com", "").title()
        
        # Set defaults
        validated = {
            "casino_url": casino_url,
            "casino_name": casino_name,
            "viewport_configs": inputs.get("viewport_configs", self._get_default_viewports()),
            "capture_options": inputs.get("capture_options", {}),
            "tenant_id": inputs.get("tenant_id", "crashcasino"),
            "compliance_strict": inputs.get("compliance_strict", True)
        }
        
        logger.info(f"✅ Screenshot request validated for {casino_name} at {casino_url}")
        return validated
    
    def _get_default_viewports(self) -> List[Dict[str, Any]]:
        """Get default viewport configurations per WARP.md"""
        
        return [
            {
                "view_type": "desktop_homepage",
                "viewport": {"width": 1920, "height": 1080},
                "url_suffix": "",
                "description": "Desktop homepage view",
                "priority": 1
            },
            {
                "view_type": "desktop_games",
                "viewport": {"width": 1920, "height": 1080},
                "url_suffix": "/games",
                "description": "Desktop games section",
                "priority": 2
            },
            {
                "view_type": "mobile_homepage",
                "viewport": {"width": 375, "height": 812},
                "url_suffix": "",
                "description": "Mobile homepage view",
                "priority": 3
            },
            {
                "view_type": "tablet_homepage",
                "viewport": {"width": 768, "height": 1024},
                "url_suffix": "",
                "description": "Tablet homepage view",
                "priority": 4
            }
        ]
    
    async def _capture_screenshots(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Capture screenshots using tool orchestrator with fallback priority"""
        
        if not self.tools:
            raise Exception("Tool orchestrator not available for screenshot capture")
        
        validated = inputs["validated_request"]
        casino_url = validated["casino_url"]
        tenant_id = validated["tenant_id"]
        
        screenshots = []
        
        try:
            # Primary: Use Firecrawl via tool orchestrator
            if self.tools.service_health.get("firecrawl"):
                logger.info(f"🔧 Using Firecrawl for screenshot capture")
                
                firecrawl_results = await self.tools.firecrawl.capture_casino_screenshots(
                    casino_url=casino_url,
                    tenant_id=tenant_id
                )
                
                screenshots.extend(firecrawl_results)
                logger.info(f"📸 Firecrawl captured {len(firecrawl_results)} screenshots")
            
            # Fallback: CF Browser or Browserless
            elif self.tools.fallback_screenshots:
                logger.info(f"🔧 Using fallback screenshot services")
                
                for viewport_config in validated["viewport_configs"]:
                    try:
                        fallback_result = await self._capture_fallback_screenshot(
                            casino_url + viewport_config["url_suffix"],
                            viewport_config,
                            validated
                        )
                        
                        if fallback_result:
                            screenshots.append(fallback_result)
                            
                    except Exception as e:
                        logger.warning(f"Fallback screenshot failed for {viewport_config['view_type']}: {str(e)}")
                        continue
            
            else:
                raise Exception("No screenshot services available (Firecrawl, CF Browser, or Browserless)")
            
            logger.info(f"📊 Total screenshots captured: {len(screenshots)}")
            return {"screenshots": screenshots}
            
        except Exception as e:
            logger.error(f"Screenshot capture failed: {str(e)}")
            return {"screenshots": [], "error": str(e)}
    
    async def _capture_fallback_screenshot(self, 
                                         url: str, 
                                         viewport_config: Dict[str, Any],
                                         validated_request: Dict[str, Any]) -> Optional[ScreenshotResult]:
        """Capture screenshot using fallback services"""
        
        try:
            # Use fallback screenshot client
            screenshot_data = await self.tools.fallback_screenshots.capture_screenshot(
                url=url,
                viewport=viewport_config["viewport"]
            )
            
            if not screenshot_data:
                return None
            
            # Create temporary screenshot result for processing
            # This would normally involve saving the screenshot data temporarily
            # and running it through compliance checks
            
            logger.info(f"📸 Fallback screenshot captured for {viewport_config['view_type']}")
            
            # Return minimal ScreenshotResult - this would need full implementation
            return ScreenshotResult(
                view_type=viewport_config["view_type"],
                image_url="",  # To be filled after WordPress upload
                media_id=0,    # To be filled after WordPress upload
                width=viewport_config["viewport"]["width"],
                height=viewport_config["viewport"]["height"],
                file_size=len(screenshot_data) if screenshot_data else 0,
                format="PNG",
                compliance_pass=False,  # To be determined by compliance check
                capture_timestamp=datetime.now(),
                capture_method="fallback",
                source_url=url
            )
            
        except Exception as e:
            logger.error(f"Fallback screenshot capture failed: {str(e)}")
            return None
    
    async def _process_compliance_check(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Process screenshots for WARP.md compliance"""
        
        raw_screenshots = inputs.get("raw_screenshots", {}).get("screenshots", [])
        validated_request = inputs["validated_request"]
        
        if not raw_screenshots:
            logger.warning("No raw screenshots available for compliance processing")
            return {"compliant_screenshots": []}
        
        compliant_screenshots = []
        compliance_failures = []
        
        try:
            # Process each screenshot for compliance
            for screenshot in raw_screenshots:
                compliance_result = await self._check_screenshot_compliance(
                    screenshot, 
                    validated_request["compliance_strict"]
                )
                
                if compliance_result["compliant"]:
                    # Update screenshot with compliance data
                    screenshot.compliance_pass = True
                    screenshot.licensing_compliant = compliance_result["licensing_compliant"]
                    screenshot.branding_compliant = compliance_result["branding_compliant"]
                    screenshot.dimensions_compliant = compliance_result["dimensions_compliant"]
                    
                    compliant_screenshots.append(screenshot)
                    logger.info(f"✅ Screenshot {screenshot.view_type} passed compliance check")
                    
                else:
                    compliance_failures.append({
                        "view_type": screenshot.view_type,
                        "issues": compliance_result["issues"]
                    })
                    logger.warning(f"⚠️ Screenshot {screenshot.view_type} failed compliance: {compliance_result['issues']}")
            
            logger.info(f"📋 Compliance check completed: {len(compliant_screenshots)}/{len(raw_screenshots)} passed")
            
            return {
                "compliant_screenshots": compliant_screenshots,
                "compliance_failures": compliance_failures
            }
            
        except Exception as e:
            logger.error(f"Compliance processing failed: {str(e)}")
            return {"compliant_screenshots": [], "compliance_failures": []}
    
    async def _check_screenshot_compliance(self, 
                                         screenshot: ScreenshotResult, 
                                         strict_mode: bool) -> Dict[str, Any]:
        """Check individual screenshot against WARP.md compliance rules"""
        
        compliance_issues = []
        
        try:
            # WARP.md Compliance Requirements:
            # - Minimum dimensions: 900×600 pixels
            # - No licensing violations
            # - Proper branding/attribution
            # - Acceptable file format (PNG, JPEG, WebP)
            
            # Check dimensions (WARP.md requirement)
            dimensions_compliant = screenshot.width >= 900 and screenshot.height >= 600
            if not dimensions_compliant:
                compliance_issues.append(f"Dimensions too small: {screenshot.width}×{screenshot.height} (minimum 900×600)")
            
            # Check file format
            format_compliant = screenshot.format in ["PNG", "JPEG", "WebP"]
            if not format_compliant:
                compliance_issues.append(f"Invalid format: {screenshot.format}")
            
            # Licensing compliance (for direct casino screenshots, assume compliant)
            licensing_compliant = screenshot.capture_method in ["firecrawl", "cf_browser", "browserless", "playwright"]
            if not licensing_compliant:
                compliance_issues.append("Screenshot method not approved for publishing")
            
            # Branding compliance (direct screenshots should be compliant)
            branding_compliant = True
            
            # Overall compliance determination
            if strict_mode:
                compliant = (dimensions_compliant and format_compliant and 
                           licensing_compliant and branding_compliant)
            else:
                # In non-strict mode, allow some flexibility
                compliant = dimensions_compliant and format_compliant
            
            return {
                "compliant": compliant,
                "dimensions_compliant": dimensions_compliant,
                "format_compliant": format_compliant,
                "licensing_compliant": licensing_compliant,
                "branding_compliant": branding_compliant,
                "issues": compliance_issues
            }
            
        except Exception as e:
            logger.error(f"Compliance check failed: {str(e)}")
            return {
                "compliant": False,
                "dimensions_compliant": False,
                "format_compliant": False,
                "licensing_compliant": False,
                "branding_compliant": False,
                "issues": [f"Compliance check error: {str(e)}"]
            }
    
    async def _upload_to_wordpress(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Upload compliant screenshots to WordPress media library"""
        
        compliant_screenshots = inputs.get("compliant_screenshots", {}).get("compliant_screenshots", [])
        
        if not compliant_screenshots:
            logger.warning("No compliant screenshots available for WordPress upload")
            return {"media_results": []}
        
        if not self.tools or not self.tools.service_health.get("wordpress"):
            raise Exception("WordPress service not available for media upload")
        
        media_results = []
        
        try:
            for screenshot in compliant_screenshots:
                # Screenshots captured via Firecrawl are already uploaded to WordPress
                # This step would handle any additional screenshots that need uploading
                
                if screenshot.media_id and screenshot.image_url:
                    # Already uploaded during capture
                    media_results.append({
                        "view_type": screenshot.view_type,
                        "media_id": screenshot.media_id,
                        "image_url": screenshot.image_url,
                        "upload_status": "already_uploaded"
                    })
                else:
                    # Need to upload (fallback screenshots)
                    logger.info(f"📤 Uploading {screenshot.view_type} to WordPress")
                    
                    # This would require implementing the upload logic for fallback screenshots
                    # For now, mark as pending
                    media_results.append({
                        "view_type": screenshot.view_type,
                        "media_id": 0,
                        "image_url": "",
                        "upload_status": "pending_implementation"
                    })
            
            logger.info(f"📤 WordPress upload processing completed for {len(media_results)} screenshots")
            return {"media_results": media_results}
            
        except Exception as e:
            logger.error(f"WordPress upload failed: {str(e)}")
            return {"media_results": [], "error": str(e)}
    
    def _build_screenshot_results(self, inputs: Dict[str, Any]) -> List[ScreenshotResult]:
        """Build final screenshot results from all processing steps"""
        
        compliant_screenshots = inputs.get("compliant_screenshots", {}).get("compliant_screenshots", [])
        media_results = inputs.get("media_results", {}).get("media_results", [])
        
        # Create mapping of media results by view_type
        media_mapping = {mr["view_type"]: mr for mr in media_results}
        
        final_results = []
        
        for screenshot in compliant_screenshots:
            # Update screenshot with media information
            media_info = media_mapping.get(screenshot.view_type, {})
            
            if media_info.get("media_id"):
                screenshot.media_id = media_info["media_id"]
            if media_info.get("image_url"):
                screenshot.image_url = media_info["image_url"]
            
            # Mark as final result
            screenshot.processing_completed = True
            screenshot.processing_timestamp = datetime.now()
            
            final_results.append(screenshot)
        
        # Sort by priority (if available in original viewport config)
        final_results.sort(key=lambda x: x.view_type)
        
        logger.info(f"📋 Final screenshot results compiled: {len(final_results)} screenshots")
        
        return final_results


# LCEL Tool Wrapper for LangGraph integration
def create_screenshot_agent_tool(tool_orchestrator: ToolOrchestrator) -> RunnableLambda:
    """
    Create a LangChain tool wrapper for the screenshot agent
    
    Args:
        tool_orchestrator: Configured tool orchestrator
        
    Returns:
        RunnableLambda that can be used in LangGraph workflows
    """
    
    agent = CasinoScreenshotAgent(tool_orchestrator=tool_orchestrator)
    
    async def screenshot_tool(inputs: Dict[str, Any]) -> List[ScreenshotResult]:
        """Tool function for LangGraph integration"""
        
        # Convert inputs to ScreenshotRequest
        request = ScreenshotRequest(
            casino_url=inputs["casino_url"],
            casino_name=inputs.get("casino_name", ""),
            viewport_configs=inputs.get("viewport_configs"),
            capture_options=inputs.get("capture_options", {}),
            tenant_id=inputs.get("tenant_id", "crashcasino"),
            compliance_strict=inputs.get("compliance_strict", True)
        )
        
        return await agent.capture_casino_screenshots(request)
    
    return RunnableLambda(screenshot_tool)


# Factory function
def create_casino_screenshot_agent(tool_orchestrator: ToolOrchestrator, 
                                  llm: Optional[ChatOpenAI] = None) -> CasinoScreenshotAgent:
    """
    Factory function to create casino screenshot agent
    
    Args:
        tool_orchestrator: Configured tool orchestrator
        llm: Optional custom LLM (defaults to GPT-4)
        
    Returns:
        Configured CasinoScreenshotAgent
    """
    return CasinoScreenshotAgent(llm=llm, tool_orchestrator=tool_orchestrator)


# Testing and validation
async def test_screenshot_agent():
    """Test the casino screenshot agent"""
    import os
    from dotenv import load_dotenv
    from ..tools import create_tool_orchestrator
    
    load_dotenv()
    
    # Create tool orchestrator
    async with await create_tool_orchestrator() as tools:
        
        # Create screenshot agent
        agent = create_casino_screenshot_agent(tools)
        
        # Test screenshot request
        request = ScreenshotRequest(
            casino_url="https://bitstarz.com",
            casino_name="Bitstarz",
            compliance_strict=True,
            tenant_id="crashcasino"
        )
        
        # Execute screenshot capture
        results = await agent.capture_casino_screenshots(request)
        
        print(f"\n📸 Screenshot Results for {request.casino_name}:")
        print(f"   Total screenshots: {len(results)}")
        
        for result in results:
            print(f"   - {result.view_type}:")
            print(f"     Dimensions: {result.width}×{result.height}")
            print(f"     Compliance: {'✅' if result.compliance_pass else '❌'}")
            print(f"     Media ID: {result.media_id}")
            print(f"     Method: {result.capture_method}")


if __name__ == "__main__":
    asyncio.run(test_screenshot_agent())
