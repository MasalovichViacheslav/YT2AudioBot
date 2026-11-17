import urllib.request

from loguru import logger


def get_egress_ip(timeout: float = 3.0) -> str:
    """Return the public IP address used for outgoing requests.

    Uses api64.ipify.org: it answers over IPv6 when the host has an IPv6
    route and falls back to IPv4 otherwise, so the result also reveals
    whether the container talks to the internet over IPv6.
    Never raises: on any failure returns "unknown".
    """
    try:
        with urllib.request.urlopen("https://api64.ipify.org", timeout=timeout) as resp:
            body: str = resp.read().decode()
        return body.strip()[:64]
    except Exception as e:
        logger.warning("Could not determine egress IP: {}", e)
        return "unknown"
