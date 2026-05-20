from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest

from services.invite import InviteService


@pytest.fixture
def service() -> InviteService:
    return InviteService()


FIXED_NOW = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)
FIXED_EXPIRY = FIXED_NOW + timedelta(hours=24)


class TestGrantAccess:
    def test_adds_user_to_whitelist(self, service: InviteService) -> None:
        service.grant_access(123)

        assert service.has_access(123) is True

    def test_returns_expiry_datetime(self, service: InviteService) -> None:
        with patch("services.invite.datetime") as mock_dt:
            mock_dt.now.return_value = FIXED_NOW

            result = service.grant_access(123)

        assert result == FIXED_EXPIRY

    def test_returns_none_if_session_already_active(
        self, service: InviteService
    ) -> None:
        service.grant_access(123)
        result = service.grant_access(123)

        assert result is None

    def test_grants_access_after_expiry(self, service: InviteService) -> None:
        with patch("services.invite.datetime") as mock_dt:
            mock_dt.now.return_value = FIXED_NOW
            service.grant_access(123)

            mock_dt.now.return_value = FIXED_NOW + timedelta(hours=25)
            result = service.grant_access(123)

        assert result is not None


class TestHasAccess:
    def test_returns_true_for_active_session(self, service: InviteService) -> None:
        service.grant_access(123)

        assert service.has_access(123) is True

    def test_returns_false_for_missing_user(self, service: InviteService) -> None:
        assert service.has_access(999) is False

    def test_returns_false_for_expired_session(self, service: InviteService) -> None:
        with patch("services.invite.datetime") as mock_dt:
            mock_dt.now.return_value = FIXED_NOW
            service.grant_access(123)

            mock_dt.now.return_value = FIXED_NOW + timedelta(hours=25)

            assert service.has_access(123) is False

    def test_cleans_up_expired_session(self, service: InviteService) -> None:
        with patch("services.invite.datetime") as mock_dt:
            mock_dt.now.return_value = FIXED_NOW
            service.grant_access(123)

            mock_dt.now.return_value = FIXED_NOW + timedelta(hours=25)
            service.has_access(123)

        assert 123 not in service._sessions


class TestEnableDisable:
    def test_enabled_by_default(self, service: InviteService) -> None:
        assert service.is_enabled() is True

    def test_disable(self, service: InviteService) -> None:
        service.disable()

        assert service.is_enabled() is False

    def test_enable_after_disable(self, service: InviteService) -> None:
        service.disable()
        service.enable()

        assert service.is_enabled() is True

    def test_disable_does_not_revoke_active_sessions(
        self, service: InviteService
    ) -> None:
        service.grant_access(123)
        service.disable()

        assert service.has_access(123) is True
