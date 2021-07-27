"""
This module is a part of Top Tracks Bot for Telegram
and is licensed under the MIT License.
Copyright (c) 2019-2021 Kirill Plotnikov
GitHub: https://github.com/pltnk/toptracksbot
"""


import json
import logging
import os
from datetime import datetime
from typing import List

import asyncpg

import fetching


DATABASE_URI = os.getenv(
    "TTBOT_DATABASE_URI",
    f"postgres://{os.getenv('TTBOT_DATABASE_USER')}:{os.getenv('TTBOT_DATABASE_PASS')}@db/toptracksbot",
)
VALID_FOR_DAYS = int(os.getenv("TTBOT_VALID_FOR_DAYS", 30))

logger = logging.getLogger("storing")
logger.setLevel(logging.DEBUG)


async def get_artist(keyphrase: str) -> str:
    """
    Get a proper artist name using keyphrase.
    :param keyphrase: Alleged artist name.
    :return: Artist name.
    """
    try:
        artist = await fetching.get_name(keyphrase)
        artist = artist.lower()
    except Exception as e:
        logger.exception(f"Unable to fetch artist name from Last.fm: {e}.")
        artist = keyphrase.lower()
    return artist


async def process(keyphrase: str) -> List[str]:
    """
    Get YouTube ids of top tracks by the given artist
    from the database if there is valid data for this artist.
    Otherwise find valid data and update the database.
    :param keyphrase: Name of an artist or a band.
    :return: List of YouTube IDs.
    """
    artist = await get_artist(keyphrase)
    today = datetime.now()
    conn = await asyncpg.connect(dsn=DATABASE_URI)
    record = await conn.fetchrow("SELECT * FROM top WHERE artist = $1", artist)
    if (
        record
        and (today - datetime.strptime(record["date"], "%Y-%m-%d")).days
        < VALID_FOR_DAYS
    ):
        logger.info(f"Found valid data for '{artist}' in the database")
        await conn.execute(
            "UPDATE top SET requests = requests + 1 WHERE artist = $1", artist
        )
        tracks = json.loads(record["tracks"])
    else:
        logger.info(f"No valid data for '{artist}' in the database")
        tracks = await fetching.create_top(artist)
        if tracks:
            tracks_json = json.dumps(tracks)
            date = datetime.strftime(today, "%Y-%m-%d")
            query = """INSERT INTO top (artist, tracks, date, requests)
                       VALUES($1, $2, $3, 1)
                       ON CONFLICT (artist)
                       DO UPDATE SET tracks = $2, date = $3, requests = top.requests + 1"""
            await conn.execute(query, artist, tracks_json, date)
            logger.info(f"Database is updated with new data for '{artist}'")
    await conn.close()
    return tracks
