from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or .env file.
    
    Purpose:
    - Keeps sensitive data (secrets, passwords) out of code
    - Different settings for dev/staging/production
    - Easy to change configuration without code changes
    """

    #define the default values
    # Database Configuration
    database_url: str = "postgresql://postgres:postgres@localhost:5432/mfa_auth_db"
    
    # JWT Token Configuration
    jwt_secret: str = "your-super-secret-jwt-key-change-this-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_seconds: int = 3600  # 1 hour
    
    # Temporary token for MFA verification (shorter lived)
    temp_token_expiration_seconds: int = 300  # 5 minutes
    
    # Encryption key for TOTP secrets (must be Fernet-compatible)
    encryption_key: str = "your-fernet-encryption-key-change-this"
    
    # Application Settings
    app_name: str = "MFA Token Authenticator"
    debug: bool = True
    
    # CORS Settings
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    # Rate Limiting
    rate_limit_per_minute: int = 5
    
    # Tell Pydantic to load from .env file
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


#REMEBER TO DISABLE THIS AND DO AN A/B TEST ON PERFORMANCE
@lru_cache
def get_settings() -> Settings:
    """
    Create a cached instance of settings.
    
    Why @lru_cache?
    - Settings are loaded once and reused
    - Avoids reading .env file on every request
    - Improves performance
    """
    return Settings()