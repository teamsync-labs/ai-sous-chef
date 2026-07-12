from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="app/.env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    APP_NAME: str = "AI Sous-Chef API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False


settings = Settings()
