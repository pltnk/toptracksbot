"""
This module is a part of Top Tracks Bot for Telegram
and is licensed under the MIT License.
Copyright (c) 2019 Kirill Plotnikov
GitHub: https://github.com/pltnk/top_tracks
"""


import bs4
import json
import logging
import os
import re
import requests


lastfm_api = os.getenv("LASTFM_API")
youtube_api = os.getenv("YOUTUBE_API")


def create_top(keyphrase: str, number: int = 3) -> list:
    """
    Create list of str containing YouTube IDs of the top tracks by the given artist according to Last.fm.
    :param keyphrase: Name of an artist or a band.
    :param number: Number of top tracks to collect.
    :return: list of str. List of YouTube IDs.
    """
    try:
        playlist = get_playlist_api(keyphrase, number)
    except Exception as e:
        logging.warning(
            f"An error occurred while creating playlist via Last.fm API: {e}"
        )
        logging.info("Creating playlist without API")
        playlist = get_playlist(keyphrase, number)
    try:
        ids = fetch_ids_api(playlist)
    except Exception as e:
        logging.warning(f"An error occurred while fetching YouTube ids via API: {e}")
        logging.info("Fetching YouTube ids without API")
        ids = fetch_ids(playlist)
    return ids


def get_playlist_api(keyphrase: str, number: int = 3) -> list:
    """
    Create a list of top tracks by given artist using Last.fm API.
    :param keyphrase: Name of an artist or a band.
    :param number: Number of top tracks to collect.
    :return: list of str. List of top tracks formatted as '<artist> - <track>'.
    """
    res = requests.get(
        f"http://ws.audioscrobbler.com/2.0/?method=artist.gettoptracks&artist={keyphrase}&limit={number}&autocorrect[1]&api_key={lastfm_api}"
    )
    res.raise_for_status()
    soup = bs4.BeautifulSoup(res.content, "lxml")
    artist = soup.find("toptracks").get("artist")
    tracks = soup.find_all("track")
    playlist = [
        f'{artist} - {tracks[i].find("name").text}'
        for i in range(min(number, len(tracks)))
    ]
    return playlist


def get_playlist(keyphrase: str, number: int = 3) -> list:
    """
    Create a list of top tracks by given artist **without** using Last.fm API.
    :param keyphrase: Name of an artist or a band.
    :param number: Number of top tracks to collect.
    :return: list of str. List of top tracks formatted as '<artist> - <track>'.
    """
    res = requests.get(f"https://www.last.fm/music/{keyphrase}/+tracks?date_preset=ALL")
    res.raise_for_status()
    soup = bs4.BeautifulSoup(res.content, "lxml")
    artist = soup.find("h1", attrs={"class": "header-new-title"}).text.strip()
    tracks = soup.find_all("a", attrs={"class": "", "title": re.compile(r".*?")})
    playlist = [
        f'{artist} - {tracks[i].get("title")}' for i in range(min(number, len(tracks)))
    ]
    return playlist


def fetch_ids_api(playlist: list) -> list:
    """
    Create a list containing an YouTube ID for each track in the given playlist using YouTube API.
    :param playlist: list of str. List of tracks formatted as '<artist> - <track>'.
    :return: list of str. List of YouTube IDs.
    """
    ids = []
    for track in playlist:
        page = requests.get(
            f"https://www.googleapis.com/youtube/v3/search?part=snippet&maxResults=1&q={track}&key={youtube_api}"
        )
        page.raise_for_status()
        parsed_page = bs4.BeautifulSoup(page.content, "lxml")
        video_id = json.loads(parsed_page.text)["items"][0]["id"]["videoId"]
        if video_id is not None:
            logging.info(f"Adding YouTube id for: {track}")
            ids.append(video_id)
    return ids


def fetch_ids(playlist: list) -> list:
    """
     Create a list containing an YouTube ID for each track in the given playlist **without** using YouTube API.
     :param playlist: list of str. List of tracks formatted as '<artist> - <track>'.
     :return: list of str. List of YouTube IDs.
     """
    ids = []
    for track in playlist:
        page = requests.get(f"https://www.youtube.com/results?search_query={track}")
        page.raise_for_status()
        parsed_page = bs4.BeautifulSoup(page.content, "html.parser")
        link = parsed_page.find("a", attrs={"dir": "ltr", "title": re.compile(r".*?")})
        if link is not None:
            logging.info(f"Adding YouTube id for: {track}")
            ids.append(link["href"][9:])
    return ids


def get_name(keyphrase: str) -> str:
    """
    Get corrected artist name from Last.fm.
    :param keyphrase: Name of an artist or a band.
    :return: Corrected artist name.
    >>> get_name('norvana')
    'Nirvana'
    """
    try:
        name = get_bio_api(keyphrase, name_only=True)
    except Exception as e:
        logging.debug(
            f"An error occurred while fetching artist name via Last.fm API: {e}. Proceeding without API."
        )
        name = get_bio(keyphrase, name_only=True)
    return name


def get_info(keyphrase: str) -> str:
    """
    Get information about the given artist from Last.fm.
    :param keyphrase: Name of an artist or a band.
    :return: Information about the artist.
    """
    try:
        info = get_bio_api(keyphrase)
    except Exception as e:
        logging.debug(
            f"An error occurred while fetching artist bio via Last.fm API: {e}. Proceeding without API."
        )
        info = get_bio(keyphrase)
    return info


def get_bio_api(keyphrase: str, name_only: bool = False) -> str:
    """
    Collect a correct name and short bio of the given artist using Last.fm API.
    :param keyphrase: Name of an artist or a band.
    :param name_only: Switch between returns.
    :return: Either just a name of an artist or their short bio.
    """
    res = requests.get(
        f"http://ws.audioscrobbler.com/2.0/?method=artist.getinfo&artist={keyphrase}&autocorrect[1]&api_key={lastfm_api}&format=json"
    )
    res.raise_for_status()
    soup = bs4.BeautifulSoup(res.content, "lxml")
    soup_dict = json.loads(soup.text)
    name = soup_dict["artist"]["name"]
    if name_only:
        return name
    else:
        logging.info(f"Collecting short bio for {name} using Last.fm API.")
        summary = soup_dict["artist"]["bio"]["summary"][:-21]
        tags = soup_dict["artist"]["tags"]["tag"]
        tags = ", ".join([tags[i]["name"] for i in range(len(tags))])
        link = soup_dict["artist"]["url"]
        bio = f"{summary}\nTags: {tags}\nRead more: {link}"
        return bio


def get_bio(keyphrase: str, name_only: bool = False) -> str:
    """
    Collect a correct name and short bio of the given artist **without** using Last.fm API.
    :param keyphrase: Name of an artist or a band.
    :param name_only: Switch between returns.
    :return: Either just a name of an artist or their short bio.
    """
    res = requests.get(f"https://www.last.fm/music/{keyphrase}/+wiki")
    res.raise_for_status()
    soup = bs4.BeautifulSoup(res.content, "lxml")
    name = soup.find("h1", attrs={"class": "header-new-title"}).text.strip()
    if name_only:
        return name
    else:
        logging.info(f"Collecting short bio for {name} without Last.fm API.")
        summary = soup.find("div", attrs={"class": "wiki-content"}).text.strip()[:600]
        link = f"https://www.last.fm/music/{name}"
        bio = f"{summary}...\nRead more: {link}"
        return bio
