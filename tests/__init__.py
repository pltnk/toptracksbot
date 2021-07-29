import os


if (
    "TTBOT_LASTFM_API_KEY" not in os.environ
    or "TTBOT_YOUTUBE_API_KEY" not in os.environ
):
    import dotenv

    dotenv.load_dotenv("../.env")
