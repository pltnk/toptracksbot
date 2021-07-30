import asyncio
import os

import asyncpg

from bot.storing import DATABASE_URI


RETRIES = int(os.getenv("TTBOT_DBCONN_RETRIES", 5))
TIMEOUT = int(os.getenv("TTBOT_DBCONN_TIMEOUT", 5))


async def ping_db(db_uri: str, retries: int, timeout: int) -> None:
    """
    Check if database is available.
    :param db_uri: URI of a database to ping.
    :param retries: Max number of retries.
    :param timeout: Timeout between retries in seconds.
    """
    for _ in range(retries):
        try:
            conn = await asyncpg.connect(dsn=db_uri)
        except Exception as e:
            print(f"Postgres is unavailable: {repr(e)}")
            print(f"Sleeping for {timeout} seconds")
            await asyncio.sleep(timeout)
        else:
            print("Postgres is ready")
            await conn.close()
            break


def main() -> None:
    asyncio.run(ping_db(DATABASE_URI, RETRIES, TIMEOUT))


if __name__ == "__main__":
    main()  # pragma: no cover
