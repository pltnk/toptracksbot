import json

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
async def test_get_yt_id(func, playlist, expected_yt_ids, bad_keyphrase):
    for counter, track in enumerate(playlist):
        res = await func(track)
        assert res == expected_yt_ids[counter]
    with pytest.raises(Exception):
        await func(bad_keyphrase)


async def test_get_yt_ids(playlist, expected_yt_ids):
    res = await youtube.get_yt_ids(playlist)
    assert isinstance(res, list)
    assert len(res) == len(playlist)
    assert all(isinstance(i, str) for i in res)
    json.dumps(res)
    assert res == expected_yt_ids
