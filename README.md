# Top Tracks Bot for Telegram
[![Telegram](https://img.shields.io/badge/telegram-%40toptracksbot-informational)](https://t.me/toptracksbot)
[![Build Status](https://img.shields.io/github/workflow/status/pltnk/toptracksbot/Run%20tests)](https://github.com/pltnk/toptracksbot/actions/workflows/run-tests.yml)
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/cae4d1afa23240e1a7ca996f7b0d92b8)](https://www.codacy.com/gh/pltnk/toptracksbot/dashboard)
[![codecov](https://codecov.io/gh/pltnk/toptracksbot/branch/main/graph/badge.svg?token=8K09IYN9SR)](https://codecov.io/gh/pltnk/toptracksbot)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License](https://img.shields.io/github/license/pltnk/top_tracks)](https://choosealicense.com/licenses/mit/)

This bot fetches video from YouTube for the top three tracks of all time by specified artist according to Last.fm charts.

The bot is deployed on Heroku and you can try it in Telegram: [@toptracksbot](http://t.me/toptracksbot)

## Usage

Just send an artist or a band name to the bot to get their top three tracks.

#### Available commands

- `/info artist_name` or `/i artist_name` - get a short bio of an artist
- `/help` or `/h` - show help message

#### Video preview

https://user-images.githubusercontent.com/807774/126999133-1e5ccd79-fcbf-4038-8c8f-1003cc7e4770.mp4

## Deployment

You can deploy this bot yourself using Docker and docker-compose.
1. Install [Docker](https://docs.docker.com/get-docker/) and [docker-compose](https://docs.docker.com/compose/install/)
2. Clone this repository
3. Create `.env` file at the root of cloned repo with the following variables declared there:
   
   Required:
   - `TTBOT_TOKEN` - Auth token of your Telegram bot ([how to get](https://core.telegram.org/bots#3-how-do-i-create-a-bot))
   - `TTBOT_LASTFM_API_KEY` - Key for Last.fm API ([how to get](https://www.last.fm/api))
   - `TTBOT_YOUTUBE_API_KEY` - Key for YouTube API ([how to get](https://developers.google.com/youtube/v3/getting-started))
   
   Optional:
   - `TTBOT_DATABASE_USER` - Set a username for the database (default `toptracks`)
   - `TTBOT_DATABASE_PASS` - Set a password for the database (default `toptracks`)
   - `TTBOT_DATABASE_PORT` - Set a port for the database (default `5432`)
   - `TTBOT_VALID_FOR_DAYS` - Number of days for which information about the artist's top three tracks is cached in the database (default `30`)
    
   Check an [example of `.env` file](./.env_example).
4. Run tests using command `docker-compose run --rm tests || sleep 5 && docker-compose rm -s -f test_db && docker image rm -f toptracksbot_tests` (this will run tests in a container and remove test containers and images after)
5. Start the bot using command `docker-compose up -d` (this will build images for the bot, database and start containers with them)

## Built With
* [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) - This library provides a pure Python interface for the Telegram Bot API.
* [HTTPX](https://github.com/encode/httpx) - Fully featured HTTP client for Python 3, which provides sync and async APIs, and support for both HTTP/1.1 and HTTP/2.
* [asyncpg](https://github.com/MagicStack/asyncpg) - A fast PostgreSQL Database Client Library for Python/asyncio.
* [Beautiful Soup 4](https://www.crummy.com/software/BeautifulSoup/) - Beautiful Soup is a library that makes it easy to scrape information from web pages. 

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
