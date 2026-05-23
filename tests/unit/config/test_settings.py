import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError
from pydantic_settings import SettingsConfigDict

from config.settings import Settings


def make_settings(**kwargs) -> Settings:
    """Instantiate Settings without reading .env file."""
    with (
        patch.object(Settings, "model_config", SettingsConfigDict(env_file=None)),
        patch.dict(os.environ, {}, clear=True),
    ):
        return Settings(**kwargs)


BASE_VALID = {
    "bot_token": "tok",
    "owner_user_id": 1,
    "invite_token": "t",
    "pixeldrain_api_key": "k",
}


class TestAllowedUserIdsParsing:
    def test_json_array_string(self):
        s = make_settings(**BASE_VALID, allowed_user_ids="[123456789]")
        assert s.allowed_user_ids == [123456789]

    def test_json_array_multiple_ids(self):
        s = make_settings(**BASE_VALID, allowed_user_ids="[123456789, 987654321]")
        assert s.allowed_user_ids == [123456789, 987654321]

    def test_already_a_list(self):
        s = make_settings(**BASE_VALID, allowed_user_ids=[123456789])
        assert s.allowed_user_ids == [123456789]

    def test_empty_default(self):
        s = make_settings(**BASE_VALID)
        assert s.allowed_user_ids == []

    def test_invalid_value_raises(self):
        with pytest.raises((ValidationError, Exception)):
            make_settings(**BASE_VALID, allowed_user_ids="[not_a_number]")


class TestRequiredFields:
    def test_missing_bot_token_raises(self):
        data = {k: v for k, v in BASE_VALID.items() if k != "bot_token"}
        with pytest.raises(ValidationError):
            make_settings(**data)

    def test_missing_pixeldrain_api_key_raises(self):
        data = {k: v for k, v in BASE_VALID.items() if k != "pixeldrain_api_key"}
        with pytest.raises(ValidationError):
            make_settings(**data)

    def test_missing_invite_token_raises(self):
        data = {k: v for k, v in BASE_VALID.items() if k != "invite_token"}
        with pytest.raises(ValidationError):
            make_settings(**data)


class TestDefaults:
    def test_max_file_size_mb_default(self):
        s = make_settings(**BASE_VALID)
        assert s.max_file_size_mb == 50

    def test_pixeldrain_timeout_sec_default(self):
        s = make_settings(**BASE_VALID)
        assert s.pixeldrain_timeout_sec == 60

    def test_temp_dir_default(self):
        s = make_settings(**BASE_VALID)
        assert s.temp_dir == "temp"
