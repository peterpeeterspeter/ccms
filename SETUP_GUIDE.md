# 🚀 CCMS Production Setup Guide

## Quick Start

1. **Install Dependencies**
   ```bash
   pip install -e .
   # OR with UV (recommended)
   uv pip install -e .
   ```

2. **Configure Environment**
   ```bash
   cp .env.ccms.example .env.ccms
   # Edit .env.ccms with your actual values
   # Then source or merge into your main .env file
   ```

3. **Setup Database**
   ```bash
   # Run the Supabase migration
   psql -h your-supabase-host -U postgres -d postgres -f migrations/001_ccms_core.sql
   ```

4. **Test Installation**
   ```bash
   ccms health
   ccms run --tenant=crashcasino --casino=viage --dry-run
   ```

## Detailed Setup

### 1. Environment Configuration

The CCMS system requires several API keys and configuration values:

#### Required Configuration
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_SERVICE_ROLE`: Service role key with full access
- `WORDPRESS_BASE_URL`: WordPress site URL (with wp-json API enabled)
- `WORDPRESS_APP_PW`: WordPress application password
- `OPENAI_API_KEY`: OpenAI API key for content generation

#### Optional Integrations
- `LANGCHAIN_API_KEY`: For LangSmith tracing and observability
- `FIRECRAWL_API_KEY`: For website screenshots and scraping
- `BROWSERLESS_TOKEN`: For browser automation screenshots
- `DATAFORSEO_LOGIN/PASSWORD`: For SERP and image discovery (research only)

### 2. Database Setup

Run the Supabase migration to create all required tables:

```sql
-- Connect to your Supabase database and run:
\i migrations/001_ccms_core.sql
```

This creates 15+ tables including:
- Multi-tenant configuration system
- Research data and topic clusters
- Compliance rules and authority links
- WordPress publishing metadata

### 3. WordPress Configuration

Ensure your WordPress site has:
- **REST API enabled** (wp-json endpoints accessible)
- **RankMath SEO plugin** installed and active
- **Advanced Custom Fields (ACF) plugin** installed 
- **Application passwords** enabled for authentication

Create ACF field groups with keys matching the publisher schema:
- `field_casino_facts`
- `field_bonus_terms` 
- `field_payment_methods`
- `field_game_stats`

### 4. CLI Usage

#### Basic Production Run
```bash
ccms run --tenant=crashcasino --casino=viage --locale=en-GB
```

#### Development & Testing
```bash
# Preview mode (no WordPress publishing)
ccms run --tenant=crashcasino --casino=napoleon-games --dry-run

# Skip compliance gates (for development)
ccms run --tenant=crashcasino --casino=betsson --skip-compliance

# Verbose logging
ccms run --tenant=crashcasino --casino=viage -v

# System health check
ccms health
```

#### Advanced Options
```bash
# Display tenant configuration
ccms config --tenant=crashcasino

# Validate casino readiness
ccms validate --casino=viage --tenant=crashcasino
```

## Pipeline Architecture

### 8-Step LCEL Pipeline
```
1. CONFIG    → Resolve tenant configuration from Supabase
2. RESEARCH  → Load casino intelligence & SERP data  
3. CONTENT   → Generate structured review blocks
4. PARALLEL  → SEO metadata | Media assets
5. MERGE     → Combine parallel results
6. COMPLY    → Validate compliance (BLOCKING)
7. PUBLISH   → WordPress with RankMath/ACF
8. METRICS   → Record quality scores & observability
```

### Compliance Gates

The system includes blocking compliance validation:
- License disclosure requirements
- Bonus terms completeness
- Content structure validation
- Responsible gambling compliance

Use `--skip-compliance` only for development/testing.

## Troubleshooting

### Common Issues

**1. Import Errors**
```bash
# Ensure all dependencies are installed
pip install -r requirements.txt
# Or use setup.py
pip install -e .
```

**2. Supabase Connection**
```bash
# Test connection
python -c "from src.tools.supabase_config_tool import supabase_config_tool; print('OK')"
```

**3. WordPress Publishing**
```bash
# Test WordPress connection
ccms run --tenant=crashcasino --casino=test --dry-run
```

**4. Environment Variables**
```bash
# Check required variables
ccms health
```

### Testing

Run the comprehensive test suite:
```bash
python -m pytest test_ccms_pipeline.py -v
```

All 7 tests should pass, validating:
- Schema validation
- Dry-run execution  
- Compliance blocking
- LCEL composition

## Production Deployment

### Security Considerations
- Use service role keys securely (environment variables only)
- Enable WordPress application passwords, disable basic auth
- Configure CORS properly for Supabase if accessing from browser
- Use HTTPS for all API endpoints

### Monitoring
- Enable LangSmith tracing with `LANGCHAIN_TRACING_V2=true`
- Monitor compliance failure rates
- Track pipeline execution times
- Set up alerts for publishing failures

### Scaling
- Configure database connection pooling for high throughput
- Use caching for configuration resolution
- Implement rate limiting for external APIs
- Consider async execution for bulk operations

## Next Steps

1. **Configure your first tenant** in the Supabase `tenants` table
2. **Add casino research data** to `research_articles` table
3. **Set up compliance rules** for your target jurisdictions
4. **Test end-to-end** with a dry run
5. **Deploy to production** with monitoring enabled

The system is now ready for production casino review generation with full compliance validation and multi-tenant configuration management!