import fetching
from datetime import datetime

db = {}

pl = ['Smells Like Teen Spirit', 'Come as You Are', 'Lithium', 'In Bloom', 'Heart-Shaped Box']
ids = ['hTWKbfoikeg', 'vabnZ9-ex7o', 'pkcJEvMcnEg', 'PbgKEjNBHqM', 'n6P0SitRwy8']


def combine(pl, ids):
    tracks = {}
    pl = [item.lower() for item in pl]
    links = [f'youtube.com/watch?v={item}' for item in ids]
    for track, link in zip(pl, links):
        tracks.setdefault(track, link)
    return tracks


def process(keyphrase, db):
    name = fetching.get_info(keyphrase, name_only=True).lower()
    if name in db:
        # if db['name']['date']:  # add delta
        return db[name]['tracks']
    else:
        pl, ids = fetching.create_top(keyphrase, number=10, ids_only=False)
        tracks = combine(pl, ids)
        db.setdefault(name, {'tracks': tracks, 'date': datetime.now()})