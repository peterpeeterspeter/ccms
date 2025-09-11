# Intelligent Screenshot Capture System

## Overview

The Intelligent Screenshot Capture System is a comprehensive solution for capturing high-quality screenshots from various websites, with specialized intelligence for casino and gaming sites. It automatically selects the most appropriate capture method based on site characteristics, anti-bot protection levels, and technical requirements.

## Features

- **Smart Tool Selection**: Automatically chooses between Playwright (with stealth), Firecrawl, Selenium, or WebBase based on site analysis
- **Casino Site Intelligence**: Built-in knowledge of casino sites' security levels and bot protection
- **Stealth Capabilities**: Multiple levels of anti-detection features for high-security sites
- **LCEL Integration**: Native LangChain Expression Language (LCEL) compatibility
- **Compliance Validation**: Automatic image compliance checking with metadata requirements
- **Supabase Integration**: Storage path configuration for captured screenshots

## Architecture

```
ScreenshotRequest → IntelligentSelector → CaptureMethod → Implementation → ComplianceGuard → Storage
                     ↓
               CasinoIntelligence
```

### Core Components

1. **IntelligentScreenshotSelector**: Analyzes target URLs and selects optimal capture method
2. **CasinoSiteIntelligence**: Domain-specific knowledge for casino sites
3. **Multiple Capturers**: Playwright, Firecrawl, Selenium implementations
4. **Compliance Guard**: Validates captured images meet publishing standards
5. **LCEL Chain**: Complete processing pipeline

## Usage

### Basic Usage

```python
from src.tools.intelligent_screenshot_capture import (
    IntelligentScreenshotCapturer,
    ScreenshotRequest
)

# Initialize capturer
capturer = IntelligentScreenshotCapturer()

# Create request
request = ScreenshotRequest(
    url="https://stake.com/",
    filename="stake_homepage.jpg",
    alt_text="Stake Casino Homepage",
    quality=90
)

# Capture screenshot
response = await capturer.capture(request)

if response.success:
    print(f"Screenshot captured using: {response.method_used}")
    # Image data available in response.image_data or response.image_url
else:
    print(f"Capture failed: {response.error_message}")

# Clean up resources
await capturer.cleanup()
```

### LCEL Chain Usage

```python
from src.tools.intelligent_screenshot_capture import create_screenshot_chain

# Create the complete processing chain
screenshot_chain = create_screenshot_chain()

# Use in LCEL pipeline
input_data = {
    'url': 'https://example.com',
    'capture_options': {
        'quality': 95,
        'full_page': True
    }
}

result = await screenshot_chain.ainvoke(input_data)
```

## Capture Methods

### 1. Playwright with Stealth
**Best for**: High-security casino sites (bet365, pokerstars, etc.)

- **Level 4**: Profile rotation, advanced fingerprinting
- **Level 3**: Advanced stealth with fingerprint masking
- **Level 2**: Moderate stealth for crypto casinos
- **Level 1**: Basic stealth for standard sites

### 2. Firecrawl v2 API
**Best for**: Simple screenshots, full-page captures

- Cloud-based screenshot service
- Fast and reliable for non-protected sites
- Returns hosted image URLs

### 3. Selenium WebDriver
**Best for**: Fallback when Playwright unavailable

- Chrome with stealth configuration
- Good compatibility across systems
- Moderate anti-detection capabilities

### 4. WebBase Loader
**Best for**: Text content extraction (not screenshots)

- LangChain document loader
- Used primarily for content scraping

## Site Intelligence

The system includes built-in intelligence about different site types:

### High-Security Domains
- `bet365.com`, `pokerstars.com`, `unibet.com`
- Requires maximum stealth (Playwright Level 4)
- Aggressive bot detection and blocking

### Crypto Casino Domains  
- `stake.com`, `roobet.com`, `bitcasino.io`
- Moderate stealth requirements (Playwright Level 2)
- Generally more permissive to crawlers

### JavaScript-Heavy Domains
- `evolution.com`, `pragmaticplay.com`, `netent.com`
- Requires browser automation for proper rendering
- Dynamic content loading

## Configuration

### Environment Variables

```bash
# Firecrawl API configuration
FIRECRAWL_API_KEY=fc-your-api-key-here

# Optional: Custom user agent
USER_AGENT="Mozilla/5.0 (compatible; CasinoReviewBot/1.0)"
```

### Request Options

```python
ScreenshotRequest(
    url="https://example.com",
    filename="optional_filename.jpg",
    alt_text="Screenshot description",
    caption="Image caption",
    target_elements=["#logo", ".main-content"],  # CSS selectors
    quality=85,                                   # 1-100
    format='jpeg',                               # jpeg, png
    timeout_ms=30000,                           # 30 seconds
    full_page=True,                             # Full page vs viewport
    stealth_required=None                       # Auto-detected if None
)
```

## Compliance Validation

The system automatically validates captured screenshots:

### Pass Criteria
- ✅ Capture successful
- ✅ Image size between 1KB and 10MB
- ✅ Complete metadata (source_url, capture_method, timestamp)
- ✅ Proper format and dimensions

### Fail Criteria
- ❌ Capture failed or timed out
- ❌ Image too small (<1KB) or too large (>10MB)
- ❌ Missing required metadata fields
- ❌ Invalid image format

## Error Handling

The system includes comprehensive error handling:

```python
# Response always includes success status
if not response.success:
    print(f"Error: {response.error_message}")
    print(f"Method attempted: {response.method_used}")
    
# Compliance issues
if response.compliance_status == 'FAIL':
    print("Compliance issues:", response.metadata.get('compliance_issues'))
```

## Testing

Run the test suite:

```bash
# Run all tests
python -m pytest tests/tools/test_intelligent_screenshot_capture.py -v

# Run specific test
python -m pytest tests/tools/test_intelligent_screenshot_capture.py::test_firecrawl_v2_capturer -v

# Run with coverage
python -m pytest tests/tools/test_intelligent_screenshot_capture.py --cov=src.tools.intelligent_screenshot_capture
```

## Troubleshooting

### Common Issues

1. **Firecrawl API Timeouts**
   ```
   Solution: Check API key, verify network connectivity, increase timeout
   ```

2. **Playwright Import Errors**
   ```
   Solution: System falls back to Selenium automatically
   ```

3. **Selenium WebDriver Issues**
   ```
   Solution: Ensure Chrome/ChromeDriver installed and in PATH
   ```

4. **High-Security Site Blocking**
   ```
   Solution: System escalates stealth levels automatically, may need retry
   ```

## Performance Considerations

- **Playwright**: Higher resource usage but best success rate
- **Firecrawl**: Fastest for simple sites, API rate limits apply
- **Selenium**: Moderate resource usage, good compatibility
- **WebBase**: Not for screenshots, text content only

## Integration with CMS

The system integrates with the Universal RAG CMS pipeline:

```python
# In your agent/chain
screenshot_chain = create_screenshot_chain()

# Combine with content extraction
content_and_screenshot = (
    extract_content_chain
    | screenshot_chain
    | compliance_validation
    | supabase_storage
)
```

## Future Enhancements

- [ ] Additional stealth methods (proxy rotation, browser profiles)
- [ ] Enhanced compliance checking (OCR, content analysis)
- [ ] Batch processing capabilities
- [ ] Custom element targeting improvements
- [ ] Performance metrics and monitoring

## License and Compliance

This system is designed for legitimate business use in casino review publishing. Always ensure compliance with:

- Target site terms of service
- Applicable data protection regulations (GDPR, CCPA)
- Image licensing and attribution requirements
- Respect for robots.txt and rate limits

---

For technical support or feature requests, refer to the project documentation or contact the development team.
