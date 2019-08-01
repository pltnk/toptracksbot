import fetching
from datetime import datetime
import logging
import re

db = {}  # json file to store data

pl = ['Smells Like Teen Spirit', 'Come as You Are', 'Lithium', 'In Bloom', 'Heart-Shaped Box']
ids = ['hTWKbfoikeg', 'vabnZ9-ex7o', 'pkcJEvMcnEg', 'PbgKEjNBHqM', 'n6P0SitRwy8']


def combine(playlist: list, ids: list):
    tracks = {}
    regex = re.compile(r'^(.*\s-\s)(.*)')
    playlist = [regex.match(item).group(2).lower() for item in playlist]
    links = [f'youtube.com/watch?v={item}' for item in ids]
    for track, link in zip(playlist, links):
        tracks.setdefault(track, link)
    return tracks


def process(keyphrase: str, db: dict):
    try:
        name = fetching.get_info(keyphrase, name_only=True).lower()
    except Exception as e:
        logging.debug(e)
        name = keyphrase.lower()
    if name not in db or db['name']['date']:  # add delta
        pl, ids = fetching.create_top(keyphrase, number=10, ids_only=False)
        tracks = combine(pl, ids)
        db.setdefault(name, {'tracks': tracks, 'date': datetime.now()})
    return db[name]['tracks']
