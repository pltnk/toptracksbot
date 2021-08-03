import json
import uuid

import pytest

from bot import fetching
from bot.exceptions import PlaylistError


NUMBERS = (0, 1, 3)
KEYPHRASE = "Nirvana"
BAD_KEYPHRASE = "".join(str(uuid.uuid4()) for _ in range(10))
PLAYLIST = [
    "Nirvana - Smells Like Teen Spirit",
    "Nirvana - Come As You Are",
    "Nirvana - Lithium",
]
YT_IDS = ["hTWKbfoikeg", "vabnZ9-ex7o", "pkcJEvMcnEg"]
CORRECTIONS = {
    "norvana": "Nirvana",
    "slipnot": "Slipknot",
    "sustem of a down": "System of a Down",
    "author and punisher": "Author & Punisher",
}

pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize(
    "func",
    [fetching.get_playlist_api, fetching.get_playlist_noapi, fetching.get_playlist],
)
async def test_get_playlist(func):
    for n in NUMBERS:
        res = await func(KEYPHRASE, n)
        assert isinstance(res, list)
        assert len(res) == n
        assert all(isinstance(i, str) for i in res)
        assert all(i.startswith(f"{KEYPHRASE} - ") for i in res)
    with pytest.raises(Exception):
        await func(BAD_KEYPHRASE)


async def test_playlists_equality():
    for n in NUMBERS:
        res1 = await fetching.get_playlist_api(KEYPHRASE, n)
        res2 = await fetching.get_playlist_noapi(KEYPHRASE, n)
        assert res1 == res2


@pytest.mark.parametrize(
    "func",
    [
        pytest.param(
            fetching.get_yt_id_api,
            marks=pytest.mark.xfail(
                reason="YouTube API quota may reach the limit", raises=ResourceWarning
            ),
        ),
        fetching.get_yt_id_noapi,
        fetching.get_yt_id,
    ],
)
async def test_get_yt_id(func):
    for counter, track in enumerate(PLAYLIST):
        res = await func(track)
        assert res == YT_IDS[counter]
    with pytest.raises(Exception):
        await func(BAD_KEYPHRASE)


async def test_get_yt_ids():
    res = await fetching.get_yt_ids(PLAYLIST)
    assert isinstance(res, list)
    assert len(res) == len(PLAYLIST)
    assert all(isinstance(i, str) for i in res)
    json.dumps(res)
    assert res == YT_IDS


async def test_create_top():
    for n in NUMBERS:
        res = await fetching.create_top(KEYPHRASE, n)
        assert isinstance(res, list)
        assert len(res) == n
        assert all(isinstance(i, str) for i in res)
        json.dumps(res)
    with pytest.raises(PlaylistError):
        await fetching.create_top(BAD_KEYPHRASE)


@pytest.mark.parametrize(
    "func, sections",
    [
        (fetching.get_bio_api, ("Tags:", "Similar:", "Read more:")),
        (fetching.get_bio, ("Similar:", "Read more:")),
    ],
)
async def test_get_bio(func, sections):
    res = await func(KEYPHRASE, name_only=True)
    assert isinstance(res, str)
    assert res == KEYPHRASE
    res = await func(KEYPHRASE)
    assert isinstance(res, str)
    assert all(s in res for s in sections)
    with pytest.raises(Exception):
        await func(BAD_KEYPHRASE)


@pytest.mark.parametrize("func", [fetching.get_corrected_name_api, fetching.get_name])
async def test_get_name(func):
    for key in CORRECTIONS:
        res = await func(key)
        assert isinstance(res, str)
        assert res == CORRECTIONS[key]
    with pytest.raises(Exception):
        await func(BAD_KEYPHRASE)


async def test_get_info():
    res = await fetching.get_info(KEYPHRASE)
    assert isinstance(res, str)
    sections = ("Similar:", "Read more:")
    assert all(s in res for s in sections)
    with pytest.raises(Exception):
        await fetching.get_info(BAD_KEYPHRASE)
