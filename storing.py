import fetching
from datetime import datetime
import logging
import re
import json
import sqlite3


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)


def combine(keyphrase) -> dict:
    tracks = {}
    playlist, ids = fetching.create_top(keyphrase, number=10, ids_only=False)
    regex = re.compile(r'^(.*\s-\s)(.*)')
    playlist = [regex.match(item).group(2).lower() for item in playlist]
    links = [f'youtube.com/watch?v={item}' for item in ids]
    for track, link in zip(playlist, links):
        tracks.setdefault(track, link)
    tracks = json.dumps(tracks)
    return tracks


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
        logging.info('exists is True')
        cur.execute(f"SELECT date FROM top WHERE artist=?", (name,))
        date = cur.fetchone()[0]
        last_updated = datetime.strptime(date, '%Y-%m-%d')
        delta = datetime.now() - last_updated
        if delta.days > 30:
            cur.execute(f"UPDATE top SET tracks=? WHERE artist=?", (combine(name), name))
            cur.execute(f"UPDATE top SET date=? WHERE artist=?", (datetime.strftime(datetime.now(), '%Y-%m-%d'), name))
    else:
        logging.info('exists is False')
        entry = (name, combine(name), datetime.strftime(datetime.now(), '%Y-%m-%d'))
        cur.execute(f"INSERT INTO top(artist, tracks, date) VALUES(?, ?, ?)", entry)
    con.commit()
    cur.execute(f"SELECT tracks FROM top WHERE artist=?", (name,))
    tracks = json.loads(cur.fetchone()[0])
    return tracks
