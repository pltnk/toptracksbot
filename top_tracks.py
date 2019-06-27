import requests, bs4, json, webbrowser, re
from flask import Flask
    

def get_playlist_api(keyphrase):
    res = requests.get(f'http://ws.audioscrobbler.com/2.0/?method=artist.gettoptracks&artist={keyphrase}&limit=10&autocorrect[1]&api_key={lastfm_api}')
    res.raise_for_status()
    soup = bs4.BeautifulSoup(res.content, 'lxml')
    artist = soup.find('toptracks').get('artist')
    tracks = soup.find_all('track')
    playlist = [f'{artist} - {tracks[i].find("name").text}' for i in range(min(10, len(tracks)))]
    return playlist


def fetch_ids_api(playlist):
    ids = []
    for item in playlist:
        page = requests.get(f'https://www.googleapis.com/youtube/v3/search?part=snippet&maxResults=1&q={item}&key={youtube_api}')
        page.raise_for_status()
        parsed_page = bs4.BeautifulSoup(page.content, 'lxml')
        video_id = json.loads(parsed_page.text)['items'][0]['id']['videoId']
        if video_id is not None:
            print(f'Adding YouTube id for: {item}')
            ids.append(video_id)
    return ids


def get_playlist(keyphrase):
    res = requests.get(f'https://www.last.fm/ru/music/{keyphrase}/+tracks?date_preset=ALL')
    res.raise_for_status()
    soup = bs4.BeautifulSoup(res.content, 'lxml')
    links = soup.find_all('a', attrs={'class': 'link-block-target', 'title': re.compile(r'.*?')})
    playlist = [f'{keyphrase} - {links[i].get("title")}' for i in range(min(10, len(links)))]
    return playlist


def fetch_ids(playlist):
    ids = []
    for item in playlist:
        page = requests.get(f'https://www.youtube.com/results?search_query={item}')
        page.raise_for_status()
        parsed_page = bs4.BeautifulSoup(page.content, 'html.parser')
        link = parsed_page.find('a', attrs={'dir': 'ltr', 'title': re.compile(r'.*?')})
        if link is not None:
            print(f'Adding YouTube id for: {item}')
            ids.append(link['href'][9:])
    return ids


app = Flask(__name__)

# todo: generate homepage based on len(yt_ids)
@app.route('/')
def homepage():
    return f"""

    <center>
    <iframe src="https://www.youtube.com/embed/{yt_ids[0]}" width="300" height="200" frameborder="0" allowfullscreen></iframe>
    <iframe src="https://www.youtube.com/embed/{yt_ids[1]}" width="300" height="200" frameborder="0" allowfullscreen></iframe>
    <iframe src="https://www.youtube.com/embed/{yt_ids[2]}" width="300" height="200" frameborder="0" allowfullscreen></iframe>
    <iframe src="https://www.youtube.com/embed/{yt_ids[3]}" width="300" height="200" frameborder="0" allowfullscreen></iframe>
    <iframe src="https://www.youtube.com/embed/{yt_ids[4]}" width="300" height="200" frameborder="0" allowfullscreen></iframe>
    </center>
    <center>
    <iframe src="https://www.youtube.com/embed/{yt_ids[5]}" width="300" height="200" frameborder="0" allowfullscreen></iframe>
    <iframe src="https://www.youtube.com/embed/{yt_ids[6]}" width="300" height="200" frameborder="0" allowfullscreen></iframe>
    <iframe src="https://www.youtube.com/embed/{yt_ids[7]}" width="300" height="200" frameborder="0" allowfullscreen></iframe>
    <iframe src="https://www.youtube.com/embed/{yt_ids[8]}" width="300" height="200" frameborder="0" allowfullscreen></iframe>
    <iframe src="https://www.youtube.com/embed/{yt_ids[9]}" width="300" height="200" frameborder="0" allowfullscreen></iframe>
    </center>
    """


if __name__ == '__main__':
    keyphrase = input('Enter an artist or a band: ')
    try:
        with open('api_keys.txt', 'r') as ak:
            keys = ak.readlines()
            lastfm_api = keys[0].strip()
            youtube_api = keys[1].strip()
        yt_ids = fetch_ids_api(get_playlist_api(keyphrase))
    except Exception as e:
        print(e)
        print('Proceeding without API.')
        yt_ids = fetch_ids(get_playlist(keyphrase))
    webbrowser.open('http://127.0.0.1:5000/')
    app.run()
