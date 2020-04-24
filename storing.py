"""
This module is a part of Top Tracks Bot for Telegram
and is licensed under the MIT License.
Copyright (c) 2019-2020 Kirill Plotnikov
GitHub: https://github.com/pltnk/toptracksbot
"""


import json
import logging
import os
from datetime import datetime

import asyncpg

import fetching


DATABASE_URL = os.environ["DATABASE_URL"]

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


async def combine(keyphrase: str) -> str:
    """
    Create JSON array containing YouTube IDs of the top tracks by the given artist according to Last.fm.
    :param keyphrase: Name of an artist or a band.
    :return: str containing JSON array.
    """
    top = await fetching.create_top(keyphrase)
    ids = json.dumps(top)
    return ids


# noinspection SqlResolve
def process(keyphrase: str) -> list:
    """
    Check if an entry for the given artist exists in the database, update it if it is outdated,
    create a new entry if it doesn't exist.
    :param keyphrase: Name of an artist or a band.
    :return: List of YouTube IDs.
    """
    try:
        name = await fetching.get_name(keyphrase)
        name = name.lower()
    except Exception as e:
        logging.debug(
            f"An error occurred while fetching artist name from Last.fm: {e}."
        )
        name = keyphrase.lower()
    conn = await asyncpg.connect(dsn=DATABASE_URL)
    record = await conn.fetch(f"SELECT * FROM top WHERE artist = '{name}'")
    if record:
        logging.info(f'There is an artist with the name "{name}" in the database')
        await conn.execute(f"UPDATE top SET requests = requests + 1 WHERE artist = '{name}'")
        last_updated = datetime.strptime(record[0]["date"], "%Y-%m-%d")
        delta = datetime.now() - last_updated
        if delta.days > 30:
            logging.info(f'Entry for "{name}" is older than 30 days. Updating...')
            tracks = await combine(name)
            date = datetime.strftime(datetime.now(), "%Y-%m-%d")
            await conn.execute(f"UPDATE top SET tracks = '{tracks}', date = '{date}' WHERE artist = '{name}'")
            logging.info(f'Entry for "{name}" is updated')
        else:
            tracks = record[0]["tracks"]
    else:
        logging.info(f'There is no artist named "{name}" in the database')
        tracks = await combine(name)
        date = datetime.strftime(datetime.now(), "%Y-%m-%d")
        await conn.execute(f"INSERT INTO top(artist, tracks, date, requests) VALUES('{name}', '{tracks}', '{date}', 1)")
        logging.info(f'Entry for "{name}" created in the database')
    await conn.close()
    return json.loads(tracks)
