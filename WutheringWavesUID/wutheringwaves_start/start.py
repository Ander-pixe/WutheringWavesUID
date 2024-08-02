import asyncio
import threading

from gsuid_core.logger import logger


async def startup():
    pass


async def all_start():
    try:
        await startup()
    except Exception as e:
        logger.exception(e)


threading.Thread(
    target=lambda: asyncio.run(all_start()),
    daemon=True,
).start()
