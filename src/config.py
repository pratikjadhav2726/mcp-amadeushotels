"""
Configuration management for the MCP Amadeus Hotels server.
"""

import os
import logging
from typing import Optional, List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Amadeus API Configuration
    amadeus_api_key: str = Field(..., env="AMADEUS_API_KEY", description="Amadeus API key")
    amadeus_api_secret: str = Field(..., env="AMADEUS_API_SECRET", description="Amadeus API secret")
    amadeus_base_url: str = Field(
        "https://test.api.amadeus.com",
        env="AMADEUS_BASE_URL",
        description="Amadeus API base URL"
    )
    
    # Server Configuration
    port: int = Field(3000, env="PORT", description="Server port")
    host: str = Field("127.0.0.1", env="HOST", description="Server host")
    log_level: str = Field("INFO", env="LOG_LEVEL", description="Logging level")
    
    # API Configuration
    api_timeout: float = Field(30.0, env="API_TIMEOUT", description="API request timeout")
    max_retries: int = Field(3, env="MAX_RETRIES", description="Maximum retry attempts")
    
    # Multithreading Configuration
    client_pool_size: int = Field(5, env="CLIENT_POOL_SIZE", description="Number of concurrent API clients")
    max_concurrent_requests: int = Field(10, env="MAX_CONCURRENT_REQUESTS", description="Maximum concurrent API requests")
    enable_connection_pooling: bool = Field(True, env="ENABLE_CONNECTION_POOLING", description="Enable HTTP connection pooling")
    
    # Caching Configuration
    enable_caching: bool = Field(False, env="ENABLE_CACHING", description="Enable response caching")
    cache_ttl: int = Field(300, env="CACHE_TTL", description="Cache time-to-live in seconds")
    cache_max_size: int = Field(1000, env="CACHE_MAX_SIZE", description="Maximum cache entries")
    
    # Authentication Configuration
    auth_enabled: bool = Field(True, env="AUTH_ENABLED", description="Enable authentication")
    api_keys: Union[List[str], str] = Field(
        default=["default-api-key"],
        env="API_KEYS",
        description="List of valid API keys (comma-separated)"
    )
    jwt_secret: Optional[str] = Field(
        default=None,
        env="JWT_SECRET",
        description="JWT secret key for token validation"
    )
    
    @field_validator('api_keys', mode='before')
    @classmethod
    def parse_api_keys(cls, v):
        """Parse comma-separated API keys into a list."""
        if isinstance(v, str):
            return [key.strip() for key in v.split(',') if key.strip()]
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


def setup_logging(log_level: str = "INFO") -> None:
    """Set up logging configuration."""
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    
    # Reduce noise from httpx
    logging.getLogger("httpx").setLevel(logging.WARNING)


def get_settings() -> Settings:
    """Get application settings."""
    try:
        return Settings()
    except Exception as e:
        logging.error(f"Failed to load settings: {e}")
        raise


# Global settings instance
settings: Optional[Settings] = None


def get_app_settings() -> Settings:
    """Get the global settings instance."""
    global settings
    if settings is None:
        settings = get_settings()
    return settings
