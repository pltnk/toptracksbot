import os

BOT_TOKEN = os.environ["TTBOT_TOKEN"]
LASTFM_API_KEY = os.environ["TTBOT_LASTFM_API_KEY"]
YOUTUBE_API_KEY = os.environ["TTBOT_YOUTUBE_API_KEY"]
DATABASE_URI = os.getenv(
    "TTBOT_DATABASE_URI",
    f"postgres://{os.getenv('TTBOT_DATABASE_USER')}:{os.getenv('TTBOT_DATABASE_PASS')}@db/toptracksbot",
)
DBCONN_RETRIES = int(os.getenv("TTBOT_DBCONN_RETRIES", 5))
DBCONN_TIMEOUT = int(os.getenv("TTBOT_DBCONN_TIMEOUT", 5))
VALID_FOR_DAYS = int(os.getenv("TTBOT_VALID_FOR_DAYS", 30))
BOT_MODE = os.getenv("TTBOT_MODE", "dev")
WEBHOOK_PORT = int(os.getenv("TTBOT_WEBHOOK_PORT", "8443"))
HEROKU_APP = os.getenv("TTBOT_HEROKU_APP", "")
