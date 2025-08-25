"""
🎯 Narrative Generation LCEL Chain
Task-012: World-class narrative-style content generation with retrieval integration

Features:
- LCEL chain with {context}, {visuals}, {affiliate_meta} retrieval
- Multi-locale prompt template loading from /src/prompts/review_narrative_{locale}.txt
- Integration with Multi-Tenant Retrieval System (Stream 1D)
- Visual content and affiliate metadata integration
- ReviewDoc output generation with QA validation hooks
"""

from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import logging
from datetime import datetime

from pydantic import BaseModel, Field
from langchain_core.runnables import (
    RunnablePassthrough, 
    RunnableLambda, 
    RunnableParallel,
    RunnableBranch
)
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import StrOutputParser, PydanticOutputParser
from langchain_openai import ChatOpenAI
from langchain_core.documents import Document

# Import our components
from src.chains.multi_tenant_retrieval_system import (
    MultiTenantRetrievalSystem,
    MultiTenantQuery,
    RetrievalResult
)
from src.schemas.review_doc import ReviewDoc, TenantConfiguration, MediaAsset
from src.schemas.casino_intelligence_schema import CasinoIntelligence


logger = logging.getLogger(__name__)


class NarrativeGenerationInput(BaseModel):
    """Input schema for narrative generation chain"""
    casino_name: str = Field(description="Name of the casino to review")
    tenant_config: TenantConfiguration = Field(description="Tenant configuration")
    query_context: str = Field(description="Additional query context")
    visual_assets: List[MediaAsset] = Field(default_factory=list, description="Available visual assets")
    affiliate_metadata: Optional[Dict[str, Any]] = Field(default=None, description="Affiliate-specific metadata")
    content_requirements: Dict[str, Any] = Field(default_factory=dict, description="Content generation requirements")


class NarrativeGenerationOutput(BaseModel):
    """Output schema for narrative generation chain"""
    generated_content: str = Field(description="Generated narrative content")
    review_doc: ReviewDoc = Field(description="Complete structured review document")
    retrieval_context: List[Document] = Field(description="Retrieved context documents")
    generation_metadata: Dict[str, Any] = Field(description="Generation process metadata")


class NarrativePromptLoader:
    """Loads and manages narrative prompt templates by locale"""
    
    PROMPT_DIR = Path("src/prompts")
    TEMPLATE_PATTERN = "review_narrative_{locale}.txt"
    
    def __init__(self):
        self._cache: Dict[str, str] = {}
        
    def load_prompt_template(self, locale: str = "en") -> str:
        """Load prompt template for specific locale"""
        if locale in self._cache:
            return self._cache[locale]
            
        template_path = self.PROMPT_DIR / self.TEMPLATE_PATTERN.format(locale=locale)
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read().strip()
                self._cache[locale] = template_content
                return template_content
                
        except FileNotFoundError:
            logger.warning(f"Prompt template not found for locale {locale}, falling back to 'en'")
            if locale != "en":
                return self.load_prompt_template("en")
            raise ValueError(f"No prompt template found for locale {locale}")
    
    def get_available_locales(self) -> List[str]:
        """Get list of available locale templates"""
        locales = []
        for template_file in self.PROMPT_DIR.glob("review_narrative_*.txt"):
            locale = template_file.stem.split('_')[-1]
            locales.append(locale)
        return sorted(locales)


class VisualContentProcessor:
    """Processes and formats visual content for narrative generation"""
    
    @staticmethod
    def format_visual_context(visual_assets: List[MediaAsset]) -> str:
        """Format visual assets into context string"""
        if not visual_assets:
            return "No visual content available."
            
        visual_descriptions = []
        for asset in visual_assets:
            description = f"• {asset.type.value.title()}: {asset.filename}"
            if asset.alt_text:
                description += f" ({asset.alt_text})"
            if asset.caption:
                description += f" - {asset.caption}"
            visual_descriptions.append(description)
            
        return "\\n".join(visual_descriptions)
    
    @staticmethod
    def extract_visual_metadata(visual_assets: List[MediaAsset]) -> Dict[str, Any]:
        """Extract metadata from visual assets for context"""
        return {
            "total_images": len(visual_assets),
            "image_types": list(set(asset.type.value for asset in visual_assets)),
            "has_screenshots": any(asset.type.name == "SCREENSHOT" for asset in visual_assets),
            "has_promotional": any(asset.type.name == "PROMOTIONAL" for asset in visual_assets),
            "visual_context": VisualContentProcessor.format_visual_context(visual_assets)
        }


class AffiliateMetadataProcessor:
    """Processes affiliate-specific metadata for narrative generation"""
    
    @staticmethod
    def format_affiliate_context(affiliate_metadata: Optional[Dict[str, Any]]) -> str:
        """Format affiliate metadata into context string"""
        if not affiliate_metadata:
            return "No affiliate-specific metadata available."
            
        context_parts = []
        
        # Commission structure
        if "commission_structure" in affiliate_metadata:
            commission = affiliate_metadata["commission_structure"]
            context_parts.append(f"Commission: {commission}")
            
        # Marketing materials
        if "marketing_materials" in affiliate_metadata:
            materials = affiliate_metadata["marketing_materials"]
            context_parts.append(f"Marketing materials: {', '.join(materials)}")
            
        # Compliance requirements
        if "compliance_requirements" in affiliate_metadata:
            compliance = affiliate_metadata["compliance_requirements"]
            context_parts.append(f"Compliance: {', '.join(compliance)}")
            
        return "; ".join(context_parts) if context_parts else "Standard affiliate terms apply."


class NarrativeGenerationChain:
    """
    LCEL chain for generating world-class narrative content with retrieval integration
    """
    
    def __init__(
        self,
        retrieval_system: MultiTenantRetrievalSystem,
        llm: Optional[ChatOpenAI] = None,
        prompt_loader: Optional[NarrativePromptLoader] = None
    ):
        self.retrieval_system = retrieval_system
        self.llm = llm or ChatOpenAI(
            model="gpt-4o",
            temperature=0.7,
            max_tokens=4096
        )
        self.prompt_loader = prompt_loader or NarrativePromptLoader()
        
        # Build the LCEL chain
        self.chain = self._build_chain()
        
    def _build_chain(self):
        """Build the complete LCEL narrative generation chain"""
        
        # Step 1: Prepare multi-tenant retrieval query
        def prepare_retrieval_query(input_data: NarrativeGenerationInput) -> MultiTenantQuery:
            """Convert input to retrieval query"""
            return MultiTenantQuery(
                query=f"{input_data.casino_name} casino review {input_data.query_context}",
                tenant_id=input_data.tenant_config.tenant_id,
                brand=input_data.tenant_config.brand_name,
                locale=input_data.tenant_config.locale,
                voice=input_data.tenant_config.voice_profile,
                limit=20  # Get comprehensive context
            )
        
        # Step 2: Retrieve contextual information
        def perform_retrieval(query: MultiTenantQuery) -> RetrievalResult:
            """Execute multi-tenant retrieval"""
            return self.retrieval_system.retrieve_with_context(query)
        
        # Step 3: Process visual and affiliate metadata
        def process_metadata(input_data: NarrativeGenerationInput) -> Dict[str, Any]:
            """Process visual and affiliate metadata"""
            visual_meta = VisualContentProcessor.extract_visual_metadata(input_data.visual_assets)
            affiliate_context = AffiliateMetadataProcessor.format_affiliate_context(input_data.affiliate_metadata)
            
            return {
                "visual_metadata": visual_meta,
                "affiliate_context": affiliate_context,
                "images": visual_meta["visual_context"]
            }
        
        # Step 4: Create generation prompt
        def create_generation_prompt(data: Dict[str, Any]) -> ChatPromptTemplate:
            """Create prompt with retrieved context"""
            input_data = data["input"]
            retrieval_result = data["retrieval_result"]
            metadata = data["metadata"]
            
            # Load locale-specific prompt template
            template_text = self.prompt_loader.load_prompt_template(input_data.tenant_config.locale)
            
            # Format context from retrieved documents
            context_text = "\\n\\n".join([
                f"Source {i+1}: {doc.page_content}" 
                for i, doc in enumerate(retrieval_result.documents)
            ])
            
            # Create the prompt template
            prompt_template = template_text + """

CONTEXT INFORMATION:
{context}

CASINO NAME: {casino_name}
LOCALE: {locale}
BRAND: {brand}
VOICE PROFILE: {voice_profile}

VISUAL ASSETS: {images}
AFFILIATE CONTEXT: {affiliate_context}

REQUIREMENTS:
- Generate comprehensive, narrative-style content
- Use retrieved context factually and cite sources
- Maintain brand voice and locale-appropriate language
- Include visual references naturally
- Ensure compliance with affiliate requirements
- Output publication-ready HTML format

Generate the casino review now:"""

            return ChatPromptTemplate.from_template(prompt_template)
        
        # Step 5: Generate content
        def generate_content(data: Dict[str, Any]) -> str:
            """Generate the narrative content"""
            input_data = data["input"]
            retrieval_result = data["retrieval_result"]
            metadata = data["metadata"]
            
            prompt = create_generation_prompt(data)
            
            # Format context
            context_text = "\\n\\n".join([
                f"Source {i+1}: {doc.page_content}" 
                for i, doc in enumerate(retrieval_result.documents)
            ])
            
            # Generate content
            generation_chain = prompt | self.llm | StrOutputParser()
            
            generated_content = generation_chain.invoke({
                "context": context_text,
                "casino_name": input_data.casino_name,
                "locale": input_data.tenant_config.locale,
                "brand": input_data.tenant_config.brand_name,
                "voice_profile": input_data.tenant_config.voice_profile,
                "images": metadata["images"],
                "affiliate_context": metadata["affiliate_context"]
            })
            
            return generated_content
        
        # Step 6: Create ReviewDoc output
        def create_review_doc(data: Dict[str, Any]) -> ReviewDoc:
            """Create structured ReviewDoc from generated content"""
            input_data = data["input"]
            generated_content = data["generated_content"]
            retrieval_result = data["retrieval_result"]
            metadata = data["metadata"]
            
            # Extract affiliate intelligence from context if available
            affiliate_intel = None
            if retrieval_result.context_metadata.get("casino_intelligence"):
                affiliate_intel = retrieval_result.context_metadata["casino_intelligence"]
            
            return ReviewDoc(
                title=f"{input_data.casino_name} Casino Review",
                content=generated_content,
                content_type="casino_review",
                tenant_config=input_data.tenant_config,
                tenant_id=input_data.tenant_config.tenant_id,
                brand=input_data.tenant_config.brand_name,
                locale=input_data.tenant_config.locale,
                target_audience=input_data.tenant_config.target_demographics,
                seo_metadata={
                    "title": f"{input_data.casino_name} Casino Review - {input_data.tenant_config.brand_name}",
                    "description": f"Comprehensive review of {input_data.casino_name} casino",
                    "keywords": [input_data.casino_name, "casino", "review", "gambling"]
                },
                visual_content=input_data.visual_assets,
                affiliate_intel=affiliate_intel,
                sources=[doc.metadata.get("source", "Unknown") for doc in retrieval_result.documents],
                research_depth_score=min(len(retrieval_result.documents) / 2.0, 10.0),
                generation_timestamp=datetime.now(),
                llm_model_used=self.llm.model_name,
                generation_parameters={
                    "temperature": self.llm.temperature,
                    "max_tokens": self.llm.max_tokens,
                    "retrieval_docs": len(retrieval_result.documents),
                    "locale": input_data.tenant_config.locale
                }
            )
        
        # Build the complete LCEL chain
        chain = (
            RunnablePassthrough.assign(
                # Step 1: Prepare retrieval query
                retrieval_query=RunnableLambda(prepare_retrieval_query)
            )
            | RunnablePassthrough.assign(
                # Step 2: Perform retrieval
                retrieval_result=RunnableLambda(lambda x: perform_retrieval(x["retrieval_query"]))
            )
            | RunnablePassthrough.assign(
                # Step 3: Process metadata
                metadata=RunnableLambda(lambda x: process_metadata(x["input"] if isinstance(x, dict) else x))
            )
            | RunnablePassthrough.assign(
                # Step 4: Generate content
                generated_content=RunnableLambda(generate_content)
            )
            | RunnablePassthrough.assign(
                # Step 5: Create ReviewDoc
                review_doc=RunnableLambda(create_review_doc)
            )
            | RunnableLambda(lambda x: NarrativeGenerationOutput(
                generated_content=x["generated_content"],
                review_doc=x["review_doc"],
                retrieval_context=x["retrieval_result"].documents,
                generation_metadata={
                    "retrieval_score": x["retrieval_result"].confidence_score,
                    "context_sources": len(x["retrieval_result"].documents),
                    "visual_assets": len(x["input"].visual_assets),
                    "processing_timestamp": datetime.now().isoformat(),
                    "locale": x["input"].tenant_config.locale
                }
            ))
        )
        
        return chain
    
    def generate_narrative(self, input_data: NarrativeGenerationInput) -> NarrativeGenerationOutput:
        """
        Generate narrative content using the LCEL chain
        
        Args:
            input_data: Complete input specification
            
        Returns:
            Generated narrative with structured output
        """
        try:
            # Execute the chain
            result = self.chain.invoke({"input": input_data})
            
            logger.info(f"Successfully generated narrative for {input_data.casino_name}")
            logger.info(f"Content length: {len(result.generated_content)} characters")
            logger.info(f"Retrieved context: {len(result.retrieval_context)} documents")
            
            return result
            
        except Exception as e:
            logger.error(f"Narrative generation failed: {str(e)}")
            raise
    
    def get_available_locales(self) -> List[str]:
        """Get available prompt locales"""
        return self.prompt_loader.get_available_locales()


# Factory function for easy instantiation
def create_narrative_generation_chain(
    retrieval_system: MultiTenantRetrievalSystem,
    llm_model: str = "gpt-4o",
    temperature: float = 0.7
) -> NarrativeGenerationChain:
    """
    Create a narrative generation chain with specified parameters
    
    Args:
        retrieval_system: Multi-tenant retrieval system
        llm_model: LLM model name
        temperature: Generation temperature
        
    Returns:
        Configured narrative generation chain
    """
    llm = ChatOpenAI(
        model=llm_model,
        temperature=temperature,
        max_tokens=4096
    )
    
    return NarrativeGenerationChain(
        retrieval_system=retrieval_system,
        llm=llm
    )