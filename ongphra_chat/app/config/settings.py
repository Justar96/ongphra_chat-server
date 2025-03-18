# app/config/settings.py
import os
from functools import lru_cache
from pathlib import Path
from typing import Optional, Dict, Any, Union, List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # API settings
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    default_model: str = Field("gpt-4o-mini", env="DEFAULT_MODEL")
    
    # App settings
    debug: bool = Field(False, env="DEBUG")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    environment: str = Field("development", env="ENVIRONMENT")  # 'development', 'staging', or 'production'
    
    # CORS settings
    cors_origins: Union[str, List[str]] = Field("*", env="CORS_ORIGINS")
    
    # Paths
    base_dir: Path = Path(__file__).parent.parent.parent
    data_dir: Optional[Union[str, Path]] = Field(None)
    categories_path: Optional[Union[str, Path]] = Field(None)
    readings_path: Optional[Union[str, Path]] = Field(None)
    
    # Cache settings
    enable_cache: bool = Field(True, env="ENABLE_CACHE")
    cache_ttl: int = Field(3600, env="CACHE_TTL")  # 1 hour default
    
    # API rate limits
    rate_limit_per_minute: int = Field(60, env="RATE_LIMIT_PER_MINUTE")
    
    # Customization
    default_language: str = Field("thai", env="DEFAULT_LANGUAGE")
    
    # Server settings
    host: str = Field("0.0.0.0", env="HOST")
    port: int = Field(8000, env="PORT")
    
    # Database settings
    db_host: str = Field("localhost", env="DB_HOST")
    db_port: int = Field(3306, env="DB_PORT")
    db_name: str = Field("gpt_log", env="DB_NAME")
    db_user: str = Field("admin_gpt_chat", env="DB_USER")
    db_password: str = Field("password", env="DB_PASSWORD")
    db_pool_min_size: int = Field(5, env="DB_POOL_MIN_SIZE")
    db_pool_max_size: int = Field(20, env="DB_POOL_MAX_SIZE")
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
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
        
        # Set default paths if not provided
        if self.data_dir is None:
            self.data_dir = self.base_dir / "data"
            
        if self.categories_path is None:
            self.categories_path = self.data_dir / "categories.csv"
            
        if self.readings_path is None:
            self.readings_path = self.data_dir / "readings.csv"


@lru_cache()
def get_settings() -> Settings:
    """
    Get application settings as a singleton
    Uses lru_cache to create only one instance
    """
    return Settings()