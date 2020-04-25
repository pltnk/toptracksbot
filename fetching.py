"""
This module is a part of Top Tracks Bot for Telegram
and is licensed under the MIT License.
Copyright (c) 2019-2020 Kirill Plotnikov
GitHub: https://github.com/pltnk/toptracksbot
"""


import asyncio
import json
import logging
import os
import re
from typing import List

import bs4
import httpx


LASTFM_API = os.getenv("LASTFM_API")
YOUTUBE_API = os.getenv("YOUTUBE_API")

logger = logging.getLogger("fetching")
logger.setLevel(logging.DEBUG)


async def get_playlist_api(keyphrase: str, number: int = 3) -> List[str]:
    """
    Create a list of top tracks by given artist using Last.fm API.
    :param keyphrase: Name of an artist or a band.
    :param number: Number of top tracks to collect.
    :return: List of top tracks formatted as '<artist> - <track>'.
    """
    async with httpx.AsyncClient() as client:
        res = await client.get(
            f"http://ws.audioscrobbler.com/2.0/?method=artist.gettoptracks&artist={keyphrase}&limit={number}&autocorrect[1]&api_key={LASTFM_API}&format=json"
        )
    res.raise_for_status()
    parsed = json.loads(res.text)
    artist = parsed["toptracks"]["@attr"]["artist"]
    tracks = parsed["toptracks"]["track"]
    playlist = [
        f'{artist} - {tracks[i]["name"]}' for i in range(min(number, len(tracks)))
    ]
    return playlist


async def get_playlist(keyphrase: str, number: int = 3) -> List[str]:
    """
    Create a list of top tracks by given artist **without** using Last.fm API.
    :param keyphrase: Name of an artist or a band.
    :param number: Number of top tracks to collect.
    :return: List of top tracks formatted as '<artist> - <track>'.
    """
    async with httpx.AsyncClient() as client:
        res = await client.get(
            f"https://www.last.fm/music/{keyphrase}/+tracks?date_preset=ALL"
        )
    res.raise_for_status()
    soup = bs4.BeautifulSoup(res.content, "lxml")
    artist = soup.find("h1", attrs={"class": "header-new-title"}).text.strip()
    tracks = soup.find_all("a", attrs={"class": "", "title": re.compile(r".*?")})
    playlist = [
        f'{artist} - {tracks[i].get("title")}' for i in range(min(number, len(tracks)))
    ]
    return playlist


async def fetch_ids_api(playlist: List[str]) -> List[str]:
    """
    Create a list containing an YouTube ID for each track in the given playlist using YouTube API.
    :param playlist: List of tracks formatted as '<artist> - <track>'.
    :return: List of YouTube IDs.
    """
    ids = []
    async with httpx.AsyncClient() as client:
        tasks = []
        for track in playlist:
            tasks.append(
                client.get(
                    f"https://www.googleapis.com/youtube/v3/search?part=snippet&maxResults=1&q={track}&key={YOUTUBE_API}"
                )
            )
        result = await asyncio.gather(*tasks)
    for counter, res in enumerate(result):
        if res.status_code == 200:
            parsed = json.loads(res.text)
            video_id = parsed["items"][0]["id"]["videoId"]
            if video_id:
                logger.info(f"Adding YouTube id for: {playlist[counter]}")
                ids.append(video_id)
    return ids


async def fetch_ids(playlist: List[str]) -> List[str]:
    """
     Create a list containing an YouTube ID for each track in the given playlist **without** using YouTube API.
     :param playlist: List of tracks formatted as '<artist> - <track>'.
     :return: List of YouTube IDs.
     """
    ids = []
    async with httpx.AsyncClient() as client:
        tasks = []
        for track in playlist:
            tasks.append(
                client.get(f"https://www.youtube.com/results?search_query={track}")
            )
        result = await asyncio.gather(*tasks)
    for counter, res in enumerate(result):
        if res.status_code == 200:
            parsed = bs4.BeautifulSoup(res.content, "lxml")
            link = parsed.find("a", attrs={"dir": "ltr", "title": re.compile(r".*?")})
            if link:
                logger.info(f"Adding YouTube id for: {playlist[counter]}")
                ids.append(link["href"][9:])
    return ids


async def create_top(keyphrase: str, number: int = 3) -> List[str]:
    """
    Create list of str containing YouTube IDs of the top tracks
    by the given artist according to Last.fm.
    :param keyphrase: Name of an artist or a band.
    :param number: Number of top tracks to collect.
    :return: List of YouTube IDs.
    """
    try:
        playlist = await get_playlist_api(keyphrase, number)
    except Exception as e:
        logger.warning(
            f"An error occurred while creating playlist via Last.fm API: {e}"
        )
        logger.info("Creating playlist without API")
        playlist = await get_playlist(keyphrase, number)
    try:
        ids = await fetch_ids_api(playlist)
    except Exception as e:
        logger.warning(f"An error occurred while fetching YouTube ids via API: {e}")
        logger.info("Fetching YouTube ids without API")
        ids = await fetch_ids(playlist)
    return ids


async def get_bio_api(keyphrase: str, name_only: bool = False) -> str:
    """
    Collect a correct name and short bio of the given artist using Last.fm API.
    :param keyphrase: Name of an artist or a band.
    :param name_only: Switch between returns.
    :return: Either just a name of an artist or their short bio.
    """
    async with httpx.AsyncClient() as client:
        res = await client.get(
            f"http://ws.audioscrobbler.com/2.0/?method=artist.getinfo&artist={keyphrase}&autocorrect[1]&api_key={LASTFM_API}&format=json"
        )
    res.raise_for_status()
    parsed = json.loads(res.text)
    name = parsed["artist"]["name"]
    if name_only:
        return name
    else:
        logger.info(f"Collecting short bio for {name} using Last.fm API.")
        summary = parsed["artist"]["bio"]["summary"][:-21]
        tags = parsed["artist"]["tags"]["tag"]
        tags = ", ".join([tags[i]["name"] for i in range(len(tags))])
        link = parsed["artist"]["url"]
        bio = f"{summary}\nTags: {tags}\nRead more: {link}"
        return bio


async def get_bio(keyphrase: str, name_only: bool = False) -> str:
    """
    Collect a correct name and short bio of the given artist **without** using Last.fm API.
    :param keyphrase: Name of an artist or a band.
    :param name_only: Switch between returns.
    :return: Either just a name of an artist or their short bio.
    """
    async with httpx.AsyncClient() as client:
        res = await client.get(f"https://www.last.fm/music/{keyphrase}/+wiki")
    res.raise_for_status()
    soup = bs4.BeautifulSoup(res.content, "lxml")
    name = soup.find("h1", attrs={"class": "header-new-title"}).text.strip()
    if name_only:
        return name
    else:
        logger.info(f"Collecting short bio for {name} without Last.fm API.")
        summary = soup.find("div", attrs={"class": "wiki-content"}).text.strip()[:600]
        link = f"https://www.last.fm/music/{name}"
        bio = f"{summary}...\nRead more: {link}"
        return bio


async def get_name(keyphrase: str) -> str:
    """
    Get corrected artist name from Last.fm.
    :param keyphrase: Name of an artist or a band.
    :return: Corrected artist name.
    >>> asyncio.run(get_name('norvana'))
    'Nirvana'
    """
    try:
        name = await get_bio_api(keyphrase, name_only=True)
    except Exception as e:
        logger.debug(
            f"An error occurred while fetching artist name via Last.fm API: {e}. Proceeding without API."
        )
        name = await get_bio(keyphrase, name_only=True)
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
