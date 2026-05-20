from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    bot_token: str
    owner_user_id: int
    allowed_user_ids: list[int] = []
    invite_token: str
    webhook_url: str = ""

    temp_dir: str = "temp"
    max_file_size_mb: int = 50
    max_video_duration_sec: int = 10800

    pixeldrain_timeout_sec: int = 60
    pixeldrain_api_key: str

    @field_validator("bot_token")
    @classmethod
    def bot_token_must_not_be_empty(cls, v: str) -> str:
        if not v:
            raise ValueError("BOT_TOKEN environment variable is not set")
        return v

    @field_validator("pixeldrain_api_key")
    @classmethod
    def pixeldrain_api_key_must_not_be_empty(cls, v: str) -> str:
        if not v:
            raise ValueError("PIXELDRAIN_API_KEY environment variable is not set")
        return v

    @field_validator("invite_token")
    @classmethod
    def invite_token_must_not_be_empty(cls, v: str) -> str:
        if not v:
            raise ValueError("INVITE_TOKEN environment variable is not set")
        return v


settings = Settings()
