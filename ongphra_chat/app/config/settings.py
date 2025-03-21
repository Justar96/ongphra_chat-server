# app/config/settings.py
import os
from functools import lru_cache
from pathlib import Path
from typing import Optional, Dict, Any, Union, List
import logging
from dotenv import load_dotenv

from pydantic import Field, field_validator, AnyHttpUrl
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)

# Get the absolute path to the .env file
ENV_PATH = Path(__file__).parent.parent.parent / '.env'

# Load environment variables from .env file
load_dotenv(ENV_PATH)

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # API settings
    api_name: str = "Thai Fortune API"
    api_version: str = "1.0.0"
    openai_api_key: str = Field(default="")
    default_model: str = Field(default="gpt-4o-mini")
    
    # OpenAI API settings
    openai_api_base: str = Field(default="https://api.openai.com/v1")
    openai_model: str = Field(default="gpt-4o-mini")
    enable_ai_readings: bool = Field(default=True)
    ai_reading_max_tokens: int = Field(default=1000)
    ai_reading_temperature: float = Field(default=0.7)
    openai_max_tokens: int = Field(default=1000)
    openai_temperature: float = Field(default=0.7)
    openai_system_prompt: str = Field(default="")
    
    # AI Model Configuration
    ai_topic_model: str = Field(default="thai-topic-v1")
    ai_topic_confidence_threshold: float = Field(default=0.6)
    ai_sentiment_model: str = Field(default="thai-sentiment-v1")
    
    # Redis settings
    redis_enabled: bool = Field(default=True)
    redis_host: str = Field(default="localhost")
    redis_port: int = Field(default=6379)
    redis_db: int = Field(default=0)
    redis_password: Optional[str] = Field(default=None)
    redis_ssl: bool = Field(default=False)
    redis_timeout: int = Field(default=5)
    redis_retry_interval: int = Field(default=300)
    redis_max_retries: int = Field(default=3)
    
    @property
    def redis_url(self) -> str:
        """Get Redis URL with proper configuration"""
        if not self.redis_enabled:
            return ""
            
        auth = f":{self.redis_password}@" if self.redis_password else ""
        protocol = "rediss" if self.redis_ssl else "redis"
        return f"{protocol}://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    # App settings
    debug: bool = Field(default=True)
    log_level: str = Field(default="INFO")
    environment: str = Field(default="development")
    
    # CORS settings
    cors_origins: List[str] = Field(default=["*"])
    
    # Paths
    base_dir: Path = Path(__file__).parent.parent.parent
    data_dir: Optional[Union[str, Path]] = Field(None)
    categories_path: Optional[Union[str, Path]] = Field(None)
    readings_path: Optional[Union[str, Path]] = Field(None)
    
    # Cache settings
    enable_cache: bool = Field(default=True)
    cache_ttl: int = Field(default=3600)
    
    # API rate limits
    rate_limit_per_minute: int = Field(default=60)
    
    # Customization
    default_language: str = Field(default="thai")
    
    # Server settings
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    
    # Database settings
    db_host: str = Field(default="localhost")
    db_port: int = Field(default=3306)
    db_name: str = Field(default="gpt_log")
    db_user: str = Field(default="admin_gpt_chat")
    db_password: str = Field(default="password")
    db_pool_min_size: int = Field(default=5)
    db_pool_max_size: int = Field(default=20)
    database_url: str = Field(default="sqlite:///./chat_history.db")
    
    model_config = {
        "env_file": str(ENV_PATH),
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore"
    }
    
    @field_validator("cors_origins")
    def validate_cors_origins(cls, v):
        if isinstance(v, str):
            if v == "*":
                return ["*"]
            return [origin.strip() for origin in v.split(",")]
        return v
    
    def __init__(self, **data: Any):
        super().__init__(**data)
        
        # Log loaded settings
        logger.info(f"Loaded settings from environment: DEBUG={self.debug}, ENV={self.environment}")
        
        # Log AI model configurations
        logger.info(f"AI Models Configuration:")
        logger.info(f"- OpenAI Model: {self.openai_model}")
        logger.info(f"- Topic Detection Model: {self.ai_topic_model}")
        logger.info(f"- Sentiment Analysis Model: {self.ai_sentiment_model}")
        logger.info(f"- AI Reading Max Tokens: {self.ai_reading_max_tokens}")
        logger.info(f"- AI Reading Temperature: {self.ai_reading_temperature}")
        
        # Log Redis configuration
        if self.redis_enabled:
            masked_url = self.redis_url.replace(self.redis_password or "", "***" if self.redis_password else "")
            logger.info(f"Redis enabled: {masked_url}")
        else:
            logger.info("Redis disabled, using in-memory cache")
        
        if self.openai_api_key:
            logger.info("OpenAI API key found")
        else:
            logger.warning("No OpenAI API key found in environment")


@lru_cache
def get_settings() -> Settings:
    """
    Get application settings. This function is cached to avoid
    loading settings on each call.
    """
    try:
        settings = Settings(
            # Override with environment variables
            openai_api_key=os.environ.get("OPENAI_API_KEY", ""),
            openai_model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
            debug=os.environ.get("DEBUG", "False").lower() in ["true", "1", "t"],
            host=os.environ.get("HOST", "0.0.0.0"),
            port=int(os.environ.get("PORT", "8000")),
            log_level=os.environ.get("LOG_LEVEL", "INFO"),
            
            # Database settings
            db_host=os.environ.get("DB_HOST", "localhost"),
            db_port=int(os.environ.get("DB_PORT", "3306")),
            db_name=os.environ.get("DB_NAME", "gpt_log"),
            db_user=os.environ.get("DB_USER", "admin_gpt_chat"),
            db_password=os.environ.get("DB_PASSWORD", "password"),
            db_pool_min_size=int(os.environ.get("DB_POOL_MIN_SIZE", "5")),
            db_pool_max_size=int(os.environ.get("DB_POOL_MAX_SIZE", "20")),
        )
        logger.info(f"Settings loaded from {ENV_PATH}")
        return settings
    except Exception as e:
        logger.error(f"Error loading settings: {e}")
        # Even if there's an error, we need to return settings
        return Settings()