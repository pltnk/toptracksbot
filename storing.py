import fetching
from datetime import datetime
import logging
import re
import json


class Database:
    def __init__(self, file):
        self.file = file
        with open(file, 'r') as db:
            self.data = json.load(db)

    def rewrite(self):
        with open(self.file, 'w') as db:
            json.dump(self.data, db)

    def add(self, entry):
        with open(self.file, 'a') as db:
            json.dump(entry, db)

    def reload(self):
        self.__init__(self.file)

    @staticmethod
    def combine(playlist: list, ids: list) -> dict:
        tracks = {}
        regex = re.compile(r'^(.*\s-\s)(.*)')
        playlist = [regex.match(item).group(2).lower() for item in playlist]
        links = [f'youtube.com/watch?v={item}' for item in ids]
        for track, link in zip(playlist, links):
            tracks.setdefault(track, link)
        return tracks

    def process(self, keyphrase: str) -> dict:
        try:
            name = fetching.get_info(keyphrase, name_only=True).lower()
        except Exception as e:
            logging.debug(e)
            name = keyphrase.lower()
        if name not in self.data or self.data[name]['date'] == 1:  # add delta:
            playlist, ids = fetching.create_top(keyphrase, number=10, ids_only=False)
            tracks = self.combine(playlist, ids)
            if self.data[name]['date'] == 1:  # add delta:
                self.data[name]['tracks'] = tracks
                self.data[name]['date'] = 0
                self.rewrite()
            else:
                entry = {name: {'tracks': tracks, 'date': 1}}
                self.add(entry)
        return self.data[name]['tracks']
