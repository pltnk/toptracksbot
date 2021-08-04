import datetime
import json

import pytest

from bot import processing
from bot.exceptions import PlaylistRetrievalError


pytestmark = pytest.mark.asyncio


async def test_get_artist(get_artist_cases):
    for key in get_artist_cases:
        res = await processing.get_artist(key)
        assert res == get_artist_cases[key]


async def test_create_top(track_nums, keyphrase, bad_keyphrase):
    for n in track_nums:
        res = await processing.create_top(keyphrase, n)
        assert isinstance(res, list)
        assert len(res) == n
        assert all(isinstance(i, str) for i in res)
        json.dumps(res)
    with pytest.raises(PlaylistRetrievalError):
        await processing.create_top(bad_keyphrase)


async def test_get_top(db_conn, keyphrase, yt_ids_num):
    res = await processing.get_top(keyphrase)
    assert isinstance(res, list)
    assert len(res) == yt_ids_num
    assert all(isinstance(i, str) for i in res)


async def test_create_record(db_conn, keyphrase):
    keyphrase_low = keyphrase.lower()
    record = await db_conn.fetchrow(
        "SELECT * FROM top WHERE artist = $1", keyphrase_low
    )
    assert record is None
    await processing.get_top(keyphrase)
    record = await db_conn.fetchrow(
        "SELECT * FROM top WHERE artist = $1", keyphrase_low
    )
    assert record
    assert all(col in record for col in ("artist", "tracks", "date", "requests"))
    assert record["artist"] == keyphrase_low
    tracks = json.loads(record["tracks"])
    assert isinstance(tracks, list)
    assert len(tracks) == 3
    assert all(isinstance(t, str) for t in tracks)
    assert record["date"] == datetime.datetime.now().date()
    assert record["requests"] == 1


async def test_update_record(db_conn, keyphrase):
    keyphrase_low = keyphrase.lower()
    old_date = (
        datetime.datetime.now() - datetime.timedelta(days=processing.VALID_FOR_DAYS + 1)
    ).date()
    mock_tracks = ["a", "b", "c"]
    mock_tracks_json = json.dumps(mock_tracks)
    await db_conn.execute(
        "INSERT INTO top (artist, tracks, date, requests) VALUES ($1, $2, $3, 1)",
        keyphrase_low,
        mock_tracks_json,
        old_date,
    )
    record = await db_conn.fetchrow(
        "SELECT * FROM top WHERE artist = $1", keyphrase_low
    )
    assert record
    assert record["artist"] == keyphrase_low
    assert record["tracks"] == mock_tracks_json
    assert record["date"] == old_date
    assert record["requests"] == 1
    real_tracks = await processing.get_top(keyphrase)
    record = await db_conn.fetchrow(
        "SELECT * FROM top WHERE artist = $1", keyphrase_low
    )
    assert record
    assert record["artist"] == keyphrase_low
    assert record["tracks"] != mock_tracks_json
    assert record["date"] == datetime.datetime.now().date()
    assert record["requests"] == 2
    assert real_tracks != mock_tracks


async def test_find_record(db_conn, keyphrase):
    keyphrase_low = keyphrase.lower()
    mock_tracks = ["a", "b", "c"]
    mock_tracks_json = json.dumps(mock_tracks)
    today = datetime.datetime.now().date()
    await db_conn.execute(
        "INSERT INTO top (artist, tracks, date, requests) VALUES ($1, $2, $3, 1)",
        keyphrase_low,
        mock_tracks_json,
        today,
    )
    res = await processing.get_top(keyphrase)
    assert res == mock_tracks
    record = await db_conn.fetchrow(
        "SELECT * FROM top WHERE artist = $1", keyphrase_low
    )
    assert record
    assert record["artist"] == keyphrase_low
    assert record["tracks"] == mock_tracks_json
    assert record["date"] == today
    assert record["requests"] == 2
