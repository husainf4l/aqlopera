"""
Core configuration for the Web Operator Agent
"""
import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # OpenAI Configuration
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o", env="OPENAI_MODEL")
    
    # Browser Configuration
    browser_type: str = Field(default="chromium", env="BROWSER_TYPE")
    headless: bool = Field(default=False, env="HEADLESS")
    browser_timeout: int = Field(default=30000, env="BROWSER_TIMEOUT")
    
    # Server Configuration
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    debug: bool = Field(default=True, env="DEBUG")
    environment: str = Field(default="development", env="ENVIRONMENT")
    
    # Security
    secret_key: str = Field(..., env="SECRET_KEY")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # Database Configuration
    database_url: str = Field(default="sqlite:///./operator.db", env="DATABASE_URL")
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: str = Field(default="operator.log", env="LOG_FILE")
    
    # Safety & Monitoring
    max_execution_time: int = Field(default=300, env="MAX_EXECUTION_TIME")
    enable_screenshots: bool = Field(default=True, env="ENABLE_SCREENSHOTS")
    screenshot_path: str = Field(default="./screenshots", env="SCREENSHOT_PATH")
    
    # Rate Limiting
    requests_per_minute: int = Field(default=60, env="REQUESTS_PER_MINUTE")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()

# Ensure required directories exist
os.makedirs(settings.screenshot_path, exist_ok=True)
os.makedirs("logs", exist_ok=True)
