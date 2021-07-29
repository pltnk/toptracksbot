import asyncio
import os

import asyncpg

from bot.storing import DATABASE_URI


RETRIES = int(os.getenv("TTBOT_DBCONN_RETRIES", 5))
TIMEOUT = int(os.getenv("TTBOT_DBCONN_TIMEOUT", 5))


async def ping_db() -> None:
    """Check if database is available."""
    for i in range(RETRIES):
        try:
            conn = await asyncpg.connect(dsn=DATABASE_URI)
        except Exception as e:
            print(f"Postgres is unavailable: {repr(e)}")
            print(f"Sleeping for {TIMEOUT} seconds")
            await asyncio.sleep(TIMEOUT)
        else:
            print("Postgres is ready")
            await conn.close()
            break


if __name__ == "__main__":
    asyncio.run(ping_db())
