#!/usr/bin/env python3
"""
Intelligent Screenshot Capture System - Tests
============================================

Unit tests for the intelligent screenshot capture system.
Tests tool selection logic, Firecrawl integration, and LCEL compatibility.

Run with: python -m pytest -xvs tests/tools/test_intelligent_screenshot_capture.py
"""

import pytest
import os
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime

from src.tools.intelligent_screenshot_capture import (
    CaptureMethod,
    ScreenshotRequest,
    ScreenshotResponse,
    CasinoSiteIntelligence,
    IntelligentScreenshotSelector,
    FirecrawlV2Capturer,
    select_screenshot_tool,
    image_compliance_guard,
    create_screenshot_chain
)

# Mock StealthLevel enum for tests without Playwright dependency
class MockStealthLevel:
    LEVEL_1_BASIC = "level_1_basic"
    LEVEL_2_ADVANCED = "level_2_advanced"
    LEVEL_3_FINGERPRINT = "level_3_fingerprint"
    LEVEL_4_PROFILE_ROTATION = "level_4_profile_rotation"

# Test ScreenshotRequest dataclass
def test_screenshot_request():
    request = ScreenshotRequest(
        url="https://example.com",
        filename="test.jpg",
        quality=90,
        stealth_required=True
    )
    
    assert request.url == "https://example.com"
    assert request.filename == "test.jpg"
    assert request.quality == 90
    assert request.stealth_required is True
    assert request.full_page is True  # Default value

# Test ScreenshotResponse dataclass
def test_screenshot_response():
    response = ScreenshotResponse(
        success=True,
        image_data=b"fake_image_data",
        metadata={"source": "test"},
        method_used="playwright"
    )
    
    assert response.success is True
    assert response.image_data == b"fake_image_data"
    assert response.metadata == {"source": "test"}
    assert response.method_used == "playwright"
    assert response.compliance_status == "PENDING"  # Default value

# Test CasinoSiteIntelligence domain classification
@patch('src.tools.intelligent_screenshot_capture.StealthLevel', MockStealthLevel)
def test_casino_site_intelligence():
    # Test initialization
    intel = CasinoSiteIntelligence()
    
    # Patch urlparse to return predictable results
    with patch('src.tools.intelligent_screenshot_capture.urlparse') as mock_urlparse:
        # Configure mock
        mock_netloc = MagicMock()
        mock_netloc.lower.return_value = "bet365.com"
        mock_urlparse.return_value.netloc = mock_netloc
        
        # Test high security site
        site_info = CasinoSiteIntelligence.analyze_site("https://bet365.com")
        assert site_info['is_high_security'] is True
        assert site_info['likely_blocks_crawlers'] is True
        assert site_info['stealth_level'] == MockStealthLevel.LEVEL_4_PROFILE_ROTATION
        
        # Test crypto casino
        mock_netloc.lower.return_value = "stake.com"
        site_info = CasinoSiteIntelligence.analyze_site("https://stake.com")
        assert site_info['is_crypto_casino'] is True
        assert site_info['stealth_level'] == MockStealthLevel.LEVEL_2_ADVANCED
        
        # Test regular site
        mock_netloc.lower.return_value = "example.com"
        site_info = CasinoSiteIntelligence.analyze_site("https://example.com")
        assert site_info['is_high_security'] is False
        assert site_info['is_crypto_casino'] is False
        assert site_info['stealth_level'] == MockStealthLevel.LEVEL_1_BASIC

# Test IntelligentScreenshotSelector logic
@patch('src.tools.intelligent_screenshot_capture.StealthLevel', MockStealthLevel)
@patch('src.tools.intelligent_screenshot_capture.PLAYWRIGHT_AVAILABLE', True)
def test_intelligent_screenshot_selector():
    selector = IntelligentScreenshotSelector()
    
    # Patch site intelligence
    with patch.object(selector.site_intelligence, 'analyze_site') as mock_analyze:
        # High security site
        mock_analyze.return_value = {
            'domain': 'bet365.com',
            'is_high_security': True,
            'is_crypto_casino': False,
            'requires_js': True,
            'stealth_level': MockStealthLevel.LEVEL_4_PROFILE_ROTATION,
            'likely_blocks_crawlers': True
        }
        
        request = ScreenshotRequest(url="https://bet365.com")
        method = selector.select_method(request)
        assert method == CaptureMethod.PLAYWRIGHT_STEALTH_MAX
        
        # Crypto casino
        mock_analyze.return_value = {
            'domain': 'stake.com',
            'is_high_security': False,
            'is_crypto_casino': True,
            'requires_js': True,
            'stealth_level': MockStealthLevel.LEVEL_2_ADVANCED,
            'likely_blocks_crawlers': False
        }
        
        request = ScreenshotRequest(url="https://stake.com")
        method = selector.select_method(request)
        assert method == CaptureMethod.PLAYWRIGHT_STEALTH_MED
        
        # JS-heavy site
        mock_analyze.return_value = {
            'domain': 'example.com',
            'is_high_security': False,
            'is_crypto_casino': False,
            'requires_js': True,
            'stealth_level': MockStealthLevel.LEVEL_1_BASIC,
            'likely_blocks_crawlers': False
        }
        
        request = ScreenshotRequest(url="https://example.com")
        method = selector.select_method(request)
        assert method == CaptureMethod.PLAYWRIGHT_BASIC
        
        # Simple site (Firecrawl)
        mock_analyze.return_value = {
            'domain': 'example.com',
            'is_high_security': False,
            'is_crypto_casino': False,
            'requires_js': False,
            'stealth_level': MockStealthLevel.LEVEL_1_BASIC,
            'likely_blocks_crawlers': False
        }
        
        request = ScreenshotRequest(url="https://example.com", full_page=True)
        method = selector.select_method(request)
        assert method == CaptureMethod.FIRECRAWL_V2

# Test FirecrawlV2Capturer
@pytest.mark.asyncio
async def test_firecrawl_v2_capturer():
    # Test with no API key
    with patch('os.getenv', return_value=None):
        capturer = FirecrawlV2Capturer()
        request = ScreenshotRequest(url="https://example.com")
        response = await capturer.capture(request)
        
        assert response.success is False
        assert "API key not configured" in response.error_message
    
    # Test successful response
    with patch('os.getenv', return_value="fake_api_key"), \
         patch('requests.post') as mock_post:
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'success': True,
            'data': {
                'screenshot': 'https://firecrawl-cdn.example/img123.jpg',
                'metadata': {'width': 1200, 'height': 800}
            }
        }
        mock_post.return_value = mock_response
        
        capturer = FirecrawlV2Capturer()
        request = ScreenshotRequest(url="https://example.com")
        response = await capturer.capture(request)
        
        assert response.success is True
        assert response.image_url == 'https://firecrawl-cdn.example/img123.jpg'
        assert response.method_used == "firecrawl_v2"
        assert 'firecrawl_metadata' in response.metadata
        
        # Verify correct API call
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert kwargs['json']['url'] == "https://example.com"
        assert kwargs['json']['formats'] == ["screenshot"]
    
    # Test API error
    with patch('os.getenv', return_value="fake_api_key"), \
         patch('requests.post') as mock_post:
        
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_post.return_value = mock_response
        
        capturer = FirecrawlV2Capturer()
        request = ScreenshotRequest(url="https://example.com")
        response = await capturer.capture(request)
        
        assert response.success is False
        assert "Firecrawl API error: 400" in response.error_message

# Test LCEL screenshot tool selection
@patch('src.tools.intelligent_screenshot_capture.StealthLevel', MockStealthLevel)
@patch('src.tools.intelligent_screenshot_capture.PLAYWRIGHT_AVAILABLE', True)
def test_select_screenshot_tool():
    with patch('src.tools.intelligent_screenshot_capture.IntelligentScreenshotSelector') as MockSelector:
        mock_instance = MagicMock()
        mock_instance.select_method.return_value = CaptureMethod.PLAYWRIGHT_STEALTH_MAX
        MockSelector.return_value = mock_instance
        
        result = select_screenshot_tool({'url': 'https://bet365.com'})
        assert result == "playwright_stealth_level_4"
        
        # Test with capture options
        result = select_screenshot_tool({
            'url': 'https://example.com',
            'capture_options': {
                'quality': 90,
                'full_page': False
            }
        })
        assert result == "playwright_stealth_level_4"  # Based on our mock

# Test image compliance guard
def test_image_compliance_guard():
    # Test failed capture
    data = {
        'success': False,
        'error_message': 'Connection error'
    }
    
    result = image_compliance_guard(data)
    assert result['compliance_status'] == 'FAIL'
    assert 'Capture failed' in result['compliance_issues']
    
    # Test image too small
    data = {
        'success': True,
        'image_data': b'x' * 500,  # 500 bytes, too small
        'metadata': {
            'source_url': 'https://example.com',
            'capture_method': 'test',
            'capture_timestamp': datetime.now().isoformat()
        }
    }
    
    result = image_compliance_guard(data)
    assert result['compliance_status'] == 'FAIL'
    assert 'Image too small' in result['compliance_issues']
    
    # Test missing metadata
    data = {
        'success': True,
        'image_data': b'x' * 10000,  # 10KB, adequate size
        'metadata': {
            'source_url': 'https://example.com'
            # Missing capture_method and capture_timestamp
        }
    }
    
    result = image_compliance_guard(data)
    assert result['compliance_status'] == 'FAIL'
    assert any('Missing metadata field' in issue for issue in result['compliance_issues'])
    
    # Test compliant image
    data = {
        'success': True,
        'image_data': b'x' * 10000,  # 10KB, adequate size
        'metadata': {
            'source_url': 'https://example.com',
            'capture_method': 'test',
            'capture_timestamp': datetime.now().isoformat()
        }
    }
    
    result = image_compliance_guard(data)
    assert result['compliance_status'] == 'PASS'
    assert 'compliance_issues' not in result

# Test LCEL screenshot chain creation
def test_create_screenshot_chain():
    """Test that the LCEL screenshot chain can be created successfully"""
    chain = create_screenshot_chain()
    assert chain is not None
    
    # Test chain structure (should be a RunnableSequence)
    from langchain_core.runnables import RunnableSequence
    
    # The chain should be a RunnableSequence (due to | operator)
    assert isinstance(chain, RunnableSequence)
    
    # Verify the chain has the expected structure
    steps = chain.steps
    assert len(steps) >= 3  # At least 3 steps in the pipeline
    
    # Verify chain is invokable (has the right interface)
    assert hasattr(chain, 'invoke')
    assert hasattr(chain, 'ainvoke')
    
    # Test that the chain can be represented as string (indicates proper construction)
    chain_str = str(chain)
    assert 'RunnablePassthrough' in chain_str
    assert 'RunnableLambda' in chain_str
