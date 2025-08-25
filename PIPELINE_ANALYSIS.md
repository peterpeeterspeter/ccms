# Universal RAG Pipeline: Native vs Custom Analysis

## 🟢 NATIVE LANGCHAIN COMPONENTS (Currently Used)

### Core LCEL Framework
- ✅ **RunnableParallel, RunnableBranch, RunnablePassthrough** - LCEL chain orchestration
- ✅ **RunnableLambda** - Function wrapping
- ✅ **with_fallbacks()** - Error handling
- ✅ **ChatPromptTemplate, PromptTemplate** - Prompt management
- ✅ **StrOutputParser, PydanticOutputParser** - Output parsing

### Vector & Storage
- ✅ **SupabaseVectorStore** - Native vector storage
- ✅ **OpenAIEmbeddings** - Text embeddings
- ✅ **Document** - Document handling

### LLM Integration  
- ✅ **ChatOpenAI, ChatAnthropic** - LLM providers
- ✅ **RedisSemanticCache** - Native caching
- ✅ **set_llm_cache()** - Global cache config

### Tools & Loaders
- ✅ **WebBaseLoader** - Web content loading  
- ✅ **TavilySearchResults** - Web search
- ✅ **BaseTool** - Tool framework (WordPress tool extends this)

## 🟡 CUSTOM COMPONENTS (Opportunity for Native Replacement)

### ❌ HEAVY CUSTOM SYSTEMS (Can be simplified/replaced):

#### 1. Advanced Prompt System (Lines 57-60)
**Current**: `OptimizedPromptManager, QueryAnalysis, QueryType, ExpertiseLevel`
**Replace with**: Native LangChain Hub + ChatPromptTemplate
```python
# CURRENT (Custom):
from .advanced_prompt_system import OptimizedPromptManager

# REPLACE WITH (Native):
from langchain.hub import pull
from langchain_core.prompts import ChatPromptTemplate
```

#### 2. Enhanced Confidence Scoring (Lines 62-66) 
**Current**: `EnhancedConfidenceCalculator, ConfidenceIntegrator, SourceQualityAnalyzer`
**Replace with**: Simple confidence calculation in LCEL chain
```python
# CURRENT (Custom):
self.confidence_calculator = EnhancedConfidenceCalculator()

# REPLACE WITH (Native):
def calculate_confidence(sources, content_length, query_analysis):
    return min(0.8 + len(sources) * 0.1, 1.0)
```

#### 3. Contextual Retrieval System (Lines 70-77)
**Current**: Custom `ContextualRetrievalSystem, HybridSearchEngine, MultiQueryRetriever`  
**Replace with**: Native LangChain retrievers
```python
# CURRENT (Custom):
from retrieval.contextual_retrieval import ContextualRetrievalSystem

# REPLACE WITH (Native):
from langchain.retrievers import MultiQueryRetriever, EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
```

#### 4. Template System v2.0 (Lines 82-88)
**Current**: `ImprovedTemplateManager` - 34 templates
**Replace with**: LangChain Hub + few key templates
```python
# CURRENT (Custom):
self.template_manager = ImprovedTemplateManager()

# REPLACE WITH (Native):
hub_template = hub.pull("casino-review-template")
```

### ⚠️ MODERATE CUSTOM SYSTEMS (Keep but simplify):

#### 5. DataForSEO Integration (Lines 92-103)
**Current**: Heavy custom `EnhancedDataForSEOImageSearch`
**Simplify to**: Lightweight tool with fallback
```python
# Current: Complex custom class
# Simplify: Simple function + fallback images
```

#### 6. WordPress Publishing (Lines 107-116) 
**Status**: ✅ Already native LangChain BaseTool - KEEP AS IS

## 🔴 UNNECESSARY CUSTOM COMPONENTS (Remove/Disable)

### Remove These Heavy Systems:
1. **FTI Content Processing** (Lines 139-151) - `ContentTypeDetector, AdaptiveChunkingStrategy`
2. **Security Manager** (Lines 154-158) - Over-engineered for current needs
3. **Performance Profiler** (Lines 161-164) - LangChain has built-in tracing
4. **MT Casino Integration** (Lines 119-136) - Redundant with WordPress tool

## 📊 REFACTORING OPPORTUNITIES

### Phase 1: Replace Heavy Custom with Native
```python
# REMOVE these custom imports:
from .advanced_prompt_system import OptimizedPromptManager
from .enhanced_confidence_scoring_system import EnhancedConfidenceCalculator  
from retrieval.contextual_retrieval import ContextualRetrievalSystem
from templates.improved_template_manager import ImprovedTemplateManager

# REPLACE with native LangChain:
from langchain.hub import pull
from langchain.retrievers import MultiQueryRetriever, EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
```

### Phase 2: Lightweight LCEL Chain
```python
# Current: Complex custom managers
# Target: Simple LCEL chain with native components

chain = (
    RunnableLambda(validate_input)
    | RunnablePassthrough.assign(
        context=MultiQueryRetriever(vectorstore=supabase_store),
        web_results=TavilySearchResults(),
        images=RunnableLambda(get_fallback_images)
    )
    | hub.pull("casino-review-template")
    | llm
    | RunnableBranch(
        (lambda x: x.get('publish'), wordpress_tool),
        RunnablePassthrough()
    )
)
```

## 🎯 RECOMMENDED ACTION PLAN

### Immediate Wins (Remove Heavy Custom):
1. **Disable** FTI processing, Security Manager, Performance Profiler 
2. **Replace** OptimizedPromptManager with LangChain Hub
3. **Replace** Enhanced Confidence with simple calculation
4. **Replace** Custom Contextual Retrieval with native retrievers

### Keep These Native Components:
- ✅ LCEL chain structure (RunnableParallel, etc.)
- ✅ SupabaseVectorStore 
- ✅ WebBaseLoader + TavilySearchResults
- ✅ WordPress BaseTool
- ✅ Native caching system

### Expected Benefits:
- **50% less custom code**
- **Faster startup time**
- **Better LangChain compatibility**  
- **Easier maintenance**
- **Native LangSmith tracing**

## 🚀 TARGET ARCHITECTURE: Lightweight Native Chain

```python
# Simple, native LangChain pipeline
chain = (
    RunnableLambda(validate_input)
    | RunnableParallel({
        "context": MultiQueryRetriever(vectorstore=supabase_store),
        "web_data": TavilySearchResults(max_results=5),
        "images": RunnableLambda(get_casino_images)
    })
    | ChatPromptTemplate.from_template(casino_review_template)
    | llm
    | RunnableBranch(
        (lambda x: x.get('publish'), wordpress_tool.as_runnable()),
        StrOutputParser()
    )
)
```

This removes ~70% of custom components while keeping all functionality!