# app/config/settings.py
import os
from functools import lru_cache
from pathlib import Path
from typing import Optional, Dict, Any, Union, List
import logging
from dotenv import load_dotenv

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)

# Get the absolute path to the .env file
ENV_PATH = Path(__file__).parent.parent.parent / '.env'

# Load environment variables from .env file
load_dotenv(ENV_PATH)

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # API settings
    openai_api_key: str = Field(default=os.getenv("OPENAI_API_KEY", ""), env="OPENAI_API_KEY")
    default_model: str = Field(default=os.getenv("DEFAULT_MODEL", "gpt-4o-mini"), env="DEFAULT_MODEL")
    
    # OpenAI API settings
    openai_api_base: str = Field(default=os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1"), env="OPENAI_API_BASE")
    openai_model: str = Field(default=os.getenv("OPENAI_MODEL", "gpt-4o-mini"), env="OPENAI_MODEL")
    enable_ai_readings: bool = Field(default=os.getenv("ENABLE_AI_READINGS", "true").lower() == "true", env="ENABLE_AI_READINGS")
    ai_reading_max_tokens: int = Field(default=int(os.getenv("AI_READING_MAX_TOKENS", "1000")), env="AI_READING_MAX_TOKENS")
    ai_reading_temperature: float = Field(default=float(os.getenv("AI_READING_TEMPERATURE", "0.7")), env="AI_READING_TEMPERATURE")
    
    # AI Model Configuration
    ai_topic_model: str = Field(default=os.getenv("AI_TOPIC_MODEL", "thai-topic-v1"), env="AI_TOPIC_MODEL")
    ai_topic_confidence_threshold: float = Field(default=float(os.getenv("AI_TOPIC_CONFIDENCE_THRESHOLD", "0.6")), env="AI_TOPIC_CONFIDENCE_THRESHOLD")
    ai_sentiment_model: str = Field(default=os.getenv("AI_SENTIMENT_MODEL", "thai-sentiment-v1"), env="AI_SENTIMENT_MODEL")
    
    # Redis settings
    redis_enabled: bool = Field(default=os.getenv("REDIS_ENABLED", "true").lower() == "true", env="REDIS_ENABLED")
    redis_host: str = Field(default=os.getenv("REDIS_HOST", "localhost"), env="REDIS_HOST")
    redis_port: int = Field(default=int(os.getenv("REDIS_PORT", "6379")), env="REDIS_PORT")
    redis_db: int = Field(default=int(os.getenv("REDIS_DB", "0")), env="REDIS_DB")
    redis_password: Optional[str] = Field(default=os.getenv("REDIS_PASSWORD"), env="REDIS_PASSWORD")
    redis_ssl: bool = Field(default=os.getenv("REDIS_SSL", "false").lower() == "true", env="REDIS_SSL")
    redis_timeout: int = Field(default=int(os.getenv("REDIS_TIMEOUT", "5")), env="REDIS_TIMEOUT")
    redis_retry_interval: int = Field(default=int(os.getenv("REDIS_RETRY_INTERVAL", "300")), env="REDIS_RETRY_INTERVAL")
    redis_max_retries: int = Field(default=int(os.getenv("REDIS_MAX_RETRIES", "3")), env="REDIS_MAX_RETRIES")
    
    @property
    def redis_url(self) -> str:
        """Get Redis URL with proper configuration"""
        if not self.redis_enabled:
            return ""
            
        auth = f":{self.redis_password}@" if self.redis_password else ""
        protocol = "rediss" if self.redis_ssl else "redis"
        return f"{protocol}://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    # App settings
    debug: bool = Field(default=os.getenv("DEBUG", "false").lower() == "true", env="DEBUG")
    log_level: str = Field(default=os.getenv("LOG_LEVEL", "INFO"), env="LOG_LEVEL")
    environment: str = Field(default=os.getenv("ENVIRONMENT", "development"), env="ENVIRONMENT")
    
    # CORS settings
    cors_origins: Union[str, List[str]] = Field(default=os.getenv("CORS_ORIGINS", "*"), env="CORS_ORIGINS")
    
    # Paths
    base_dir: Path = Path(__file__).parent.parent.parent
    data_dir: Optional[Union[str, Path]] = Field(None)
    categories_path: Optional[Union[str, Path]] = Field(None)
    readings_path: Optional[Union[str, Path]] = Field(None)
    
    # Cache settings
    enable_cache: bool = Field(default=os.getenv("ENABLE_CACHE", "true").lower() == "true", env="ENABLE_CACHE")
    cache_ttl: int = Field(default=int(os.getenv("CACHE_TTL", "3600")), env="CACHE_TTL")
    
    # API rate limits
    rate_limit_per_minute: int = Field(default=int(os.getenv("RATE_LIMIT_PER_MINUTE", "60")), env="RATE_LIMIT_PER_MINUTE")
    
    # Customization
    default_language: str = Field(default=os.getenv("DEFAULT_LANGUAGE", "thai"), env="DEFAULT_LANGUAGE")
    
    # Server settings
    host: str = Field(default=os.getenv("HOST", "0.0.0.0"), env="HOST")
    port: int = Field(default=int(os.getenv("PORT", "8000")), env="PORT")
    
    # Database settings
    db_host: str = Field(default=os.getenv("DB_HOST", "localhost"), env="DB_HOST")
    db_port: int = Field(default=int(os.getenv("DB_PORT", "3306")), env="DB_PORT")
    db_name: str = Field(default=os.getenv("DB_NAME", "gpt_log"), env="DB_NAME")
    db_user: str = Field(default=os.getenv("DB_USER", "admin_gpt_chat"), env="DB_USER")
    db_password: str = Field(default=os.getenv("DB_PASSWORD", "password"), env="DB_PASSWORD")
    db_pool_min_size: int = Field(default=int(os.getenv("DB_POOL_MIN_SIZE", "5")), env="DB_POOL_MIN_SIZE")
    db_pool_max_size: int = Field(default=int(os.getenv("DB_POOL_MAX_SIZE", "20")), env="DB_POOL_MAX_SIZE")
    
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


@lru_cache()
def get_settings() -> Settings:
    """
    Get application settings as a singleton
    Uses lru_cache to create only one instance
    """
    try:
        settings = Settings()
        logger.info(f"Settings loaded from {ENV_PATH}")
        return settings
    except Exception as e:
        logger.error(f"Error loading settings: {str(e)}")
        raise