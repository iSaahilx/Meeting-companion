import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    # API Keys
    openai_api_key: str = ""
    deepgram_api_key: str = ""
    pinecone_api_key: str = ""
    serper_api_key: str = ""
    
    # Pinecone Configuration
    pinecone_index_name: str = "voicerag-documents"
    
    # OpenAI Configuration
    openai_model: str = "gpt-4-1106-preview"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536
    
    # Application Configuration
    upload_dir: str = "uploads"
    max_file_size: int = 50000000  # 50MB
    allowed_extensions: List[str] = ["pdf"]
    
    # CORS Configuration
    frontend_url: str = "http://localhost:3000"
    
    # Voice Configuration
    deepgram_model: str = "nova-2"
    deepgram_language: str = "en-US"
    deepgram_encoding: str = "linear16"
    deepgram_sample_rate: int = 16000
    
    # Vector Store Configuration
    chunk_size: int = 1000
    chunk_overlap: int = 200
    top_k_results: int = 5
    similarity_threshold: float = 0.3  # Lowered from 0.7 to get more results
    
    # Web Search Configuration
    serper_num_results: int = 10
    
    # For Pydantic V2, we use model_config instead of a nested Config class
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        env_file_encoding='utf-8',
        extra='ignore'
    )

# Global settings instance
settings = Settings()

# Validate required API keys
def validate_api_keys():
    required_keys = [
        ("OPENAI_API_KEY", settings.openai_api_key),
        ("DEEPGRAM_API_KEY", settings.deepgram_api_key),
        ("PINECONE_API_KEY", settings.pinecone_api_key),
        ("SERPER_API_KEY", settings.serper_api_key),
    ]
    
    missing_keys = []
    for key_name, key_value in required_keys:
        if not key_value:
            missing_keys.append(key_name)
    
    if missing_keys:
        raise ValueError(f"Missing required API keys in .env file: {', '.join(missing_keys)}")

# Create upload directory if it doesn't exist (at runtime)
def ensure_upload_dir():
    """Ensure upload directory exists"""
    os.makedirs(settings.upload_dir, exist_ok=True)
    
# Don't create directories at import time - only when needed 