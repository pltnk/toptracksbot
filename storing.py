import fetching
from datetime import datetime
import logging
import re
import json

with open('database.json', 'r') as db:
    data = json.load(db)


def combine(playlist: list, ids: list) -> dict:
    tracks = {}
    regex = re.compile(r'^(.*\s-\s)(.*)')
    playlist = [regex.match(item).group(2).lower() for item in playlist]
    links = [f'youtube.com/watch?v={item}' for item in ids]
    for track, link in zip(playlist, links):
        tracks.setdefault(track, link)
    return tracks


def process(keyphrase: str, data: dict) -> dict:
    try:
        name = fetching.get_info(keyphrase, name_only=True).lower()
    except Exception as e:
        logging.debug(e)
        name = keyphrase.lower()
    if name not in data or data[name]['date'] == 1:  # add delta:
        playlist, ids = fetching.create_top(keyphrase, number=10, ids_only=False)
        tracks = combine(playlist, ids)
        if data[name]['date'] == 1:  # add delta:
            data[name]['tracks'] = tracks
            data[name]['date'] = 0
        else:
            # data.setdefault(name, {'tracks': tracks, 'date': 1})
            entry = {name: {'tracks': tracks, 'date': 1}}
            with open('database.json', 'a') as db:
                # json.dump(data, db)
                json.dump(entry, db)
    return data[name]['tracks']
