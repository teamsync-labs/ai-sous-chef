from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    APP_NAME: str = "AI Sous-Chef API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    DATABASE_URL: str = ""

    YANDEX_API_KEY: str = ""
    YANDEX_FOLDER_ID: str = ""

    AI_MODE: Literal["stub", "real"] = "stub"

    CONSENT_JOURNAL_URL: str = Field(min_length=1)
    CONSENT_JOURNAL_API_KEY: str = Field(min_length=1)
    CONSENT_PUBLIC_BASE: str = Field(min_length=1)
    API_KEY_BOT: str = Field(min_length=1)
    API_KEY_APP: str = Field(min_length=1)
    API_KEY_SITE: str = Field(min_length=1)


settings = Settings()
