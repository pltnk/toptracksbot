import datetime

import pytest

from bot import wait_for_db


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "db_uri, retries, timeout",
    [
        (
            wait_for_db.DATABASE_URI,
            wait_for_db.DBCONN_RETRIES,
            wait_for_db.DBCONN_TIMEOUT,
        ),
        ("invalid URI", 3, 1),
    ],
)
async def test_ping_db(db_uri: str, retries: int, timeout: int) -> None:
    start = datetime.datetime.now()
    await wait_for_db.ping_db(db_uri, retries, timeout)
    end = datetime.datetime.now()
    passed = (end - start).seconds
    assert passed <= retries * timeout


def test_main() -> None:
    wait_for_db.main()
