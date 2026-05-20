from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from loguru import logger

from bot.middleware import WhitelistMiddleware
from bot.routers import audio
from config.settings import settings

WEBHOOK_PATH = "/webhook"


async def on_startup(bot: Bot) -> None:
    if settings.webhook_url:
        await bot.set_webhook(f"{settings.webhook_url}{WEBHOOK_PATH}")
        logger.info(f"Webhook set to {settings.webhook_url}{WEBHOOK_PATH}")
    else:
        logger.warning("WEBHOOK_URL is not set, skipping webhook registration")


async def on_shutdown(bot: Bot) -> None:
    if settings.webhook_url:
        await bot.delete_webhook()
        logger.info("Webhook deleted")


async def health(request: web.Request) -> web.Response:
    return web.Response(text="OK")


def main() -> None:
    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()

    dp.message.middleware(WhitelistMiddleware())
    dp.callback_query.middleware(WhitelistMiddleware())

    dp.include_router(audio.router)

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    app = web.Application()
    app.router.add_get("/health", health)

    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)

    web.run_app(app, host="0.0.0.0", port=8080)


if __name__ == "__main__":
    main()
