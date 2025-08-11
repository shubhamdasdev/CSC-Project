"""
Application settings configuration using pydantic-settings.

This module provides centralized configuration management for the competitive
intelligence system, loading settings from environment variables and files.
"""

import os
from pathlib import Path
from typing import Optional, List
from pydantic import Field, validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import yaml


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""
    
    supabase_url: str = Field(..., description="Supabase project URL")
    supabase_service_role_key: str = Field(..., description="Supabase service role key")
    supabase_anon_key: Optional[str] = Field(None, description="Supabase anonymous key")
    
    class Config:
        env_prefix = "SUPABASE_"


class APISettings(BaseSettings):
    """API configuration settings."""
    
    firecrawl_api_key: str = Field(..., description="Firecrawl API key")
    claude_api_key: str = Field(..., description="Anthropic Claude API key")
    
    # API limits and timeouts
    firecrawl_timeout: int = Field(default=60, description="Firecrawl request timeout")
    claude_timeout: int = Field(default=30, description="Claude request timeout")
    
    # Rate limiting
    max_concurrent_requests: int = Field(
        default=10, 
        description="Maximum concurrent requests",
        ge=1,
        le=50
    )
    rate_limit_per_minute: int = Field(
        default=60,
        description="API rate limit per minute",
        ge=1,
        le=1000
    )
    
    class Config:
        env_prefix = ""


class CrawlingSettings(BaseSettings):
    """Web crawling configuration settings."""
    
    crawl_depth: int = Field(
        default=2,
        description="Default crawl depth",
        ge=1,
        le=5
    )
    max_pages_per_competitor: int = Field(
        default=50,
        description="Maximum pages per competitor",
        ge=1,
        le=1000
    )
    extraction_timeout: int = Field(
        default=30,
        description="AI extraction timeout per page",
        ge=5,
        le=300
    )
    
    # Data quality thresholds
    min_url_success_rate: float = Field(
        default=0.95,
        description="Minimum URL success rate",
        ge=0.0,
        le=1.0
    )
    min_price_extraction_rate: float = Field(
        default=0.90,
        description="Minimum price extraction rate",
        ge=0.0,
        le=1.0
    )
    min_image_access_rate: float = Field(
        default=0.95,
        description="Minimum image access rate",
        ge=0.0,
        le=1.0
    )
    max_duplicate_rate: float = Field(
        default=0.05,
        description="Maximum duplicate rate",
        ge=0.0,
        le=1.0
    )
    
    class Config:
        env_prefix = ""


class LoggingSettings(BaseSettings):
    """Logging configuration settings."""
    
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )
    log_file: str = Field(
        default="logs/pipeline.log",
        description="Log file path"
    )
    max_log_file_size: int = Field(
        default=10485760,  # 10MB
        description="Maximum log file size in bytes"
    )
    log_backup_count: int = Field(
        default=5,
        description="Number of log file backups to keep"
    )
    
    @validator('log_level')
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()
    
    class Config:
        env_prefix = "LOG_"


class ApplicationSettings(BaseSettings):
    """Main application settings."""
    
    # Environment
    environment: str = Field(
        default="development",
        description="Application environment"
    )
    debug: bool = Field(
        default=False,
        description="Debug mode"
    )
    
    # Timing constraints
    pipeline_timeout_minutes: int = Field(
        default=80,
        description="Maximum pipeline execution time in minutes",
        ge=1,
        le=300
    )
    
    # Data paths
    data_dir: Path = Field(
        default=Path("data"),
        description="Data directory path"
    )
    exports_dir: Path = Field(
        default=Path("data/exports"),
        description="Exports directory path"
    )
    
    # API Settings (flattened)
    firecrawl_api_key: str = Field(..., description="Firecrawl API key")
    claude_api_key: str = Field(..., description="Anthropic Claude API key")
    firecrawl_timeout: int = Field(default=60, description="Firecrawl request timeout")
    claude_timeout: int = Field(default=30, description="Claude request timeout")
    max_concurrent_requests: int = Field(default=10, description="Maximum concurrent requests", ge=1, le=50)
    rate_limit_per_minute: int = Field(default=60, description="API rate limit per minute", ge=1, le=1000)
    
    # Database Settings (flattened)
    supabase_url: str = Field(..., description="Supabase project URL")
    supabase_service_role_key: str = Field(..., description="Supabase service role key")
    supabase_anon_key: Optional[str] = Field(None, description="Supabase anonymous key")
    
    # Crawling Settings (flattened)
    crawl_depth: int = Field(default=2, description="Default crawl depth", ge=1, le=5)
    max_pages_per_competitor: int = Field(default=50, description="Maximum pages per competitor", ge=1, le=1000)
    extraction_timeout: int = Field(default=30, description="AI extraction timeout per page", ge=5, le=300)
    min_url_success_rate: float = Field(default=0.95, description="Minimum URL success rate", ge=0.0, le=1.0)
    min_price_extraction_rate: float = Field(default=0.90, description="Minimum price extraction rate", ge=0.0, le=1.0)
    min_image_access_rate: float = Field(default=0.95, description="Minimum image access rate", ge=0.0, le=1.0)
    max_duplicate_rate: float = Field(default=0.05, description="Maximum duplicate rate", ge=0.0, le=1.0)
    
    # Logging Settings (flattened)
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: str = Field(default="logs/pipeline.log", description="Log file path")
    max_log_file_size: int = Field(default=10485760, description="Maximum log file size in bytes")
    log_backup_count: int = Field(default=5, description="Number of log file backups to keep")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        validate_assignment = True
    
    @validator('environment')
    def validate_environment(cls, v):
        """Validate environment setting."""
        valid_envs = ['development', 'staging', 'production', 'test']
        if v.lower() not in valid_envs:
            raise ValueError(f"Environment must be one of: {valid_envs}")
        return v.lower()
    
    @validator('log_level')
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()
    
    def ensure_directories(self):
        """Ensure all required directories exist."""
        directories = [
            self.data_dir,
            self.exports_dir,
            self.data_dir / "raw",
            self.data_dir / "processed",
            self.data_dir / "images",
            Path("logs")
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)


def load_competitor_config(config_path: str = "config/competitors.yml"):
    """
    Load competitor configuration from YAML file.
    
    Args:
        config_path: Path to competitors configuration file
        
    Returns:
        dict: Competitor configuration data
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If config file is invalid YAML
    """
    config_file = Path(config_path)
    
    if not config_file.exists():
        raise FileNotFoundError(f"Competitor config file not found: {config_path}")
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        # Validate basic structure
        if 'competitors' not in config_data:
            raise ValueError("Config file must contain 'competitors' key")
        
        if not isinstance(config_data['competitors'], list):
            raise ValueError("'competitors' must be a list")
        
        if len(config_data['competitors']) == 0:
            raise ValueError("At least one competitor must be configured")
        
        return config_data
        
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Invalid YAML in config file: {e}")


def get_settings() -> ApplicationSettings:
    """
    Get application settings with proper error handling.
    
    Returns:
        ApplicationSettings: Configured application settings
        
    Raises:
        ValueError: If settings validation fails
    """
    # Load environment variables from .env file
    load_dotenv()
    
    try:
        settings = ApplicationSettings()
        
        # Ensure required directories exist
        settings.ensure_directories()
        
        return settings
        
    except Exception as e:
        error_msg = f"Failed to load settings: {e}"
        
        # Provide helpful error messages for common issues
        if "supabase_url" in str(e).lower():
            error_msg += "\nMake sure to set SUPABASE_URL in your .env file"
        elif "api_key" in str(e).lower():
            error_msg += "\nMake sure to set API keys in your .env file"
        
        raise ValueError(error_msg) from e


def validate_api_keys(settings: ApplicationSettings) -> List[str]:
    """
    Validate that all required API keys are present and non-empty.
    
    Args:
        settings: Application settings to validate
        
    Returns:
        List[str]: List of validation errors, empty if all valid
    """
    errors = []
    
    # Check required API keys
    if not settings.firecrawl_api_key or settings.firecrawl_api_key == "your_firecrawl_api_key_here":
        errors.append("FIRECRAWL_API_KEY is missing or using placeholder value")
    
    if not settings.claude_api_key or settings.claude_api_key == "your_anthropic_api_key_here":
        errors.append("CLAUDE_API_KEY is missing or using placeholder value")
    
    if not settings.supabase_url or settings.supabase_url == "your_supabase_project_url":
        errors.append("SUPABASE_URL is missing or using placeholder value")
    
    if not settings.supabase_service_role_key or settings.supabase_service_role_key == "your_service_role_key":
        errors.append("SUPABASE_SERVICE_ROLE_KEY is missing or using placeholder value")
    
    return errors


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent


def get_data_directory(settings: ApplicationSettings, subdir: str = "") -> Path:
    """
    Get data directory path.
    
    Args:
        settings: Application settings
        subdir: Subdirectory name
        
    Returns:
        Path: Data directory path
    """
    if subdir:
        return settings.data_dir / subdir
    return settings.data_dir


# Global settings instance (initialized on first import)
_settings_instance: Optional[ApplicationSettings] = None


def get_global_settings() -> ApplicationSettings:
    """Get global settings instance (singleton pattern)."""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = get_settings()
    return _settings_instance
