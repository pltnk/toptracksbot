import datetime
import os

import pytest

from bot import wait_for_db


DATABASE_URI = os.environ["TTBOT_DATABASE_URI"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "db_uri, retries, timeout",
    [
        (DATABASE_URI, wait_for_db.RETRIES, wait_for_db.TIMEOUT),
        ("invalid URI", wait_for_db.RETRIES, wait_for_db.TIMEOUT),
    ],
)
async def test_ping_db(db_uri: str, retries: int, timeout: int):
    start = datetime.datetime.now()
    await wait_for_db.ping_db(db_uri, retries, timeout)
    end = datetime.datetime.now()
    passed = (end - start).seconds
    assert passed <= retries * timeout


def test_main():
    wait_for_db.main()
