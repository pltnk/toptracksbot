import os


REQUIRED_ENV_VARS = ("TTBOT_TOKEN", "TTBOT_LASTFM_API_KEY", "TTBOT_YOUTUBE_API_KEY")


def test_required_env_vars():
    assert all(var in os.environ for var in REQUIRED_ENV_VARS)
