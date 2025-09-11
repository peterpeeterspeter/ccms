# 🚀 LangGraph Research Agent - Usage Guide

## Overview

The new LangGraph Research Agent represents a major upgrade to your CCMS research capabilities, bringing:

- **Persistent state management** with checkpointing
- **Real-time streaming updates** for progress monitoring  
- **Multi-phase workflow** with error recovery
- **Human-in-the-loop** quality control
- **Full backward compatibility** with existing CCMS pipeline

## Quick Start

### 1. Basic Usage (Drop-in Replacement)

```python
from src.integrations.langgraph_research_integration import create_backward_compatible_agent

# Replace your existing research agent with this enhanced version
research_agent = create_backward_compatible_agent()

# Use exactly the same API as before
result = await research_agent.research_casino(
    casino_name="Betway Casino",
    casino_url="https://betway.com"
)

print(result)  # Same string format as original agent
```

### 2. Enhanced Usage (Full Features)

```python
from src.integrations.langgraph_research_integration import create_enhanced_research_agent

# Create enhanced agent with all LangGraph features
research_agent = create_enhanced_research_agent(
    model_name="gpt-4o",
    enable_streaming=True,
    enable_human_checkpoints=True
)

# Use enhanced API with structured data
result = await research_agent.research_casino_enhanced(
    casino_name="Betway Casino",
    casino_url="https://betway.com",
    locale="en-US",
    tenant_id="crashcasino"
)

print(f"Research ID: {result['research_id']}")
print(f"Quality Score: {result['quality_metrics']['data_quality_score']:.2f}")
print(f"WordPress Ready: {result['wordpress_ready']}")
print(f"Visual Assets: {len(result['visual_assets']['screenshots'])} screenshots")
```

### 3. Real-time Streaming

```python
# Stream research progress in real-time
async for update in research_agent.stream_research_progress("Betway Casino"):
    print(f"{update['phase']}: {update['progress']:.1%} - {update['message']}")
    
    if update['phase'] == 'completed':
        final_result = update['final_result']
        break
```

## Architecture

### Research Workflow Phases

1. **Initialized** - Session setup and validation
2. **Basic Info Gathering** - Supabase lookup, web search, website loading
3. **Detailed Research** - Targeted searches for specific casino aspects
4. **Visual Capture** - Screenshot capture with Firecrawl, fallback generation
5. **Intelligence Extraction** - 95+ field structured data extraction
6. **Quality Review** - Automated quality scoring and issue detection
7. **Human Checkpoint** - Optional human review and approval
8. **Completed** - Final result packaging for CCMS pipeline

### State Management

The `ResearchState` maintains 30+ fields including:

```python
{
    "research_id": "unique-session-id",
    "casino_name": "Target Casino",
    "current_phase": ResearchPhase.BASIC_INFO_GATHERING,
    "progress_percentage": 0.4,
    "quality_metrics": {
        "data_quality_score": 0.85,
        "source_reliability_score": 0.9,
        "completeness_score": 0.8,
        "extraction_confidence": 0.7
    },
    "visual_assets": {
        "screenshots": ["url1.png", "url2.png"],
        "fallback_images": ["placeholder1.png"]
    },
    "casino_intelligence": CasinoIntelligence(...),
    "wordpress_ready": True
}
```

## Integration Patterns

### 1. Drop-in Replacement

```python
# OLD: Original research agent
from src.agents.research_agent import CasinoResearchAgent
old_agent = CasinoResearchAgent()
result = await old_agent.research_casino("Casino Name")

# NEW: Enhanced LangGraph agent (same API)
from src.integrations.langgraph_research_integration import create_backward_compatible_agent
new_agent = create_backward_compatible_agent()
result = await new_agent.research_casino("Casino Name")  # Same result format
```

### 2. CCMS Pipeline Integration

```python
# Get CCMS-ready data structure
research_id = "session-123"
pipeline_data = research_agent.get_ccms_pipeline_data(research_id)

# Use with existing CCMS components
from src.tools.comprehensive_content_generator import generate_comprehensive_content
content = generate_comprehensive_content(
    pipeline_data["casino_intelligence"],
    pipeline_data["visual_assets"]
)
```

### 3. Session Management

```python
# Track research sessions
research_id = await research_agent.research_casino_enhanced("Casino Name")

# Check status later
status = research_agent.get_research_status(research_id)
print(f"Phase: {status['current_phase']}")
print(f"Progress: {status['progress_percentage']:.1%}")

# Cleanup old sessions
research_agent.cleanup_old_sessions(max_age_hours=24)
```

## Configuration Options

### Model Configuration

```python
research_agent = create_enhanced_research_agent(
    model_name="gpt-4o",  # or "gpt-4o-mini" for faster/cheaper
    temperature=0.1,      # Lower for more consistent results
    max_retries=3         # Retry attempts for failed operations
)
```

### Feature Toggles

```python
research_agent = create_enhanced_research_agent(
    enable_streaming=True,           # Real-time progress updates
    enable_human_checkpoints=True,   # Pause for human review
    enable_caching=True             # Cache results for efficiency
)
```

### Multi-tenant Support

```python
result = await research_agent.research_casino_enhanced(
    casino_name="Betway Casino",
    locale="de-DE",           # German locale
    tenant_id="germansite"    # German site configuration
)
```

## Error Handling

The LangGraph agent provides robust error handling:

```python
result = await research_agent.research_casino_enhanced("Problematic Casino")

# Check for errors
if not result['success']:
    print(f"Research failed: {result.get('error', 'Unknown error')}")

# Review error details
errors = result.get('errors', [])
for error in errors:
    print(f"Phase {error['phase']}: {error['type']} - {error['message']}")

# Check quality issues
quality_issues = result['quality_metrics'].get('quality_issues', [])
for issue in quality_issues:
    if issue['severity'] == 'high':
        print(f"High priority issue: {issue['description']}")
```

## Performance Considerations

### Concurrent Research

```python
# Run multiple research sessions in parallel
import asyncio

casinos = ["Casino A", "Casino B", "Casino C"]
tasks = [
    research_agent.research_casino_enhanced(casino) 
    for casino in casinos
]

results = await asyncio.gather(*tasks, return_exceptions=True)
```

### Memory Management

```python
# Prevent memory leaks in long-running applications
research_agent.cleanup_old_sessions(max_age_hours=12)

# Monitor active sessions
active_count = len(research_agent.active_research_sessions)
print(f"Active research sessions: {active_count}")
```

## Testing

Run the comprehensive test suite:

```bash
# Run all tests
python -m pytest tests/test_langgraph_research_agent.py -v

# Run specific test categories
python -m pytest tests/test_langgraph_research_agent.py::TestLangGraphResearchAgent -v
python -m pytest tests/test_langgraph_research_agent.py::TestCCMSLangGraphIntegration -v

# Run performance tests
python -m pytest tests/test_langgraph_research_agent.py::TestPerformance -v
```

## Migration Guide

### From Original Research Agent

1. **Phase 1**: Test compatibility
   ```python
   # Test with backward compatible agent
   agent = create_backward_compatible_agent()
   result = await agent.research_casino("Test Casino")
   # Verify result format matches expectations
   ```

2. **Phase 2**: Gradual enhancement
   ```python
   # Gradually adopt enhanced features
   agent = create_enhanced_research_agent(enable_streaming=False)
   result = await agent.research_casino_enhanced("Test Casino")
   # Access structured data while maintaining compatibility
   ```

3. **Phase 3**: Full LangGraph adoption
   ```python
   # Use full LangGraph capabilities
   agent = create_enhanced_research_agent(
       enable_streaming=True,
       enable_human_checkpoints=True
   )
   # Implement streaming UI and human review workflows
   ```

## Troubleshooting

### Common Issues

1. **Missing API Keys**
   ```bash
   export OPENAI_API_KEY="your-openai-key"
   export TAVILY_API_KEY="your-tavily-key"
   export FIRECRAWL_API_KEY="your-firecrawl-key"
   ```

2. **Import Errors**
   ```python
   # Ensure CCMS is in Python path
   import sys
   sys.path.append('/path/to/ccms')
   ```

3. **Memory Issues**
   ```python
   # Regular cleanup in long-running applications
   research_agent.cleanup_old_sessions(max_age_hours=6)
   ```

## Best Practices

1. **Use appropriate model** - `gpt-4o-mini` for development, `gpt-4o` for production
2. **Enable streaming** for long-running research to provide user feedback
3. **Implement error handling** to gracefully handle API failures
4. **Regular cleanup** of research sessions to prevent memory leaks
5. **Monitor quality scores** to ensure research meets standards
6. **Use human checkpoints** for critical casino research

## Next Steps

1. **Content Generation Integration** - Connect with enhanced content generator
2. **WordPress Publishing** - Automatic publishing of research results
3. **Dashboard Integration** - Real-time progress monitoring UI
4. **Quality Analytics** - Track research quality metrics over time

---

## 🏆 Summary

The LangGraph Research Agent represents a major architectural upgrade:

- **8-phase workflow** with persistent state management
- **Real-time streaming** for progress monitoring
- **Quality control** with automated scoring and human checkpoints
- **Full backward compatibility** with existing CCMS pipeline
- **Production ready** with comprehensive error handling and testing

This upgrade maintains your existing API contracts while adding powerful new capabilities for durable, persistent, and high-quality casino research.
