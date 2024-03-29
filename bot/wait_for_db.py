import asyncio

import asyncpg

from bot.config import DATABASE_URI, DBCONN_RETRIES, DBCONN_TIMEOUT


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
            print(f"Postgres is unavailable: {repr(e)}, waiting for {timeout} seconds")
            await asyncio.sleep(timeout)
        else:
            print("Postgres is ready")
            await conn.close()
            break


def main() -> None:
    asyncio.run(ping_db(DATABASE_URI, DBCONN_RETRIES, DBCONN_TIMEOUT))


if __name__ == "__main__":
    main()  # pragma: no cover
