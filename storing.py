import fetching
from datetime import datetime

db = {}

pl = ['Nirvana - Smells Like Teen Spirit',
      'Nirvana - Come as You Are',
      'Nirvana - Lithium',
      'Nirvana - In Bloom',
      'Nirvana - Heart-Shaped Box']
ids = ['hTWKbfoikeg', 'vabnZ9-ex7o', 'pkcJEvMcnEg', 'PbgKEjNBHqM', 'n6P0SitRwy8']


def create_entry(pl, ids):
    tracks = {}
    pl = [item.lower() for item in pl]
    links = [f'youtube.com/watch?v={item}' for item in ids]
    for track, link in zip(pl, links):
        tracks.setdefault(track, link)
    return tracks


def search(keyphrase):
    name = fetching.get_info(keyphrase, name_only=True)
    if name.lower() in db:
        if db['name']['date']:  # add delta
            return db['name']['tracks']
    else:
        # fetching.create_top()
        tracks = create_entry(pl, ids)
        db.setdefault(name, {'tracks': tracks, 'date': datetime.now()})