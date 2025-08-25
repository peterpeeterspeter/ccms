"""
Native LangChain RAG Configuration
=================================

Configuration settings and presets for the native LangChain RAG implementation.
Provides easy setup for different deployment scenarios.
"""

import os
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from enum import Enum


class VectorStoreType(str, Enum):
    """Supported vector store types"""
    FAISS = "faiss"
    CHROMA = "chroma" 
    REDIS = "redis"
    SUPABASE = "supabase"


class ModelProvider(str, Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE = "azure"
    LOCAL = "local"


class DeploymentMode(str, Enum):
    """Deployment modes"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    LOCAL = "local"


@dataclass
class NativeRAGConfig:
    """Configuration for Native LangChain RAG Chain"""
    
    # Model Configuration
    model_name: str = "gpt-4o-mini"
    model_provider: ModelProvider = ModelProvider.OPENAI
    temperature: float = 0.1
    max_tokens: int = 4000
    
    # Vector Store Configuration
    vector_store_type: VectorStoreType = VectorStoreType.FAISS
    vector_store_path: Optional[str] = None
    embedding_model: str = "text-embedding-3-small"
    
    # Retrieval Configuration
    retrieval_k: int = 6
    enable_multi_query: bool = True
    enable_compression: bool = True
    enable_ensemble: bool = True
    ensemble_weights: List[float] = None
    
    # Memory Configuration
    enable_memory: bool = True
    memory_type: str = "summary_buffer"
    memory_max_tokens: int = 1000
    
    # Caching Configuration
    enable_caching: bool = True
    cache_type: str = "redis_semantic"
    cache_ttl: int = 3600  # 1 hour
    
    # Web Search Configuration
    enable_web_search: bool = True
    web_search_max_results: int = 5
    
    # Performance Configuration
    enable_streaming: bool = True
    enable_async: bool = True
    batch_size: int = 10
    
    # Deployment Configuration
    deployment_mode: DeploymentMode = DeploymentMode.DEVELOPMENT
    enable_logging: bool = True
    log_level: str = "INFO"
    
    def __post_init__(self):
        """Post-initialization validation and setup"""
        if self.ensemble_weights is None:
            self.ensemble_weights = [0.5, 0.5]
        
        # Validate environment variables based on configuration
        self._validate_environment()
    
    def _validate_environment(self):
        """Validate required environment variables"""
        required_vars = []
        optional_vars = []
        
        # Model provider requirements
        if self.model_provider == ModelProvider.OPENAI:
            required_vars.append("OPENAI_API_KEY")
        elif self.model_provider == ModelProvider.ANTHROPIC:
            required_vars.append("ANTHROPIC_API_KEY")
        elif self.model_provider == ModelProvider.AZURE:
            required_vars.extend([
                "AZURE_OPENAI_API_KEY",
                "AZURE_OPENAI_ENDPOINT"
            ])
        
        # Vector store requirements
        if self.vector_store_type == VectorStoreType.REDIS:
            required_vars.append("REDIS_URL")
        elif self.vector_store_type == VectorStoreType.SUPABASE:
            required_vars.extend([
                "SUPABASE_URL",
                "SUPABASE_SERVICE_KEY"
            ])
        
        # Optional services
        if self.enable_web_search:
            optional_vars.append("TAVILY_API_KEY")
        
        if self.enable_caching and self.cache_type == "redis_semantic":
            optional_vars.append("REDIS_URL")
        
        # Check required variables
        missing_required = [var for var in required_vars if not os.getenv(var)]
        if missing_required:
            raise ValueError(f"Missing required environment variables: {missing_required}")
        
        # Warn about optional variables
        missing_optional = [var for var in optional_vars if not os.getenv(var)]
        if missing_optional:
            print(f"⚠️ Optional features disabled due to missing env vars: {missing_optional}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary"""
        return {
            "model_name": self.model_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "vector_store_type": self.vector_store_type.value,
            "enable_caching": self.enable_caching,
            "enable_memory": self.enable_memory,
            "enable_web_search": self.enable_web_search,
        }


# Predefined configurations for different scenarios

DEVELOPMENT_CONFIG = NativeRAGConfig(
    model_name="gpt-4o-mini",
    temperature=0.1,
    vector_store_type=VectorStoreType.FAISS,
    enable_caching=False,
    enable_web_search=False,
    deployment_mode=DeploymentMode.DEVELOPMENT,
    log_level="DEBUG"
)

PRODUCTION_CONFIG = NativeRAGConfig(
    model_name="gpt-4o",
    temperature=0.05,
    vector_store_type=VectorStoreType.REDIS,
    enable_caching=True,
    enable_web_search=True,
    deployment_mode=DeploymentMode.PRODUCTION,
    log_level="INFO",
    memory_max_tokens=2000,
    retrieval_k=8
)

STAGING_CONFIG = NativeRAGConfig(
    model_name="gpt-4o-mini",
    temperature=0.1,
    vector_store_type=VectorStoreType.CHROMA,
    enable_caching=True,
    enable_web_search=True,
    deployment_mode=DeploymentMode.STAGING,
    log_level="INFO"
)

LOCAL_CONFIG = NativeRAGConfig(
    model_name="gpt-4o-mini",
    temperature=0.2,
    vector_store_type=VectorStoreType.FAISS,
    enable_caching=False,
    enable_web_search=False,
    deployment_mode=DeploymentMode.LOCAL,
    log_level="DEBUG",
    enable_memory=False
)

# Configuration registry
CONFIG_REGISTRY = {
    "development": DEVELOPMENT_CONFIG,
    "staging": STAGING_CONFIG, 
    "production": PRODUCTION_CONFIG,
    "local": LOCAL_CONFIG
}


def get_config(mode: str = "development") -> NativeRAGConfig:
    """Get configuration for specified mode"""
    if mode not in CONFIG_REGISTRY:
        raise ValueError(f"Unknown configuration mode: {mode}. Available: {list(CONFIG_REGISTRY.keys())}")
    
    return CONFIG_REGISTRY[mode]


def create_custom_config(**kwargs) -> NativeRAGConfig:
    """Create a custom configuration with overrides"""
    base_config = DEVELOPMENT_CONFIG
    
    # Create new config with overrides
    config_dict = base_config.to_dict()
    config_dict.update(kwargs)
    
    return NativeRAGConfig(**config_dict)


def load_config_from_env() -> NativeRAGConfig:
    """Load configuration from environment variables"""
    
    config = NativeRAGConfig(
        # Model settings
        model_name=os.getenv("RAG_MODEL_NAME", "gpt-4o-mini"),
        temperature=float(os.getenv("RAG_TEMPERATURE", "0.1")),
        max_tokens=int(os.getenv("RAG_MAX_TOKENS", "4000")),
        
        # Vector store settings
        vector_store_type=VectorStoreType(os.getenv("RAG_VECTOR_STORE", "faiss")),
        retrieval_k=int(os.getenv("RAG_RETRIEVAL_K", "6")),
        
        # Feature flags
        enable_caching=os.getenv("RAG_ENABLE_CACHING", "true").lower() == "true",
        enable_memory=os.getenv("RAG_ENABLE_MEMORY", "true").lower() == "true",
        enable_web_search=os.getenv("RAG_ENABLE_WEB_SEARCH", "true").lower() == "true",
        
        # Deployment
        deployment_mode=DeploymentMode(os.getenv("RAG_DEPLOYMENT_MODE", "development")),
        log_level=os.getenv("RAG_LOG_LEVEL", "INFO")
    )
    
    return config


# Convenience functions for common use cases

def get_casino_review_config() -> NativeRAGConfig:
    """Configuration optimized for casino review generation"""
    return NativeRAGConfig(
        model_name="gpt-4o",
        temperature=0.05,  # Lower temperature for factual content
        vector_store_type=VectorStoreType.CHROMA,
        retrieval_k=8,  # More sources for comprehensive reviews
        enable_web_search=True,  # Real-time casino information
        enable_compression=True,  # Better context utilization
        memory_max_tokens=1500,  # Longer context for detailed reviews
        web_search_max_results=8  # More web sources
    )


def get_fast_response_config() -> NativeRAGConfig:
    """Configuration optimized for fast responses"""
    return NativeRAGConfig(
        model_name="gpt-4o-mini",
        temperature=0.2,
        vector_store_type=VectorStoreType.FAISS,
        retrieval_k=4,  # Fewer sources for speed
        enable_compression=False,  # Skip compression for speed
        enable_web_search=False,  # No web search for speed
        enable_memory=False,  # No memory for speed
        max_tokens=2000  # Shorter responses
    )


def get_high_quality_config() -> NativeRAGConfig:
    """Configuration optimized for highest quality output"""
    return NativeRAGConfig(
        model_name="gpt-4o",
        temperature=0.05,
        vector_store_type=VectorStoreType.REDIS,
        retrieval_k=10,  # Maximum sources
        enable_compression=True,
        enable_web_search=True,
        enable_ensemble=True,
        memory_max_tokens=2000,
        web_search_max_results=10,
        max_tokens=6000  # Longer, detailed responses
    )


if __name__ == "__main__":
    # Example usage
    print("🔧 Native RAG Configuration Examples")
    
    # Test different configurations
    configs = [
        ("Development", get_config("development")),
        ("Production", get_config("production")),
        ("Casino Review", get_casino_review_config()),
        ("Fast Response", get_fast_response_config()),
        ("High Quality", get_high_quality_config())
    ]
    
    for name, config in configs:
        print(f"\n--- {name} Configuration ---")
        print(f"Model: {config.model_name}")
        print(f"Vector Store: {config.vector_store_type.value}")
        print(f"Retrieval K: {config.retrieval_k}")
        print(f"Web Search: {config.enable_web_search}")
        print(f"Caching: {config.enable_caching}")
        print(f"Memory: {config.enable_memory}")
    
    print("\n✅ Configuration examples completed!")