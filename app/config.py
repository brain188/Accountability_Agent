"""
Configuration Module

Handles application configuration using Pydantic Settings.
Loads environment variables and provides validated configuration objects.
"""

import logging
from functools import lru_cache
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    uses Pydantic for validation and type checking.
    Values are loaded from .env file or environment variables.
    """

    # Application Settings
    app_name: str = Field(default = "Personal AI Agent", description = "Application Name")
    app_version: str = Field(default = "1.0.0", description = "Application Version")
    debug_mode: bool = Field(default = False, description = "Enable Debug Mode")
    log_level: str = Field(default = "INFO", description = "Logging Level")

    # API Settings
    api_host: str = Field(default = "0.0.0.0", description = "API Host")
    api_port: int = Field(default = 8000, description = "API Port")

    # Database Settings
    database_url: str = Field(
        ...,
        description = "PostgreSQL Database URL",
        env = "DATABASE_URL"
    )

    # SendGrid Email Settings
    sendgrid_api_key: str = Field(..., description="SendGrid API key")
    sendgrid_from_email: str = Field(..., description="Email sender address")
    sendgrid_reply_to_email: str = Field(..., description="Reply-to email address")
    
    # Timezone Settings
    timezone: str = Field(
        default="America/New_York",
        description="Timezone for scheduling (e.g., America/New_York)"
    )
    
    # Webhook Settings
    webhook_secret: str = Field(..., description="Secret for webhook authentication")
    
    # GitHub Settings (optional global token)
    github_global_token: Optional[str] = Field(
        default=None,
        description="Global GitHub token (optional)"
    )
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is one of the standard levels."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v_upper
    
    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate database URL format."""
        if not v.startswith(("postgresql://", "postgresql+psycopg2://")):
            raise ValueError("database_url must be a PostgreSQL connection string")
        return v
    
    def configure_logging(self) -> None:
        """
        Configure application-wide logging.
        
        Sets up logging format, level, and handlers based on configuration.
        """
        log_format = (
            "%(asctime)s - %(name)s - %(levelname)s - "
            "%(filename)s:%(lineno)d - %(message)s"
        )
        
        logging.basicConfig(
            level=getattr(logging, self.log_level),
            format=log_format,
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        
        # Reduce noise from third-party libraries
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("sendgrid").setLevel(logging.WARNING)
        logging.getLogger("github").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Uses lru_cache to ensure only one Settings instance is created.
    This is the recommended way to access settings throughout the application.
    
    Returns:
        Settings: Cached settings instance
    """
    settings = Settings()
    settings.configure_logging()
    return settings


# Create a module-level logger
logger = logging.getLogger(__name__)