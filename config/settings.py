from pydantic import Json, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    bot_token: str
    owner_user_id: int
    allowed_user_ids: Json[list[int]] | list[int] = []
    invite_token: str
    webhook_url: str = ""

    temp_dir: str = "temp"
    max_file_size_mb: int = 50

    pixeldrain_timeout_sec: int = 60
    pixeldrain_api_key: str

    @field_validator("allowed_user_ids", mode="before")
    @classmethod
    def parse_allowed_user_ids(cls, v: object) -> object:
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            stripped = v.strip()
            if stripped.startswith("["):
                return json.loads(stripped)
            return [int(x.strip()) for x in stripped.split(",") if x.strip()]
        if isinstance(v, int):
            return [v]
        return v

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
