import fetching
import json
import logging
import os
import psycopg2

from datetime import datetime


DATABASE_URL = os.environ["DATABASE_URL"]

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


def combine(keyphrase: str) -> str:
    """
    Create JSON array containing YouTube IDs of the top tracks by the given artist according to Last.fm.
    :param keyphrase: Name of an artist or a band.
    :return: str containing JSON array.
    """
    ids = json.dumps(fetching.create_top(keyphrase))
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
        name = fetching.get_name(keyphrase).lower()
    except Exception as e:
        logging.debug(
            f"An error occurred while fetching artist name from Last.fm: {e}."
        )
        name = keyphrase.lower()
    con = psycopg2.connect(DATABASE_URL, sslmode="require")
    cur = con.cursor()
    cur.execute(f"SELECT EXISTS(SELECT * FROM top WHERE artist = %s)", (name,))
    exists = cur.fetchone()
    if exists[0]:
        logging.info(f'There is an artist with the name "{name}" in the database')
        cur.execute(f"SELECT date FROM top WHERE artist = %s", (name,))
        date = cur.fetchone()[0]
        last_updated = datetime.strptime(date, "%Y-%m-%d")
        delta = datetime.now() - last_updated
        if delta.days > 30:
            logging.info(f'Entry for "{name}" is older than 30 days. Updating...')
            cur.execute(
                f"UPDATE top SET tracks = %s WHERE artist = %s", (combine(name), name)
            )
            cur.execute(
                f"UPDATE top SET date = %s WHERE artist = %s",
                (datetime.strftime(datetime.now(), "%Y-%m-%d"), name),
            )
            logging.info(f'Entry for "{name}" is updated')
    else:
        logging.info(f'There is no artist named "{name}" in the database')
        entry = (name, combine(name), datetime.strftime(datetime.now(), "%Y-%m-%d"), 0)
        cur.execute(
            f"INSERT INTO top(artist, tracks, date, requests) VALUES(%s, %s, %s, %s)",
            entry,
        )
        logging.info(f'Entry for "{name}" created in the database')
    cur.execute(f"UPDATE top SET requests = requests + 1 WHERE artist = %s", (name,))
    con.commit()
    cur.execute(f"SELECT tracks FROM top WHERE artist = %s", (name,))
    tracks = json.loads(cur.fetchone()[0])
    cur.close()
    con.close()
    return tracks
