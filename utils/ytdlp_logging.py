from loguru import logger


class YtDlpLogger:
    """Forward yt-dlp log messages to loguru.

    yt-dlp accepts any object with debug/info/warning/error methods
    via the `logger` option in its params. Passing an instance of this
    class makes yt-dlp output (including warnings that are normally
    suppressed by `no_warnings`) appear in the application logs.
    """

    def debug(self, msg: str) -> None:
        # yt-dlp routes both its debug messages (prefixed with "[debug] ")
        # and regular informational messages (no prefix) through this method.
        # Split them so real debug output stays at DEBUG level.
        if msg.startswith("[debug] "):
            logger.debug("yt-dlp: {}", msg.removeprefix("[debug] "))
        else:
            logger.info("yt-dlp: {}", msg)

    def info(self, msg: str) -> None:
        logger.info("yt-dlp: {}", msg)

    def warning(self, msg: str) -> None:
        logger.warning("yt-dlp warning: {}", msg)

    def error(self, msg: str) -> None:
        logger.error("yt-dlp error: {}", msg)
