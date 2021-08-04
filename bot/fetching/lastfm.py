import asyncio
import json
import logging
import re
from typing import List

import bs4
import httpx

from bot.config import LASTFM_API_KEY
from bot.fetching.util import _quote


logger = logging.getLogger("lastfm")
logger.setLevel(logging.DEBUG)


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
            raise
    return playlist


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


async def get_info(keyphrase: str) -> str:
    """
    Get information about the given artist from Last.fm.
    :param keyphrase: Name of an artist or a band.
    :return: Information about the artist.
    """
    try:
        info = await get_bio_api(keyphrase)
    except Exception as e:
        logger.warning(
            f"Unable to get artist bio via Last.fm API: {repr(e)}. Proceeding without API."
        )
        info = await get_bio(keyphrase)
    return info


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
            f"Unable to get artist name via Last.fm API method artist.getCorrection: {repr(e)}. "
            f"Proceeding with artist.getInfo method."
        )
        try:
            name = await get_bio_api(keyphrase, name_only=True)
        except Exception as e:
            logger.debug(
                f"Unable to get artist name via Last.fm API: {repr(e)}. Proceeding without API."
            )
            name = await get_bio(keyphrase, name_only=True)
    logger.debug(f"Got corrected name '{name}' for keyphrase '{keyphrase}'")
    return name
