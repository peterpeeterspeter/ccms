import asyncio
import sys
sys.path.append('src')
import os

os.environ['WORDPRESS_SITE_URL'] = 'https://crashcasino.io'
os.environ['WORDPRESS_USERNAME'] = 'nmlwh'
os.environ['WORDPRESS_APP_PASSWORD'] = 'ReUA 1ZNM lnDr pmgJ nAgz eR6g'

async def test_final():
    print('🌟 TESTING WORLD-CLASS PROMPTS')
    
    from chains.universal_rag_lcel import create_universal_rag_chain
    
    chain = create_universal_rag_chain(
        model_name='gpt-4o-mini',
        temperature=0.1,
        enable_contextual_retrieval=True,
        enable_comprehensive_web_research=True, 
        enable_web_search=True,
        enable_dataforseo_images=True,
        enable_wordpress_publishing=True,
        enable_response_storage=True,
        enable_enhanced_confidence=False,
        enable_prompt_optimization=False,
        enable_template_system_v2=False
    )
    
    query = {
        'query': 'Write comprehensive casino review about Crashino casino',
        'publish_to_wordpress': True
    }
    
    print('📝 Running with world-class narrative prompts...')
    
    result = await chain.ainvoke(query)
    
    if hasattr(result, 'answer'):
        content = result.answer
        print(f'Generated: {len(content)} chars, {len(content.split())} words')
        
        # Check structure
        lines = content.split('\n')
        bullets = sum(1 for line in lines if line.strip().startswith(('•', '-', '*', '1.', '2.')))
        paras = sum(1 for line in lines if len(line.strip()) > 50)
        
        print(f'Structure: {paras} paragraphs, {bullets} bullets')
        
        # Show preview  
        print('\nPreview:')
        print(content[:600])
        
        if bullets < paras:
            print('\n✅ NARRATIVE SUCCESS')
        else:
            print('\n❌ Still lists')
            
        # Publishing check
        pub = getattr(result, 'publishing_result', None)
        if pub and isinstance(pub, dict) and pub.get('success'):
            print(f'✅ Published: {pub.get("url")}')
    
    return result

result = asyncio.run(test_final())
