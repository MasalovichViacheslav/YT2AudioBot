from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    bot_token: str = ""

    temp_dir: str = "temp"
    max_file_size_mb: int = 50

    @field_validator("bot_token")
    @classmethod
    def bot_token_must_not_be_empty(cls, v: str) -> str:
        if not v:
            raise ValueError("BOT_TOKEN environment variable is not set")
        return v


settings = Settings()
