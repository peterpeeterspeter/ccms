#!/usr/bin/env python3
"""
🤖 Mock Agent Factories for Agentic System Testing
==================================================

Creates mock agents that can be used to test the agentic workflow
without needing all the complex tool integrations working perfectly.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

logger = logging.getLogger(__name__)

# Mock data for testing
MOCK_RESEARCH_DATA = {
    "casino_name": "Test Casino",
    "casino_url": "https://example.com",
    "license_type": "malta",  # Using valid enum value
    "license_jurisdiction": "Test Jurisdiction", 
    "license_number": "TL-12345",
    "license_valid": True,
    "establishment_year": 2020,
    "operator_name": "Test Operator Ltd",
    "brand_group": "Test Gaming Group",
    "regulatory_score": 8.5,
    "compliance_flags": [],
    "payment_methods": ["credit_card", "e_wallet", "crypto"],
    "currencies_supported": ["USD", "EUR", "BTC"],
    "countries_restricted": ["US", "UK"],
    "languages_supported": ["English", "Spanish", "French"],
    "software_providers": ["Test Provider 1", "Test Provider 2"],
    "game_categories": ["Slots", "Table Games", "Live Dealer"],
    "total_games": 1200,
    "slots_count": 800,
    "table_games_count": 150,
    "live_dealer_count": 100,
    "progressive_jackpots": 25,
    "welcome_bonus_amount": 500,
    "welcome_bonus_percentage": 100,
    "wagering_requirements": "35x",
    "max_withdrawal_limit": 5000,
    "withdrawal_timeframe": "24-72 hours",
    "customer_support_channels": ["Live Chat", "Email"],
    "support_availability": "24/7",
    "ssl_certificate": True,
    "encryption_level": "256-bit SSL",
    "responsible_gambling_tools": True,
    "third_party_audits": ["eCOGRA"],
    "security_score": 9.1,
    "user_experience_score": 7.8,
    "mobile_compatibility": True,
    "mobile_app_available": False,
    "website_speed_score": 85,
    "navigation_quality": "Good",
    "design_quality": "Modern",
    "trust_score": 8.2,
    "overall_rating": 7.9,
    "research_accuracy": 0.95,
    "data_freshness": "2024-01-15",
    "last_updated": datetime.now(),
    "research_sources": ["Official Website", "Licensing Authority", "Industry Reports"],
    "verification_status": "Verified",
    "research_notes": "Comprehensive analysis completed successfully"
}

MOCK_SCREENSHOT_DATA = [
    {
        "view_type": "desktop_homepage",
        "image_url": "https://storage.googleapis.com/firecrawl-scrape-media/mock-homepage.png",
        "media_id": 12345,
        "width": 1920,
        "height": 1080,
        "file_size": 256000,
        "format": "PNG",
        "compliance_pass": True,
        "licensing_compliant": True,
        "branding_compliant": True,
        "dimensions_compliant": True,
        "capture_timestamp": datetime.now(),
        "capture_method": "mock_firecrawl",
        "source_url": "https://example.com",
        "storage_path": "images/crashcasino/test-casino/homepage/2024-01-15.png"
    }
]

MOCK_REVIEW_CONTENT = {
    "title": "Test Casino Review 2024 - Comprehensive Analysis",
    "meta_description": "Comprehensive review of Test Casino. Licensed gaming with 1200+ games, secure payments, and 24/7 support. Read our detailed analysis.",
    "excerpt": "Our comprehensive analysis reveals Test Casino as a solid online gaming destination with strong regulatory compliance and diverse game selection.",
    "sections": [
        {
            "title": "Casino Overview",
            "content": "Test Casino operates under a valid gaming license and offers over 1200 games to players worldwide. Established in 2020, the casino has built a reputation for reliable gaming services.",
            "order": 1,
            "word_count": 28
        },
        {
            "title": "Licensing & Regulation",
            "content": "Licensed by Test Gaming Authority, the casino maintains high regulatory standards with a compliance score of 8.5/10. The license is valid and regularly audited.",
            "order": 2,
            "word_count": 24
        },
        {
            "title": "Games & Software",
            "content": "The casino features 800 slot games, 150 table games, and 100 live dealer options from top software providers including Test Provider 1 and Test Provider 2.",
            "order": 3,
            "word_count": 29
        },
        {
            "title": "Bonuses & Promotions",
            "content": "New players receive a 100% welcome bonus up to $500 with 35x wagering requirements. Additional promotions are available for existing players.",
            "order": 4,
            "word_count": 23
        },
        {
            "title": "Security & Safety",
            "content": "Security measures include 256-bit SSL encryption and regular third-party audits by eCOGRA, earning a security score of 9.1/10.",
            "order": 5,
            "word_count": 21
        }
    ],
    "pros": [
        "Valid gaming license with strong regulatory oversight",
        "Large game selection with 1200+ titles",
        "24/7 customer support via live chat and email", 
        "Strong security measures with SSL encryption",
        "Mobile-compatible platform"
    ],
    "cons": [
        "No dedicated mobile app available",
        "Some countries are restricted",
        "Wagering requirements could be lower"
    ],
    # Required rating fields for CasinoReviewDoc
    "overall_rating": 7.9,
    "game_variety_rating": 8.5,
    "bonus_rating": 7.0,
    "mobile_rating": 7.8,
    "payment_rating": 7.2,
    "support_rating": 8.0,
    "trust_rating": 8.2,
    
    # Required target audience fields
    "ideal_for": ["Slot enthusiasts", "Live casino players", "Bonus seekers", "Mobile players"],
    "not_recommended_for": ["High-stakes VIP players", "Players seeking instant withdrawals", "US residents"],
    
    # Required content metadata
    "word_count": 2850,
    "reading_time": 12,
    "content_template": "comprehensive_casino_review_v2",
    
    # Required SEO fields
    "focus_keywords": ["Test Casino review", "online casino review", "Test Casino bonus", "casino games"]
}

class MockResearchAgent:
    """Mock research agent for testing"""
    
    def __init__(self, tools=None):
        self.tools = tools
        self.name = "MockResearchAgent"
        
    async def research_casino(self, request):
        """Mock casino research"""
        logger.info(f"🔍 Mock research for {request.casino_name}")
        
        # Simulate research delay
        await asyncio.sleep(0.1)
        
        # Create mock research pack
        research_data = MOCK_RESEARCH_DATA.copy()
        research_data["casino_name"] = request.casino_name
        research_data["casino_url"] = request.casino_url
        
        # Import the schema to create proper object
        try:
            from schemas.casino_review import CasinoResearchPack
            return CasinoResearchPack(**research_data)
        except Exception as e:
            logger.error(f"Failed to create CasinoResearchPack: {e}")
            # Return raw dict if schema creation fails
            return research_data

class MockScreenshotAgent:
    """Mock screenshot agent for testing"""
    
    def __init__(self, tools=None):
        self.tools = tools
        self.name = "MockScreenshotAgent"
        
    async def capture_casino_screenshots(self, request):
        """Mock screenshot capture"""
        logger.info(f"📸 Mock screenshot capture for {request.casino_name}")
        
        # Simulate capture delay
        await asyncio.sleep(0.1)
        
        # Create mock screenshots
        screenshots_data = []
        for mock_data in MOCK_SCREENSHOT_DATA:
            mock_data_copy = mock_data.copy()
            mock_data_copy["source_url"] = request.casino_url
            screenshots_data.append(mock_data_copy)
        
        # Import the schema to create proper objects
        try:
            from schemas.casino_review import ScreenshotResult
            return [ScreenshotResult(**data) for data in screenshots_data]
        except Exception as e:
            logger.error(f"Failed to create ScreenshotResult: {e}")
            return screenshots_data

class MockContentAgent:
    """Mock content generation agent"""
    
    def __init__(self):
        self.name = "MockContentAgent"
        
    async def generate_review_content(self, research_pack, screenshots, target_keywords=None):
        """Mock content generation"""
        logger.info("✍️ Mock content generation")
        
        # Simulate generation delay
        await asyncio.sleep(0.2)
        
        # Update content with actual casino name if available
        content_data = MOCK_REVIEW_CONTENT.copy()
        if hasattr(research_pack, 'casino_name'):
            casino_name = research_pack.casino_name
            content_data["title"] = f"{casino_name} Review 2024 - Comprehensive Analysis"
            content_data["meta_description"] = f"Comprehensive review of {casino_name}. Licensed gaming with 1200+ games, secure payments, and 24/7 support."
        
        # Import the schema to create proper object
        try:
            from schemas.casino_review import CasinoReviewDoc
            return CasinoReviewDoc(**content_data)
        except Exception as e:
            logger.error(f"Failed to create CasinoReviewDoc: {e}")
            return content_data

class MockQAAgent:
    """Mock QA validation agent"""
    
    def __init__(self, strict_compliance=True):
        self.strict_compliance = strict_compliance
        self.name = "MockQAAgent"
        
    async def validate_review(self, review_doc, research_pack=None, screenshots=None):
        """Mock QA validation"""
        logger.info("🔍 Mock QA validation")
        
        # Simulate validation delay
        await asyncio.sleep(0.1)
        
        # Create mock QA report
        qa_data = {
            "overall_pass": True,
            "compliance_score": 0.95,
            "failure_summary": "",
            "recommendations": [],
            "factual_accuracy_pass": True,
            "completeness_score": 0.98,
            "compliance_pass": True,
            "content_quality_pass": True,
            "missing_fields": [],
            "factual_issues": [],
            "compliance_issues": [],
            "quality_issues": [],
            "word_count_adequate": True,
            "readability_score": 68.5,
            "keyword_density_ok": True,
            "featured_image_set": True,
            "all_images_compliant": True,
            "media_ids_valid": True,
            "recommendation": "PUBLISH",
            "priority_fixes": [],
            "qa_timestamp": datetime.now(),
            "qa_agent_version": "1.0"
        }
        
        # Import the schema to create proper object
        try:
            from schemas.casino_review import QAReport
            return QAReport(**qa_data)
        except Exception as e:
            logger.error(f"Failed to create QAReport: {e}")
            return qa_data

class MockPublishingAgent:
    """Mock publishing agent"""
    
    def __init__(self, tools=None):
        self.tools = tools
        self.name = "MockPublishingAgent"
        
    async def publish_review(self, review_doc, qa_report, screenshots=None):
        """Mock publishing"""
        logger.info("🚀 Mock publishing to WordPress")
        
        # Simulate publishing delay  
        await asyncio.sleep(0.1)
        
        # Create mock publish result
        publish_data = {
            "post_id": 12345,
            "post_url": "https://crashcasino.io/test-casino-review/",
            "post_status": "draft",
            "featured_media_id": 67890,
            "additional_media_ids": [67891, 67892],
            "media_ids": [67890, 67891, 67892],
            "custom_fields_populated": 25,
            "taxonomies_assigned": ["Casino Reviews", "Online Casinos"],
            "categories_assigned": ["Casino Reviews", "Online Casinos"],
            "tags_assigned": ["casino review", "online gambling", "slots"],
            "meta_title": review_doc.title if hasattr(review_doc, 'title') else "Test Casino Review",
            "meta_description": review_doc.meta_description if hasattr(review_doc, 'meta_description') else "Test casino review",
            "word_count": review_doc.word_count if hasattr(review_doc, 'word_count') else 2850,
            "processing_time_seconds": 0.5,
            "compliance_score": 0.95,
            "published_timestamp": datetime.now(),
            "tenant_id": "crashcasino",
            "success": True,
            "errors": [],
            "warnings": []
        }
        
        # Import the schema to create proper object
        try:
            from schemas.casino_review import PublishResult
            return PublishResult(**publish_data)
        except Exception as e:
            logger.error(f"Failed to create PublishResult: {e}")
            return publish_data

# Factory functions that match the expected API
def create_casino_research_agent(tools=None):
    """Create mock research agent"""
    return MockResearchAgent(tools)

def create_casino_screenshot_agent(tools=None):
    """Create mock screenshot agent"""
    return MockScreenshotAgent(tools)

def create_casino_content_agent():
    """Create mock content agent"""
    return MockContentAgent()

def create_casino_qa_agent(strict_compliance=True):
    """Create mock QA agent"""
    return MockQAAgent(strict_compliance)

def create_casino_publishing_agent(tools=None):
    """Create mock publishing agent"""
    return MockPublishingAgent(tools)

async def test_mock_agents():
    """Test all mock agents"""
    print("🤖 Testing Mock Agents")
    print("=" * 50)
    
    # Test research agent
    research_agent = create_casino_research_agent()
    
    # Create a simple request object
    class SimpleRequest:
        def __init__(self, casino_name, casino_url):
            self.casino_name = casino_name
            self.casino_url = casino_url
    
    request = SimpleRequest("Test Casino", "https://example.com")
    
    research_result = await research_agent.research_casino(request)
    print(f"✅ Research agent: {type(research_result)}")
    
    # Test screenshot agent
    screenshot_agent = create_casino_screenshot_agent()
    screenshot_results = await screenshot_agent.capture_casino_screenshots(request)
    print(f"✅ Screenshot agent: {len(screenshot_results)} screenshots")
    
    # Test content agent
    content_agent = create_casino_content_agent()
    content_result = await content_agent.generate_review_content(research_result, screenshot_results)
    print(f"✅ Content agent: {type(content_result)}")
    
    # Test QA agent
    qa_agent = create_casino_qa_agent()
    qa_result = await qa_agent.validate_review(content_result, research_result, screenshot_results)
    print(f"✅ QA agent: {type(qa_result)}")
    
    # Test publishing agent
    publishing_agent = create_casino_publishing_agent()
    publish_result = await publishing_agent.publish_review(content_result, qa_result, screenshot_results)
    print(f"✅ Publishing agent: {type(publish_result)}")
    
    print("🎉 All mock agents working correctly!")

if __name__ == "__main__":
    asyncio.run(test_mock_agents())
