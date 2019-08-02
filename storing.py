import fetching
from datetime import datetime
import logging
import json
import sqlite3


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)


def combine(keyphrase: str) -> str:
    ids = fetching.create_top(keyphrase, number=10)
    links = json.dumps([f'youtube.com/watch?v={item}' for item in ids])
    return links


# noinspection SqlResolve
def process(keyphrase: str, db: str = 'database.db') -> dict:
    try:
        name = fetching.get_info(keyphrase, name_only=True).lower()
    except Exception as e:
        logging.debug(e)
        name = keyphrase.lower()
    con = sqlite3.connect(db)
    cur = con.cursor()
    cur.execute(f"SELECT EXISTS(SELECT * FROM top WHERE artist=?)", (name,))
    exists = cur.fetchone()
    if exists == (1,):
        logging.info(f'There is an artist with the name "{name}" in the database')
        cur.execute(f"SELECT date FROM top WHERE artist=?", (name,))
        date = cur.fetchone()[0]
        last_updated = datetime.strptime(date, '%Y-%m-%d')
        delta = datetime.now() - last_updated
        if delta.days > 30:
            logging.info(f'Entry for "{name}" is older than 30 days. Updating...')
            cur.execute(f"UPDATE top SET tracks=? WHERE artist=?", (combine(name), name))
            cur.execute(f"UPDATE top SET date=? WHERE artist=?", (datetime.strftime(datetime.now(), '%Y-%m-%d'), name))
            logging.info(f'Entry for "{name}" is updated')
    else:
        logging.info(f'There is no artist named "{name}" in the database')
        entry = (name, combine(name), datetime.strftime(datetime.now(), '%Y-%m-%d'), 0)
        cur.execute(f"INSERT INTO top(artist, tracks, date, requests) VALUES(?, ?, ?, ?)", entry)
        logging.info(f'Entry for "{name}" created in the database')
    cur.execute(f"UPDATE top SET requests=requests+1 WHERE artist=?", (name,))
    con.commit()
    cur.execute(f"SELECT tracks FROM top WHERE artist=?", (name,))
    tracks = json.loads(cur.fetchone()[0])
    return tracks
