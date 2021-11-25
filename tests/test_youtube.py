import json
from typing import Callable, List

import pytest

from bot.fetching import youtube


pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize(
    "func",
    [
        pytest.param(
            youtube.get_yt_id_api,
            marks=pytest.mark.xfail(
                reason="YouTube API quota may reach the limit", raises=ResourceWarning
            ),
        ),
        youtube.get_yt_id_noapi,
        youtube.get_yt_id,
    ],
)
async def test_get_yt_id(
    func: Callable, playlist: List[str], expected_yt_ids: List[str], bad_keyphrase: str
) -> None:
    for counter, track in enumerate(playlist):
        res = await func(track)
        assert res == expected_yt_ids[counter]
    with pytest.raises(Exception):
        await func(None)


async def test_get_yt_ids(playlist: List[str], expected_yt_ids: List[str]) -> None:
    res = await youtube.get_yt_ids(playlist)
    assert isinstance(res, list)
    assert len(res) == len(playlist)
    assert all(isinstance(i, str) for i in res)
    json.dumps(res)
    assert res == expected_yt_ids
