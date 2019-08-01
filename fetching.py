import bs4
import json
import logging
import os
import re
import requests
from typing import Union

lastfm_api = os.getenv('LASTFM_API')
youtube_api = os.getenv('YOUTUBE_API')


def create_top(keyphrase: str, number: int = 5, ids_only: bool = True) -> Union[list, tuple]:
    try:
        playlist = get_playlist_api(keyphrase, number)
    except Exception as e:
        logging.warning(e)
        logging.info('Creating playlist without API')
        playlist = get_playlist(keyphrase, number)
    try:
        ids = fetch_ids_api(playlist)
    except Exception as e:
        logging.warning(e)
        logging.info('Fetching YouTube ids without API')
        ids = fetch_ids(playlist)
    if ids_only:
        return ids
    else:
        return playlist, ids


def get_playlist_api(keyphrase: str, number: int) -> list:
    res = requests.get(f'http://ws.audioscrobbler.com/2.0/?method=artist.gettoptracks&artist={keyphrase}&limit=10&autocorrect[1]&api_key={lastfm_api}')
    res.raise_for_status()
    soup = bs4.BeautifulSoup(res.content, 'lxml')
    artist = soup.find('toptracks').get('artist')
    tracks = soup.find_all('track')
    playlist = [f'{artist} - {tracks[i].find("name").text}' for i in range(min(number, len(tracks)))]
    return playlist


def get_playlist(keyphrase: str, number: int) -> list:
    res = requests.get(f'https://www.last.fm/ru/music/{keyphrase}/+tracks?date_preset=ALL')
    res.raise_for_status()
    soup = bs4.BeautifulSoup(res.content, 'lxml')
    links = soup.find_all('a', attrs={'class': 'link-block-target', 'title': re.compile(r'.*?')})
    artist = soup.find('h1', attrs={'class': 'header-title'}).text.strip()
    playlist = [f'{artist} - {links[i].get("title")}' for i in range(min(number, len(links)))]
    return playlist


def fetch_ids_api(playlist: list) -> list:
    ids = []
    for item in playlist:
        page = requests.get(f'https://www.googleapis.com/youtube/v3/search?part=snippet&maxResults=1&q={item}&key={youtube_api}')
        page.raise_for_status()
        parsed_page = bs4.BeautifulSoup(page.content, 'lxml')
        video_id = json.loads(parsed_page.text)['items'][0]['id']['videoId']
        if video_id is not None:
            logging.info(f'Adding YouTube id for: {item}')
            ids.append(video_id)
    return ids


def fetch_ids(playlist: list) -> list:
    ids = []
    for item in playlist:
        page = requests.get(f'https://www.youtube.com/results?search_query={item}')
        page.raise_for_status()
        parsed_page = bs4.BeautifulSoup(page.content, 'html.parser')
        link = parsed_page.find('a', attrs={'dir': 'ltr', 'title': re.compile(r'.*?')})
        if link is not None:
            logging.info(f'Adding YouTube id for: {item}')
            ids.append(link['href'][9:])
    return ids


def get_info(keyphrase: str, name_only: bool = False) -> str:
    res = requests.get(f'http://ws.audioscrobbler.com/2.0/?method=artist.getinfo&artist={keyphrase}&autocorrect[1]&api_key={lastfm_api}&format=json')
    res.raise_for_status()
    soup = bs4.BeautifulSoup(res.content, 'lxml')
    soup_dict = json.loads(soup.text)
    name = soup_dict['artist']['name']
    if name_only:
        return name
    else:
        summary = soup_dict['artist']['bio']['summary']
        link = soup_dict['artist']['url']
        logging.info(f'Collecting short bio for {name}')
        info = f'{summary}: {link}'
        return info
