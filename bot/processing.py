"""
This module is a part of Top Tracks Bot for Telegram
and is licensed under the MIT License.
Copyright (c) 2019-2021 Kirill Plotnikov
GitHub: https://github.com/pltnk/toptracksbot
"""


import json
import logging
from datetime import datetime
from typing import List

import asyncpg

from bot.config import DATABASE_URI, VALID_FOR_DAYS
from bot.exceptions import PlaylistRetrievalError, VideoIDsRetrievalError
from bot.fetching.lastfm import get_name, get_playlist
from bot.fetching.youtube import get_yt_ids


logger = logging.getLogger("processing")
logger.setLevel(logging.DEBUG)


async def get_artist(keyphrase: str) -> str:
    """
    Get a proper artist name using keyphrase.
    :param keyphrase: Alleged artist name.
    :return: Artist name.
    """
    try:
        artist = await get_name(keyphrase)
        artist = artist.lower()
    except Exception as e:
        logger.error(f"Unable to fetch artist name from Last.fm: {repr(e)}.")
        artist = keyphrase.lower()
    return artist


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


async def get_top(keyphrase: str) -> List[str]:
    """
    Get YouTube ids of top tracks by the given artist
    from the database if there is valid data for this artist.
    Otherwise find valid data and update the database.
    :param keyphrase: Name of an artist or a band.
    :return: List of YouTube IDs.
    """
    artist = await get_artist(keyphrase)
    today = datetime.now().date()
    conn = await asyncpg.connect(dsn=DATABASE_URI)
    record = await conn.fetchrow(
        "UPDATE top SET requests = requests + 1 WHERE artist = $1 RETURNING tracks, date",
        artist,
    )
    if record and (today - record["date"]).days < VALID_FOR_DAYS:
        logger.info(f"Found valid data for '{artist}' in the database")
        tracks = json.loads(record["tracks"])
    else:
        logger.info(f"No valid data for '{artist}' in the database")
        tracks = await create_top(artist)
        if tracks:
            tracks_json = json.dumps(tracks)
            query = """INSERT INTO top (artist, tracks, date, requests)
                       VALUES($1, $2, $3, 1)
                       ON CONFLICT (artist)
                       DO UPDATE SET tracks = $2, date = $3"""
            await conn.execute(query, artist, tracks_json, today)
            logger.info(f"Database is updated with new data for '{artist}'")
    await conn.close()
    return tracks
