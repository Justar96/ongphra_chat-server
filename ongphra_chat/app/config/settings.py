# app/config/settings.py
import os
from functools import lru_cache
from pathlib import Path
from typing import Optional, Dict, Any, Union

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # API settings
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    default_model: str = Field("gpt-4o-mini", env="DEFAULT_MODEL")
    
    # App settings
    debug: bool = Field(False, env="DEBUG")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    
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
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }
    
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