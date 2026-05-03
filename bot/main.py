import asyncio

from loguru import logger


async def main() -> None:
    logger.info("YT2AudioBot starting...")


if __name__ == "__main__":
    asyncio.run(main())
