from functools import partial
from typing import Callable, Dict, List, Tuple

import pytest

from bot.fetching import lastfm


pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize(
    "func",
    [lastfm.get_playlist_api, lastfm.get_playlist_noapi, lastfm.get_playlist],
)
async def test_get_playlist(
    func: Callable, track_nums: List[int], keyphrase: str, bad_keyphrase: str
) -> None:
    for n in track_nums:
        res = await func(keyphrase, n)
        assert isinstance(res, list)
        assert len(res) == n
        assert all(isinstance(i, str) for i in res)
        assert all(i.startswith(f"{keyphrase} - ") for i in res)
    with pytest.raises(Exception):
        await func(bad_keyphrase)


async def test_playlists_equality(track_nums: List[int], keyphrase: str) -> None:
    for n in track_nums:
        res1 = await lastfm.get_playlist_api(keyphrase, n)
        res2 = await lastfm.get_playlist_noapi(keyphrase, n)
        assert res1 == res2


@pytest.mark.parametrize(
    "func, sections",
    [
        (lastfm.get_bio_api, ("Tags:", "Similar:", "Read more:")),
        (lastfm.get_bio_noapi, ("Similar:", "Read more:")),
        (lastfm.get_info, ("Similar:", "Read more:")),
    ],
)
async def test_get_info(
    func: Callable, sections: Tuple[str, ...], keyphrase: str, bad_keyphrase: str
) -> None:
    res = await func(keyphrase)
    assert isinstance(res, str)
    assert all(s in res for s in sections)
    with pytest.raises(Exception):
        await func(bad_keyphrase)


@pytest.mark.parametrize(
    "func",
    [
        pytest.param(
            partial(lastfm.get_bio_api, name_only=True),
            id="get_bio_api_name_only",
            marks=pytest.mark.xfail(
                reason="'autocorrect' parameter of artist.getinfo method of Last.fm API may work incorrectly",
                raises=RuntimeWarning,
            ),
        ),
        pytest.param(
            partial(lastfm.get_bio_noapi, name_only=True), id="get_bio_noapi_name_only"
        ),
        lastfm.get_corrected_name_api,
        lastfm.get_name,
    ],
)
async def test_get_name(
    func: Callable, name_corrections: Dict[str, str], bad_keyphrase: str
) -> None:
    for key in name_corrections:
        res = await func(key)
        assert isinstance(res, str)
        try:
            assert res == name_corrections[key]
        except AssertionError as e:
            raise RuntimeWarning from e
    with pytest.raises(Exception):
        await func(bad_keyphrase)
