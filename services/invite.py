from datetime import UTC, datetime, timedelta

from loguru import logger


class InviteService:
    """Manages temporary access sessions granted via invite link."""

    ACCESS_DURATION_HOURS = 24

    def __init__(self) -> None:
        self._sessions: dict[int, datetime] = {}
        self._enabled: bool = True

    def grant_access(self, user_id: int) -> datetime | None:
        """Grant temporary access for a user if not already active.

        Args:
            user_id: Telegram user ID.

        Returns:
            Datetime (UTC) when the access expires, or None if access
            was already active (no changes made).
        """
        if self.has_access(user_id):
            return None

        expires_at = datetime.now(UTC) + timedelta(hours=self.ACCESS_DURATION_HOURS)
        self._sessions[user_id] = expires_at
        logger.info(
            f"Temporary access granted: user_id={user_id}, expires={expires_at}"
        )
        return expires_at

    def has_access(self, user_id: int) -> bool:
        """Check whether a user has an active temporary session.

        Args:
            user_id: Telegram user ID.

        Returns:
            True if the user has a non-expired session, False otherwise.
        """
        expires_at = self._sessions.get(user_id)
        if expires_at is None:
            return False
        if datetime.now(UTC) >= expires_at:
            logger.debug(f"Temporary access expired: user_id={user_id}")
            del self._sessions[user_id]
            return False
        return True

    def is_enabled(self) -> bool:
        """Return whether invite access is currently accepting new users."""
        return self._enabled

    def enable(self) -> None:
        """Enable invite access for new users."""
        self._enabled = True
        logger.info("Invite access enabled")

    def disable(self) -> None:
        """Disable invite access for new users (existing sessions unaffected)."""
        self._enabled = False
        logger.info("Invite access disabled")
