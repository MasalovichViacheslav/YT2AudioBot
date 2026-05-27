import sys

from loguru import logger


def log_memory(label: str) -> None:
    rss_mb: float = -1.0
    available_mb: float = -1.0
    used_mb: float = -1.0

    if sys.platform != "win32":
        try:
            import resource

            rss_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
        except Exception:
            pass

        try:
            meminfo: dict[str, int] = {}
            with open("/proc/meminfo") as f:
                for line in f:
                    key = line.split(":")[0]
                    val = int(line.split()[1])
                    meminfo[key] = val
            available_mb = meminfo["MemAvailable"] / 1024
            used_mb = (meminfo["MemTotal"] - meminfo["MemAvailable"]) / 1024
        except Exception:
            pass

    logger.info(
        f"[{label}] rss={rss_mb:.0f}MB | "
        f"sys_used={used_mb:.0f}MB | "
        f"sys_available={available_mb:.0f}MB"
    )
