import os


if (
    "TTBOT_LASTFM_API_KEY" not in os.environ
    or "TTBOT_YOUTUBE_API_KEY" not in os.environ
):
    dotenv_path = "../.env"
    if os.path.exists(dotenv_path):
        import dotenv

        dotenv.load_dotenv("../.env")
    else:
        raise RuntimeError(".env file is missing at the root of the repository")
