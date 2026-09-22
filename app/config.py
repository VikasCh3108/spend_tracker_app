from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_SECRET_KEY = "dev-secret-key-change-in-production"


class Settings(BaseSettings):
    """Application settings loaded from environment variables with sensible defaults."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Database
    database_url: str = "sqlite:///./spend_tracker.db"

    # JWT
    secret_key: str = DEFAULT_SECRET_KEY
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # App
    app_name: str = "Spend Tracker API"
    debug: bool = False


settings = Settings()
