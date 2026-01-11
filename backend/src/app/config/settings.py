from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    APP_NAME: str = "MagicBox"
    ENV: str = Field(default="development", description="environment name")

    # Database
    DATABASE_URL: str = Field(
        default="sqlite:///./dev.db",
        description="Database connection string",
    )

    # Auth
    JWT_SECRET: str = Field(
        default="dev-secret-change-me",
        description="JWT signing secret",
    )
    JWT_ALGORITHM: str = "HS256"
    
    # AI Services
    GEMINI_API_KEY: str = Field(
        default="",
        description="Google Gemini API key for AI content generation",
    )

    # Public URLs (used for OAuth redirects)
    BACKEND_PUBLIC_URL: str = Field(
        default="http://localhost:8000",
        description="Publicly reachable backend base URL (for OAuth redirect_uri)",
    )
    FRONTEND_PUBLIC_URL: str = Field(
        default="http://localhost:8080",
        description="Publicly reachable frontend base URL (for OAuth post-redirect)",
    )

    # Encryption (for storing OAuth tokens at rest)
    ENCRYPTION_KEY: str = Field(
        default="",
        description="Fernet key (urlsafe base64) used to encrypt tokens at rest",
    )
    
    # Social Media API Keys (will be stored per-tenant in database, but defaults here)
    FACEBOOK_APP_ID: str = Field(default="", description="Facebook App ID")
    FACEBOOK_APP_SECRET: str = Field(default="", description="Facebook App Secret")
    INSTAGRAM_CLIENT_ID: str = Field(default="", description="Instagram Client ID")
    INSTAGRAM_CLIENT_SECRET: str = Field(default="", description="Instagram Client Secret")
    YOUTUBE_CLIENT_ID: str = Field(default="", description="YouTube Client ID")
    YOUTUBE_CLIENT_SECRET: str = Field(default="", description="YouTube Client Secret")
    LINKEDIN_CLIENT_ID: str = Field(default="", description="LinkedIn Client ID")
    LINKEDIN_CLIENT_SECRET: str = Field(default="", description="LinkedIn Client Secret")
    TWITTER_API_KEY: str = Field(default="", description="Twitter/X API Key")
    TWITTER_API_SECRET: str = Field(default="", description="Twitter/X API Secret")
    TIKTOK_CLIENT_KEY: str = Field(default="", description="TikTok Client Key")
    TIKTOK_CLIENT_SECRET: str = Field(default="", description="TikTok Client Secret")
    
    # WhatsApp Notifications (Twilio)
    TWILIO_ACCOUNT_SID: str = Field(default="", description="Twilio Account SID for WhatsApp")
    TWILIO_AUTH_TOKEN: str = Field(default="", description="Twilio Auth Token")
    TWILIO_WHATSAPP_NUMBER: str = Field(default="", description="Twilio WhatsApp number (format: whatsapp:+1234567890)")
    
    # Celery (Background Jobs) - RabbitMQ
    CELERY_BROKER_URL: str = Field(
        default="amqp://guest:guest@localhost:5672//",
        description="Celery broker URL (RabbitMQ AMQP)"
    )
    CELERY_RESULT_BACKEND: str = Field(
        default="rpc://",
        description="Celery result backend (RPC for RabbitMQ)"
    )

    # ---- Validation for prod ----
    def model_post_init(self, __context):
        if self.ENV == "production":
            if self.JWT_SECRET == "dev-secret-change-me":
                raise ValueError("JWT_SECRET must be set in production")
            if self.DATABASE_URL.startswith("sqlite"):
                raise ValueError("DATABASE_URL must not be sqlite in production")
            if not self.ENCRYPTION_KEY:
                raise ValueError("ENCRYPTION_KEY must be set in production")


settings = Settings()
