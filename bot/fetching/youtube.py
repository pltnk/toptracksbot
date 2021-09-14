"""
This module is a part of Top Tracks Bot for Telegram
and is licensed under the MIT License.
Copyright (c) 2019-2021 Kirill Plotnikov
GitHub: https://github.com/pltnk/toptracksbot
"""


import asyncio
import json
import logging
import re
from typing import List

import httpx

from bot.config import YOUTUBE_API_KEY
from bot.fetching.util import _quote


YOUTUBE_REGEXP = re.compile("var ytInitialData = (?P<json>{.+});<")

logger = logging.getLogger("youtube")
logger.setLevel(logging.DEBUG)


async def get_yt_id_api(track: str) -> str:
    """
    Get YouTube video ID for a track using YouTube API.
    :param track: Track title formatted as '<artist> - <track>'.
    :return: Corresponding YouTube video ID.
    :raise ResourceWarning: if API quota hit the limit.
    :raise Exception: if unable to get ID via API.
    """
    async with httpx.AsyncClient() as client:
        res = await client.get(
            f"https://www.googleapis.com/youtube/v3/search"
            f"?part=snippet&maxResults=1&q={_quote(track)}&key={YOUTUBE_API_KEY}"
        )
    if res.status_code == 403:
        raise ResourceWarning("YouTube API quota has reached the limit")
    res.raise_for_status()
    parsed = res.json()
    video_id = parsed["items"][0]["id"]["videoId"]
    return video_id


async def get_yt_id_noapi(track: str) -> str:
    """
    Get YouTube video ID for a track *without* using YouTube API.
    :param track: Track title formatted as '<artist> - <track>'.
    :return: Corresponding YouTube video ID.
    :raise Exception: if unable to get ID without API.
    """
    async with httpx.AsyncClient() as client:
        res = await client.get(
            f"https://www.youtube.com/results?search_query={_quote(track)}"
        )
    res.raise_for_status()
    match = YOUTUBE_REGEXP.search(res.text)
    data = json.loads(match.group("json"))  # type: ignore
    # fmt:off
    slr = data["contents"]["twoColumnSearchResultsRenderer"]["primaryContents"]["sectionListRenderer"]
    video_id = slr["contents"][0]["itemSectionRenderer"]["contents"][0]["videoRenderer"]["videoId"]
    # fmt:on
    return video_id


async def get_yt_id(track: str) -> str:
    """
    Get YouTube video ID for a track.
    :param track: Track title formatted as '<artist> - <track>'.
    :return: Corresponding YouTube video ID.
    :raise Exception: if unable to get ID neither via API nor without it.
    """
    try:
        yt_id = await get_yt_id_api(track)
    except Exception as e:
        logger.warning(
            f"Unable to get YouTube ID for '{track}' via API: {repr(e)}. Proceeding without API."
        )
        try:
            yt_id = await get_yt_id_noapi(track)
        except Exception as e:
            logger.error(
                f"Unable to get YouTube ID for '{track}' *without* API: {repr(e)}"
            )
            raise
    return yt_id


async def get_yt_ids(playlist: List[str]) -> List[str]:
    """
    Create a list containing a YouTube ID for each track
    in the given playlist.
    :param playlist: List of tracks formatted as '<artist> - <track>'.
    :return: List of corresponding YouTube IDs.
    """
    tasks = [get_yt_id(track) for track in playlist]
    result = await asyncio.gather(*tasks, return_exceptions=True)
    yt_ids = [i for i in result if isinstance(i, str)]
    return yt_ids
