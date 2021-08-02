import datetime
import json
import os

import asyncpg
import pytest

from bot import storing


DATABASE_URI = os.environ["TTBOT_DATABASE_URI"]
INIT_SQL_PATH = "./db/init.sql"
KEYPHRASE = "Nirvana"
IDS_NUM = 3

pytestmark = pytest.mark.asyncio


@pytest.fixture(scope="function")
async def db_conn():
    conn = await asyncpg.connect(dsn=DATABASE_URI)
    with open(INIT_SQL_PATH, "r") as f:
        query = f.read()
    await conn.execute(query)
    yield conn
    await conn.close()


async def test_get_artist():
    cases = {
        "Norvana": "nirvana",
        "Slipnot": "slipknot",
        "Sustem Of A Down": "system of a down",
        "Random Text That Is No Way A Band Name": "random text that is no way a band name",
    }
    for key in cases:
        res = await storing.get_artist(key)
        assert res == cases[key]


async def test_process(db_conn):
    res = await storing.process(KEYPHRASE)
    assert isinstance(res, list)
    assert len(res) == IDS_NUM
    assert all(isinstance(i, str) for i in res)


async def test_create_record(db_conn):
    keyphrase = KEYPHRASE.lower()
    record = await db_conn.fetchrow("SELECT * FROM top WHERE artist = $1", keyphrase)
    assert record is None
    await storing.process(KEYPHRASE)
    record = await db_conn.fetchrow("SELECT * FROM top WHERE artist = $1", keyphrase)
    assert record
    assert all(col in record for col in ("artist", "tracks", "date", "requests"))
    assert record["artist"] == keyphrase
    tracks = json.loads(record["tracks"])
    assert isinstance(tracks, list)
    assert len(tracks) == 3
    assert all(isinstance(t, str) for t in tracks)
    assert record["date"] == datetime.datetime.now().date()
    assert record["requests"] == 1


async def test_update_record(db_conn):
    keyphrase = KEYPHRASE.lower()
    old_date = (
        datetime.datetime.now() - datetime.timedelta(days=storing.VALID_FOR_DAYS + 1)
    ).date()
    mock_tracks = ["a", "b", "c"]
    mock_tracks_json = json.dumps(mock_tracks)
    await db_conn.execute(
        "INSERT INTO top (artist, tracks, date, requests) VALUES ($1, $2, $3, 1)",
        keyphrase,
        mock_tracks_json,
        old_date,
    )
    record = await db_conn.fetchrow("SELECT * FROM top WHERE artist = $1", keyphrase)
    assert record
    assert record["artist"] == keyphrase
    assert record["tracks"] == mock_tracks_json
    assert record["date"] == old_date
    assert record["requests"] == 1
    real_tracks = await storing.process(KEYPHRASE)
    record = await db_conn.fetchrow("SELECT * FROM top WHERE artist = $1", keyphrase)
    assert record
    assert record["artist"] == keyphrase
    assert record["tracks"] != mock_tracks_json
    assert record["date"] == datetime.datetime.now().date()
    assert record["requests"] == 2
    assert real_tracks != mock_tracks


async def test_find_record(db_conn):
    keyphrase = KEYPHRASE.lower()
    mock_tracks = ["a", "b", "c"]
    mock_tracks_json = json.dumps(mock_tracks)
    today = datetime.datetime.now().date()
    await db_conn.execute(
        "INSERT INTO top (artist, tracks, date, requests) VALUES ($1, $2, $3, 1)",
        keyphrase,
        mock_tracks_json,
        today,
    )
    res = await storing.process(KEYPHRASE)
    assert res == mock_tracks
    record = await db_conn.fetchrow("SELECT * FROM top WHERE artist = $1", keyphrase)
    assert record
    assert record["artist"] == keyphrase
    assert record["tracks"] == mock_tracks_json
    assert record["date"] == today
    assert record["requests"] == 2
