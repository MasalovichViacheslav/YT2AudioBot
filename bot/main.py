import asyncio

from aiohttp import web
from loguru import logger


async def health(request: web.Request) -> web.Response:
    return web.Response(text="OK")


async def main() -> None:
    logger.info("YT2AudioBot starting...")

    app = web.Application()
    app.router.add_get("/health", health)

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, host="0.0.0.0", port=8080)
    await site.start()

    logger.info("Health endpoint started on port 8080")

    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
