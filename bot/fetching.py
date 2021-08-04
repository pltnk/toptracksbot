"""
This module is a part of Top Tracks Bot for Telegram
and is licensed under the MIT License.
Copyright (c) 2019-2021 Kirill Plotnikov
GitHub: https://github.com/pltnk/toptracksbot
"""


import asyncio
import json
import logging
import os
import re
from functools import partial
from typing import List
from urllib.parse import quote

import bs4
import httpx

from bot.exceptions import PlaylistRetrievalError, VideoIDsRetrievalError


LASTFM_API_KEY = os.environ["TTBOT_LASTFM_API_KEY"]
YOUTUBE_API_KEY = os.environ["TTBOT_YOUTUBE_API_KEY"]
YOUTUBE_REGEXP = re.compile("var ytInitialData = (?P<json>{.+});<")

logger = logging.getLogger("fetching")
logger.setLevel(logging.DEBUG)


_quote = partial(quote, safe="")


async def get_playlist_api(keyphrase: str, number: int = 3) -> List[str]:
    """
    Create a list of top tracks by the given artist using Last.fm API.
    :param keyphrase: Name of an artist or a band.
    :param number: Number of top tracks to collect.
    :return: List of top tracks formatted as '<artist> - <track>'.
    """
    async with httpx.AsyncClient() as client:
        res = await client.get(
            f"https://ws.audioscrobbler.com/2.0/"
            f"?method=artist.gettoptracks&artist={_quote(keyphrase)}&limit={number}"
            f"&autocorrect[1]&api_key={LASTFM_API_KEY}&format=json"
        )
    res.raise_for_status()
    parsed = json.loads(res.text)
    artist = parsed["toptracks"]["@attr"]["artist"]
    tracks = parsed["toptracks"]["track"]
    playlist = [
        f'{artist} - {tracks[i]["name"]}' for i in range(min(number, len(tracks)))
    ]
    return playlist


async def get_playlist_noapi(keyphrase: str, number: int = 3) -> List[str]:
    """
    Create a list of top tracks by the given artist **without** using Last.fm API.
    :param keyphrase: Name of an artist or a band.
    :param number: Number of top tracks to collect.
    :return: List of top tracks formatted as '<artist> - <track>'.
    """
    async with httpx.AsyncClient() as client:
        res = await client.get(
            f"https://www.last.fm/music/{_quote(keyphrase)}/+tracks?date_preset=ALL"
        )
    res.raise_for_status()
    soup = bs4.BeautifulSoup(res.content, "lxml")
    artist = soup.find("h1", attrs={"class": "header-new-title"}).text.strip()
    tracks = soup.find_all("a", attrs={"class": "", "title": re.compile(r".*?")})
    playlist = [
        f'{artist} - {tracks[i].get("title")}' for i in range(min(number, len(tracks)))
    ]
    return playlist


async def get_playlist(keyphrase: str, number: int = 3) -> List[str]:
    """
    Create a list of top tracks by the given artist.
    :param keyphrase: Name of an artist or a band.
    :param number: Number of top tracks to collect.
    :return: List of top tracks formatted as '<artist> - <track>'.
    :raise Exception: if unable to get playlist neither via API nor without it.
    """
    try:
        playlist = await get_playlist_api(keyphrase, number)
    except Exception as e:
        logger.warning(
            f"Unable to get playlist for '{keyphrase}' via Last.fm API: {repr(e)}. Proceeding without API."
        )
        try:
            playlist = await get_playlist_noapi(keyphrase, number)
        except Exception as e:
            logger.error(
                f"Unable to get playlist for '{keyphrase}' *without* Last.fm  API: {repr(e)}"
            )
            raise e
    return playlist


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
    parsed = json.loads(res.text)
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
    data = json.loads(match.group("json"))
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
            raise e
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


async def create_top(keyphrase: str, number: int = 3) -> List[str]:
    """
    Create list of str containing YouTube IDs of the top tracks
    by the given artist according to Last.fm overall charts.
    :param keyphrase: Name of an artist or a band.
    :param number: Number of top tracks to collect.
    :return: List of YouTube IDs.
    :raise PlaylistError: if unable to get playlist from Last.fm.
    :raise VideoIDSError: if unable to get video ids from YouTube.
    """
    try:
        playlist = await get_playlist(keyphrase, number)
    except Exception as e:
        raise PlaylistRetrievalError(keyphrase) from e
    try:
        yt_ids = await get_yt_ids(playlist)
    except Exception as e:
        raise VideoIDsRetrievalError(playlist) from e
    return yt_ids


async def get_bio_api(keyphrase: str, name_only: bool = False) -> str:
    """
    Collect a correct name and a short bio of the given artist using Last.fm API.
    :param keyphrase: Name of an artist or a band.
    :param name_only: If True return only artist's name.
    :return: Either just a name of an artist or their short bio.
    """
    async with httpx.AsyncClient() as client:
        res = await client.get(
            f"https://ws.audioscrobbler.com/2.0/"
            f"?method=artist.getinfo&artist={_quote(keyphrase)}&autocorrect[1]"
            f"&api_key={LASTFM_API_KEY}&format=json"
        )
    res.raise_for_status()
    parsed = json.loads(res.text)
    name = parsed["artist"]["name"]
    if name_only:
        return name
    else:
        logger.info(f"Collecting short bio for {name} using Last.fm API.")
        summary = parsed["artist"]["bio"]["summary"].split("<a href=")[0]
        tags = parsed["artist"]["tags"]["tag"]
        tags_str = ", ".join([item["name"] for item in tags])
        similar = parsed["artist"]["similar"]["artist"]
        similar_str = ", ".join([item["name"] for item in similar])
        link = parsed["artist"]["url"]
        bio = f"{summary}\n\nTags: {tags_str}\n\nSimilar: {similar_str}\n\nRead more: {link}"
        return bio


async def get_bio(keyphrase: str, name_only: bool = False) -> str:
    """
    Collect a correct name and a short bio of the given artist **without** using Last.fm API.
    :param keyphrase: Name of an artist or a band.
    :param name_only: If True return only artist's name.
    :return: Either just a name of an artist or their short bio.
    """
    async with httpx.AsyncClient() as client:
        res = await client.get(f"https://www.last.fm/music/{_quote(keyphrase)}/+wiki")
    res.raise_for_status()
    soup = bs4.BeautifulSoup(res.content, "lxml")
    name = soup.find("h1", attrs={"class": "header-new-title"}).text.strip()
    if name_only:
        return name
    else:
        logger.info(f"Collecting short bio for {name} without Last.fm API.")
        summary = soup.find("div", attrs={"class": "wiki-content"}).text.strip()[:600]
        similar_block = soup.find(
            "section", attrs={"class": "buffer-standard hidden-xs"}
        )
        similar = similar_block.find_all("a", attrs={"class": "link-block-target"})
        similar_str = ", ".join([item.text for item in similar])
        link = f"https://www.last.fm/music/{name}"
        bio = f"{summary}...\n\nSimilar: {similar_str}\n\nRead more: {link}"
        return bio


async def get_corrected_name_api(keyphrase: str) -> str:
    """
    Get corrected artist name via Last.fm API method
    artist.getCorrection. See: https://last.fm/api/show/artist.getCorrection
    :param keyphrase: Name of an artist or a band.
    :return: Corrected artist name.
    """
    async with httpx.AsyncClient() as client:
        res = await client.get(
            f"https://ws.audioscrobbler.com/2.0/"
            f"?method=artist.getcorrection&artist={_quote(keyphrase)}"
            f"&api_key={LASTFM_API_KEY}&format=json"
        )
    res.raise_for_status()
    parsed = json.loads(res.text)
    name = parsed["corrections"]["correction"]["artist"]["name"]
    return name


async def get_name(keyphrase: str) -> str:
    """
    Get corrected artist name from Last.fm.
    :param keyphrase: Name of an artist or a band.
    :return: Corrected artist name.
    >>> asyncio.run(get_name('norvana'))
    'Nirvana'
    """
    try:
        name = await get_corrected_name_api(keyphrase)
    except Exception as e:
        logger.debug(
            f"Unable to fetch artist name via Last.fm API method artist.getCorrection: {e}. "
            f"Proceeding with artist.getInfo method."
        )
        try:
            name = await get_bio_api(keyphrase, name_only=True)
        except Exception as e:
            logger.debug(
                f"An error occurred while fetching artist name via Last.fm API: {e}. Proceeding without API."
            )
            name = await get_bio(keyphrase, name_only=True)
    logger.debug(f"Got corrected name '{name}' for keyphrase '{keyphrase}'")
    return name


async def get_info(keyphrase: str) -> str:
    """
    Get information about the given artist from Last.fm.
    :param keyphrase: Name of an artist or a band.
    :return: Information about the artist.
    """
    try:
        info = await get_bio_api(keyphrase)
    except Exception as e:
        logger.debug(
            f"An error occurred while fetching artist bio via Last.fm API: {e}. Proceeding without API."
        )
        info = await get_bio(keyphrase)
    return info
