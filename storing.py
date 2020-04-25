"""
This module is a part of Top Tracks Bot for Telegram
and is licensed under the MIT License.
Copyright (c) 2019-2020 Kirill Plotnikov
GitHub: https://github.com/pltnk/toptracksbot
"""


import json
import logging
import os
import ssl
from datetime import datetime

import asyncpg

import fetching


DATABASE_URI = os.environ["DATABASE_URI"]
VALID_FOR_DAYS = 30

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


def process(keyphrase: str) -> list:
    """
    Check if an entry for the given artist exists in the database, update it if it is outdated,
    create a new entry if it doesn't exist.
    :param keyphrase: Name of an artist or a band.
    :return: List of YouTube IDs.
    """
    try:
        artist = await fetching.get_name(keyphrase)
        artist = artist.lower()
    except Exception as e:
        logging.debug(
            f"An error occurred while fetching artist name from Last.fm: {e}."
        )
        artist = keyphrase.lower()
    today = datetime.now()
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    conn = await asyncpg.connect(dsn=DATABASE_URL, ssl=ctx)
    record = await conn.fetch(f"SELECT * FROM top WHERE artist = '{artist}'")
    if (
        record
        and (today - datetime.strptime(record[0]["date"], "%Y-%m-%d")).days
        < VALID_FOR_DAYS
    ):
        logging.info(f'There is an artist with the name "{artist}" in the database')
        await conn.execute(
            f"UPDATE top SET requests = requests + 1 WHERE artist = '{artist}'"
        )
        tracks = json.loads(record[0]["tracks"])
    else:
        logging.info(
            f'There is no artist named "{artist}" in the database or the entry is older than {VALID_FOR_DAYS} days'
        )
        tracks = await fetching.create_top(artist)
        tracks_json = json.dumps(tracks)
        date = datetime.strftime(today, "%Y-%m-%d")
        query = f"""INSERT INTO top (artist, tracks, date, requests) 
                    VALUES('{artist}', '{tracks_json}', '{date}', 1)
                    ON CONFLICT (artist)
                    DO UPDATE SET tracks = '{tracks_json}', date = '{date}', requests = top.requests + 1"""
        await conn.execute(query)
        logging.info(f'Entry for "{artist}" created/updated in the database')
    await conn.close()
    return tracks
