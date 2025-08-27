#!/usr/bin/env python3
"""
Quick test to verify the content generation fix
"""
import sys
sys.path.append('src')

from dotenv import load_dotenv
load_dotenv()

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# Mock research data similar to what the pipeline provides
mock_research = {
    "casino_name": "Betway Casino",
    "license": "Malta Gaming Authority (MGA/B2C/102/2000)",
    "games": "4000+ games including slots, table games, live dealer",
    "welcome_bonus": "100% up to €1,000 + 200 free spins",
    "payments": "Visa, MasterCard, PayPal, Skrill, Neteller, bank transfer",
    "customer_support": "24/7 live chat, email support",
    "security": "256-bit SSL encryption, licensed operation"
}

casino_name = "Betway Casino"

# Use the FIXED direct LCEL narrative approach
content_prompt = ChatPromptTemplate.from_template("""
Write a comprehensive, professional 2,500+ word casino review for {casino_name}.

Research Data:
{research_data}

Write flowing narrative paragraphs (NO bullet points, NO raw field data) covering:

1. **Introduction**: Casino overview, launch details, parent company, licensing
2. **Licensing**: Regulatory framework, compliance, player protection  
3. **Games**: Complete game portfolio analysis with specific numbers
4. **Bonuses**: Welcome bonus structure, promotions, wagering requirements
5. **Payments**: Banking methods, processing times, limits, fees
6. **Support**: Customer service channels, response times, quality
7. **Mobile**: Mobile platform, functionality, user experience
8. **Security**: Encryption, fair play certification, responsible gambling
9. **Verdict**: Final assessment, pros/cons, player recommendations

IMPORTANT REQUIREMENTS:
- Write in professional narrative style, not bullet points
- Use specific facts and numbers from research data
- Maintain consistent entity naming throughout
- NO template artifacts or raw field references
- NO placeholder text or demo content
- Professional tone suitable for publication

Casino: {casino_name}
""")

# Direct LCEL chain for narrative generation (following successful Viage pattern)
narrative_chain = (
    RunnablePassthrough.assign(
        casino_name=lambda x: casino_name,
        research_data=lambda x: "\n".join([f"{k}: {v}" for k, v in mock_research.items()])
    )
    | content_prompt
    | ChatOpenAI(model="gpt-4o-mini", temperature=0.7, max_tokens=4000)  # Using mini for speed
    | StrOutputParser()
)

print("🧪 Testing fixed content generation approach...")
print("=" * 60)

# Generate content using the fixed approach
result = narrative_chain.invoke({"casino_name": casino_name})

print(f"📝 Generated Content Length: {len(result.split())} words")
print("\n🎯 Content Preview (first 500 characters):")
print("-" * 50)
print(result[:500] + "...")
print("-" * 50)

# Check for success indicators
success_indicators = [
    ("No raw field data", "'field':" not in result and "'value':" not in result),
    ("Uses casino name consistently", "Betway Casino" in result),
    ("Professional narrative", result.count(".") > 50),  # Many sentences
    ("No template artifacts", "{{" not in result and "}}" not in result),
    ("Substantial content", len(result.split()) > 1000)
]

print("\n✅ QUALITY CHECKS:")
for check, passed in success_indicators:
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"   {status}: {check}")

all_passed = all(passed for _, passed in success_indicators)
print(f"\n🏆 OVERALL: {'SUCCESS - Fixed content generation!' if all_passed else 'Issues remaining'}")

if all_passed:
    print("\n🎯 This confirms the fix works - direct LCEL narrative generation eliminates the data format issues!")
    print("The pipeline should now produce quality content similar to the successful Viage review.")