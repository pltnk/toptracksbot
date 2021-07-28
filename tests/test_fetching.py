import os

import pytest

if (
    "TTBOT_LASTFM_API_KEY" not in os.environ
    or "TTBOT_YOUTUBE_API_KEY" not in os.environ
):
    import dotenv

    dotenv.load_dotenv("../.env")

from bot import fetching


NUMBERS = (0, 1, 3, 5)
KEYPHRASE = "Nirvana"
PLAYLIST = [
    "Nirvana - Smells Like Teen Spirit",
    "Nirvana - Come As You Are",
    "Nirvana - Lithium",
]
CORRECTIONS = {
    "norvana": "Nirvana",
    "slipnot": "Slipknot",
    "sustem of a down": "System of a Down",
}

pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize("func", [fetching.get_playlist_api, fetching.get_playlist])
async def test_get_playlist(func):
    for n in NUMBERS:
        res = await func(KEYPHRASE, n)
        assert isinstance(res, list)
        assert len(res) == n
        assert all(isinstance(i, str) for i in res)
        assert all(i.startswith(f"{KEYPHRASE} - ") for i in res)


@pytest.mark.parametrize("func", [fetching.fetch_ids_api, fetching.fetch_ids])
async def test_fetch_ids(func):
    res = await func(PLAYLIST)
    assert isinstance(res, list)
    assert len(res) == len(PLAYLIST)
    assert all(isinstance(i, str) for i in res)


async def test_create_top():
    for n in NUMBERS:
        res = await fetching.create_top(KEYPHRASE, n)
        assert isinstance(res, list)
        assert len(res) == n
        assert all(isinstance(i, str) for i in res)


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


@pytest.mark.parametrize("func", [fetching.get_corrected_name_api, fetching.get_name])
async def test_get_name(func):
    for key in CORRECTIONS:
        res = await func(key)
        assert isinstance(res, str)
        assert res == CORRECTIONS[key]
    with pytest.raises(Exception):
        await func("random text that is no way a band name")


async def test_get_info():
    res = await fetching.get_info(KEYPHRASE)
    assert isinstance(res, str)
    sections = ("Similar:", "Read more:")
    assert all(s in res for s in sections)