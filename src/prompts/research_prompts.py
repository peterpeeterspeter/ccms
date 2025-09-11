"""
Casino Research Prompts
========================

Prompt templates for the casino research agent.
Following WARP.md prompt hygiene - prompts loaded by path, not inline.
"""

CASINO_RESEARCH_SYSTEM_PROMPT = """You are a professional casino industry research analyst with expertise in:

- Online gambling market analysis
- Casino licensing and regulatory compliance
- Gaming software and provider ecosystems  
- Payment processing and banking in gambling
- SEO and digital marketing for casinos
- Player behavior and market segmentation

Your role is to analyze casino data comprehensively and provide structured, factual insights that help create accurate and valuable casino reviews. Focus on factual accuracy, market positioning, and actionable intelligence.

Always maintain objectivity and base conclusions on verifiable data points."""

CASINO_ANALYSIS_PROMPT = """Analyze the following casino research data and provide comprehensive insights:

**Casino**: {casino_name}
**URL**: {casino_url}
**Research Data**: {research_data}

Please provide a structured analysis covering:

1. **Market Position**: How this casino compares to competitors in terms of offerings, licensing, and reputation
2. **Strengths & Differentiators**: What makes this casino unique or compelling to players
3. **Potential Issues**: Any concerns regarding licensing, payment processing, game fairness, or player complaints
4. **Target Audience**: What types of players would be most attracted to this casino
5. **SEO Opportunities**: Keywords and content gaps that could be leveraged for review optimization

Format your response as structured insights that can be used to create an accurate, balanced casino review."""

SEO_PLANNING_PROMPT = """Based on the casino research data, create an SEO strategy for a comprehensive casino review:

**Casino**: {casino_name}
**Primary Keywords**: {primary_keywords}
**Competitor Analysis**: {competitor_data}
**Search Volume Data**: {search_volumes}

Generate an SEO plan including:

1. **Primary Keywords** (3-5 main target keywords)
2. **Secondary Keywords** (8-12 supporting keywords)
3. **Meta Title** (optimized for search and click-through)
4. **Meta Description** (compelling and keyword-optimized, under 160 chars)
5. **Content Strategy** (key topics and sections to include)
6. **Internal Linking** (opportunities to link to related content)
7. **Competitor Gaps** (content opportunities our review should address)

Focus on search intent matching and competitive differentiation."""

CASINO_VALIDATION_PROMPT = """Review the following casino research findings for accuracy and completeness:

**Research Pack**: {research_pack}

Validate and flag any potential issues with:

1. **Factual Accuracy**: Are the stated facts verifiable and current?
2. **Licensing Claims**: Can the licensing information be verified?
3. **Game Counts**: Are the game library numbers realistic?
4. **Payment Methods**: Are the listed payment options accurate?
5. **Bonus Terms**: Are bonus descriptions accurate and not misleading?
6. **Completeness**: What critical information is missing?

Provide a validation report with confidence scores and recommendations for additional research needed."""
